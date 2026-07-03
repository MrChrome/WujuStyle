"""Scoreboard API for wujustyle.com (Master Yi: The Wuju Bladesman).

Routes (proxied through CloudFront /api/*):
  POST /api/session  -> issue a single-use game-session token
  GET  /api/scores   -> top 10 global scores
  POST /api/scores   -> submit {token, name, score, wave}

Anti-fraud:
  - score must be achievable for the wave reached (mirrors game constants)
  - session token is single-use and enforces a minimum real elapsed time
  - per-IP daily submission cap
The wave/score/timing formulas MUST stay in sync with index.html.
"""
import hashlib
import json
import os
import re
import time
import uuid

import boto3
from boto3.dynamodb.conditions import Key

TABLE = boto3.resource("dynamodb").Table(os.environ["TABLE"])
DAILY_IP_CAP = 20
SESSION_MAX_AGE = 7200

NAME_RE = re.compile(r"^[A-Z]{3}$")
NAME_BLOCKLIST = {"ASS", "FUK", "FUC", "FCK", "SHT", "CNT", "DIK", "COK", "FAG", "NIG", "KKK"}


def wave_is_boss(w):
    return w % 4 == 0


def scout_count(w):
    return min(2 + w // 2, 8) if wave_is_boss(w) else min(3 + w, 12)


def max_score(reached_wave):
    total = 0
    for w in range(1, reached_wave + 1):
        total += scout_count(w) * (100 + 10 * w)
        if wave_is_boss(w):
            total += 1000
    return total


def min_elapsed(reached_wave):
    # Completed waves only (player may die instantly in the reached wave).
    # Per wave: 1.8s intro + 0.4s first spawn + stagger to the last spawn.
    t = 0.0
    for w in range(1, reached_wave):
        n = scout_count(w) + (1 if wave_is_boss(w) else 0)
        t += 1.8 + 0.4 + (n - 1) * max(0.5, 1.4 - 0.05 * w)
    return 0.8 * t  # safety margin for clock skew


def resp(code, body):
    return {
        "statusCode": code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, _ctx):
    http = event["requestContext"]["http"]
    route = http["method"] + " " + event["rawPath"]
    ip = http.get("sourceIp", "0.0.0.0")
    now = int(time.time())

    if route == "POST /api/session":
        token = uuid.uuid4().hex
        TABLE.put_item(Item={
            "board": "session", "rank": token,
            "createdAt": now, "ttl": now + SESSION_MAX_AGE,
        })
        return resp(200, {"token": token})

    if route == "GET /api/scores":
        q = TABLE.query(KeyConditionExpression=Key("board").eq("global"), Limit=10)
        scores = [
            {"name": i["name"], "score": int(i["score"]), "wave": int(i["wave"])}
            for i in q["Items"]
        ]
        return resp(200, {"scores": scores})

    if route == "POST /api/scores":
        try:
            body = json.loads(event.get("body") or "{}")
            token = str(body.get("token", ""))
            name = str(body.get("name", "")).upper()
            score = int(body.get("score"))
            wave = int(body.get("wave"))
        except (ValueError, TypeError):
            return resp(400, {"error": "bad request"})

        if not NAME_RE.match(name) or name in NAME_BLOCKLIST:
            return resp(400, {"error": "bad name"})
        if not (1 <= wave <= 80) or not (0 < score <= max_score(wave)):
            return resp(400, {"error": "implausible score"})
        if not re.match(r"^[0-9a-f]{32}$", token):
            return resp(403, {"error": "bad session"})

        # per-IP daily cap
        day = time.strftime("%Y-%m-%d", time.gmtime())
        iph = hashlib.sha256(ip.encode()).hexdigest()[:16]
        counter = TABLE.update_item(
            Key={"board": "ip#" + day, "rank": iph},
            UpdateExpression="ADD #c :one SET #t = if_not_exists(#t, :exp)",
            ExpressionAttributeNames={"#c": "count", "#t": "ttl"},
            ExpressionAttributeValues={":one": 1, ":exp": now + 172800},
            ReturnValues="UPDATED_NEW",
        )
        if int(counter["Attributes"]["count"]) > DAILY_IP_CAP:
            return resp(429, {"error": "daily limit"})

        # single-use session token, atomically marked as spent
        try:
            session = TABLE.update_item(
                Key={"board": "session", "rank": token},
                UpdateExpression="SET usedAt = :now",
                ConditionExpression="attribute_exists(createdAt) AND attribute_not_exists(usedAt)",
                ExpressionAttributeValues={":now": now},
                ReturnValues="ALL_NEW",
            )
        except TABLE.meta.client.exceptions.ConditionalCheckFailedException:
            return resp(403, {"error": "bad session"})

        elapsed = now - int(session["Attributes"]["createdAt"])
        if elapsed < min_elapsed(wave) or elapsed > SESSION_MAX_AGE:
            return resp(403, {"error": "implausible timing"})

        inv = str(999999999 - score).zfill(9)
        TABLE.put_item(Item={
            "board": "global",
            "rank": inv + "#" + str(now) + "#" + iph[:6],
            "name": name, "score": score, "wave": wave,
            "ts": now, "ip": iph,
            "ua": (event.get("headers") or {}).get("user-agent", "")[:120],
        })
        return resp(200, {"ok": True})

    return resp(404, {"error": "not found"})

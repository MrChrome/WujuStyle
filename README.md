# Master Yi: The Wuju Bladesman

A browser game styled as a Tiger Electronics LCD handheld. Master Yi defends
the Ionian jungle from waves of dart-blowing Teemos. The entire page is the
green handheld: the game runs on the amber "LCD" screen and the physical
ability buttons show live cooldowns.

**Live site:** https://wujustyle.com (and https://d28r3plj89s9tx.cloudfront.net)

## Gameplay

Yi swings automatically at any Teemo in blade range — you position him and
spend abilities, all based on his real League of Legends kit:

| Ability | Key | Effect |
|---|---|---|
| Double Strike (passive) | — | Every 4th blow lands twice |
| Alpha Strike | Q / button | Blink untargetably through up to 4 Teemos |
| Meditate | W / button | Channel to heal, take 1/3 damage; moving cancels |
| Highlander | R / button | Speed burst; kills extend it and refund 70% of cooldowns |

Teemo fights back with blinding darts (your swings MISS), trapper Teemos plant
poison mushrooms, and every 4th wave the Swift Scout arrives as a boss.
Move with arrow keys / A,D or the on-screen D-pad. Enter starts/pauses,
M toggles sound. Hi-score persists in localStorage. Touch-friendly.

## Project layout

- `index.html` — the whole game (single self-contained file: HTML, CSS, JS, Web Audio)
- `audio/teemo-hut.mp3` — Teemo's "Hut, two, three, four!" voice line (Omega Squad,
  from the League of Legends Wiki), played occasionally while Teemos are on screen
- `deploy.sh` — uploads `index.html` and `audio/` to S3 and invalidates the CloudFront cache
- `aws/` — infrastructure reference (see below)

## Deploying changes

```sh
./deploy.sh
```

Requires AWS CLI credentials for account 104553935045.

## Infrastructure (created 2026-07-02, us-east-1)

| Resource | Value |
|---|---|
| S3 bucket | `wujustyle.com` (private; CloudFront-only via Origin Access Control) |
| CloudFront distribution | `E1CQ5SC9R4MTO` → d28r3plj89s9tx.cloudfront.net |
| Route 53 hosted zone | `Z00693291YUDN6ZFRKXGW` (wujustyle.com) |
| ACM certificate | `beab76b4-32c1-4a2b-bf26-266b13e05e73` (wujustyle.com + www) |

`aws/` files:

- `cloudfront-config.json` — the distribution config used at creation
- `dns-records.json` — Route 53 change batch: ACM validation CNAMEs + A/AAAA
  aliases for apex and www pointing at CloudFront (already applied)
- `attach-cert.sh` — waits for the ACM cert to validate, then attaches the
  cert + domain aliases to the distribution. Run once after the nameserver
  switch below if it hasn't already completed.

### One-time DNS cutover (manual)

The domain is registered at Namecheap. For wujustyle.com to resolve, its
nameservers must point at the Route 53 hosted zone:
Namecheap → Domain List → wujustyle.com → Manage → Nameservers → Custom DNS:

```
ns-1540.awsdns-00.co.uk
ns-1059.awsdns-04.org
ns-739.awsdns-28.net
ns-297.awsdns-37.com
```

After propagation (~15–60 min) the ACM cert validates automatically and
`aws/attach-cert.sh` puts the custom domain live on CloudFront.

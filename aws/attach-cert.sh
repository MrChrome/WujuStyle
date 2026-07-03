#!/bin/bash
# Waits for the ACM cert to be ISSUED (i.e. after nameservers move to Route 53),
# then attaches the cert + wujustyle.com aliases to the CloudFront distribution.
set -e
CERT="arn:aws:acm:us-east-1:104553935045:certificate/beab76b4-32c1-4a2b-bf26-266b13e05e73"
DIST="E1CQ5SC9R4MTO"
DIR="$(cd "$(dirname "$0")" && pwd)"

for i in $(seq 1 360); do
  STATUS=$(aws acm describe-certificate --certificate-arn "$CERT" --region us-east-1 \
    --query Certificate.Status --output text)
  echo "[$i] cert status: $STATUS"
  if [ "$STATUS" = "ISSUED" ]; then
    aws cloudfront get-distribution-config --id "$DIST" --output json > "$DIR/dist-current.json"
    ETAG=$(python3 - "$DIR/dist-current.json" "$DIR/dist-updated.json" "$CERT" <<'PY'
import json, sys
src, out, cert = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(src))
cfg = d["DistributionConfig"]
cfg["Aliases"] = {"Quantity": 2, "Items": ["wujustyle.com", "www.wujustyle.com"]}
cfg["ViewerCertificate"] = {
    "ACMCertificateArn": cert,
    "Certificate": cert,
    "CertificateSource": "acm",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021",
}
json.dump(cfg, open(out, "w"))
print(d["ETag"])
PY
)
    aws cloudfront update-distribution --id "$DIST" --if-match "$ETAG" \
      --distribution-config "file://$DIR/dist-updated.json" \
      --query 'Distribution.Status' --output text
    echo "SUCCESS: certificate + aliases attached to $DIST"
    exit 0
  fi
  sleep 60
done
echo "TIMEOUT: cert not issued after 6h — run this script again after switching nameservers"
exit 1

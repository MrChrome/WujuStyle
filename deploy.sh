#!/bin/bash
# Deploy index.html to S3 and invalidate the CloudFront cache.
set -euo pipefail
cd "$(dirname "$0")"

BUCKET="wujustyle.com"
DISTRIBUTION="E1CQ5SC9R4MTO"

aws s3 cp index.html "s3://$BUCKET/index.html" \
  --content-type "text/html; charset=utf-8" \
  --cache-control "public, max-age=300"

aws s3 sync audio "s3://$BUCKET/audio" \
  --cache-control "public, max-age=86400"

aws s3 sync img "s3://$BUCKET/img" \
  --cache-control "public, max-age=86400"

aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION" \
  --paths "/index.html" "/" \
  --query 'Invalidation.{Id:Id,Status:Status}' --output table

echo "Deployed:"
echo "  https://wujustyle.com          (once nameservers point to Route 53)"
echo "  https://d28r3plj89s9tx.cloudfront.net"

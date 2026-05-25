#!/bin/bash
# garage_buckets.sh — Garage bucket listing via AWS CLI
# Output: {"buckets": ["bucket1", ...]} — valid JSON
# Sources /etc/garage/garage.env for credentials, overrides ~/.aws to avoid real AWS key interference.

if [ -f /etc/garage/garage.env ]; then
    set -a
    source /etc/garage/garage.env
    export AWS_ACCESS_KEY_ID="$GARAGE_ACCESS_KEY_ID"
    export AWS_SECRET_ACCESS_KEY="$GARAGE_SECRET_ACCESS_KEY"
    set +a
    export AWS_CONFIG_FILE=/dev/null
    export AWS_DEFAULT_REGION=garage
else
    echo '{"buckets":[]}'
    exit 0
fi

if command -v aws &>/dev/null; then
    buckets=$(AWS_CONFIG_FILE=/dev/null AWS_DEFAULT_REGION=garage \
        aws s3 ls --endpoint-url "${AWS_ENDPOINT_URL:-http://localhost:3900}" 2>/dev/null \
        | awk '{print $NF}' \
        | python3 -c "import sys,json; print(json.dumps([b.strip() for b in sys.stdin.read().splitlines() if b.strip()]))" 2>/dev/null || echo "[]")
    echo "{\"buckets\":$buckets}"
else
    echo '{"buckets":[]}'
fi

#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/allaun/Research Stack/4-Infrastructure/infra/ene-rds"
BIN="${ENE_API_BIN:-$ROOT/target/release/ene-api}"

if [[ ! -x "$BIN" ]]; then
  BIN="$ROOT/target/debug/ene-api"
fi

if [[ ! -x "$BIN" ]]; then
  echo "ene-api binary not found; run: cargo build --release -p ene-api" >&2
  exit 127
fi

export AWS_REGION="${AWS_REGION:-us-east-1}"
export RDS_HOST="${RDS_HOST:-database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com}"
export RDS_PORT="${RDS_PORT:-5432}"
export RDS_USER="${RDS_USER:-postgres}"
export RDS_DB="${RDS_DB:-postgres}"
export ENE_API_BIND="${ENE_API_BIND:-0.0.0.0:3000}"

if [[ -z "${RDS_IAM_TOKEN:-}" && -z "${RDS_PASSWORD:-}" ]]; then
  export RDS_IAM_TOKEN="$(
    aws rds generate-db-auth-token \
      --hostname "$RDS_HOST" \
      --port "$RDS_PORT" \
      --username "$RDS_USER" \
      --region "$AWS_REGION"
  )"
fi

cd "$ROOT"
exec "$BIN"

#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
LOCAL_GITLEAKS="$ROOT_DIR/.tools/bin/gitleaks"

if [ -x "$LOCAL_GITLEAKS" ]; then
    GITLEAKS_BIN="$LOCAL_GITLEAKS"
elif command -v gitleaks >/dev/null 2>&1; then
    GITLEAKS_BIN=$(command -v gitleaks)
else
    echo "gitleaks is not installed." >&2
    echo "Bootstrap it with: sh scripts/bootstrap_gitleaks_linux.sh" >&2
    exit 127
fi

exec "$GITLEAKS_BIN" detect \
    --source "$ROOT_DIR" \
    --config "$ROOT_DIR/.gitleaks.toml" \
    --no-banner


#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REMOTE="${1:-forgejo/main}"
DATE_STAMP="$(date +%F)"
OUT_DIR="artifacts/gdrive_refill"
mkdir -p "$OUT_DIR"

echo "[1/5] Fetching Forgejo..."
git fetch forgejo --prune

REV="$(git rev-parse --short=12 "$REMOTE")"
ARCHIVE="$OUT_DIR/research-stack-forgejo-main-${REV}.tar.zst"

echo "[2/5] Building clean archive from $REMOTE ($REV)..."
if [[ ! -f "$ARCHIVE" ]]; then
  if command -v zstd >/dev/null 2>&1; then
    git archive --format=tar --prefix="research-stack-forgejo-main-${REV}/" "$REMOTE" \
      | zstd -T0 -3 -o "$ARCHIVE"
  else
    ARCHIVE="$OUT_DIR/research-stack-forgejo-main-${REV}.tar.gz"
    git archive --format=tar --prefix="research-stack-forgejo-main-${REV}/" "$REMOTE" \
      | gzip -6 > "$ARCHIVE"
  fi
fi

echo "[3/5] Writing checksum and manifest..."
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
FILES="$(git ls-tree -r --name-only "$REMOTE" | wc -l)"
BYTES="$(git ls-tree -r -l "$REMOTE" | awk '{s += $4} END {print s}')"
SHA="$(cut -d' ' -f1 "$ARCHIVE.sha256")"
cat > "$OUT_DIR/REFILL_MANIFEST.md" <<EOF
# Google Drive Refill Manifest

Generated: $(date -Iseconds)
Source remote: $REMOTE
Source commit: $(git rev-parse "$REMOTE")
Tracked files: $FILES
Tracked bytes: $BYTES
Archive: $ARCHIVE
Archive SHA-256: $SHA

## Upload Target

\`\`\`bash
rclone copy artifacts/gdrive_refill Gdrive:topological_storage/research-stack/forgejo-refill/$DATE_STAMP/ --progress --checksum
\`\`\`
EOF

echo "[4/5] Checking Gdrive rclone access..."
if ! rclone lsf Gdrive: >/dev/null 2>&1; then
  echo "Gdrive: is not authenticated."
  echo "Run: rclone config reconnect Gdrive:"
  echo "Then rerun: bash scripts/refill_gdrive_from_forgejo.sh"
  exit 2
fi

echo "[5/5] Uploading refill bundle to Google Drive..."
rclone copy "$OUT_DIR" "Gdrive:topological_storage/research-stack/forgejo-refill/$DATE_STAMP/" \
  --progress \
  --checksum

echo "Done. Uploaded $OUT_DIR to Gdrive:topological_storage/research-stack/forgejo-refill/$DATE_STAMP/"

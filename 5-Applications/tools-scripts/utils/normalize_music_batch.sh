#!/usr/bin/env bash
# normalize_music_batch.sh — Batch FLAC genre normalization via rclone
#
# Downloads a batch of music from GDrive, runs normalize_flac_genres.py --fix,
# re-uploads only changed files, then cleans the local batch.
#
# Usage:
#   ./normalize_music_batch.sh [--dry-run] [ARTIST_PREFIX]
#
# Examples:
#   ./normalize_music_batch.sh               # all artists
#   ./normalize_music_batch.sh "Disturbed"   # single artist
#   ./normalize_music_batch.sh --dry-run     # audit only, no re-upload

set -euo pipefail

GDRIVE_ROOT="Gdrive:RELAXATION/music"
LOCAL_BATCH="/tmp/music_batch_$$"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NORMALIZER="$SCRIPT_DIR/normalize_flac_genres.py"

DRY_RUN=false
ARTIST_FILTER=""

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        *) ARTIST_FILTER="$arg" ;;
    esac
done

REMOTE_PATH="$GDRIVE_ROOT${ARTIST_FILTER:+/$ARTIST_FILTER}"

echo "=== FLAC Genre Normalization Batch ==="
echo "  Source : $REMOTE_PATH"
echo "  DryRun : $DRY_RUN"
echo ""

echo "Downloading..."
mkdir -p "$LOCAL_BATCH"
rclone copy "$REMOTE_PATH" "$LOCAL_BATCH" \
    --include "*.flac" \
    --progress \
    2>&1

TRACK_COUNT=$(find "$LOCAL_BATCH" -name "*.flac" | wc -l)
echo "Downloaded $TRACK_COUNT tracks"
echo ""

echo "Auditing..."
REPORT="$LOCAL_BATCH/audit_before.json"
python3 "$NORMALIZER" "$LOCAL_BATCH" --report "$REPORT" 2>&1 | grep -E "^WARN|^===|Scanned|normalize|non_ascii|multi_value|missing"

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "DRY RUN — no changes written. Re-run without --dry-run to fix."
    rm -rf "$LOCAL_BATCH"
    exit 0
fi

echo ""
echo "Fixing..."
python3 "$NORMALIZER" "$LOCAL_BATCH" --fix 2>&1 | grep -E "^FIX|^==="

echo ""
echo "Re-uploading changed files..."
rclone copy "$LOCAL_BATCH" "$REMOTE_PATH" \
    --include "*.flac" \
    --checksum \
    --progress \
    2>&1

echo ""
echo "Cleaning local batch..."
rm -rf "$LOCAL_BATCH"
echo "Done."

#!/run/current-system/sw/bin/bash
set -euo pipefail

BACKUP_DIR="${1:-/var/lib/backups/appflowy}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "${BACKUP_DIR}" 2>/dev/null || true

PODMAN="/run/current-system/sw/bin/podman"
PGDUMP="/usr/lib/postgresql/16/bin/pg_dump"
CAT="/run/current-system/sw/bin/cat"
GREP="/run/current-system/sw/bin/grep"
GZIP="/run/current-system/sw/bin/gzip"
WC="/run/current-system/sw/bin/wc"
RM="/run/current-system/sw/bin/rm"
LS="/run/current-system/sw/bin/ls"
XARGS="/run/current-system/sw/bin/xargs"

echo "Backing up AppFlowy postgres to ${BACKUP_DIR}..."
$PODMAN exec appflowy-cloud_postgres_1 $PGDUMP \
  -U postgres -d appflowy 2>/dev/null | \
  $GREP -v '^\\restrict \|^\\unrestrict ' > "${BACKUP_DIR}/appflowy-${TIMESTAMP}.sql"

BYTES=$($WC -c < "${BACKUP_DIR}/appflowy-${TIMESTAMP}.sql")
echo "Saved: ${BACKUP_DIR}/appflowy-${TIMESTAMP}.sql (${BYTES} bytes)"
$GZIP -f "${BACKUP_DIR}/appflowy-${TIMESTAMP}.sql"
$LS -lh "${BACKUP_DIR}/appflowy-${TIMESTAMP}.sql.gz"

$LS -t "${BACKUP_DIR}/appflowy-"*.sql.gz 2>/dev/null | $XARGS -r $RM 2>/dev/null; true

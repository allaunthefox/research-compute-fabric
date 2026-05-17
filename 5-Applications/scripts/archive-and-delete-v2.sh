#!/bin/bash
# Final GitHub Cleanup Script - v2
# Hides standalone repos from profile and/or deletes them.

set -e

REPOS=(
    "braid-field-papers"
    "AMMR"
    "bezier-kit"
    "Newtonian-Superfluid-Simulation"
    "heat-2D"
    "chunked-audio-DSP"
    "matter-frequencies"
    "Allelica"
    "parametric-learn"
    "text-to-cad"
    "WasmGPU"
    "OTOM"
    "NoDupeLabs"
)

echo "=== Research Stack: GitHub Cleanup ==="
echo "This will archive (hide) and optionally delete the following repos:"
for repo in "${REPOS[@]}"; do echo "  - allaunthefox/$repo"; done

echo ""
read -p "Do you want to PERMANENTLY DELETE these repos? (type DELETE to confirm, otherwise they will only be ARCHIVED): " ACTION

if [ "$ACTION" == "DELETE" ]; then
    echo "Requesting delete_repo scope..."
    gh auth refresh -h github.com -s delete_repo
fi

for repo in "${REPOS[@]}"; do
    echo "--- allaunthefox/$repo ---"

    # Always archive first to be safe
    echo "  Archiving..."
    gh repo archive "allaunthefox/$repo" --yes || echo "  Already archived or missing."

    if [ "$ACTION" == "DELETE" ]; then
        echo "  Deleting..."
        gh repo delete "allaunthefox/$repo" --yes || echo "  Failed to delete. Check permissions."
    fi
done

echo ""
echo "Done. Your GitHub profile should now be focused on the Research-Stack umbrella."

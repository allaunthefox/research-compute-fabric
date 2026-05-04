#!/bin/bash
# Sovereign Stack: Forensic Integrity Manifest Generator
# Purpose: Generate a canonical SHA256 manifest of a directory for future audit.

if [ -z "$1" ]; then
    echo "Usage: $0 <target_directory_or_zip>"
    exit 1
fi

TARGET=$1
OUTPUT="forensic_manifest_$(date +%Y%m%d_%H%M%S).txt"

echo "[*] Generating forensic manifest for: $TARGET"
echo "[*] Output file: $OUTPUT"

# Find files, calculate SHA256, and format as: HASH  FILE
find "$TARGET" -type f -exec sha256sum {} + | sort -k 2 > "$OUTPUT"

echo "[*] Manifest complete. Total files hashed: $(wc -l < "$OUTPUT")"
echo "[*] Recommended: Sign this manifest with your private key or store in the Sovereign Stack out/ directory."

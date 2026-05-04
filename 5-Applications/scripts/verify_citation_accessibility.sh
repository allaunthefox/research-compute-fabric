#!/bin/bash
# Citation Accessibility Verification
# Checks HTTP/HTTPS URLs in markdown files for accessibility

set -e

REPO_ROOT="/home/allaun/Research Stack"
REPORT_DIR="$REPO_ROOT/docs/provenance"
REPORT_FILE="$REPORT_DIR/citation_accessibility_report_$(date +%Y%m%d).txt"

mkdir -p "$REPORT_DIR"

echo "Citation Accessibility Verification Report" > "$REPORT_FILE"
echo "Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$REPORT_FILE"
echo "=========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Find all HTTP/HTTPS URLs in markdown files
echo "Extracting URLs from markdown files..." >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Extract URLs from docs directory
urls=$(grep -r -h -o 'https\?://[^ )"]*' "$REPO_ROOT/docs"/*.md 2>/dev/null | sort -u)

if [ -z "$urls" ]; then
    echo "No URLs found in markdown files." >> "$REPORT_FILE"
else
    echo "Found URLs:" >> "$REPORT_FILE"
    echo "$urls" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    echo "Checking accessibility..." >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    for url in $urls; do
        echo "Checking: $url" >> "$REPORT_FILE"
        # Use curl with timeout to check if URL is accessible
        # -s: silent mode
        # -o /dev/null: discard output
        # -w "%{http_code}": output HTTP status code
        # -L: follow redirects
        # --max-time 10: timeout after 10 seconds
        status=$(curl -s -o /dev/null -w "%{http_code}" -L --max-time 10 "$url" 2>/dev/null || echo "000")
        
        if [ "$status" = "200" ] || [ "$status" = "301" ] || [ "$status" = "302" ]; then
            echo "  Status: $status - ACCESSIBLE" >> "$REPORT_FILE"
        else
            echo "  Status: $status - NOT ACCESSIBLE" >> "$REPORT_FILE"
        fi
        echo "" >> "$REPORT_FILE"
    done
fi

echo "=========================================" >> "$REPORT_FILE"
echo "Verification complete." >> "$REPORT_FILE"
echo "Report saved to: $REPORT_FILE" >> "$REPORT_FILE"

cat "$REPORT_FILE"

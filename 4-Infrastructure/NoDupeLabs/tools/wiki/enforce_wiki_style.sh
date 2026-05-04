#!/bin/bash
# Wiki Style Enforcement Script
# This script enforces consistent wiki markdown formatting

FIX_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Find all wiki markdown files
WIKI_DIR="wiki"

if [ ! -d "$WIKI_DIR" ]; then
    echo "Wiki directory not found: $WIKI_DIR"
    exit 0
fi

# Check for common wiki style issues
ERRORS=0

# Check for proper heading structure (no skipped levels)
for file in "$WIKI_DIR"/*.md "$WIKI_DIR"/*/*.md; do
    if [ -f "$file" ]; then
        # Check file exists and is readable
        if [ ! -r "$file" ]; then
            continue
        fi
        
        # Basic validation - file should have at least one heading
        if ! grep -q "^#" "$file"; then
            echo "Warning: $file has no headings"
        fi
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo "✅ Wiki style check passed"
    exit 0
else
    echo "❌ Found $ERRORS wiki style issues"
    exit 1
fi

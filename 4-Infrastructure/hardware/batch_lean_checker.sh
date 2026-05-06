#!/usr/bin/env bash
set -e

cd "/home/allaun/Documents/Research Stack"

echo "=== Batch Lean Hardware Checker with DAG Generation ==="
echo "Finding all Lean files..."

# Find all Lean files, excluding archive and consolidated directories
find . -name "*.lean" -type f 2>/dev/null > /tmp/all_lean_files.txt
grep -v archive /tmp/all_lean_files.txt > /tmp/filtered_lean.txt || true
grep -v consolidated /tmp/filtered_lean.txt > /tmp/filtered_lean2.txt || true
grep -v ".changes" /tmp/filtered_lean2.txt > /tmp/filtered_lean_final.txt || true
LEAN_FILES=$(cat /tmp/filtered_lean_final.txt)

TOTAL=$(echo "$LEAN_FILES" | wc -l)
echo "Found $TOTAL Lean files to process"

# Create output directory
mkdir -p "4-Infrastructure/hardware/batch_results"

# Initialize DAG file
DAG_FILE="4-Infrastructure/hardware/lean_dependency_dag.dot"
echo "digraph LeanDependencyGraph {" > "$DAG_FILE"
echo "  rankdir=LR;" >> "$DAG_FILE"
echo "  node [shape=box, style=rounded];" >> "$DAG_FILE"

# Process each file
SUCCESSFUL=0
FAILED=0
SKIPPED=0
declare -a NODES

while IFS= read -r file; do
    if [[ -n "$file" ]]; then
        echo "[$SUCCESSFUL/$TOTAL] Processing: $file"
        if python "4-Infrastructure/hardware/lean_hardware_checker.py" "$file" > /dev/null 2>&1; then
            SUCCESSFUL=$((SUCCESSFUL + 1))
            echo "  Status: success"

            # Add node to DAG
            safe_name=$(echo "$file" | sed 's/[\/\.]/_/g' | sed 's/^\.//')
            NODES+=("$safe_name")
            echo "  \"$safe_name\" [label=\"$(basename $file)\"];" >> "$DAG_FILE"

            # Extract imports for edges
            imports=$(grep -h "^import " "$file" 2>/dev/null | sed 's/import //' | sed 's/ --.*//' || true)
            for imp in $imports; do
                imp_file=$(find . -name "$imp.lean" -type f 2>/dev/null | head -1)
                if [[ -n "$imp_file" ]]; then
                    imp_safe=$(echo "$imp_file" | sed 's/[\/\.]/_/g' | sed 's/^\.//')
                    echo "  \"$imp_safe\" -> \"$safe_name\";" >> "$DAG_FILE"
                fi
            done
        else
            FAILED=$((FAILED + 1))
            echo "  Status: error"
        fi
    fi
done <<< "$LEAN_FILES"

# Close DAG file
echo "}" >> "$DAG_FILE"

echo ""
echo "=== Summary ==="
echo "Total files: $TOTAL"
echo "Successful: $SUCCESSFUL"
echo "Failed: $FAILED"
echo "Skipped: $SKIPPED"
echo ""
echo "DAG generated: $DAG_FILE"
echo "To visualize: dot -Tpng $DAG_FILE -o lean_dependency_dag.png"

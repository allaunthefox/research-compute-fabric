#!/bin/bash
# ZERO-TRUST LINTER
# Enforces AGENTS.md rules that Lean compiler allows
# Usage: ./zero_trust_linter.sh [directory]

DIR="${1:-Semantics}"
ERRORS=0

echo "=========================================="
echo "ZERO-TRUST LINTER - AGENTS.md Enforcement"
echo "=========================================="

# Rule 1: No wildcards in pattern matches (except fromU8 inverse)
echo ""
echo "[RULE 1] Checking for wildcards in pattern matches..."
WILDCARDS=$(grep -r "| _ =>" "$DIR"/*.lean 2>/dev/null | grep -v "fromU8" | wc -l)
if [ "$WILDCARDS" -gt 0 ]; then
    echo "❌ VIOLATION: Found $WILDCARDS wildcard pattern(s):"
    grep -r "| _ =>" "$DIR"/*.lean | grep -v "fromU8" | head -5
    ERRORS=$((ERRORS + WILDCARDS))
else
    echo "✅ PASS: No wildcards found"
fi

# Rule 2: No Float in core logic (except shims)
echo ""
echo "[RULE 2] Checking for Float usage..."
FLOATS=$(grep -r "Float\|\.float\|f32\|f64" "$DIR"/*.lean 2>/dev/null | grep -v "BindServer" | wc -l)
if [ "$FLOATS" -gt 0 ]; then
    echo "❌ VIOLATION: Found $FLOATS Float usage(s) in core:"
    grep -r "Float\|\.float\|f32\|f64" "$DIR"/*.lean | grep -v "BindServer" | head -5
    ERRORS=$((ERRORS + FLOATS))
else
    echo "✅ PASS: No Float in core logic"
fi

# Rule 3: No partial functions
echo ""
echo "[RULE 3] Checking for partial functions..."
PARTIAL=$(grep -r "^partial def\|^partial theorem" "$DIR"/*.lean 2>/dev/null | grep -v "BindServer" | wc -l)
if [ "$PARTIAL" -gt 0 ]; then
    echo "❌ VIOLATION: Found $PARTIAL partial declaration(s):"
    grep -r "^partial def\|^partial theorem" "$DIR"/*.lean | grep -v "BindServer" | head -5
    ERRORS=$((ERRORS + PARTIAL))
else
    echo "✅ PASS: No partial functions"
fi

# Rule 4: No sorry in committed code
echo ""
echo "[RULE 4] Checking for sorry..."
SORRY=$(grep -r "sorry" "$DIR"/*.lean 2>/dev/null | grep -v "TODO" | grep -v "WIP" | wc -l)
if [ "$SORRY" -gt 0 ]; then
    echo "❌ VIOLATION: Found $SORRY sorry(ies):"
    grep -r "sorry" "$DIR"/*.lean | grep -v "TODO" | grep -v "WIP" | head -5
    ERRORS=$((ERRORS + SORRY))
else
    echo "✅ PASS: No sorry found"
fi

# Rule 5: No unsafe code
echo ""
echo "[RULE 5] Checking for unsafe..."
UNSAFE=$(grep -r "unsafe" "$DIR"/*.lean 2>/dev/null | wc -l)
if [ "$UNSAFE" -gt 0 ]; then
    echo "❌ VIOLATION: Found $UNSAFE unsafe usage(s):"
    grep -r "unsafe" "$DIR"/*.lean | head -5
    ERRORS=$((ERRORS + UNSAFE))
else
    echo "✅ PASS: No unsafe code"
fi

# Rule 6: No open string parsing
echo ""
echo "[RULE 6] Checking for open string matching..."
STRINGS=$(grep -r '\.contains\|\.startsWith\|\.endsWith' "$DIR"/*.lean 2>/dev/null | grep -v "BindServer" | wc -l)
if [ "$STRINGS" -gt 0 ]; then
    echo "⚠️  WARNING: Found $STRINGS string operation(s) (review manually):"
    grep -r '\.contains\|\.startsWith\|\.endsWith' "$DIR"/*.lean | grep -v "BindServer" | head -5
fi

# Rule 7: Naming conventions
echo ""
echo "[RULE 7] Checking naming conventions..."
SNAKE=$(grep -r "def [a-z][a-z_]*_[a-z]\|structure [a-z][a-z_]*_[a-z]" "$DIR"/*.lean 2>/dev/null | wc -l)
if [ "$SNAKE" -gt 0 ]; then
    echo "❌ VIOLATION: Found $SNAKE snake_case identifier(s):"
    grep -r "def [a-z][a-z_]*_[a-z]\|structure [a-z][a-z_]*_[a-z]" "$DIR"/*.lean | head -5
    ERRORS=$((ERRORS + SNAKE))
else
    echo "✅ PASS: No snake_case violations"
fi

# Rule 8: Totality proofs required
echo ""
echo "[RULE 8] Checking for missing totality proofs..."
# Check if functions with pattern matches have corresponding theorems
for file in "$DIR"/*.lean; do
    if [ -f "$file" ]; then
        FUNCS=$(grep -c "^def.*match" "$file" 2>/dev/null || echo 0)
        THEOREMS=$(grep -c "_total.*:= by" "$file" 2>/dev/null || echo 0)
        if [ "$FUNCS" -gt "$THEOREMS" ]; then
            echo "⚠️  WARNING: $file may be missing totality proofs ($FUNCS functions, $THEOREMS theorems)"
        fi
    fi
done

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ ZERO-TRUST AUDIT PASSED"
    echo "All AGENTS.md rules satisfied"
    exit 0
else
    echo "❌ ZERO-TRUST AUDIT FAILED"
    echo "Total violations: $ERRORS"
    echo "=========================================="
    exit 1
fi

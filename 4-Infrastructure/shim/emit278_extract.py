#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
emit278_extract.py — run `lake build Semantics.AVMIsa.Emit` and capture the
`#eval emitRrcCorpus278` output, writing it as emit278.json.

Python role: subprocess + I/O only.
Lean role: all alignment-gate, receipt-stamping, and JSON-emission logic.

Usage:
    python3 4-Infrastructure/shim/emit278_extract.py
    python3 4-Infrastructure/shim/emit278_extract.py --out /tmp/emit278.json
    python3 4-Infrastructure/shim/emit278_extract.py --validate-only
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path("/home/allaun/Research Stack")
LEAN_DIR = ROOT / "0-Core-Formalism/lean/Semantics"
DEFAULT_OUT = ROOT / "shared-data/data/stack_solidification/emit278.json"

# The #eval for emitRrcCorpus278 is in AVMIsa/Emit.lean — its info: line
# will contain the string starting with {"schema":"avm_rrc_corpus278_v1",...}
# In the raw lake output the JSON string is Lean-repr-escaped, so quotes appear
# as \" — we search for both forms.
MARKER = 'avm_rrc_corpus278_v1'


def build_and_capture() -> str:
    """Run lake build and return the raw info: line containing MARKER."""
    print("Running: lake build Semantics.AVMIsa.Emit ...", file=sys.stderr)
    result = subprocess.run(
        ["lake", "build", "Semantics.AVMIsa.Emit"],
        cwd=str(LEAN_DIR),
        capture_output=True,
        text=True,
    )
    # lake prints #eval output to stderr as "info: <file>:<line>:<col>: <value>"
    combined = result.stdout + result.stderr
    for line in combined.splitlines():
        if MARKER in line:
            return line
    raise RuntimeError(
        f"MARKER '{MARKER}' not found in lake build output.\n"
        f"Return code: {result.returncode}\n"
        f"Last 20 lines:\n" + "\n".join(combined.splitlines()[-20:])
    )


def extract_json(info_line: str) -> str:
    """
    Strip the `info: <path>:<line>:<col>: ` prefix and outer Lean string quotes,
    then unescape Lean string escapes to produce a raw JSON string.
    """
    # info: Semantics/AVMIsa/Emit.lean:260:0: "{...json...}"
    # We want everything after the last `: ` that starts with `"`
    m = re.search(r'info:.*?:\d+:\d+:\s*(".*)', info_line, re.DOTALL)
    if not m:
        raise RuntimeError(f"Cannot parse info line: {info_line[:200]}")
    quoted = m.group(1).strip()
    # The Lean repr wraps the string in outer quotes and escapes internal quotes.
    # Remove outer quotes and unescape.
    if quoted.startswith('"') and quoted.endswith('"'):
        inner = quoted[1:-1]
    else:
        raise RuntimeError(f"Expected outer quotes in: {quoted[:200]}")
    # Unescape Lean string escapes (only \\ and \" are used in our JSON emitter)
    inner = inner.replace('\\"', '"').replace('\\\\', '\\')
    return inner


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract emit278.json from lake build output")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Output JSON path")
    ap.add_argument("--validate-only", action="store_true",
                    help="Parse and validate JSON only; do not write file")
    args = ap.parse_args()

    info_line = build_and_capture()
    json_str  = extract_json(info_line)

    # Validate JSON
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse failed: {e}", file=sys.stderr)
        print(f"First 500 chars: {json_str[:500]}", file=sys.stderr)
        sys.exit(1)

    # Sanity checks
    schema = parsed.get("schema")
    total  = parsed.get("summary", {}).get("total")
    claim  = parsed.get("claim_boundary")
    print(f"schema            : {schema}", file=sys.stderr)
    print(f"total_rows        : {total}", file=sys.stderr)
    print(f"claim_boundary    : {claim}", file=sys.stderr)
    print(f"avm_canaries_pass : {parsed.get('avm_canaries_passed')}", file=sys.stderr)
    print(f"bundle_receipt_ok : {parsed.get('bundle_receipt_valid')}", file=sys.stderr)
    rows_val  = parsed.get("rows", [])
    row_count = len(rows_val) if isinstance(rows_val, list) else \
                len(rows_val.get("rows", [])) if isinstance(rows_val, dict) else -1
    print(f"rows in JSON      : {row_count}", file=sys.stderr)

    if schema != "avm_rrc_corpus278_v1":
        print(f"ERROR: unexpected schema '{schema}'", file=sys.stderr)
        sys.exit(1)
    if total != 278 or row_count != 278:
        print(f"ERROR: expected 278 rows, got total={total}, rows={row_count}", file=sys.stderr)
        sys.exit(1)

    if args.validate_only:
        print("Validation OK (--validate-only; file not written)", file=sys.stderr)
        return

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(parsed, indent=2))
    print(f"Wrote {out}", file=sys.stderr)
    print(f"Validation: python3 -m json.tool {out} > /dev/null", file=sys.stderr)
    # Final python3 -m json.tool validation
    check = subprocess.run(
        ["python3", "-m", "json.tool", str(out)],
        capture_output=True, text=True
    )
    if check.returncode != 0:
        print(f"ERROR: json.tool validation failed:\n{check.stderr}", file=sys.stderr)
        sys.exit(1)
    print("json.tool validation PASSED", file=sys.stderr)


if __name__ == "__main__":
    main()

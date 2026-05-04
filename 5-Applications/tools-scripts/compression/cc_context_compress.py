#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Claude Code context compressor.

Preprocesses file content through the context gate before it enters
Claude Code's context window.  Prefers substrate cache and hyperlut
surfaces over raw token ingestion.

Usage:
    # Compress a file for context ingestion:
    python 5-Applications/scripts/cc_context_compress.py read /path/to/file.py

    # Compress arbitrary text:
    echo "sensitive payload" | python 5-Applications/scripts/cc_context_compress.py stdin

    # Check cache stats:
    python 5-Applications/scripts/cc_context_compress.py stats

    # Pre-warm cache for a directory:
    python 5-Applications/scripts/cc_context_compress.py warm /path/to/dir --glob "*.py"

The compressed output is what Claude Code's context window should see.
Original content is cached in substrate_index.db and can be resolved
locally via Warden refs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import sqlite3
from pathlib import Path

# Ensure Research Stack is on path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

from context_gate import ContextGate, GateMode

try:
    from pbacs.kimi_context_optimizer import KimiContextOptimizer
    _kimi_compressor = KimiContextOptimizer(token_budget=16000)
except Exception:
    _kimi_compressor = None

# Default hot terms — proprietary vocabulary that should never
# appear raw in an external context window.
_HOT_TERMS = [
    "soliton", "omnitoken", "tardygrada", "waveprobe", "ptos",
    "hyperlut", "neuromorphic", "geomtree", "kolmogorov",
    "metatransport", "phonon", "triumvirate", "cognitivesmoother",
    "hutter", "metafoam", "hyperfluid",
]


def _gate() -> ContextGate:
    return ContextGate(
        warden_db_path=_ROOT / "warden_attestation.db",
        substrate_db_path=_ROOT / "substrate_index.db",
        hot_terms=_HOT_TERMS,
        compressor=_kimi_compressor,
    )


def cmd_read(args):
    """Compress a file through the context gate."""
    gate = _gate()
    path = Path(args.file)
    if not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(errors="replace")

    mode = GateMode[args.mode.upper()]
    result = gate.process(content, mode=mode)

    # Output: compact header + safe text
    header = {
        "source": str(path),
        "mode": result.mode.value,
        "cache_hit": result.cache_hit,
        "compression_ratio": round(result.compression_ratio, 2),
        "original_sha256": result.original_sha256[:16],
        "warden_ref": result.warden_ref,
    }

    if args.json:
        print(json.dumps({"header": header, "content": result.safe_text}))
    else:
        # Human-readable: just the safe text with a one-line header
        print(f"# [{mode.value}] {path.name} → {result.warden_ref}"
              f"  (ratio={result.compression_ratio:.1f}x"
              f"  cache={'HIT' if result.cache_hit else 'MISS'})")
        print(result.safe_text)


def cmd_stdin(args):
    """Compress stdin through the context gate."""
    gate = _gate()
    content = sys.stdin.read()
    mode = GateMode[args.mode.upper()]
    result = gate.process(content, mode=mode)
    print(result.safe_text)


def cmd_stats(args):
    """Show cache statistics."""
    db_path = _ROOT / "substrate_index.db"
    if not db_path.exists():
        print("No substrate_index.db found.")
        return

    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT COUNT(*), SUM(hits), "
            "AVG(compression_ratio) FROM context_cache"
        ).fetchone()
        print(f"Cached entries:       {row[0]}")
        print(f"Total cache hits:     {row[1] or 0}")
        print(f"Avg compression ratio: {row[2] or 0:.1f}x")
    except sqlite3.OperationalError:
        print("context_cache table not yet created.")
    conn.close()


def cmd_warm(args):
    """Pre-warm the cache for a directory."""
    gate = _gate()
    root = Path(args.directory)
    pattern = args.glob or "*.py"
    count = 0
    hits = 0

    for path in sorted(root.rglob(pattern)):
        if path.is_file() and path.stat().st_size < 500_000:
            content = path.read_text(errors="replace")
            result = gate.process(content, mode=GateMode.COMPRESS)
            count += 1
            if result.cache_hit:
                hits += 1

    print(f"Warmed {count} files ({hits} already cached).")


def main():
    p = argparse.ArgumentParser(
        description="Claude Code context compressor"
    )
    sub = p.add_subparsers(dest="command")

    r = sub.add_parser("read", help="Compress a file")
    r.add_argument("file", help="Path to file")
    r.add_argument("--mode", default="compress",
                   choices=["compress", "opaque", "flatten"])
    r.add_argument("--json", action="store_true",
                   help="Output as JSON")
    r.set_defaults(func=cmd_read)

    s = sub.add_parser("stdin", help="Compress stdin")
    s.add_argument("--mode", default="compress",
                   choices=["compress", "opaque", "flatten"])
    s.set_defaults(func=cmd_stdin)

    st = sub.add_parser("stats", help="Show cache stats")
    st.set_defaults(func=cmd_stats)

    w = sub.add_parser("warm", help="Pre-warm cache for directory")
    w.add_argument("directory", help="Directory to warm")
    w.add_argument("--glob", default="*.py",
                   help="File pattern (default: *.py)")
    w.set_defaults(func=cmd_warm)

    args = p.parse_args()
    if not args.command:
        p.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()

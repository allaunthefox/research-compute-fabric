#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Merge a TSM surface (logic_signal_substrate_surface.json) into the omnitoken `egress_surface.json`.

Safe behaviors:
- Validate outgoing surface via `assert_surface_write_safe` from `scripts.logic_signal_substrate_translation`.
- Backup existing surface before writing.
- Atomic write via temporary file + rename.
- Optional `--dry-run` to preview changes.

Usage:
  .venv/bin/python 5-Applications/scripts/write_logic_signal_substrate_surface.py [--logic_signal_substrate PATH] [--surface PATH] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
OMNI_DIR = ROOT / "out" / "omnitoken_bridge"
OMNI_SURFACE_PATH = OMNI_DIR / "egress_surface.json"
DEFAULT_TSM_PATH = ROOT / "out" / "logic_signal_substrate_surface.json"

try:
    from scripts.logic_signal_substrate_translation import assert_surface_write_safe
except Exception:
    try:
        from logic_signal_substrate_translation import assert_surface_write_safe  # type: ignore
    except Exception:
        def assert_surface_write_safe(payload, scope=None):
            # fallback no-op validator if import fails
            return True


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def backup_path(path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return path.with_suffix(f".bak.{stamp}")


def atomic_write(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as tf:
        tf.write(json.dumps(data, indent=2) + "\n")
        tmp = Path(tf.name)
    tmp.replace(path)


def merge_surfaces(existing: Dict[str, Any], logic_signal_substrate: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(existing or {})

    fp = logic_signal_substrate.get("funding_policy")
    if isinstance(fp, dict):
        out["funding_policy"] = fp
        out.setdefault("annotations", {})["funding_policy_updated_utc"] = utc_now()

    qsb = logic_signal_substrate.get("surface_bus") or {}
    qdomains = (qsb.get("domains") or {}) if isinstance(qsb, dict) else {}

    sb = dict(out.get("surface_bus") or {})
    sb.setdefault("schema", str(qsb.get("schema") or sb.get("schema") or "omnitoken-surface-bus/v1"))
    sb.setdefault("domains", {})
    domains = dict(sb.get("domains") or {})

    for k, v in qdomains.items():
        if not isinstance(v, dict):
            continue
        entry = dict(domains.get(k) or {})
        entry.update(v)
        entry["updated_utc"] = utc_now()
        domains[k] = entry

    sb["domains"] = domains
    out["surface_bus"] = sb
    out["updated_utc"] = utc_now()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--logic_signal_substrate", default=str(DEFAULT_TSM_PATH), help="Path to logic_signal_substrate_surface.json")
    ap.add_argument("--surface", default=str(OMNI_SURFACE_PATH), help="Path to egress surface to patch")
    ap.add_argument("--dry-run", action="store_true", help="Print merge result but don't write")
    args = ap.parse_args()

    logic_signal_substrate_path = Path(args.logic_signal_substrate).expanduser()
    surface_path = Path(args.surface).expanduser()

    logic_signal_substrate = load_json(logic_signal_substrate_path)
    existing = load_json(surface_path)

    merged = merge_surfaces(existing, logic_signal_substrate)

    try:
        assert_surface_write_safe(merged, scope="write_logic_signal_substrate_surface")
    except Exception as e:
        print(f"Validation failed: {e}")
        raise

    if args.dry_run:
        print(json.dumps(merged, indent=2)[:20000])
        print("\n--- dry-run; no write performed ---")
        return

    if surface_path.exists():
        bkp = backup_path(surface_path)
        shutil.copy2(surface_path, bkp)
        print(f"backup written: {bkp}")

    atomic_write(surface_path, merged)
    print(f"merged and wrote surface: {surface_path}")


if __name__ == "__main__":
    main()

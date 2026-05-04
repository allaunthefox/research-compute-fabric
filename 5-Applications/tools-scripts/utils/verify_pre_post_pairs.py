#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRE_SCHEMA = PROJECT_ROOT / "schemas" / "pre_record.schema.json"
POST_SCHEMA = PROJECT_ROOT / "schemas" / "post_record.schema.json"


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            s = line.strip()
            if s:
                rows.append(json.loads(s))
    return rows


def load_schema(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify PRE/POST record schema validity and one-to-one pairing.")
    parser.add_argument("--pre", required=True, help="Path to pre_records.jsonl")
    parser.add_argument("--post", required=True, help="Path to post_records.jsonl")
    parser.add_argument("--out", help="Optional output JSON report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pre_rows = load_jsonl(Path(args.pre))
    post_rows = load_jsonl(Path(args.post))

    pre_schema = load_schema(PRE_SCHEMA)
    post_schema = load_schema(POST_SCHEMA)

    for row in pre_rows:
        validate(instance=row, schema=pre_schema)
    for row in post_rows:
        validate(instance=row, schema=post_schema)

    pre_ids = [str(r["pre_record_id"]) for r in pre_rows]
    post_pre_ids = [str(r["pre_record_id"]) for r in post_rows]

    pre_set = set(pre_ids)
    post_ref_set = set(post_pre_ids)

    missing_post_for_pre = sorted(pre_set - post_ref_set)
    orphan_post_refs = sorted(post_ref_set - pre_set)

    duplicate_pre = sorted([x for x in pre_set if pre_ids.count(x) > 1])
    duplicate_post_ref = sorted([x for x in post_ref_set if post_pre_ids.count(x) > 1])

    ok = not (missing_post_for_pre or orphan_post_refs or duplicate_pre or duplicate_post_ref)

    report: Dict[str, Any] = {
        "ok": ok,
        "pre_count": len(pre_rows),
        "post_count": len(post_rows),
        "missing_post_for_pre": missing_post_for_pre,
        "orphan_post_refs": orphan_post_refs,
        "duplicate_pre_record_ids": duplicate_pre,
        "duplicate_post_pre_refs": duplicate_post_ref,
        "pairing_ratio": (len(post_rows) / len(pre_rows)) if pre_rows else 0,
    }

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

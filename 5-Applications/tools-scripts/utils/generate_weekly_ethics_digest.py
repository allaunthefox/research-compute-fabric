#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, cast


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            s = line.strip()
            if s:
                rows.append(json.loads(s))
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly ethical accountability digest from PRE/POST records.")
    parser.add_argument("--pre", required=True, help="Path to pre_records.jsonl")
    parser.add_argument("--post", required=True, help="Path to post_records.jsonl")
    parser.add_argument("--days", type=int, default=7, help="Trailing window in days")
    parser.add_argument("--out", required=True, help="Output markdown path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pre_rows = load_jsonl(Path(args.pre))
    post_rows = load_jsonl(Path(args.post))

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    post_recent = [r for r in post_rows if parse_iso(str(r["timestamp_utc"])) >= since]
    pre_ids = {str(r["pre_record_id"]) for r in pre_rows}

    outcomes = Counter(str(r["outcome"]) for r in post_recent)
    reason_codes = Counter(str(r["reason_code"]) for r in post_recent)

    orphan = [str(r["post_record_id"]) for r in post_recent if str(r["pre_record_id"]) not in pre_ids]
    ethical_flags = 0
    for row in post_recent:
        e_raw = row.get("ethical_impact", {})
        e: Dict[str, Any] = cast(Dict[str, Any], e_raw) if isinstance(e_raw, dict) else {}
        if bool(e.get("retail_disadvantage_flag")) or bool(e.get("liquidation_side_effect_flag")):
            ethical_flags += 1
        anomaly_flags = cast(List[Any], e.get("anomaly_flags", []))
        ethical_flags += len(anomaly_flags)

    digest: List[str] = []
    digest.append("# Weekly Ethical Accountability Digest")
    digest.append("")
    digest.append(f"Generated UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}")
    digest.append(f"Window: last {args.days} days")
    digest.append("")
    digest.append("## Summary")
    digest.append("")
    digest.append(f"- Total post records in window: {len(post_recent)}")
    digest.append(f"- EXECUTED: {outcomes.get('EXECUTED', 0)}")
    digest.append(f"- PAUSED: {outcomes.get('PAUSED', 0)}")
    digest.append(f"- Ethical/anomaly flag count: {ethical_flags}")
    digest.append(f"- Orphan POST records: {len(orphan)}")
    digest.append("")
    digest.append("## Top Reason Codes")
    digest.append("")
    if reason_codes:
        for code, count in reason_codes.most_common(10):
            digest.append(f"- {code}: {count}")
    else:
        digest.append("- No reason codes in selected window.")
    digest.append("")
    digest.append("## Exceptions")
    digest.append("")
    if orphan:
        for item in orphan[:20]:
            digest.append(f"- Orphan post_record_id: {item}")
    else:
        digest.append("- No orphan POST records detected.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(digest) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), "post_records_in_window": len(post_recent)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

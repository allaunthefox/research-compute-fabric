#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAIN_SCHEMA = PROJECT_ROOT / "schemas" / "passive_chain_record.schema.json"


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
    parser = argparse.ArgumentParser(description="Daily integrity check for passive all-market monitor records.")
    parser.add_argument("--records", required=True, help="Path to chain_records.jsonl")
    parser.add_argument("--target-chain", action="append", dest="target_chains", required=True, help="Expected chain. Repeatable.")
    parser.add_argument("--max-age-minutes", type=int, default=1440, help="Maximum record staleness in minutes.")
    parser.add_argument("--out", help="Optional output JSON report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema = json.loads(CHAIN_SCHEMA.read_text(encoding="utf-8"))
    rows = load_jsonl(Path(args.records))

    for row in rows:
        validate(instance=row, schema=schema)

    now = datetime.now(timezone.utc)
    max_age = timedelta(minutes=args.max_age_minutes)
    targets = {c.strip().lower() for c in args.target_chains if c.strip()}

    latest_by_chain: Dict[str, datetime] = {}
    for row in rows:
        chain = str(row["chain"]).strip().lower()
        ts = parse_iso(str(row["timestamp_utc"]))
        if chain not in latest_by_chain or ts > latest_by_chain[chain]:
            latest_by_chain[chain] = ts

    missing = sorted(list(targets - set(latest_by_chain.keys())))
    stale = sorted(
        [chain for chain, ts in latest_by_chain.items() if now - ts > max_age]
    )

    coverage_ratio = (len(set(latest_by_chain.keys()) & targets) / len(targets)) if targets else 0
    freshness_ratio = (
        (len(targets) - len(stale) - len(missing)) / len(targets)
        if targets
        else 0
    )

    report: Dict[str, Any] = {
        "ok": len(missing) == 0 and len(stale) == 0,
        "target_chain_count": len(targets),
        "observed_chain_count": len(set(latest_by_chain.keys()) & targets),
        "coverage_ratio": round(coverage_ratio, 6),
        "freshness_ratio": round(freshness_ratio, 6),
        "missing_chains": missing,
        "stale_chains": stale,
        "max_age_minutes": args.max_age_minutes,
    }

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

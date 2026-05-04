#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent))
from rfc3161_stamp import stamp as rfc3161_stamp


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate monthly PRE/POST accountability attestation package.")
    parser.add_argument("--pairing-report", required=True, help="Path to pairing report JSON")
    parser.add_argument("--integrity-report", required=True, help="Path to monitor integrity report JSON")
    parser.add_argument("--weekly-digest", required=True, help="Path to weekly digest markdown")
    parser.add_argument("--pre", required=True, help="Path to pre_records.jsonl")
    parser.add_argument("--post", required=True, help="Path to post_records.jsonl")
    parser.add_argument("--chain", required=True, help="Path to chain_records.jsonl")
    parser.add_argument("--out", required=True, help="Output JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    pairing_path = Path(args.pairing_report)
    integrity_path = Path(args.integrity_report)
    weekly_digest_path = Path(args.weekly_digest)
    pre_path = Path(args.pre)
    post_path = Path(args.post)
    chain_path = Path(args.chain)
    out_path = Path(args.out)

    pairing = load_json(pairing_path)
    integrity = load_json(integrity_path)

    attestation: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "scope": "monthly_prepost_accountability",
        "status": "PASS" if pairing.get("ok") and integrity.get("ok") else "REVIEW_REQUIRED",
        "inputs": {
            "pairing_report": {
                "path": str(pairing_path),
                "sha256": sha256_file(pairing_path),
                "ok": bool(pairing.get("ok")),
            },
            "integrity_report": {
                "path": str(integrity_path),
                "sha256": sha256_file(integrity_path),
                "ok": bool(integrity.get("ok")),
            },
            "weekly_digest": {
                "path": str(weekly_digest_path),
                "sha256": sha256_file(weekly_digest_path),
            },
            "pre_records": {
                "path": str(pre_path),
                "sha256": sha256_file(pre_path),
            },
            "post_records": {
                "path": str(post_path),
                "sha256": sha256_file(post_path),
            },
            "chain_records": {
                "path": str(chain_path),
                "sha256": sha256_file(chain_path),
            },
        },
        "controls": {
            "pre_post_pairing_ratio": pairing.get("pairing_ratio"),
            "missing_post_for_pre": pairing.get("missing_post_for_pre", []),
            "orphan_post_refs": pairing.get("orphan_post_refs", []),
            "coverage_ratio": integrity.get("coverage_ratio"),
            "freshness_ratio": integrity.get("freshness_ratio"),
            "missing_chains": integrity.get("missing_chains", []),
            "stale_chains": integrity.get("stale_chains", []),
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(attestation, indent=2) + "\n", encoding="utf-8")
    out_sha256 = sha256_file(out_path)
    try:
        ts_info = rfc3161_stamp(out_path)
    except Exception as exc:
        ts_info = {"error": str(exc)}
    print(json.dumps({"wrote": str(out_path), "status": attestation["status"], "sha256": out_sha256, "rfc3161": ts_info}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate executable simulator policy from logic model JSON.")
    parser.add_argument("--model-json", required=True, help="Path to successful_bot_logic_model.json")
    parser.add_argument("--out-policy", required=True, help="Output policy file path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_payload = json.loads(Path(args.model_json).read_text(encoding="utf-8"))
    model = model_payload.get("model", {}) if isinstance(model_payload, dict) else {}

    gates = model.get("gates", {}) if isinstance(model, dict) else {}
    constraints = model.get("constraints", {}) if isinstance(model, dict) else {}
    allowed_motifs = constraints.get("allowed_motifs", []) if isinstance(constraints, dict) else []

    allowlist: List[Dict[str, Any]] = []
    if isinstance(allowed_motifs, list):
        for item in allowed_motifs:
            if isinstance(item, dict):
                chain = str(item.get("chain", "")).lower()
                pair = str(item.get("pair", "")).upper()
                if chain and pair:
                    allowlist.append({"chain": chain, "pair": pair})

    policy: Dict[str, Any] = {
        "policy_name": "learned_bot_policy_v1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_model": str(args.model_json),
        "enforce_allowlist": True,
        "allowlist_motifs": allowlist,
        "gates": {
            "max_gas_usd": float(gates.get("max_gas_usd", 0.0) or 0.0),
            "max_slippage_bps": float(gates.get("max_slippage_bps", 0.0) or 0.0),
            "min_net_pnl_usd": float(gates.get("min_net_pnl_usd", 0.0) or 0.0),
        },
    }

    out_path = Path(args.out_policy)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"wrote": str(out_path), "allowlist_motifs": len(allowlist)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Weld tailnet node connector settings into the omnitoken bridge surface.

This script reads nodes inventory + optional rollout report and writes:
- 5-Applications/out/omnitoken_bridge/tailnet_connector_surface.json
- 5-Applications/out/omnitoken_bridge/<profile>.json (updated SMTP host/port for connector)

Usage:
  .venv/bin/python 5-Applications/scripts/weld_omintoken_tailnet_surface.py \
    --inventory 5-Applications/scripts/nodes_inventory.json \
    --profile proton_main
"""

from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

ROOT = Path(__file__).resolve().parent.parent
OMNI_DIR = ROOT / "out" / "omnitoken_bridge"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_transaction_generation(profile_name: str) -> Dict[str, Any]:
    # Transaction ids are assigned by execution systems; this block enforces
    # per-transaction generation policy in the OmniToken profile.
    return {
        "enabled": True,
        "mode": "per_transaction",
        "generation_namespace": profile_name,
        "assignment_point": "pre_submit",
        "id_format": "otx-{utc_basic}-{seq6}-{intent8}",
        "sequence_scope": "utc_day",
        "idempotency_required": True,
        "idempotency_key_basis": [
            "payout_intent_id",
            "recipient_id",
            "gross_amount_base",
            "currency",
        ],
        "fail_closed": True,
    }


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_rollout_report() -> Optional[Path]:
    paths = sorted(glob.glob(str(ROOT / "out" / "logic_execution_layer_ominrouter" / "rollout" / "rollout_report_*.json")))
    if not paths:
        return None
    return Path(paths[-1])


def choose_connector(inventory_nodes: List[Dict[str, Any]], report_path: Optional[Path]) -> Dict[str, Any]:
    # Prefer nodes that reached at least "mkdir_remote_workdir" in latest report,
    # then fall back to first inventory node.
    by_name = {str(n.get("name")): n for n in inventory_nodes}
    if report_path and report_path.exists():
        report = load_json(report_path)
        results_obj = report.get("results")
        results = cast(List[Any], results_obj) if isinstance(results_obj, list) else []
        for item_obj in results:
            if not isinstance(item_obj, dict):
                continue
            item = cast(Dict[str, Any], item_obj)
            name = str(item.get("node") or "")
            steps_obj = item.get("steps")
            steps = cast(List[Any], steps_obj) if isinstance(steps_obj, list) else []
            if name in by_name and len(steps) >= 1:
                return by_name[name]
    return inventory_nodes[0]


def weld(profile_name: str, connector_node: Dict[str, Any], report_path: Optional[Path]) -> Dict[str, Any]:
    OMNI_DIR.mkdir(parents=True, exist_ok=True)
    profile_path = OMNI_DIR / f"{profile_name}.json"
    profile: Dict[str, Any] = {}
    if profile_path.exists():
        profile = load_json(profile_path)

    mail_host = str(connector_node.get("mail_host") or connector_node.get("host"))
    smtp_obj: Dict[str, Any] = dict(profile.get("smtp") or {})
    smtp_obj["host"] = mail_host
    smtp_obj["port"] = int(smtp_obj.get("port") or 587)
    smtp_obj["encryption"] = str(smtp_obj.get("encryption") or "STARTTLS")
    smtp_obj.setdefault("auth_methods", ["PLAIN", "LOGIN"])

    profile["schema"] = str(profile.get("schema") or "omnitoken-bridge/v1")
    profile["name"] = str(profile.get("name") or profile_name)
    profile["provider"] = "tailnet-smtp-submission"
    profile["updated_utc"] = utc_now()
    profile["smtp"] = smtp_obj
    profile["transaction_generation"] = dict(
        profile.get("transaction_generation") or default_transaction_generation(profile_name)
    )
    profile["tailnet_connector"] = {
        "node": str(connector_node.get("name") or "unknown"),
        "host": str(connector_node.get("host") or "unknown"),
        "mail_host": str(connector_node.get("mail_host") or "unknown"),
        "mail_domain": str(connector_node.get("mail_domain") or "unknown"),
        "admin_email": str(connector_node.get("admin_email") or "unknown"),
        "source_report": str(report_path) if report_path else None,
    }

    notes = list(profile.get("notes") or [])
    weld_note = "Tailnet connector welded from nodes inventory and rollout report."
    if weld_note not in notes:
        notes.append(weld_note)
    profile["notes"] = notes

    profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")

    surface: Dict[str, Any] = {
        "generated_utc": utc_now(),
        "profile": str(profile_path),
        "connector": profile["tailnet_connector"],
        "transaction_generation": profile["transaction_generation"],
        "smtp": {
            "host": mail_host,
            "port": smtp_obj["port"],
            "encryption": smtp_obj["encryption"],
        },
    }
    surface_path = OMNI_DIR / "tailnet_connector_surface.json"
    surface_path.write_text(json.dumps(surface, indent=2) + "\n", encoding="utf-8")

    return {
        "profile_path": str(profile_path),
        "surface_path": str(surface_path),
        "connector_node": str(connector_node.get("name") or "unknown"),
        "smtp_host": mail_host,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--profile", default="proton_main")
    args = ap.parse_args()

    inv_path = Path(args.inventory)
    if not inv_path.exists():
        raise SystemExit(f"Inventory not found: {inv_path}")

    inv = load_json(inv_path)
    nodes_obj = inv.get("nodes")
    nodes = cast(List[Any], nodes_obj) if isinstance(nodes_obj, list) else []
    if not nodes:
        raise SystemExit("Inventory has no nodes")
    inventory_nodes: List[Dict[str, Any]] = []
    for node_obj in nodes:
        if isinstance(node_obj, dict):
            inventory_nodes.append(cast(Dict[str, Any], node_obj))
    if not inventory_nodes:
        raise SystemExit("Inventory has no valid node objects")

    report = latest_rollout_report()
    connector = choose_connector(inventory_nodes, report)
    out = weld(args.profile, connector, report)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

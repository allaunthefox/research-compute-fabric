# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

from __future__ import annotations

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
"""Bulk-deploy mail server bootstrap and logic_execution_layer ominrouter profiles to all nodes.

Usage:
  .venv/bin/python 5-Applications/scripts/deploy_mail_ominrouter_to_nodes.py \
    --inventory 5-Applications/scripts/nodes_inventory.json \
    --apply

Default behavior is dry-run unless --apply is provided.
"""


import argparse
import json
import shlex
# import subprocess (REMOVED BY WARDEN)
import sys
import traceback
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, cast

ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = ROOT / "scripts" / "bootstrap_dag_mail_server.sh"
ROUTER_BUILDER = ROOT / "scripts" / "logic_execution_layer_create_ominrouter.py"
ROUTER_OUT = ROOT / "out" / "logic_execution_layer_ominrouter" / "nodes"
ROLLOUT_OUT = ROOT / "out" / "logic_execution_layer_ominrouter" / "rollout"


def run(cmd: List[str], dry_run: bool) -> None:
    printable = " ".join(shlex.quote(x) for x in cmd)
    print(f"  $ {printable}")
    if dry_run:
        return
    subprocess.run(cmd, check=True)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ssh_cmd(node: Dict[str, Any], remote_cmd: str) -> List[str]:
    port = str(node.get("ssh_port", 22))
    user = node["user"]
    host = node["host"]
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=12",
        "-p",
        port,
        f"{user}@{host}",
        remote_cmd,
    ]


def scp_cmd(node: Dict[str, Any], src: Path, remote_dest: str) -> List[str]:
    port = str(node.get("ssh_port", 22))
    user = node["user"]
    host = node["host"]
    return [
        "scp",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=12",
        "-P",
        port,
        str(src),
        f"{user}@{host}:{remote_dest}",
    ]


def load_inventory(path: Path) -> List[Dict[str, Any]]:
    payload_obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload_obj, dict):
        raise ValueError("Inventory root must be an object")
    payload = cast(Dict[str, Any], payload_obj)
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("Inventory must contain a non-empty 'nodes' array")
    nodes_list = cast(List[Any], nodes)
    required = ["name", "host", "user", "mail_domain", "mail_host", "admin_email"]
    validated_nodes: List[Dict[str, Any]] = []
    for node_obj in nodes_list:
        if not isinstance(node_obj, dict):
            raise ValueError("Each node entry must be an object")
        node = cast(Dict[str, Any], node_obj)
        for key in required:
            if key not in node or not node[key]:
                raise ValueError(f"Node {node.get('name', '<unnamed>')} missing required key: {key}")
        validated_nodes.append(node)
    return validated_nodes


def build_router_for_node(node: Dict[str, Any], apply_local_logic_execution_layer_profile: bool, dry_run: bool) -> Path:
    ROUTER_OUT.mkdir(parents=True, exist_ok=True)
    name = str(node["name"])
    router_name = f"ominrouter_{name}"
    cmd = [
        sys.executable,
        str(ROUTER_BUILDER),
        "--router-name",
        router_name,
        "--mail-host",
        str(node["mail_host"]),
        "--mail-domain",
        str(node["mail_domain"]),
    ]
    if apply_local_logic_execution_layer_profile and node.get("logic_execution_layer_profile_path"):
        cmd.extend(["--logic_execution_layer-profile", str(node["logic_execution_layer_profile_path"]), "--apply"])
    run(cmd, dry_run)
    return ROUTER_OUT.parent / f"{router_name}.json"


def deploy_node(node: Dict[str, Any], apply: bool, apply_local_logic_execution_layer_profile: bool) -> Dict[str, Any]:
    dry_run = not apply
    name = str(node["name"])
    host = str(node["host"])
    remote_workdir = str(node.get("remote_workdir", "/opt/omni_stack"))
    remote_bootstrap = f"{remote_workdir}/bootstrap_dag_mail_server.sh"
    remote_router = f"{remote_workdir}/ominrouter_{name}.json"

    print(f"\n=== Node: {name} ({host}) ===")

    result: Dict[str, Any] = {
        "node": name,
        "host": host,
        "status": "ok",
        "dry_run": dry_run,
        "steps": [],
    }

    try:
        # 1) Build node-specific router profile locally.
        router_json = build_router_for_node(node, apply_local_logic_execution_layer_profile, dry_run)
        result["router_json"] = str(router_json)
        result["steps"].append("build_router")

        # 2) Ensure remote working directory exists.
        run(ssh_cmd(node, f"mkdir -p {shlex.quote(remote_workdir)}"), dry_run)
        result["steps"].append("mkdir_remote_workdir")

        # 3) Copy bootstrap + router profile to remote.
        run(scp_cmd(node, BOOTSTRAP, remote_bootstrap), dry_run)
        run(scp_cmd(node, router_json, remote_router), dry_run)
        result["steps"].append("copy_artifacts")

        # 4) Execute remote bootstrap as root.
        remote_run = (
            f"sudo bash {shlex.quote(remote_bootstrap)} "
            f"--mail-domain {shlex.quote(str(node['mail_domain']))} "
            f"--mail-host {shlex.quote(str(node['mail_host']))} "
            f"--admin-email {shlex.quote(str(node['admin_email']))}"
        )
        run(ssh_cmd(node, remote_run), dry_run)
        result["steps"].append("bootstrap_mail_server")

        # 5) Place router in a stable path and print sanity checks.
        remote_finalize = (
            "sudo mkdir -p /etc/logic_execution_layer && "
            f"sudo cp {shlex.quote(remote_router)} /etc/logic_execution_layer/ominrouter.json && "
            "sudo chmod 640 /etc/logic_execution_layer/ominrouter.json && "
            "echo '[ok] router installed at /etc/logic_execution_layer/ominrouter.json' && "
            "sudo ss -ltn '( sport = :25 or sport = :587 or sport = :465 or sport = :993 )' | cat"
        )
        run(ssh_cmd(node, remote_finalize), dry_run)
        result["steps"].append("install_router_and_check_ports")
    except (subprocess.CalledProcessError, OSError, ValueError, RuntimeError) as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        result["traceback"] = traceback.format_exc()

    return result


def run_rollout(
    nodes: List[Dict[str, Any]],
    apply: bool,
    apply_local_logic_execution_layer_profile: bool,
    workers: int,
) -> List[Dict[str, Any]]:
    if workers <= 1:
        return [deploy_node(node, apply=apply, apply_local_logic_execution_layer_profile=apply_local_logic_execution_layer_profile) for node in nodes]

    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(deploy_node, node, apply, apply_local_logic_execution_layer_profile): node for node in nodes
        }
        for future in as_completed(future_map):
            node = future_map[future]
            try:
                results.append(future.result())
            except (subprocess.CalledProcessError, OSError, ValueError, RuntimeError) as exc:
                results.append(
                    {
                        "node": str(node.get("name", "<unknown>")),
                        "host": str(node.get("host", "<unknown>")),
                        "status": "error",
                        "error": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                )
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inventory", required=True, help="Path to nodes inventory JSON")
    ap.add_argument("--apply", action="store_true", help="Execute commands (default is dry-run)")
    ap.add_argument(
        "--apply-local-logic_execution_layer-profile",
        action="store_true",
        help="Also patch local logic_execution_layer profiles listed in inventory entries",
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Parallel workers for node rollout (default 4). Use 1 for sequential mode.",
    )
    args = ap.parse_args()

    inventory_path = Path(args.inventory)
    if not inventory_path.exists():
        raise SystemExit(f"Inventory not found: {inventory_path}")

    nodes = load_inventory(inventory_path)

    print(f"Loaded {len(nodes)} node(s) from {inventory_path}")
    if not args.apply:
        print("DRY-RUN mode active. Re-run with --apply to execute.")

    results = run_rollout(
        nodes=nodes,
        apply=args.apply,
        apply_local_logic_execution_layer_profile=args.apply_local_logic_execution_layer_profile,
        workers=args.workers,
    )

    ok = sum(1 for r in results if r.get("status") == "ok")
    err = sum(1 for r in results if r.get("status") == "error")

    ROLLOUT_OUT.mkdir(parents=True, exist_ok=True)
    report: Dict[str, Any] = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inventory": str(inventory_path),
        "apply": bool(args.apply),
        "workers": int(args.workers),
        "totals": {"nodes": len(results), "ok": ok, "error": err},
        "results": results,
    }
    report_path = ROLLOUT_OUT / f"rollout_report_{utc_stamp()}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nRollout complete.")
    print(f"Summary: ok={ok} error={err} total={len(results)}")
    print(f"Report: {report_path}")
    if err > 0 and args.apply:
        raise SystemExit(1)



if __name__ == "__main__":
    main()

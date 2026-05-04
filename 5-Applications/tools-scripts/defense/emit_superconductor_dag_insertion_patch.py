# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import difflib
import hashlib
import json
from pathlib import Path
from typing import Any


def map_tier(tier_name: str, mapping: dict[str, Any]) -> int:
    return int(mapping.get(tier_name, 1))


def build_node_id(node_module: str, capsule_hash: str) -> str:
    seed = f"{node_module}:{capsule_hash}".encode("utf-8")
    return hashlib.sha256(seed).hexdigest()


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    meta_path = root / "Research Documents" / "superconductor_hybrid_metaindex_v0.json"
    capsule_path = root / "out" / "superconductor_hybrid_dag_capsule.json"
    dag_path = root / "Research Documents" / "resonant_stack_v5.dag.json"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    capsule = json.loads(capsule_path.read_text(encoding="utf-8"))
    dag = json.loads(dag_path.read_text(encoding="utf-8"))
    original_text = dag_path.read_text(encoding="utf-8")

    cfg = meta.get("dag_capsule_payload", {})
    ins = cfg.get("insertion_params", {})

    parent_hint = str(ins.get("parent_hint", "cba2d4cef575a399e8acd0a10b0eab47d2199feea2556dbb6ee71de5fc9903c8"))
    compute_weight = float(ins.get("compute_weight", 9.4))
    timestamp = float(ins.get("timestamp", 1773952200.0))
    tier_map = ins.get("tier_name_to_number", {})

    node_module = str(capsule["node_module"])
    capsule_hash = str(capsule["meta_capsule_hash"])
    node_id = build_node_id(node_module, capsule_hash)

    tier_name = str(capsule.get("tier", "CRYSTALLINE"))
    tier_num = map_tier(tier_name, tier_map)

    node_entry: dict[str, Any] = {
        "tier": tier_num,
        "tier_name": tier_name,
        "equation_version": dag.get("equation_version", "Σ-EQ-ALL-01"),
        "ruleset_version": dag.get("ruleset_version", "Σ-RULESET-03"),
        "signature": dag.get("signature", "ML-DSA-BULK"),
        "tags": capsule.get("tags", []),
        "compute_weight": compute_weight,
        "meta_capsule": capsule["meta_capsule"],
        "meta_capsule_hash": capsule_hash,
        "parent": parent_hint,
        "timestamp": timestamp,
    }

    dag_nodes = dag["dag_nodes"]
    dag_nodes[node_id] = node_entry

    dag["node_count"] = len(dag_nodes)
    dag["compute_metrics"]["actions"] = len(dag_nodes)
    dag["compute_metrics"]["energy"] = round(sum(float(v["compute_weight"]) for v in dag_nodes.values()), 1)
    dag["compute_metrics"]["last_action_hash"] = node_id
    dag["root_hash"] = hashlib.sha256(
        json.dumps(dag_nodes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    updated_text = json.dumps(dag, indent=2, ensure_ascii=True) + "\n"
    patch_lines = difflib.unified_diff(
        original_text.splitlines(),
        updated_text.splitlines(),
        fromfile=str(dag_path),
        tofile=str(dag_path),
        lineterm="",
    )
    patch_text = "\n".join(patch_lines) + "\n"

    out_path = root / str(ins.get("patch_output_path", "5-Applications/out/graph_os_superconductor_node_insertion.patch"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(patch_text, encoding="utf-8")

    summary: dict[str, Any] = {
        "node_id": node_id,
        "parent": parent_hint,
        "compute_weight": compute_weight,
        "timestamp": timestamp,
        "new_root_hash": dag["root_hash"],
        "new_node_count": dag["node_count"],
        "new_energy": dag["compute_metrics"]["energy"],
        "patch_path": str(out_path),
    }
    (root / "out" / "graph_os_superconductor_node_insertion_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print("[+] Wrote patch:", out_path)
    print("[+] New node id:", node_id)
    print("[+] New root hash:", dag["root_hash"])


if __name__ == "__main__":
    main()

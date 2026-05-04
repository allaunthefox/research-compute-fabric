# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
import hashlib
import sys
import os
from pathlib import Path
from typing import Any

# Add project root to sys.path to import TSM_COMPILER
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from TSM_COMPILER import TSM_Kernel
except ImportError:
    from TSM_COMPILER import TSM_Kernel

def build_payload(meta: dict[str, Any]) -> dict[str, Any]:
    capsule_cfg: dict[str, Any] = meta.get("dag_capsule_payload", {})
    claim_status: dict[str, Any] = capsule_cfg.get("claim_status", {})

    source_paths: list[str] = capsule_cfg.get("payload_source_paths", [])
    payload: dict[str, Any] = {}
    for p in source_paths:
        if p in meta:
            payload[p] = meta[p]

    payload["module"] = capsule_cfg.get("node_module", "SUPERCONDUCTOR_HYBRID_NEEDS_REGISTER")
    payload["status"] = capsule_cfg.get("status", "DAG_READY_PAYLOAD")
    payload["claim_status"] = claim_status
    return payload

def main() -> None:
    root = Path(__file__).resolve().parent.parent
    meta_path = root / "Research Documents" / "superconductor_hybrid_metaindex_v0.json"
    out_path = root / "out" / "superconductor_hybrid_dag_capsule.json"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    payload = build_payload(meta)
    
    # Initialize Kernel (v3.2-USAL)
    kernel = TSM_Kernel(substrate="superconductor")
    
    # Absorb into manifold using unified USAL logic
    label = "superconductor_hybrid_capsule"
    manifold_id = kernel.absorb(label, payload)
    absorbed = kernel.manifold[label]

    output: dict[str, Any] = {
        "logic_signal_substrate_version": "v3.2-USAL",
        "isa_version": "ISA-v1",
        "manifold_id": manifold_id,
        "substrate_transparency": "ENABLED",
        "stability_metric": kernel.surface.stability_metric,
        "node_module": payload["module"],
        "tier": meta.get("dag_capsule_payload", {}).get("tier", "CRYSTALLINE"),
        "tags": meta.get("dag_capsule_payload", {}).get("tags", []),
        "claim_status": payload["claim_status"],
        "metadata_payload": payload,
        "metadata_payload_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "meta_capsule": absorbed["blob"],
        "meta_capsule_hash": absorbed["id"],
        "encoding": "base64url(zlib(json_sorted_compact)) via USAL v1.0"
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    print("[+] Wrote USAL-aligned DAG capsule payload:", out_path)
    print("[+] meta_capsule_hash:", output["meta_capsule_hash"])


if __name__ == "__main__":
    main()

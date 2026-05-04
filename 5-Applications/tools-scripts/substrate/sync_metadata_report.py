# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import json
from pathlib import Path
from typing import Any


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def compare(curated: dict[str, Any], canonical: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    curated_keys = set(curated)
    canonical_keys = set(canonical)

    missing_in_curated = sorted(canonical_keys - curated_keys)
    missing_in_canonical = sorted(curated_keys - canonical_keys)

    mismatched_nodes: list[str] = []
    for node_id in sorted(curated_keys & canonical_keys):
        if canonical_bytes(curated[node_id]) != canonical_bytes(canonical[node_id]):
            mismatched_nodes.append(node_id)

    return missing_in_curated, missing_in_canonical, mismatched_nodes


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    root = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Check and optionally sync metadata_report.json with regenerated canonical metadata."
    )
    parser.add_argument(
        "--curated",
        type=Path,
        default=root / "metadata_report.json",
        help="Path to curated metadata report",
    )
    parser.add_argument(
        "--canonical",
        type=Path,
        default=root / "out" / "graph_os_decoded_metadata_regenerated.json",
        help="Path to canonical regenerated metadata",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="If set, overwrite curated file with canonical bytes before checking",
    )
    args = parser.parse_args()

    curated_path = args.curated
    canonical_path = args.canonical

    if not curated_path.exists():
        print(f"[!] Curated file not found: {curated_path}")
        return 2
    if not canonical_path.exists():
        print(f"[!] Canonical file not found: {canonical_path}")
        return 2

    if args.sync:
        curated_path.write_bytes(canonical_path.read_bytes())
        print(f"[+] Synced curated from canonical: {curated_path}")

    curated = load_json(curated_path)
    canonical = load_json(canonical_path)

    missing_in_curated, missing_in_canonical, mismatched_nodes = compare(curated, canonical)
    raw_bytes_equal = curated_path.read_bytes() == canonical_path.read_bytes()

    print("[+] Check summary")
    print(f"    curated_nodes={len(curated)} canonical_nodes={len(canonical)}")
    print(f"    missing_in_curated={len(missing_in_curated)}")
    print(f"    missing_in_canonical={len(missing_in_canonical)}")
    print(f"    value_mismatch_nodes={len(mismatched_nodes)}")
    print(f"    raw_bytes_equal={raw_bytes_equal}")

    if missing_in_curated:
        print("[!] Missing node ids in curated:")
        for node_id in missing_in_curated:
            print(f"    - {node_id}")

    if missing_in_canonical:
        print("[!] Missing node ids in canonical:")
        for node_id in missing_in_canonical:
            print(f"    - {node_id}")

    if mismatched_nodes:
        print("[!] Value-mismatched node ids:")
        for node_id in mismatched_nodes:
            print(f"    - {node_id}")

    all_equal = (
        len(missing_in_curated) == 0
        and len(missing_in_canonical) == 0
        and len(mismatched_nodes) == 0
    )

    if all_equal:
        print("[+] Metadata is fully aligned.")
        return 0

    print("[!] Metadata is not fully aligned.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

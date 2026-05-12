#!/usr/bin/env python3
"""Run the Tammes-focused adversarial route prior over wiki8 trial results.

This consumes a real reversible compression approach receipt and asks:

* does the Tammes/focus/adversarial priority select byte-winning routes?
* does it prune near-duplicate or fragile candidates before promotion?
* does it improve measured bytes over the existing best route?

It does not invent a new transform.  Improvement here means better route
selection among already evaluated exact routes, not a new compressed payload.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
DEFAULT_APPROACH = SHIM / "tammes_focused_adversarial_hutter_wiki8_approach_trial_receipt.json"
PRIOR = SHIM / "tammes_focused_adversarial_hutter_prior_receipt.json"
OUT = SHIM / "tammes_focused_adversarial_hutter_wiki8_trial_receipt.json"

TOPOLOGY_WITNESS_BYTES = 16


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def route_key(route: dict[str, Any]) -> str:
    return f"{route['transform']}->{route['codec']}"


def feature_vector(route: dict[str, Any], raw_baseline: int) -> list[float]:
    transform_index = {
        "raw": 0.0,
        "xml_token": 1.0,
        "class_lane_boat": 2.0,
        "delta_boat": 3.0,
    }.get(route["transform"], 4.0)
    codec_index = {
        "stored": 0.0,
        "zlib9": 1.0,
        "bz2": 2.0,
        "lzma": 3.0,
    }.get(route["codec"], 4.0)
    encoded = float(route["encoded_size"])
    compressed = float(route["compressed_size"])
    gain = float(raw_baseline - compressed)
    ratio = float(route["ratio"])
    metadata_cost = float(len(stable_json(route.get("metadata", {}))))
    return [
        transform_index / 4.0,
        codec_index / 4.0,
        min(encoded / max(1.0, compressed * 4.0), 4.0) / 4.0,
        max(-1.0, min(1.0, gain / max(1.0, raw_baseline))),
        min(ratio, 1.0),
        min(metadata_cost / 2048.0, 1.0),
    ]


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def nearest_distance(route: dict[str, Any], routes: list[dict[str, Any]], raw_baseline: int) -> float:
    own = feature_vector(route, raw_baseline)
    distances = [
        euclidean(own, feature_vector(other, raw_baseline))
        for other in routes
        if other is not route
    ]
    return min(distances) if distances else 0.0


def adversarial_fragility(route: dict[str, Any]) -> float:
    """Cheap deterministic stress proxy for already-evaluated routes.

    Real adversarial Conway stress will need a separate local rewrite arena.
    This proxy penalizes routes that already failed rehydration, have unbounded
    metadata, or expand badly before codec rescue.
    """

    if not route.get("rehydrated_ok"):
        return 1.0
    encoded = int(route["encoded_size"])
    compressed = int(route["compressed_size"])
    metadata = len(stable_json(route.get("metadata", {})))
    expansion = max(0.0, encoded / max(1, compressed) - 4.0) / 8.0
    metadata_pressure = metadata / 4096.0
    return max(0.0, min(1.0, expansion + metadata_pressure))


def focus_score(route: dict[str, Any], routes: list[dict[str, Any]]) -> float:
    same_transform = [other for other in routes if other["transform"] == route["transform"]]
    if not routes:
        return 0.0
    # Higher when this transform family is a small, coherent subfrontier and
    # the selected route is the best member of that family.
    family_fraction = len(same_transform) / len(routes)
    best_family = min(same_transform, key=lambda item: item["compressed_size"])
    best_bonus = 1.0 if best_family is route else 0.0
    return max(0.0, min(1.0, (1.0 - family_fraction) * 0.5 + best_bonus * 0.5))


def priority(route: dict[str, Any], routes: list[dict[str, Any]], raw_baseline: int) -> dict[str, Any]:
    witness = 0 if route["transform"] == "raw" else TOPOLOGY_WITNESS_BYTES
    total = int(route["compressed_size"]) + witness
    gain_floor = (raw_baseline - total) / max(1, raw_baseline)
    residual_floor = 0.0 if route.get("rehydrated_ok") else 1.0
    witness_floor = witness / max(1, raw_baseline)
    decoder_floor = {
        "stored": 0.0,
        "zlib9": 0.03,
        "bz2": 0.05,
        "lzma": 0.09,
    }.get(route["codec"], 0.12)
    tammes = nearest_distance(route, routes, raw_baseline)
    focus = focus_score(route, routes)
    adv = adversarial_fragility(route)
    score = (
        8.0 * gain_floor
        + 0.03 * tammes
        + 0.03 * focus
        - residual_floor
        - witness_floor
        - 0.15 * decoder_floor
        - 0.03 * adv
    )
    return {
        "route": route_key(route),
        "transform": route["transform"],
        "codec": route["codec"],
        "compressed_bytes": int(route["compressed_size"]),
        "witness_bytes": witness,
        "total_bytes": total,
        "gain_vs_raw_after_witness_bytes": raw_baseline - total,
        "gain_floor": gain_floor,
        "tammes_diversity": tammes,
        "composition_focus": focus,
        "adversarial_fragility": adv,
        "decoder_floor": decoder_floor,
        "priority": score,
        "rehydrated_ok": bool(route.get("rehydrated_ok")),
    }


def unique_slices(slices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int, str]] = set()
    unique = []
    for item in slices:
        key = (
            item.get("slice_name", ""),
            int(item.get("source_bytes", 0)),
            item.get("source_hash_sha256", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def evaluate_slice(item: dict[str, Any]) -> dict[str, Any]:
    routes = item["results"]
    raw_baseline = int(item["best_raw_baseline"]["compressed_size"])
    scored = [priority(route, routes, raw_baseline) for route in routes]
    selected = max(scored, key=lambda row: row["priority"])
    measured_best = min(
        scored,
        key=lambda row: row["total_bytes"],
    )
    raw_best = min(
        (row for row in scored if row["transform"] == "raw"),
        key=lambda row: row["total_bytes"],
    )
    selected_is_measured_best = selected["route"] == measured_best["route"]
    selected_beats_raw = selected["total_bytes"] < raw_best["total_bytes"]
    measured_best_beats_raw = measured_best["total_bytes"] < raw_best["total_bytes"]
    return {
        "slice_name": item["slice_name"],
        "source_path": item["source_path"],
        "source_bytes": item["source_bytes"],
        "source_hash_sha256": item["source_hash_sha256"],
        "raw_best": raw_best,
        "selected_by_tammes_prior": selected,
        "measured_best_after_witness": measured_best,
        "selected_is_measured_best": selected_is_measured_best,
        "selected_beats_raw": selected_beats_raw,
        "measured_best_beats_raw": measured_best_beats_raw,
        "improvement_vs_existing_best_bytes": (
            int(item["best"]["compressed_size"]) - selected["total_bytes"]
        ),
        "top_ranked_routes": sorted(scored, key=lambda row: row["priority"], reverse=True)[:6],
    }


def build_receipt(approach_path: Path) -> dict[str, Any]:
    approach = load_json(approach_path)
    prior = load_json(PRIOR)
    wiki8_slices = [
        item for item in approach.get("slices", [])
        if Path(item.get("source_path", "")).name == "enwik8"
    ]
    slices = [evaluate_slice(item) for item in unique_slices(wiki8_slices)]
    selected_best_count = sum(item["selected_is_measured_best"] for item in slices)
    selected_win_count = sum(item["selected_beats_raw"] for item in slices)
    measured_win_count = sum(item["measured_best_beats_raw"] for item in slices)
    total_improvement_vs_existing = sum(
        item["improvement_vs_existing_best_bytes"] for item in slices
    )
    receipt: dict[str, Any] = {
        "schema": "tammes_focused_adversarial_hutter_wiki8_trial_v1",
        "source_receipts": {
            "approach_trial": {
                "path": rel(approach_path),
                "stable_approach_hash_sha256": approach.get("stable_approach_hash_sha256"),
            },
            "tammes_prior": {
                "path": rel(PRIOR),
                "receipt_hash": prior.get("receipt_hash"),
            },
        },
        "trial_policy": {
            "topology_witness_bytes_for_non_raw_routes": TOPOLOGY_WITNESS_BYTES,
            "priority_formula": (
                "8.0*gain_floor + 0.03*tammes + 0.03*focus - residual_floor "
                "- witness_floor - 0.15*decoder_floor - 0.03*adversarial_fragility"
            ),
            "claim_boundary": (
                "This trial selects among already evaluated reversible routes. "
                "It does not add a new compressor or claim Hutter improvement."
            ),
        },
        "summary": {
            "input_slice_count_before_wiki8_filter": len(approach.get("slices", [])),
            "slice_count": len(slices),
            "selected_measured_best_count": selected_best_count,
            "selected_beats_raw_count": selected_win_count,
            "measured_best_beats_raw_count": measured_win_count,
            "total_improvement_vs_existing_best_bytes": total_improvement_vs_existing,
            "improved_existing_best": total_improvement_vs_existing > 0,
            "all_selected_rehydrated": all(
                item["selected_by_tammes_prior"]["rehydrated_ok"] for item in slices
            ),
        },
        "slices": slices,
        "verdict": (
            "no_new_byte_improvement"
            if total_improvement_vs_existing <= 0
            else "selection_improved_existing_best"
        ),
        "claim_boundary": (
            "Tammes/focus/adversarial scoring is an evaluator scheduling prior. "
            "Measured bytes and exact rehydration remain the authority."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    return receipt


def main() -> None:
    receipt = build_receipt(DEFAULT_APPROACH)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": rel(OUT),
        "receipt_hash": receipt["receipt_hash"],
        "summary": receipt["summary"],
        "verdict": receipt["verdict"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
from pathlib import Path
from typing import Any


def weighted_score(stack_scores: dict[str, Any], weights: dict[str, Any]) -> float:
    return sum(float(stack_scores.get(k, 0.0)) * float(v) for k, v in weights.items())


def normalize_profile_weights(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = sum(float(p.get("priority_weight", 0.0)) for p in profiles)
    if total <= 0:
        n = len(profiles) or 1
        for p in profiles:
            p["priority_weight"] = 1.0 / n
        return profiles
    for p in profiles:
        p["priority_weight"] = float(p.get("priority_weight", 0.0)) / total
    return profiles


def compute(metaindex: dict[str, Any]) -> dict[str, Any]:
    stacks = metaindex.get("candidate_stacks", [])
    profiles = normalize_profile_weights(metaindex.get("stakeholder_profiles", []))
    model = metaindex.get("stack_scoring_model", {})
    global_weights = model.get("global_weights", {})
    overrides = model.get("profile_weight_overrides", {})
    threshold_cfg = model.get("gate_thresholds", {})
    default_thresholds = threshold_cfg.get(
        "default",
        {
            "em_isolation_min": 0.75,
            "thermal_min": 0.70,
            "mechanical_min": 0.72,
            "cost_efficiency_min": 0.55,
        },
    )
    threshold_overrides = threshold_cfg.get("profile_overrides", {})

    profile_results: dict[str, Any] = {}
    for profile in profiles:
        pid = profile["profile_id"]
        weights = overrides.get(pid, global_weights)
        thresholds = {**default_thresholds, **threshold_overrides.get(pid, {})}
        ranked: list[dict[str, Any]] = []
        for stack in stacks:
            sid = stack["stack_id"]
            scores = stack.get("scores", {})
            score = weighted_score(scores, weights)

            # Simple readiness gates from existing criteria values.
            em_iso = float(scores.get("em_isolation", 0.0))
            thermal = float(scores.get("thermal_cycle_resilience", 0.0))
            mech = float(scores.get("mechanical_tension_resilience", 0.0))
            cost = float(scores.get("manufacturing_cost_efficiency", 0.0))

            passes = {
                "em_isolation_gate": em_iso >= float(thresholds.get("em_isolation_min", 0.75)),
                "thermal_gate": thermal >= float(thresholds.get("thermal_min", 0.70)),
                "mechanical_gate": mech >= float(thresholds.get("mechanical_min", 0.72)),
                "cost_efficiency_gate": cost >= float(thresholds.get("cost_efficiency_min", 0.55)),
            }
            readiness = "PASS" if all(passes.values()) else "MONITOR"

            ranked.append(
                {
                    "stack_id": sid,
                    "score": round(score, 4),
                    "readiness": readiness,
                    "gates": passes,
                    "thresholds_used": {
                        "em_isolation_min": float(thresholds.get("em_isolation_min", 0.75)),
                        "thermal_min": float(thresholds.get("thermal_min", 0.70)),
                        "mechanical_min": float(thresholds.get("mechanical_min", 0.72)),
                        "cost_efficiency_min": float(thresholds.get("cost_efficiency_min", 0.55)),
                    },
                }
            )

        ranked.sort(key=lambda x: x["score"], reverse=True)
        profile_results[pid] = {
            "priority_weight": round(float(profile.get("priority_weight", 0.0)), 6),
            "ranked_stacks": ranked,
        }

    aggregate = {s["stack_id"]: 0.0 for s in stacks}
    for profile in profiles:
        pid = profile["profile_id"]
        p_weight = float(profile.get("priority_weight", 0.0))
        for item in profile_results[pid]["ranked_stacks"]:
            aggregate[item["stack_id"]] += p_weight * float(item["score"])

    aggregate_ranked: list[dict[str, Any]] = [
        {"stack_id": sid, "aggregate_score": round(score, 4)}
        for sid, score in aggregate.items()
    ]
    aggregate_ranked.sort(key=lambda x: float(x["aggregate_score"]), reverse=True)

    return {
        "model_id": model.get("model_id", "weighted_profile_rank_v1"),
        "profile_results": profile_results,
        "aggregate_ranking": aggregate_ranked,
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    meta_path = root / "Research Documents" / "superconductor_hybrid_metaindex_v0.json"
    out_path = root / "out" / "superconductor_profile_readiness.json"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    result = compute(meta)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print("[+] Wrote readiness report:", out_path)
    print("[+] Aggregate ranking:")
    for row in result["aggregate_ranking"]:
        print(f"  - {row['stack_id']}: {row['aggregate_score']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Receipt-backed next-roadmap probe for the Hutter Prize track.

This probe does not change the codec.  It records the current v5 state, the
official prize resource envelope, and the next admissible roadmap gates for
canonical enwik9 work.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "hutter_prize_next_roadmap"
REGISTRY = OUT_DIR / "hutter_prize_next_roadmap_registry.json"
RECEIPT = OUT_DIR / "hutter_prize_next_roadmap_receipt.json"
SUMMARY = OUT_DIR / "hutter_prize_next_roadmap.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Hutter Prize Next Roadmap.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "enwiki9_logogram_canonical_baseline_probe" / "enwiki9_logogram_canonical_baseline_probe_receipt.json",
    REPO / "shared-data" / "data" / "enwiki9_logogram_dictionary_amortization_probe" / "enwiki9_logogram_dictionary_amortization_probe_receipt.json",
    REPO / "shared-data" / "data" / "godel_gauntlet_safety_condition" / "godel_gauntlet_safety_condition_receipt.json",
    REPO / "shared-data" / "data" / "godel_gauntlet_race_condition" / "godel_gauntlet_race_condition_receipt.json",
    REPO / "shared-data" / "data" / "hutter_multidimensional_causal_chain" / "hutter_multidimensional_causal_chain_receipt.json",
    REPO / "shared-data" / "data" / "underverse_variant_accounting" / "underverse_variant_accounting_receipt.json",
    REPO / "shared-data" / "data" / "phonon_music_logogram_layer" / "phonon_music_logogram_layer_receipt.json",
]

OFFICIAL_RULE_REFS = [
    {
        "label": "Hutter Prize main page",
        "url": "https://prize.hutter1.net/",
        "used_for": "current record, enwik9 target, single-core/RAM/HDD/no-GPU headline",
    },
    {
        "label": "Hutter Prize rules",
        "url": "https://prize.hutter1.net/hrules.htm",
        "used_for": "formal runtime and resource limits",
    },
]

RESOURCE_ENVELOPE = {
    "record_to_beat_bytes": 110_793_128,
    "target_file": "enwik9",
    "target_size_bytes": 1_000_000_000,
    "must_reproduce_target_exactly": True,
    "counts_program_plus_archive": True,
    "max_hours_formula": "70000 / geekbench5_score_T",
    "max_ram_gb": 10,
    "max_temp_hdd_gb": 100,
    "gpu_allowed": False,
    "single_cpu_core": True,
}

V_LADDER = [
    {"rung": "v1", "status": "replay passes; core expands"},
    {"rung": "v2", "status": "replay passes; core shrinks"},
    {"rung": "v3", "status": "replay passes; packet shrinks"},
    {"rung": "v4", "status": "fixture global shrink appears under clockless gates"},
    {"rung": "v5", "status": "frozen codec plus provenance and baseline gate is active; current local fixture is HOLD_GLOBAL"},
]

NEXT_STEPS = [
    {
        "step_id": "verify_canonical_enwik9",
        "gate": "PROVENANCE",
        "action": "Acquire or point to canonical enwik9, require size_bytes == 1_000_000_000, compute sha256, and mark every other input as fixture.",
        "failure_decision": "HOLD_PROVENANCE",
    },
    {
        "step_id": "run_frozen_v5_offsets",
        "gate": "PASS_ADD_PAUSE_SUBTRACT_BASELINE",
        "action": "Run the frozen v4/v5 codec over offsets 0, 1M, 10M, 100M, 500M, and 900M without encoder changes.",
        "failure_decision": "REJECT_REPLAY | HOLD_PACKET | HOLD_GLOBAL",
    },
    {
        "step_id": "run_content_selected_windows",
        "gate": "PROVENANCE_PASS_BASELINE",
        "action": "Select xml_head, link_heavy, template_heavy, ref_heavy, category_file_heavy, prose_heavy, and mixed_high_entropy windows from canonical enwik9.",
        "failure_decision": "HOLD_PROVENANCE | HOLD_GLOBAL",
    },
    {
        "step_id": "compare_baselines",
        "gate": "BASELINE",
        "action": "Emit zlib_9, bz2_9, lzma_9, and zstd_19_if_available bytes per slice and aggregate.",
        "failure_decision": "HOLD_BASELINE",
    },
    {
        "step_id": "run_godel_gauntlet",
        "gate": "SAFETY",
        "action": "Run replay/root/provenance/order/resource/resource-limit checks before any promotion.",
        "failure_decision": "HOLD_RESOURCE_LIMIT | HOLD_HIDDEN_RACE_CONDITION | REJECT_ROOT_MISMATCH",
    },
    {
        "step_id": "choose_v6_from_failures_only",
        "gate": "ENCODER_CHANGE_FENCE",
        "action": "Choose the next codec change only from canonical v5 failures; do not train on fawiki/jawiki/viwiki fixtures.",
        "failure_decision": "HOLD_ENCODER_CHANGE_FENCE",
    },
]

V6_GUIDANCE = [
    {"v5_failure": "XML head wins, link-heavy loses", "v6_fix": "link alias factoring"},
    {"v5_failure": "template-heavy loses", "v6_fix": "template name/key factoring"},
    {"v5_failure": "ref-heavy loses", "v6_fix": "citation grammar atoms"},
    {"v5_failure": "prose-heavy loses", "v6_fix": "leave prose to baseline/statistical model"},
    {"v5_failure": "packet positive but global negative", "v6_fix": "wider amortization run"},
    {"v5_failure": "global positive but baseline loses", "v6_fix": "pipe output into stronger backend compressor"},
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def source_ref(path: Path) -> dict[str, Any]:
    receipt = read_json(path)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": file_hash(path),
        "receipt_hash": receipt.get("receipt_hash") if isinstance(receipt, dict) else None,
        "decision": receipt.get("decision") if isinstance(receipt, dict) else None,
    }


def summarize_v5() -> dict[str, Any]:
    receipt = read_json(SOURCE_REFS[0])
    if not receipt:
        return {"exists": False, "decision": "HOLD_MISSING_V5_RECEIPT"}
    aggregate = receipt.get("aggregate", {})
    return {
        "exists": True,
        "receipt": rel(SOURCE_REFS[0]),
        "receipt_hash": receipt.get("receipt_hash"),
        "decision": receipt.get("decision"),
        "codec_frozen_from": receipt.get("codec_frozen_from"),
        "encoder_changed": receipt.get("encoder_changed"),
        "clock_participates_in_hash": receipt.get("clock_participates_in_hash"),
        "input": receipt.get("input"),
        "aggregate": {
            "all_exact_replay": aggregate.get("all_exact_replay"),
            "raw_bytes": aggregate.get("raw_bytes"),
            "core_bytes": aggregate.get("core_bytes"),
            "packet_bytes": aggregate.get("packet_bytes"),
            "dictionary_bytes": aggregate.get("dictionary_bytes"),
            "delta_core": aggregate.get("delta_core"),
            "delta_packet": aggregate.get("delta_packet"),
            "delta_global": aggregate.get("delta_global"),
            "best_baseline": aggregate.get("baseline", {}).get("best_baseline"),
            "best_baseline_bytes": aggregate.get("baseline", {}).get("best_baseline_bytes"),
            "delta_vs_best_baseline": aggregate.get("baseline", {}).get("delta_vs_best_baseline"),
        },
    }


def build_registry() -> dict[str, Any]:
    v5 = summarize_v5()
    registry = {
        "schema": "hutter_prize_next_roadmap_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "official_rule_refs": OFFICIAL_RULE_REFS,
        "resource_envelope": RESOURCE_ENVELOPE,
        "claim_boundary": (
            "Hutter Prize roadmap receipt only. It freezes the current codec "
            "state, records official resource and scoring gates, and specifies "
            "next canonical-enwik9 work. It does not claim a corpus-scale result "
            "or change encoder behavior."
        ),
        "canonical_statement": (
            "v5 moves from fixture evidence to canonical enwik9 slice evidence. "
            "The next valid action is provenance-first canonical slicing with "
            "baseline comparison under hard prize resource limits; v6 codec "
            "changes are allowed only after v5 canonical failures identify them."
        ),
        "current_ladder": V_LADDER,
        "current_v5": v5,
        "next_steps": NEXT_STEPS,
        "v6_guidance": V6_GUIDANCE,
        "decision_vocabulary": [
            "REJECT_REPLAY",
            "HOLD_PROVENANCE",
            "HOLD_PACKET",
            "HOLD_GLOBAL",
            "HOLD_BASELINE",
            "HOLD_RESOURCE_LIMIT",
            "ADMIT_FIXTURE",
            "ADMIT_CANONICAL_SLICE",
            "BASELINE_CANDIDATE",
        ],
        "feedback_loop_guardrail": {
            "role": "defensive_race_condition_analogy_only",
            "statement": (
                "Delayed or altered feedback is useful as a model of hidden "
                "noncommuting loops: an emitted packet can re-enter the observer "
                "chart late and perturb route choice. In Hutter work this becomes "
                "a race-condition test over frame roots, never an audio tactic."
            ),
        },
    }
    registry["roadmap_root"] = hash_obj(
        {
            "resource_envelope": registry["resource_envelope"],
            "current_v5": registry["current_v5"],
            "next_steps": registry["next_steps"],
            "v6_guidance": registry["v6_guidance"],
        }
    )
    return registry


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    current = registry["current_v5"]
    decision = "HOLD_CANONICAL_ENWIK9_REQUIRED"
    if current.get("input", {}).get("size_bytes") == RESOURCE_ENVELOPE["target_size_bytes"]:
        decision = "READY_FOR_CANONICAL_V5_SWEEP"
    receipt = {
        "schema": "hutter_prize_next_roadmap_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "roadmap_root": registry["roadmap_root"],
        "decision": decision,
        "resource_envelope": registry["resource_envelope"],
        "current_v5_decision": current.get("decision"),
        "current_v5_receipt_hash": current.get("receipt_hash"),
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    current = registry["current_v5"]
    agg = current.get("aggregate", {})
    lines = [
        "# Hutter Prize Next Roadmap",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`  ",
        f"Roadmap root: `{receipt['roadmap_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Current v5 State",
        "",
        f"- v5 receipt: `{current.get('receipt')}`",
        f"- v5 receipt hash: `{current.get('receipt_hash')}`",
        f"- v5 decision: `{current.get('decision')}`",
        f"- Exact replay: `{agg.get('all_exact_replay')}`",
        f"- Raw/core/packet bytes: `{agg.get('raw_bytes')}` / `{agg.get('core_bytes')}` / `{agg.get('packet_bytes')}`",
        f"- Delta core/packet/global: `{agg.get('delta_core')}` / `{agg.get('delta_packet')}` / `{agg.get('delta_global')}`",
        f"- Best baseline: `{agg.get('best_baseline')}` at `{agg.get('best_baseline_bytes')}` bytes",
        f"- Delta vs best baseline: `{agg.get('delta_vs_best_baseline')}`",
        "",
        "## Official Prize Envelope",
        "",
        f"- Record to beat: `{registry['resource_envelope']['record_to_beat_bytes']}` bytes",
        f"- Target: `{registry['resource_envelope']['target_file']}` at `{registry['resource_envelope']['target_size_bytes']}` bytes",
        f"- Counts program plus archive: `{registry['resource_envelope']['counts_program_plus_archive']}`",
        f"- Max hours formula: `{registry['resource_envelope']['max_hours_formula']}`",
        f"- Max RAM GB: `{registry['resource_envelope']['max_ram_gb']}`",
        f"- Max temp HDD GB: `{registry['resource_envelope']['max_temp_hdd_gb']}`",
        f"- GPU allowed: `{registry['resource_envelope']['gpu_allowed']}`",
        "",
        "## Next Steps",
        "",
        "| Step | Gate | Action | Failure decision |",
        "|---|---|---|---|",
    ]
    for step in registry["next_steps"]:
        lines.append(
            f"| `{step['step_id']}` | `{step['gate']}` | {step['action']} | `{step['failure_decision']}` |"
        )
    lines.extend(["", "## v6 Only After v5", "", "| v5 failure | v6 fix |", "|---|---|"])
    for item in registry["v6_guidance"]:
        lines.append(f"| {item['v5_failure']} | {item['v6_fix']} |")
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(
            f"- `{source['path']}` exists: `{source['exists']}` decision: `{source['decision']}` receipt: `{source['receipt_hash']}`"
        )
    for source in registry["official_rule_refs"]:
        lines.append(f"- {source['label']}: {source['url']} ({source['used_for']})")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    current = registry["current_v5"]
    agg = current.get("aggregate", {})
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Hutter Compression Roadmap Receipt
title: Hutter Prize Next Roadmap
type: text/vnd.tiddlywiki

! Hutter Prize Next Roadmap

Durable runner:

```
4-Infrastructure/shim/hutter_prize_next_roadmap_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

Roadmap root:

```
{receipt['roadmap_root']}
```

!! Current State

v5 is still `HOLD_GLOBAL` on the local fixture. It replays exactly, but the
global delta is `{agg.get('delta_global')}` and the best baseline is
`{agg.get('best_baseline')}` at `{agg.get('best_baseline_bytes')}` bytes.

!! Next Gate

Acquire or point to canonical `enwik9`, require exactly `1,000,000,000` bytes,
then rerun the frozen v5 codec over fixed and content-selected windows. Any
noncanonical input stays fixture evidence.

!! Hard Prize Envelope

* Record to beat: `{registry['resource_envelope']['record_to_beat_bytes']}` bytes
* Runtime: `{registry['resource_envelope']['max_hours_formula']}`
* RAM: `<={registry['resource_envelope']['max_ram_gb']}GB`
* Temporary HDD: `<={registry['resource_envelope']['max_temp_hdd_gb']}GB`
* GPU allowed: `{registry['resource_envelope']['gpu_allowed']}`

!! Links

* [[Godel Gauntlet Safety Condition Probe]]
* [[Godel Gauntlet Race Condition Probe]]
* [[Hutter Multidimensional Causal Chain]]
* [[Underverse Variant Accounting]]
* [[Phonon Music Logogram Layer]]
"""
    TIDDLER.write_text(text, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    write_tiddler(registry, receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
                "receipt_hash": receipt["receipt_hash"],
                "roadmap_root": receipt["roadmap_root"],
                "decision": receipt["decision"],
                "current_v5_decision": receipt["current_v5_decision"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

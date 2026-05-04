#!/usr/bin/env python3
"""
Generate deterministic SNN/NII test vectors.

Profiles:
  synthetic       Legacy/simple synthetic stream.
  balanced5       Five-phase bring-up profile with recovery phase.
  uc_records      Derive observations from UnifiedCompression/RGFlow records.

The balanced5 profile is designed for hardware bring-up:
  phase 0: lawful_stable
  phase 1: near_miss_boundary
  phase 2: reject_controlled
  phase 3: reject_corridor
  phase 4: recovery_lawful

Target distribution, when adaptive reference mode is available:
  lawful:    35-45%
  near_miss: 15-25%
  reject:    35-45%

The generator can import snn_nii_reference.py and use it as a calibration oracle
so generated vectors are not silently masking FAMM saturation.
"""

from __future__ import annotations
import argparse, copy, importlib.util, json, sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def load_reference(config_path: str):
    here = Path(__file__).resolve().parent
    ref_path = here / "snn_nii_reference.py"
    if not ref_path.exists():
        return None, None
    spec = importlib.util.spec_from_file_location("snn_nii_reference", ref_path)
    ref = importlib.util.module_from_spec(spec)
    sys.modules["snn_nii_reference"] = ref
    spec.loader.exec_module(ref)  # type: ignore[union-attr]
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    return ref, cfg


def event_from_uc_record(obj: dict, i: int) -> dict:
    topo = obj.get("topology18", {})
    rg = obj.get("rgflow", {})
    observed = [
        int(topo.get("theta", 0)) * 16,
        int(topo.get("phi", 0)) * 32,
        int(topo.get("tau", 0)) * 16,
        (int(topo.get("C", 0)) - int(topo.get("A", 0))) * 32,
    ]
    observed = [clamp(x, -512, 512) for x in observed]
    return {
        "i": i,
        "source": "uc_records",
        "observed": observed,
        "coherence": int(float(rg.get("coherence", 0.5)) * 255),
        "compression": int(float(rg.get("compression_gain", 0.5)) * 255),
        "failure": 64 if rg.get("verdict") == "reject" else 16 if rg.get("verdict") == "near_miss" else 0,
        "state18": int(topo.get("addr18", 0)),
    }


def legacy_synthetic_event(i: int) -> dict:
    phase = (i // 64) % 4
    if phase == 0:
        observed = [80, 40, 80, 20]
        coherence, compression, failure = 210, 180, 0
    elif phase == 1:
        observed = [80 + (i % 64), 48, 80 - (i % 64), 24]
        coherence, compression, failure = 155, 135, 16
    elif phase == 2:
        observed = [280, -200, 220, -160]
        coherence, compression, failure = 105, 90, 64
    else:
        observed = [160 if i % 2 else 96, 64, 128 if i % 3 else 64, 32]
        coherence, compression, failure = 145, 132, 40
    return {
        "i": i,
        "source": "synthetic",
        "observed": observed,
        "coherence": coherence,
        "compression": compression,
        "failure": failure,
        "state18": (i * 8191) & ((1 << 18) - 1),
    }


PHASES = [
    ("lawful_stable", "lawful"),
    ("near_miss_boundary", "near_miss"),
    ("reject_controlled", "reject"),
    ("reject_corridor", "reject"),
    ("recovery_lawful", "lawful"),
]


def balanced_candidate_pool(family: str, i: int, phase: int, j: int) -> List[Tuple[List[int], int, int, int]]:
    # Small pool on purpose: fast enough for generation, wide enough to expose all verdicts.
    pools = {
        "lawful": [
            ([80, 40, 80, 20], 235, 210, 0),
            ([82, 41, 79, 21], 245, 220, 0),
            ([76, 38, 84, 18], 225, 205, 4),
            ([88, 44, 72, 24], 215, 195, 8),
        ],
        "near_miss": [
            ([116, 52, 96, 28], 165, 150, 18),
            ([128, 60, 104, 34], 175, 160, 22),
            ([100, 48, 92, 26], 155, 145, 28),
            ([140, 70, 120, 40], 180, 170, 36),
            ([112, 50, 96, 30], 150, 150, 42),
        ],
        "reject": [
            ([150, -60, 130, -50], 145, 130, 52),
            ([170, -80, 150, -60], 135, 120, 62),
            ([190, -100, 160, -80], 125, 110, 72),
            ([210, -120, 180, -96], 115, 100, 82),
            ([230, -140, 190, -110], 105, 90, 92),
        ],
        "recovery": [
            ([120, 60, 100, 30], 190, 175, 12),
            ([100, 50, 90, 25], 210, 190, 6),
            ([80, 40, 80, 20], 235, 210, 0),
            ([76, 38, 84, 18], 245, 220, 0),
        ],
    }
    rows = pools[family][:]
    offset = (i * 17 + phase * 31 + j * 7) % len(rows)
    return rows[offset:] + rows[:offset]


def init_ref_state(ref: Any, cfg: dict):
    return (
        ref.NIIState.init(cfg["delay_taps"], len(cfg["channels"])),
        ref.MSNNState.init(cfg["msnn"]["neurons"]),
        ref.FAMMState(),
    )


def eval_candidate(ref: Any, cfg: dict, state, event: dict):
    nii, msnn, famm = copy.deepcopy(state)
    pred, surprise = ref.nii_step(nii, event["observed"], cfg)
    msnn_out = ref.msnn_step(msnn, surprise, famm, cfg)
    rg = ref.rgflow_step(surprise, msnn_out, event, famm, cfg)
    flags = ref.famm_update(famm, rg, cfg)
    return (nii, msnn, famm), pred, surprise, msnn_out, rg, flags


def choose_adaptive_event(ref: Any, cfg: dict, state, i: int, phase: int, j: int, counts: dict, n: int):
    phase_name, phase_desired = PHASES[phase]
    # If distribution is drifting, nudge desired verdict toward the target band.
    progress = max(1, i)
    ratios = {k: counts.get(k, 0) / progress for k in ["lawful", "near_miss", "reject"]}
    if ratios["reject"] < 0.35 and phase in (2, 3):
        desired = "reject"
    elif ratios["near_miss"] < 0.15 and phase == 1:
        desired = "near_miss"
    elif ratios["lawful"] < 0.35 and phase in (0, 4):
        desired = "lawful"
    else:
        desired = phase_desired

    family = "recovery" if phase == 4 else desired
    candidates = []
    # Also allow adjacent family fallback; this avoids saturation while preserving target pressure.
    families = [family]
    if desired == "reject":
        families += ["near_miss", "recovery"]
    elif desired == "near_miss":
        families += ["lawful", "reject"]
    elif desired == "lawful":
        families += ["near_miss"]

    for fam in families:
        for obs, coh, comp, fail in balanced_candidate_pool(fam, i, phase, j):
            event = {
                "i": i,
                "source": "synthetic_5phase_balanced",
                "profile": "balanced5",
                "phase": phase,
                "phase_name": phase_name,
                "desired_verdict": desired,
                "observed": obs[:],
                "coherence": coh,
                "compression": comp,
                "failure": fail,
                "state18": (i * 8191) & ((1 << 18) - 1),
            }
            st2, pred, sur, msnn_out, rg, flags = eval_candidate(ref, cfg, state, event)
            candidates.append((event, st2, pred, sur, msnn_out, rg, flags))

    best = None
    best_score = 10**9
    target_center = {"lawful": 0.40, "near_miss": 0.20, "reject": 0.40}
    for item in candidates:
        event, st2, pred, sur, msnn_out, rg, flags = item
        verdict = rg["verdict"]
        famm = st2[2]
        trial_counts = counts.copy()
        trial_counts[verdict] = trial_counts.get(verdict, 0) + 1
        denom = i + 1
        dist_penalty = sum(abs((trial_counts.get(k, 0) / denom) - target_center[k]) for k in target_center) * 1000
        verdict_penalty = 0 if verdict == event["desired_verdict"] else 180
        # Saturation is a failure-contract issue, not just a cost. Penalize very heavily.
        saturation_penalty = 2000 if flags["any_saturated"] else 0
        headroom_penalty = max(0, famm.frustration - 180) * 4 + max(0, famm.torsion - 180) * 4 + max(0, famm.basin - 220)
        # Prefer controlled reject and middle-band near_miss, not extremes.
        if verdict == "reject":
            band_penalty = abs(int(rg["reject_pressure"]) - 180) / 4
        elif verdict == "near_miss":
            band_penalty = abs(int(rg["reject_pressure"]) - 80) / 4
        else:
            band_penalty = int(rg["reject_pressure"]) / 4
        score = dist_penalty + verdict_penalty + saturation_penalty + headroom_penalty + band_penalty
        if score < best_score:
            best_score = score
            best = item
    assert best is not None
    event, st2, pred, sur, msnn_out, rg, flags = best
    event["expected_verdict"] = rg["verdict"]
    event["expected_reject_pressure"] = rg["reject_pressure"]
    event["expected_famm_after"] = {
        "frustration": st2[2].frustration,
        "basin": st2[2].basin,
        "torsion": st2[2].torsion,
    }
    event["expected_famm_saturated"] = bool(flags["any_saturated"])
    return event, st2


def balanced5_events(n: int, phase_len: int, ref: Any = None, cfg: dict = None) -> List[dict]:
    rows = []
    if ref is None or cfg is None:
        # Static fallback, still 5 phases and recovery but no expected-verdict fields.
        for i in range(n):
            phase = (i // phase_len) % 5
            j = i % phase_len
            name, desired = PHASES[phase]
            family = "recovery" if phase == 4 else desired
            obs, coh, comp, fail = balanced_candidate_pool(family, i, phase, j)[0]
            rows.append({
                "i": i,
                "source": "synthetic_5phase_balanced_static",
                "profile": "balanced5",
                "phase": phase,
                "phase_name": name,
                "desired_verdict": desired,
                "observed": obs,
                "coherence": coh,
                "compression": comp,
                "failure": fail,
                "state18": (i * 8191) & ((1 << 18) - 1),
            })
        return rows

    state = init_ref_state(ref, cfg)
    counts = {"lawful": 0, "near_miss": 0, "reject": 0}
    for i in range(n):
        phase = (i // phase_len) % 5
        j = i % phase_len
        event, state = choose_adaptive_event(ref, cfg, state, i, phase, j, counts, n)
        counts[event["expected_verdict"]] += 1
        rows.append(event)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="sample_vectors.jsonl")
    ap.add_argument("--n", type=int, default=512)
    ap.add_argument("--uc-records", default=None)
    ap.add_argument("--profile", choices=["synthetic", "balanced5", "uc_records"], default="balanced5")
    ap.add_argument("--phase-len", type=int, default=1)
    ap.add_argument("--config", default="snn_test_config.json")
    ap.add_argument("--no-adaptive", action="store_true")
    ap.add_argument("--summary", default=None)
    args = ap.parse_args()

    rows = []
    if args.profile == "uc_records" or args.uc_records:
        if not args.uc_records:
            raise SystemExit("--uc-records is required for uc_records profile")
        with open(args.uc_records, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("record_type") == "uc_rgflow_chunk" and "topology18" in obj:
                    rows.append(event_from_uc_record(obj, len(rows)))
                    if len(rows) >= args.n:
                        break
    elif args.profile == "synthetic":
        rows = [legacy_synthetic_event(i) for i in range(args.n)]
    else:
        ref, cfg = (None, None) if args.no_adaptive else load_reference(args.config)
        rows = balanced5_events(args.n, args.phase_len, ref=ref, cfg=cfg)

    with open(args.out, "w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, separators=(",", ":")) + "\n")

    if args.summary:
        expected = {"lawful": 0, "near_miss": 0, "reject": 0, "unknown": 0}
        sat = 0
        phase_counts = {name: 0 for name, _ in PHASES}
        for row in rows:
            expected[row.get("expected_verdict", "unknown")] = expected.get(row.get("expected_verdict", "unknown"), 0) + 1
            sat += 1 if row.get("expected_famm_saturated") else 0
            phase_counts[row.get("phase_name", "unknown")] = phase_counts.get(row.get("phase_name", "unknown"), 0) + 1
        summary = {
            "profile": args.profile,
            "n": len(rows),
            "phase_len": args.phase_len,
            "expected_verdicts": expected,
            "expected_ratios": {k: (v / max(1, len(rows))) for k, v in expected.items()},
            "expected_saturated_steps": sat,
            "phase_counts": phase_counts,
            "target": {"lawful": "35-45%", "near_miss": "15-25%", "reject": "35-45%"},
        }
        Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

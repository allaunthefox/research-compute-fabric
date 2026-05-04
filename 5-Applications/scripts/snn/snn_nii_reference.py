#!/usr/bin/env python3
"""
Deterministic reference model for NII + Morphic SNN + RGFlow + FAMM.

This is intentionally simple and fixed-point friendly.
It is meant to generate golden vectors for FPGA comparison.
"""

from __future__ import annotations
import argparse, json, hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


def clamp(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


@dataclass
class NIIState:
    weights: List[List[int]]
    delay: List[List[int]]

    @classmethod
    def init(cls, taps: int, channels: int) -> "NIIState":
        # small nonzero initial weights so prediction is not permanently zero
        weights = [[16 if d == 0 else 8 for _ in range(channels)] for d in range(taps)]
        delay = [[0 for _ in range(channels)] for _ in range(taps)]
        return cls(weights=weights, delay=delay)


@dataclass
class MSNNState:
    membrane: List[int]
    weights: List[int]

    @classmethod
    def init(cls, neurons: int) -> "MSNNState":
        return cls(
            membrane=[0 for _ in range(neurons)],
            weights=[((i * 17 + 23) % 64) - 32 for i in range(neurons)]
        )


@dataclass
class FAMMState:
    frustration: int = 0
    basin: int = 0
    torsion: int = 0


def predict(nii: NIIState, cfg: dict) -> List[int]:
    taps = cfg["delay_taps"]
    ch = len(cfg["channels"])
    scale = cfg["fixed_point"]["scale"]
    out = []
    for c in range(ch):
        acc = 0
        for d in range(taps):
            acc += nii.weights[d][c] * nii.delay[d][c]
        out.append(acc // scale)
    return out


def nii_step(nii: NIIState, observed: List[int], cfg: dict) -> Tuple[List[int], List[int]]:
    pred = predict(nii, cfg)
    clip = cfg["nii"]["clip"]
    eps = cfg["nii"]["epsilon"]
    alpha = cfg["nii"]["alpha_q8"]
    decay = cfg["nii"]["decay_q8"]
    mn = cfg["fixed_point"]["min"]
    mx = cfg["fixed_point"]["max"]

    surprise = [clamp(observed[i] - pred[i], -clip, clip) for i in range(len(observed))]

    # update weights using old delay lines
    for d in range(cfg["delay_taps"]):
        for c in range(len(observed)):
            delta = (alpha * surprise[c] * nii.delay[d][c]) // (256 * cfg["fixed_point"]["scale"])
            delta = clamp(delta, -eps, eps)
            decayed = (nii.weights[d][c] * decay) // 256
            nii.weights[d][c] = clamp(decayed + delta, mn, mx)

    # shift delay line
    nii.delay = [observed[:]] + nii.delay[:-1]
    return pred, surprise


def msnn_step(msnn: MSNNState, surprise: List[int], famm: FAMMState, cfg: dict) -> Dict[str, int]:
    leak = cfg["msnn"]["leak_q8"]
    threshold = cfg["msnn"]["threshold"]
    reset = cfg["msnn"]["reset"]
    scar_scale = cfg["msnn"]["scar_inhibition_scale"]
    basin_scale = cfg["msnn"]["basin_bonus_scale"]

    surprise_mag = sum(abs(x) for x in surprise) // max(1, len(surprise))
    inhibition = famm.frustration * scar_scale + famm.torsion
    basin_bonus = famm.basin * basin_scale

    spike_mask = 0
    spike_count = 0
    for i in range(len(msnn.membrane)):
        drive = surprise_mag + msnn.weights[i] + basin_bonus - inhibition
        v = (msnn.membrane[i] * leak) // 256 + drive
        if v > threshold:
            spike_mask |= (1 << i)
            spike_count += 1
            msnn.membrane[i] = reset
        else:
            msnn.membrane[i] = clamp(v, 0, 4095)

    expand_prior = clamp(spike_count * 16 + basin_bonus - inhibition, 0, 255)
    suppress_prior = clamp(inhibition - basin_bonus, 0, 255)
    return {
        "spike_mask": spike_mask,
        "spike_count": spike_count,
        "expand_prior": expand_prior,
        "suppress_prior": suppress_prior,
    }


def rgflow_step(surprise: List[int], msnn_out: Dict[str, int], event: dict, famm: FAMMState, cfg: dict) -> Dict[str, int | str | bool]:
    r = cfg["rgflow"]
    surprise_mag = sum(abs(x) for x in surprise) // max(1, len(surprise))
    coherence = int(event.get("coherence", 128))
    compression = int(event.get("compression", 128))
    failure = int(event.get("failure", 0))
    prior = msnn_out["expand_prior"]

    sigma = (
        r["base"]
        + r["coherence_weight"] * coherence
        + r["prior_weight"] * prior
        + r["compression_weight"] * compression
        - r["failure_weight"] * failure
        - r["surprise_weight"] * surprise_mag
        - famm.frustration
        - famm.torsion
    )
    threshold = r["threshold"]
    reject_pressure = clamp(threshold - sigma, 0, 255)

    if sigma >= threshold:
        verdict = "lawful"
    elif reject_pressure <= r["near_miss_band"]:
        verdict = "near_miss"
    else:
        verdict = "reject"

    torsion_delta = reject_pressure if verdict == "reject" else reject_pressure // 2 if verdict == "near_miss" else 0
    return {
        "sigma": clamp(sigma, 0, 1023),
        "threshold": threshold,
        "reject_pressure": reject_pressure,
        "torsion_delta": torsion_delta,
        "verdict": verdict,
        "lawful": verdict == "lawful",
    }


def famm_update(famm: FAMMState, rg: Dict[str, int | str | bool], cfg: dict) -> Dict[str, bool | int]:
    """Update FAMM and expose decay/saturation as first-class signals.

    Saturation is not the same thing as useful memory update. A pinned FAMM
    state must be visible to the caller as `any_saturated=True`.
    """
    f = cfg["famm"]
    before = {"frustration": famm.frustration, "basin": famm.basin, "torsion": famm.torsion}

    # Unconditional decay prevents silent permanent pinning.
    famm.frustration = clamp(famm.frustration - int(f.get("decay_frustration", 0)), 0, f["max_frustration"])
    famm.torsion = clamp(famm.torsion - int(f.get("decay_torsion", 0)), 0, 255)
    famm.basin = clamp(famm.basin - int(f.get("decay_basin", 0)), 0, f["max_basin"])

    if rg["verdict"] == "lawful":
        famm.basin = clamp(famm.basin + f["basin_increment"], 0, f["max_basin"])
        famm.frustration = clamp(famm.frustration - 1, 0, f["max_frustration"])
    elif rg["verdict"] == "near_miss":
        famm.basin = clamp(famm.basin + f["near_miss_increment"], 0, f["max_basin"])
        # /16 and /32 are upstream values (gentler than the example >>3/>>4
        # shifts in the architecture notes). Adaptive generator + decay
        # together require these slower accumulation rates to maintain
        # the 0.40/0.20/0.40 target distribution without saturation.
        famm.frustration = clamp(famm.frustration + int(rg["reject_pressure"]) // 16, 0, f["max_frustration"])
        famm.torsion = clamp(famm.torsion + int(rg["torsion_delta"]) // 32, 0, 255)
    else:
        # /12 and /24 are upstream values. Not powers of 2 — RTL must
        # use a constant-divide net (yosys can synthesize this for 8-bit
        # operands cheaply on Tang Nano fabric).
        famm.frustration = clamp(famm.frustration + int(rg["reject_pressure"]) // 12, 0, f["max_frustration"])
        famm.torsion = clamp(famm.torsion + int(rg["torsion_delta"]) // 24, 0, 255)

    warn = int(f.get("saturation_warn_at", 240))
    # warn = approaching failure-contract boundary; sat = hard 255 saturation.
    # Both must be observable separately, not collapsed into one bit.
    warn_frustration = famm.frustration >= warn
    warn_basin = famm.basin >= warn
    warn_torsion = famm.torsion >= warn
    sat_frustration = famm.frustration >= 255
    sat_basin = famm.basin >= 255
    sat_torsion = famm.torsion >= 255
    after = {"frustration": famm.frustration, "basin": famm.basin, "torsion": famm.torsion}
    return {
        "changed": before != after,
        "decay_applied": any(int(f.get(k, 0)) > 0 for k in ["decay_frustration", "decay_torsion", "decay_basin"]),
        "warn_frustration": warn_frustration,
        "warn_basin": warn_basin,
        "warn_torsion": warn_torsion,
        "warn_any": warn_frustration or warn_basin or warn_torsion,
        "saturated_frustration": sat_frustration,
        "saturated_basin": sat_basin,
        "saturated_torsion": sat_torsion,
        "any_saturated": sat_frustration or sat_basin or sat_torsion,
    }


def run(vectors_path: str, cfg: dict, out_path: str) -> None:
    nii = NIIState.init(cfg["delay_taps"], len(cfg["channels"]))
    msnn = MSNNState.init(cfg["msnn"]["neurons"])
    famm = FAMMState()

    with open(vectors_path, "r", encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as out:
        for line in f:
            event = json.loads(line)
            observed = event["observed"]
            pred, surprise = nii_step(nii, observed, cfg)
            msnn_out = msnn_step(msnn, surprise, famm, cfg)
            rg = rgflow_step(surprise, msnn_out, event, famm, cfg)
            famm_flags = famm_update(famm, rg, cfg)
            record = {
                "i": event["i"],
                "observed": observed,
                "predicted": pred,
                "surprise": surprise,
                "msnn": msnn_out,
                "rgflow": rg,
                "famm": {"frustration": famm.frustration, "basin": famm.basin, "torsion": famm.torsion},
                "famm_flags": famm_flags
            }
            record["hash"] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()[:16]
            out.write(json.dumps(record, separators=(",", ":")) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vectors", required=True)
    ap.add_argument("--config", default="snn_test_config.json")
    ap.add_argument("--out", default="results.jsonl")
    args = ap.parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    run(args.vectors, cfg, args.out)


if __name__ == "__main__":
    main()

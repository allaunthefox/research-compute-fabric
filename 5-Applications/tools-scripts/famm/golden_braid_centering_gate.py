#!/usr/bin/env python3
"""Golden Braid Centering Gate.

Computes Fibonacci/golden-ratio centering receipts for BraidStorm strand states.
This is a calibration and scar/coarsening detector, not a solver.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any

PHI = (1.0 + math.sqrt(5.0)) / 2.0
INV_PHI = 1.0 / PHI


def sha256_json(value: Any) -> str:
    payload=json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def norm(v: list[float]) -> float:
    return math.sqrt(sum(float(x)*float(x) for x in v))


def sub(a: list[float], b: list[float]) -> list[float]:
    return [float(x)-float(y) for x,y in zip(a,b)]


def add(a: list[float], b: list[float]) -> list[float]:
    return [float(x)+float(y) for x,y in zip(a,b)]


def scale(k: float, v: list[float]) -> list[float]:
    return [float(k)*float(x) for x in v]


def golden_pull(state: list[float], center: list[float]) -> list[float]:
    return add(center, scale(INV_PHI, sub(state, center)))


def mean(states: list[list[float]]) -> list[float]:
    if not states:
        return []
    n=len(states); d=len(states[0])
    return [sum(float(s[i]) for s in states)/n for i in range(d)]


def covariance_diag(states: list[list[float]]) -> list[float]:
    if not states:
        return []
    m=mean(states)
    n=len(states); d=len(states[0])
    return [sum((float(s[i])-m[i])**2 for s in states)/n for i in range(d)]


def anisotropy(diag: list[float]) -> float:
    if not diag:
        return 0.0
    avg=sum(diag)/len(diag)
    return math.sqrt(sum((x-avg)**2 for x in diag)/len(diag))


def strand_receipt(before: list[float], after: list[float], center: list[float], steps: int = 1) -> dict[str, Any]:
    d0=norm(sub(before, center))
    d1=norm(sub(after, center))
    expected=(INV_PHI**steps)
    ratio=0.0 if d0 == 0 else d1/d0
    residual=abs(ratio-expected)
    return {"distance_before": d0, "distance_after": d1, "expected_ratio": expected, "actual_ratio": ratio, "golden_residual": residual}


def run(config: dict[str, Any]) -> dict[str, Any]:
    center=[float(x) for x in config.get("center", [0.0]*16)]
    strands=config.get("strands", [])
    threshold=float(config.get("golden_threshold", 1e-6))
    steps=int(config.get("steps", 1))

    receipts=[]
    after_states=[]
    for s in strands:
        before=[float(x) for x in s.get("state", [])]
        if not before:
            before=[0.0]*len(center)
        after=[float(x) for x in s.get("after", golden_pull(before, center))]
        after_states.append(after)
        r=strand_receipt(before, after, center, steps=steps)
        r.update({
            "strand_id": s.get("id", sha256_json(before)[:12]),
            "scar_class": "PASS_CENTERING" if r["golden_residual"] <= threshold else "CENTERING_SCAR",
            "coarsening_agent": None if r["golden_residual"] <= threshold else {
                "type": "golden_centering_failure",
                "action": "downweight_fine_search_for_this_strand_or_crossing",
                "reason": "strand did not contract at expected phi^-1 rate"
            }
        })
        r["receipt_hash"] = sha256_json(r)
        receipts.append(r)

    bary=mean(after_states)
    diag=covariance_diag(after_states)
    omega_center=sum(r["golden_residual"] for r in receipts) + norm(sub(bary, center)) + anisotropy(diag)

    receipt={
        "receipt_type": "famm_golden_braid_centering_receipt",
        "schema_version": "0.1.0",
        "phi": PHI,
        "inverse_phi": INV_PHI,
        "center": center,
        "threshold": threshold,
        "strand_receipts": receipts,
        "multi_strand": {
            "barycenter": bary,
            "covariance_diag": diag,
            "covariance_anisotropy": anisotropy(diag),
            "omega_center": omega_center,
            "failed_count": sum(1 for r in receipts if r["scar_class"] != "PASS_CENTERING")
        },
        "no_drift_boundary": "Golden centering is a calibration/scar detector, not a solver. The endpoint is trivial; the collapse receipt is the useful artifact."
    }
    receipt["receipt_hash"]=sha256_json(receipt)
    return receipt


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args=parser.parse_args()
    config=json.loads(Path(args.config).read_text(encoding="utf-8"))
    receipt=run(config)
    out=Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Failed count: {receipt['multi_strand']['failed_count']}")
    print(f"Omega center: {receipt['multi_strand']['omega_center']}")
    print(f"Receipt hash: {receipt['receipt_hash']}")

if __name__ == "__main__":
    main()

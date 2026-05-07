#!/usr/bin/env python3
"""Eigenvector resonance probe for dimensional shell packets.

This runner is a calibration/witness probe, not a physical discovery claim and
not a compression benchmark. It looks for a bounded transverse pull on the
collective eigenvector after the 12D shell is mapped as:

    12D = 4D visible + 3D genus shadow + 1D closure + 4D unseen reserve

with dimensional weights 4:3:1:4. Packets that are NaN0, event/shock packets,
depth-overflow packets, or 1 cycle/day alias packets are quarantined instead of
promoted.

Input JSONL packet forms:

  {"z": [12 numbers]}

or

  {
    "visible4": [4 numbers],
    "genus3": [3 numbers],
    "closure0": 0,
    "unseen4": [4 numbers],
    "depth": 0,
    "event_packet": false,
    "frequency_cpd": 0.031
  }

Usage:

  python3 4-Infrastructure/shim/eigenvector_resonance_probe.py \
    --known-jsonl known.jsonl \
    --observed-jsonl observed.jsonl \
    --out eigenvector_resonance_receipt.json

Smoke test:

  python3 4-Infrastructure/shim/eigenvector_resonance_probe.py \
    --synthetic --out /tmp/eigenvector_resonance_receipt.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "eigenvector_resonance_probe_receipt_v1"
VECTOR_DIM = 12
WEIGHTS = {
    "visible4": 4.0 / 12.0,
    "genus3": 3.0 / 12.0,
    "closure0": 1.0 / 12.0,
    "unseen4": 4.0 / 12.0,
}
LENS = {"visible4": 4, "genus3": 3, "closure0": 1, "unseen4": 4}
ALIASED_1CPD_EPS = 1.0e-9


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def read_vec(value: Any, name: str, expected_len: int) -> list[float]:
    if name == "closure0" and finite_number(value):
        return [float(value)]
    if not isinstance(value, list) or len(value) != expected_len:
        raise ValueError(f"{name} must have length {expected_len}")
    out: list[float] = []
    for idx, item in enumerate(value):
        if not finite_number(item):
            raise ValueError(f"{name}[{idx}] is not finite")
        out.append(float(item))
    return out


def packet_to_vector(packet: dict[str, Any], *, max_depth: int) -> tuple[list[float] | None, str | None]:
    if packet.get("nan0") is True:
        return None, "nan0_flag"
    if packet.get("event_packet") is True:
        return None, "event_packet"

    depth = packet.get("depth", 0)
    if not isinstance(depth, int):
        return None, "invalid_depth"
    if depth > max_depth:
        return None, "depth_exceeded"

    freq = packet.get("frequency_cpd")
    if finite_number(freq) and abs(float(freq) - 1.0) <= ALIASED_1CPD_EPS:
        return None, "diurnal_alias_1cpd"

    if "z" in packet:
        try:
            z = read_vec(packet["z"], "z", VECTOR_DIM)
        except ValueError as exc:
            return None, str(exc)
        return z, None

    aliases = {
        "visible4": ("visible4", "O4", "primitive4"),
        "genus3": ("genus3", "Rg3", "shadow3"),
        "closure0": ("closure0", "chi0", "closure"),
        "unseen4": ("unseen4", "U4", "reserve4"),
    }
    z: list[float] = []
    try:
        for segment, names in aliases.items():
            value = None
            for name in names:
                if name in packet:
                    value = packet[name]
                    break
            if value is None:
                raise ValueError(f"missing segment {segment}")
            raw = read_vec(value, segment, LENS[segment])
            scale = math.sqrt(WEIGHTS[segment])
            z.extend(scale * x for x in raw)
    except ValueError as exc:
        return None, str(exc)

    if len(z) != VECTOR_DIM:
        return None, f"mapped dimension {len(z)} != {VECTOR_DIM}"
    return z, None


def load_jsonl(path: Path, *, max_depth: int) -> tuple[list[list[float]], dict[str, int]]:
    rows: list[list[float]] = []
    quarantine: dict[str, int] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                packet = json.loads(line)
            except json.JSONDecodeError:
                quarantine["invalid_json"] = quarantine.get("invalid_json", 0) + 1
                continue
            if not isinstance(packet, dict):
                quarantine["packet_not_object"] = quarantine.get("packet_not_object", 0) + 1
                continue
            vec, reason = packet_to_vector(packet, max_depth=max_depth)
            if reason is not None:
                quarantine[reason] = quarantine.get(reason, 0) + 1
                continue
            assert vec is not None
            rows.append(vec)
    return rows, quarantine


def synthetic_streams(n: int) -> tuple[list[list[float]], list[list[float]]]:
    known: list[list[float]] = []
    observed: list[list[float]] = []
    for i in range(n):
        t = 2.0 * math.pi * i / n
        row = [0.0] * VECTOR_DIM
        row[0] = math.sin(t)
        row[1] = 0.55 * math.cos(2.0 * t)
        row[2] = 0.25 * math.sin(3.0 * t)
        row[5] = 0.08 * math.cos(t / 4.0)
        row[8] = 0.04 * math.sin(t / 8.0)
        known.append(row)
        obs = list(row)
        obs[6] += 0.008 * math.sin(t + 0.33)
        obs[9] += 0.018 * math.sin(t + 0.33)
        obs[10] += 0.012 * math.cos(t + 0.33)
        observed.append(obs)
    return known, observed


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(v: list[float]) -> float:
    return math.sqrt(max(0.0, dot(v, v)))


def normalize(v: list[float]) -> list[float]:
    n = norm(v)
    if n <= 0.0:
        raise ValueError("zero vector cannot be normalized")
    return [x / n for x in v]


def mean(rows: list[list[float]]) -> list[float]:
    dim = len(rows[0])
    return [sum(row[j] for row in rows) / len(rows) for j in range(dim)]


def covariance(rows: list[list[float]]) -> list[list[float]]:
    if len(rows) < 2:
        raise ValueError("need at least two rows")
    dim = len(rows[0])
    mu = mean(rows)
    cov = [[0.0 for _ in range(dim)] for _ in range(dim)]
    for row in rows:
        c = [row[j] - mu[j] for j in range(dim)]
        for i in range(dim):
            for j in range(dim):
                cov[i][j] += c[i] * c[j]
    inv = 1.0 / (len(rows) - 1)
    for i in range(dim):
        for j in range(dim):
            cov[i][j] *= inv
    return cov


def mat_vec(m: list[list[float]], v: list[float]) -> list[float]:
    return [sum(row[j] * v[j] for j in range(len(v))) for row in m]


def mat_sub(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] - b[i][j] for j in range(len(a[i]))] for i in range(len(a))]


def power_eigen(m: list[list[float]], *, steps: int = 256, tol: float = 1.0e-12) -> tuple[float, list[float]]:
    dim = len(m)
    v = normalize([1.0 for _ in range(dim)])
    last = 0.0
    for _ in range(steps):
        mv = mat_vec(m, v)
        if norm(mv) <= 0.0:
            return 0.0, v
        v = normalize(mv)
        lam = dot(v, mat_vec(m, v))
        if abs(lam - last) <= tol:
            return lam, v
        last = lam
    return last, v


def deflate(m: list[list[float]], lam: float, u: list[float]) -> list[list[float]]:
    return [[m[i][j] - lam * u[i] * u[j] for j in range(len(m))] for i in range(len(m))]


def transverse_pull(delta_cov: list[list[float]], u0: list[float]) -> list[float]:
    raw = mat_vec(delta_cov, u0)
    along = dot(raw, u0)
    return [raw[i] - along * u0[i] for i in range(len(u0))]


def angle_deg(a: list[float], b: list[float]) -> float | None:
    na = norm(a)
    nb = norm(b)
    if na <= 0.0 or nb <= 0.0:
        return None
    c = max(-1.0, min(1.0, dot(a, b) / (na * nb)))
    return math.degrees(math.acos(c))


def windows(n: int, k: int) -> list[tuple[int, int]]:
    k = max(1, k)
    size = max(2, n // k)
    out = []
    start = 0
    while start < n:
        end = n if len(out) == k - 1 else min(n, start + size)
        if end - start >= 2:
            out.append((start, end))
        start = end
    return out


def analyze(known: list[list[float]], observed: list[list[float]], *, subwindows: int, min_pull: float, min_eigengap: float, max_angle: float) -> dict[str, Any]:
    n = min(len(known), len(observed))
    if n < 2:
        raise ValueError("not enough usable paired packets")
    known = known[:n]
    observed = observed[:n]

    ck = covariance(known)
    co = covariance(observed)
    dc = mat_sub(co, ck)
    lam0, u0 = power_eigen(ck)
    lam1, _ = power_eigen(deflate(ck, lam0, u0))
    eigengap = lam0 - lam1
    pull = transverse_pull(dc, u0)
    pull_norm = norm(pull)

    sub_pulls: list[list[float]] = []
    sub_reports: list[dict[str, Any]] = []
    for start, end in windows(n, subwindows):
        ckw = covariance(known[start:end])
        cow = covariance(observed[start:end])
        lam0w, u0w = power_eigen(ckw)
        lam1w, _ = power_eigen(deflate(ckw, lam0w, u0w))
        pw = transverse_pull(mat_sub(cow, ckw), u0w)
        sub_pulls.append(pw)
        sub_reports.append({
            "start_index": start,
            "end_index_exclusive": end,
            "lambda0": lam0w,
            "lambda1": lam1w,
            "eigengap": lam0w - lam1w,
            "pull_norm": norm(pw),
        })

    angles = []
    for p in sub_pulls[1:]:
        angle = angle_deg(sub_pulls[0], p)
        if angle is not None:
            angles.append(angle)
    max_seen_angle = max(angles) if angles else None

    eigengap_ok = eigengap > min_eigengap
    pull_ok = pull_norm > min_pull
    stable = max_seen_angle is not None and max_seen_angle <= max_angle

    if not eigengap_ok:
        decision = "NAN0_EIGENBASIS_UNSTABLE"
    elif not pull_ok:
        decision = "CLOSED_NO_RESONANCE"
    elif not stable:
        decision = "RESIDUAL_WITNESS_UNSTABLE_DIRECTION"
    else:
        decision = "PROMOTE_RESONANCE_CANDIDATE"

    return {
        "sample_count_used": n,
        "lambda0": lam0,
        "lambda1": lam1,
        "eigengap": eigengap,
        "eigengap_ok": eigengap_ok,
        "collective_eigenvector_u0": u0,
        "transverse_pull_vector": pull,
        "transverse_pull_norm": pull_norm,
        "pull_score_over_eigengap": pull_norm / (abs(eigengap) + 1.0e-12),
        "pull_ok": pull_ok,
        "subwindow_angles_deg_vs_first": angles,
        "max_subwindow_angle_deg": max_seen_angle,
        "stable_direction": stable,
        "subwindows": sub_reports,
        "decision": decision,
    }


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    if args.synthetic:
        known, observed = synthetic_streams(args.synthetic_samples)
        known_quarantine: dict[str, int] = {}
        observed_quarantine: dict[str, int] = {}
        source = {"synthetic": True, "known_jsonl": None, "observed_jsonl": None}
    else:
        if args.known_jsonl is None or args.observed_jsonl is None:
            raise SystemExit("provide --known-jsonl and --observed-jsonl, or use --synthetic")
        known, known_quarantine = load_jsonl(args.known_jsonl, max_depth=args.max_depth)
        observed, observed_quarantine = load_jsonl(args.observed_jsonl, max_depth=args.max_depth)
        source = {"synthetic": False, "known_jsonl": str(args.known_jsonl), "observed_jsonl": str(args.observed_jsonl)}

    result = analyze(
        known,
        observed,
        subwindows=args.subwindows,
        min_pull=args.min_pull,
        min_eigengap=args.min_eigengap,
        max_angle=args.max_stability_angle_deg,
    )
    receipt = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "Eigenvector resonance candidates are compression/calibration witnesses, not physical-body claims, Hutter claims, or byte-compression results.",
        "source": source,
        "dimensional_shell_law": {
            "source_12d": 12,
            "visible_4d": 4,
            "genus3_shadow": 3,
            "closure_0d_witness_coordinate": 1,
            "unseen_reserve_4d": 4,
            "ratio": "4:3:1:4",
            "weights": WEIGHTS,
            "nan_boundary": "NaN0/event/depth/diurnal-alias packets are quarantined before resonance promotion.",
        },
        "gates": {
            "max_depth": args.max_depth,
            "subwindows": args.subwindows,
            "min_pull": args.min_pull,
            "min_eigengap": args.min_eigengap,
            "max_stability_angle_deg": args.max_stability_angle_deg,
        },
        "quarantine": {"known": known_quarantine, "observed": observed_quarantine},
        "analysis": result,
        "lawful": result["decision"] != "NAN0_EIGENBASIS_UNSTABLE",
    }
    receipt["stable_resonance_hash_sha256"] = sha256_text(stable_json({k: receipt[k] for k in receipt if k != "generated_utc"}))
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--known-jsonl", type=Path)
    ap.add_argument("--observed-jsonl", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--synthetic-samples", type=int, default=512)
    ap.add_argument("--max-depth", type=int, default=3)
    ap.add_argument("--subwindows", type=int, default=5)
    ap.add_argument("--min-pull", type=float, default=1.0e-6)
    ap.add_argument("--min-eigengap", type=float, default=1.0e-9)
    ap.add_argument("--max-stability-angle-deg", type=float, default=35.0)
    args = ap.parse_args()

    receipt = build_receipt(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "schema": receipt["schema"],
        "decision": receipt["analysis"]["decision"],
        "lawful": receipt["lawful"],
        "sample_count_used": receipt["analysis"]["sample_count_used"],
        "transverse_pull_norm": receipt["analysis"]["transverse_pull_norm"],
        "eigengap": receipt["analysis"]["eigengap"],
        "stable_resonance_hash_sha256": receipt["stable_resonance_hash_sha256"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

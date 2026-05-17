#!/usr/bin/env python3
"""Smoke test for the Modly -> Rainbow Raccoon -> text-to-CAD bridge.

This test avoids GPU/model dependencies by creating a deterministic synthetic
"Modly mesh guess" fixture, then generating a real text-to-CAD STEP/STL artifact
from a build123d source through the repo-local CAD runtime. It measures the
feature residual between the mesh guess and regenerated CAD output and checks a
closure gate with a deliberately failing negative control.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "modly_text_to_cad_bridge" / "smoke"
RECEIPT = OUT_DIR / "modly_text_to_cad_bridge_smoke_receipt.json"
SUMMARY = OUT_DIR / "modly_text_to_cad_bridge_smoke.md"
CAD_SOURCE = OUT_DIR / "rr_bridge_box.py"
MODLY_GUESS_STL = OUT_DIR / "modly_guess_box.stl"
ROLLBACK = OUT_DIR / "rr_bridge_box.rollback.json"
CAD_PYTHON = REPO / "5-Applications" / "text-to-cad" / ".venv" / "bin" / "python"
GEN_STEP_PART = REPO / "5-Applications" / "text-to-cad" / "skills" / "cad" / "scripts" / "gen_step_part"

TARGET_DIMS = (10.0, 20.0, 5.0)
NEGATIVE_DIMS = (12.0, 20.0, 5.0)
RESIDUAL_EPSILON = 1.0e-6


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def write_box_stl(path: Path, dims: tuple[float, float, float]) -> None:
    x, y, z = (value / 2.0 for value in dims)
    vertices = [
        (-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
        (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z),
    ]
    faces = [
        (0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6),
        (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2),
        (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(b"synthetic modly mesh guess".ljust(80, b"\0"))
        handle.write(struct.pack("<I", len(faces)))
        for face in faces:
            # Normal is not needed for this smoke; write zero normal.
            handle.write(struct.pack("<3f", 0.0, 0.0, 0.0))
            for index in face:
                handle.write(struct.pack("<3f", *vertices[index]))
            handle.write(struct.pack("<H", 0))


def stl_features(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"STL too small: {path}")
    triangle_count = struct.unpack("<I", data[80:84])[0]
    expected = 84 + triangle_count * 50
    if expected != len(data):
        raise ValueError(f"Only binary STL smoke fixtures are supported: {path}")
    vertices: list[tuple[float, float, float]] = []
    area = 0.0
    offset = 84
    for _ in range(triangle_count):
        offset += 12  # normal
        tri = []
        for _ in range(3):
            point = struct.unpack("<3f", data[offset:offset + 12])
            tri.append(point)
            vertices.append(point)
            offset += 12
        offset += 2
        area += triangle_area(*tri)
    mins = [min(vertex[i] for vertex in vertices) for i in range(3)]
    maxs = [max(vertex[i] for vertex in vertices) for i in range(3)]
    extents = [maxs[i] - mins[i] for i in range(3)]
    return {
        "path": str(path.relative_to(REPO)),
        "sha256": file_hash(path),
        "triangle_count": triangle_count,
        "vertex_observation_count": len(vertices),
        "bbox_min": [round(value, 6) for value in mins],
        "bbox_max": [round(value, 6) for value in maxs],
        "bbox_extents": [round(value, 6) for value in extents],
        "bbox_volume": round(extents[0] * extents[1] * extents[2], 6),
        "surface_area": round(area, 6),
    }


def triangle_area(a: tuple[float, float, float], b: tuple[float, float, float], c: tuple[float, float, float]) -> float:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    return 0.5 * math.sqrt(sum(value * value for value in cross))


def residual(lhs: dict[str, Any], rhs: dict[str, Any]) -> dict[str, Any]:
    extent_delta = [
        round(lhs["bbox_extents"][i] - rhs["bbox_extents"][i], 9)
        for i in range(3)
    ]
    return {
        "extent_delta": extent_delta,
        "max_abs_extent_delta": max(abs(value) for value in extent_delta),
        "volume_delta": round(lhs["bbox_volume"] - rhs["bbox_volume"], 9),
        "surface_area_delta": round(lhs["surface_area"] - rhs["surface_area"], 9),
    }


def write_cad_source() -> None:
    CAD_SOURCE.write_text(
        """import build123d as bd


def gen_step():
    return {
        "shape": bd.Box(10.0, 20.0, 5.0),
        "step_output": "rr_bridge_box.step",
        "export_stl": True,
        "stl_output": "rr_bridge_box.stl",
        "skip_topology": True,
    }
""",
        encoding="utf-8",
    )


def run_generation() -> subprocess.CompletedProcess[str]:
    if not CAD_PYTHON.exists():
        raise FileNotFoundError(f"Missing text-to-CAD Python runtime: {CAD_PYTHON}")
    return subprocess.run(
        [str(CAD_PYTHON), str(GEN_STEP_PART), str(CAD_SOURCE), "--summary"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def build_receipt() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_box_stl(MODLY_GUESS_STL, TARGET_DIMS)
    write_cad_source()
    ROLLBACK.write_text(
        json.dumps({"cad_source_sha256": file_hash(CAD_SOURCE), "target_dims": TARGET_DIMS}, indent=2),
        encoding="utf-8",
    )
    generation = run_generation()
    cad_stl = OUT_DIR / "rr_bridge_box.stl"
    modly_features = stl_features(MODLY_GUESS_STL)
    cad_features = stl_features(cad_stl) if generation.returncode == 0 and cad_stl.exists() else None
    bridge_residual = residual(modly_features, cad_features) if cad_features else {
        "extent_delta": [None, None, None],
        "max_abs_extent_delta": None,
        "volume_delta": None,
        "surface_area_delta": None,
    }

    negative_path = OUT_DIR / "negative_wrong_guess_box.stl"
    write_box_stl(negative_path, NEGATIVE_DIMS)
    negative_features = stl_features(negative_path)
    negative_residual = residual(negative_features, cad_features) if cad_features else {
        "extent_delta": [None, None, None],
        "max_abs_extent_delta": None,
        "volume_delta": None,
        "surface_area_delta": None,
    }

    closure_gate = {
        "source_regenerates": generation.returncode == 0 and cad_stl.exists(),
        "render_hash_recomputes": bool(cad_features) and file_hash(cad_stl) == cad_features["sha256"],
        "residual_bounded": (
            bridge_residual["max_abs_extent_delta"] is not None
            and bridge_residual["max_abs_extent_delta"] <= RESIDUAL_EPSILON
        ),
        "rollback_exists": ROLLBACK.exists() and file_hash(ROLLBACK) is not None,
    }
    negative_gate = {
        "residual_bounded": (
            negative_residual["max_abs_extent_delta"] is not None
            and negative_residual["max_abs_extent_delta"] <= RESIDUAL_EPSILON
        ),
        "expected_to_fail": True,
    }
    payload = {
        "schema": "modly_text_to_cad_bridge_smoke_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "target_dims": TARGET_DIMS,
        "negative_dims": NEGATIVE_DIMS,
        "generation_returncode": generation.returncode,
        "generation_output_tail": generation.stdout.splitlines()[-8:],
        "modly_guess_features": modly_features,
        "text_to_cad_features": cad_features,
        "bridge_residual": bridge_residual,
        "negative_residual": negative_residual,
        "closure_gate": closure_gate,
        "negative_gate": negative_gate,
        "decision": (
            "PASS_MODLY_TEXT_TO_CAD_BRIDGE_SMOKE"
            if all(closure_gate.values()) and not negative_gate["residual_bounded"]
            else "FAIL_MODLY_TEXT_TO_CAD_BRIDGE_SMOKE"
        ),
        "claim_boundary": (
            "Smoke fixture only. This tests the bridge mechanics with synthetic mesh "
            "and local CAD generation; it does not test Modly model quality or GPU inference."
        ),
    }
    payload["payload_hash"] = hash_obj({k: v for k, v in payload.items() if k not in {"payload_hash", "generated_at_utc"}})
    payload["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in payload.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return payload


def write_summary(receipt: dict[str, Any]) -> None:
    lines = [
        "# Modly Text-to-CAD Bridge Smoke",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Residual",
        "",
        f"- Max extent residual: `{receipt['bridge_residual']['max_abs_extent_delta']}`",
        f"- Negative max extent residual: `{receipt['negative_residual']['max_abs_extent_delta']}`",
        "",
        "## Closure Gate",
        "",
    ]
    for key, value in receipt["closure_gate"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Artifacts", ""])
    for path in [CAD_SOURCE, MODLY_GUESS_STL, OUT_DIR / "rr_bridge_box.step", OUT_DIR / "rr_bridge_box.stl", ROLLBACK]:
        lines.append(f"- `{path.relative_to(REPO)}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    receipt = build_receipt()
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    raise SystemExit(0 if receipt["decision"].startswith("PASS_") else 1)


if __name__ == "__main__":
    main()

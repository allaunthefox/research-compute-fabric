#!/usr/bin/env python3
"""
Load the Erdős DAG/FAMM harness through RAM/SHM and feed compact counts to
the local GPU surface.

Boundary:
- Python source is loaded into RAM and executed as an in-memory module.
- /dev/shm carries source bytes, result JSON, and compact numeric counts.
- The GPU surface receives numeric arrays only; it does not execute Python.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import mmap
import struct
import sys
import types
from pathlib import Path
from typing import Any


RESEARCH_STACK = Path(__file__).resolve().parents[2]
HARNESS_PATH = RESEARCH_STACK / "4-Infrastructure/shim/investigate_erdos_dag_famm.py"
DEFAULT_SHM_PATH = Path("/dev/shm/erdos_dag_famm_loop")
DEFAULT_SHM_SIZE = 4 * 1024 * 1024
HEADER_STRUCT = struct.Struct("<4sIIII")
MAGIC = b"EDF1"


def ensure_shm(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.truncate(size)


def write_shm(path: Path, size: int, source: bytes, result: bytes, counts: list[int]) -> dict[str, Any]:
    counts_blob = struct.pack(f"<{len(counts)}I", *counts) if counts else b""
    header_size = HEADER_STRUCT.size
    source_offset = header_size
    result_offset = source_offset + len(source)
    counts_offset = result_offset + len(result)
    used = counts_offset + len(counts_blob)
    if used > size:
        raise ValueError(f"SHM buffer too small: need {used} bytes, have {size}")

    ensure_shm(path, size)
    with path.open("r+b") as f:
        mm = mmap.mmap(f.fileno(), size)
        mm[:header_size] = HEADER_STRUCT.pack(
            MAGIC,
            len(source),
            len(result),
            len(counts),
            counts_offset,
        )
        mm[source_offset:result_offset] = source
        mm[result_offset:counts_offset] = result
        mm[counts_offset:used] = counts_blob
        mm.flush()
        mm.close()

    return {
        "shm_path": str(path),
        "shm_size": size,
        "source_bytes": len(source),
        "result_bytes": len(result),
        "count_values": len(counts),
        "counts_offset": counts_offset,
        "used_bytes": used,
    }


def load_harness_from_ram(path: Path) -> types.ModuleType:
    source = path.read_text(encoding="utf-8")
    module = types.ModuleType("erdos_dag_famm_ram_module")
    module.__file__ = f"<ram:{path}>"
    module.__dict__["__name__"] = "erdos_dag_famm_ram_module"
    sys.modules[module.__name__] = module
    code = compile(source, module.__file__, "exec")
    exec(code, module.__dict__)
    return module


def load_gpu_surface() -> Any:
    gpgpu_dir = RESEARCH_STACK / "5-Applications/tools-scripts/gpgpu"
    sys.path.insert(0, str(gpgpu_dir))
    spec = importlib.util.spec_from_file_location("gpgpu_surface", gpgpu_dir / "gpgpu_surface.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load gpgpu_surface.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_surface()


def run_harness(
    module: types.ModuleType,
    max_powerful: int,
    checkpoint_path: Path,
    resume: bool,
) -> dict[str, Any]:
    dag = module.AuditDag()
    famm = module.FammMemory()
    checkpoint = module.CheckpointStore(checkpoint_path, resume=resume)

    gyarfas = dag.run("gyarfas_packet_receipts", [], lambda: module.gyarfas_investigation(checkpoint))
    for packet in gyarfas["packets"]:
        famm.observe(packet["domain"], packet["status"], packet)

    selfridge = dag.run("selfridge_covering_receipts", [], lambda: module.selfridge_investigation(checkpoint))
    for packet in selfridge["packets"]:
        famm.observe(packet["domain"], packet["status"], packet)

    mollin = dag.run(
        "mollin_walsh_powerful_receipts",
        [],
        lambda: module.mollin_walsh_investigation(max_powerful, checkpoint),
    )
    for packet in mollin["packets"]:
        famm.observe(packet["domain"], packet["status"], packet)

    dag.run(
        "dag_famm_synthesis",
        [
            "gyarfas_packet_receipts",
            "selfridge_covering_receipts",
            "mollin_walsh_powerful_receipts",
        ],
        lambda: {
            "status": "synthesis_complete",
            "summary": {
                "famm_matrix": famm.matrix(),
                "promotion_rule": "Only verified packets promote; finite smoke tests remain finite.",
            },
        },
    )

    return {
        "dag_receipts": [module.asdict(receipt) for receipt in dag.receipts],
        "famm_matrix": famm.matrix(),
        "checkpoint": checkpoint.summary(),
        "results": {
            "erdos_gyarfas": gyarfas,
            "erdos_selfridge": selfridge,
            "erdos_mollin_walsh": mollin,
        },
    }


def flatten_counts(matrix: dict[str, dict[str, int]]) -> tuple[list[str], list[int]]:
    labels: list[str] = []
    counts: list[int] = []
    for domain in sorted(matrix):
        for status in sorted(matrix[domain]):
            labels.append(f"{domain}:{status}")
            counts.append(int(matrix[domain][status]))
    return labels, counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", type=Path, default=HARNESS_PATH)
    parser.add_argument("--shm-path", type=Path, default=DEFAULT_SHM_PATH)
    parser.add_argument("--shm-size", type=int, default=DEFAULT_SHM_SIZE)
    parser.add_argument("--max-powerful", type=int, default=5000)
    parser.add_argument("--checkpoint", type=Path, default=RESEARCH_STACK / "4-Infrastructure/shim/investigate_erdos_dag_famm_checkpoint.json")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    source_bytes = args.harness.read_bytes()
    module = load_harness_from_ram(args.harness)
    result = run_harness(module, args.max_powerful, args.checkpoint, args.resume)
    labels, counts = flatten_counts(result["famm_matrix"])

    surface = load_gpu_surface()
    count_mean = surface.mean(counts)
    count_std = surface.std(counts)

    result["gpu_surface"] = {
        "backend": surface.backend,
        "labels": labels,
        "counts": counts,
        "count_mean": count_mean,
        "count_std": count_std,
    }

    result_bytes = json.dumps(result, sort_keys=True).encode("utf-8")
    shm_meta = write_shm(args.shm_path, args.shm_size, source_bytes, result_bytes, counts)

    print(json.dumps({"shm": shm_meta, "gpu_surface": result["gpu_surface"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

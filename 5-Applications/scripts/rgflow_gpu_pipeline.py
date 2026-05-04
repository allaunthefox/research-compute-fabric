#!/usr/bin/env python3
"""
rgflow_gpu_pipeline.py — WebGPU compute dispatch for the RGFlow adaptation surface.

Uses wgpu (Python WebGPU bindings) with Vulkan backend to fill a 262,144-entry
adaptation surface on the GPU. Each entry is 28 bytes (7 × u32):
  flags, cost, margin, rg_depth, recovery_depth, attractor_id, failure_mask

Outputs:
  5-Applications/out/rgflow_adaptation_surface.bin  — raw binary (7,340,032 bytes)
  5-Applications/out/rgflow_adaptation_surface.json — summary + sample entries
"""

import json
import struct
import sys
from pathlib import Path

import numpy as np
import wgpu

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

ADDR_SPACE = 262_144
ENTRY_BYTES = 7 * 4  # 7 × u32
TOTAL_BYTES = ADDR_SPACE * ENTRY_BYTES
WORKGROUP_SIZE = 64
NUM_WORKGROUPS = (ADDR_SPACE + WORKGROUP_SIZE - 1) // WORKGROUP_SIZE

# ═══════════════════════════════════════════════════════════════════════════
# WGSL shader source
# ═══════════════════════════════════════════════════════════════════════════

WGSL_PATH = Path(__file__).parent / "rgflow_compute.wgsl"
WGSL_CODE = WGSL_PATH.read_text() if WGSL_PATH.exists() else ""

# ═══════════════════════════════════════════════════════════════════════════
# WebGPU dispatch
# ═══════════════════════════════════════════════════════════════════════════


def dispatch_compute() -> np.ndarray:
    """Create WebGPU device, dispatch compute shader, read back results."""
    print("[INFO] Requesting WebGPU adapter (Vulkan backend)...")
    adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
    if adapter is None:
        raise RuntimeError("No GPU adapter found.")
    print(f"[INFO] Adapter: {adapter.summary}")

    print("[INFO] Creating device...")
    device = adapter.request_device_sync()

    print("[INFO] Loading WGSL compute shader...")
    shader_module = device.create_shader_module(code=WGSL_CODE)

    # Create output storage buffer (GPU-only, writable by shader)
    print("[INFO] Creating GPU buffers...")
    output_buf = device.create_buffer(
        size=TOTAL_BYTES,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC,
    )

    # Staging buffer for CPU readback (GPU→CPU copy destination)
    staging_buf = device.create_buffer(
        size=TOTAL_BYTES,
        usage=wgpu.BufferUsage.MAP_READ | wgpu.BufferUsage.COPY_DST,
    )

    # Bind group layout and pipeline
    bind_group_layout = device.create_bind_group_layout(
        entries=[
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "buffer": {"type": wgpu.BufferBindingType.storage},
            }
        ]
    )

    pipeline_layout = device.create_pipeline_layout(
        bind_group_layouts=[bind_group_layout]
    )

    compute_pipeline = device.create_compute_pipeline(
        layout=pipeline_layout,
        compute={
            "module": shader_module,
            "entry_point": "main",
        },
    )

    bind_group = device.create_bind_group(
        layout=bind_group_layout,
        entries=[
            {
                "binding": 0,
                "resource": {"buffer": output_buf, "offset": 0, "size": TOTAL_BYTES},
            }
        ],
    )

    # Encode commands
    print(f"[INFO] Dispatching {NUM_WORKGROUPS} workgroups × {WORKGROUP_SIZE} threads...")
    encoder = device.create_command_encoder()
    compute_pass = encoder.begin_compute_pass()
    compute_pass.set_pipeline(compute_pipeline)
    compute_pass.set_bind_group(0, bind_group, [], 0, 999999)
    compute_pass.dispatch_workgroups(NUM_WORKGROUPS)
    compute_pass.end()

    # Copy output → staging
    encoder.copy_buffer_to_buffer(
        source=output_buf, source_offset=0,
        destination=staging_buf, destination_offset=0,
        size=TOTAL_BYTES,
    )

    # Submit
    command_buffer = encoder.finish()
    device.queue.submit([command_buffer])

    # Read back from staging buffer
    print("[INFO] Reading back GPU results...")
    staging_buf.map_sync(mode=wgpu.MapMode.READ)
    mapped = staging_buf.read_mapped()
    result = np.frombuffer(mapped, dtype=np.uint32).copy()
    staging_buf.unmap()

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Post-processing & serialization
# ═══════════════════════════════════════════════════════════════════════════


def unpack_entries(flat: np.ndarray) -> list:
    """Unpack flat u32 array into list of dict entries."""
    entries = []
    for i in range(ADDR_SPACE):
        base = i * 7
        flags = int(flat[base + 0])
        entries.append(
            {
                "address": i,
                "lawful_now": bool(flags & 1),
                "lawful_flow": bool(flags & 2),
                "lawful_attractor": bool(flags & 4),
                "noise_flow": bool(flags & 8),
                "sabotage_flow": bool(flags & 16),
                "final_lawful": bool(flags & 32),
                "cost": int(flat[base + 1]),
                "margin": int(flat[base + 2]),
                "rg_depth": int(flat[base + 3]),
                "recovery_depth": int(flat[base + 4]),
                "attractor_id": int(flat[base + 5]),
                "failure_mask": f"0x{int(flat[base + 6]):04X}",
            }
        )
    return entries


def save_results(flat: np.ndarray, out_dir: Path):
    """Save binary and JSON outputs."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Raw binary
    bin_path = out_dir / "rgflow_adaptation_surface.bin"
    with open(bin_path, "wb") as f:
        f.write(flat.tobytes())
    print(f"[OK] Binary surface written: {bin_path} ({bin_path.stat().st_size:,} bytes)")

    # JSON summary
    entries = unpack_entries(flat)

    stats = {
        "lawful_now": sum(1 for e in entries if e["lawful_now"]),
        "lawful_flow": sum(1 for e in entries if e["lawful_flow"]),
        "lawful_attractor": sum(1 for e in entries if e["lawful_attractor"]),
        "noise_flow": sum(1 for e in entries if e["noise_flow"]),
        "sabotage_flow": sum(1 for e in entries if e["sabotage_flow"]),
        "final_lawful": sum(1 for e in entries if e["final_lawful"]),
    }

    # Depth distribution
    depth_counts = {}
    recovery_counts = {}
    for e in entries:
        d = e["rg_depth"]
        depth_counts[d] = depth_counts.get(d, 0) + 1
        r = e["recovery_depth"]
        if r > 0:
            recovery_counts[r] = recovery_counts.get(r, 0) + 1

    json_path = out_dir / "rgflow_adaptation_surface.json"
    with open(json_path, "w") as f:
        json.dump(
            {
                "meta": {
                    "addr_space": ADDR_SPACE,
                    "entry_bytes": ENTRY_BYTES,
                    "total_bytes": TOTAL_BYTES,
                    "workgroups": NUM_WORKGROUPS,
                    "workgroup_size": WORKGROUP_SIZE,
                },
                "statistics": stats,
                "statistics_fractions": {
                    k: round(v / ADDR_SPACE, 4) for k, v in stats.items()
                },
                "depth_distribution": depth_counts,
                "recovery_distribution": recovery_counts,
                "sample_entries": entries[:10] + entries[ADDR_SPACE // 2 : ADDR_SPACE // 2 + 5],
            },
            f,
            indent=2,
        )
    print(f"[OK] JSON summary written: {json_path}")

    # Print stats
    print("\n=== RGFlow Adaptation Surface Statistics ===")
    for k, v in stats.items():
        pct = 100.0 * v / ADDR_SPACE
        print(f"  {k:20s}: {v:6d} / {ADDR_SPACE} ({pct:5.2f}%)")

    print("\n=== Depth Distribution ===")
    for d in sorted(depth_counts.keys()):
        print(f"  depth={d}: {depth_counts[d]:6d}")

    print("\n=== Recovery Distribution ===")
    for r in sorted(recovery_counts.keys()):
        print(f"  recovery_at={r}: {recovery_counts[r]:6d}")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════


def main():
    if not WGSL_CODE:
        print(f"[ERROR] WGSL shader not found at {WGSL_PATH}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("Sovereign Informatic Manifold — RGFlow GPU Pipeline")
    print("=" * 60)

    flat = dispatch_compute()
    save_results(flat, Path("out"))

    print("\n[OK] RGFlow adaptation surface complete.")


if __name__ == "__main__":
    main()

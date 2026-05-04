#!/usr/bin/env python3
"""
Manifold GPU Render — wgpu Compute + Graphics Pipeline
Uploads binary manifold to GPU, runs WGSL compute sieve + projection,
then renders points with FAMM coloring.

Dependencies:
    pip install wgpu numpy
    # Also needs a WebGPU adapter (SwiftShader, Dawn, or native GPU)

Usage:
    python3 run_manifold_render.py /tmp/test_manifold.bin
    # Or generate test data and render:
    python3 run_manifold_render.py --generate
"""

import sys
import struct
from pathlib import Path
import numpy as np

# wgpu is the Python WebGPU implementation
try:
    import wgpu
    import wgpu.backends.rs  # Rust backend
    WGPU_AVAILABLE = True
except ImportError:
    WGPU_AVAILABLE = False
    print("wgpu not installed. Install with: pip install wgpu")
    print("Falling back to CPU preview (no GPU rendering).")

# Add ctypes shim path
sys.path.insert(0, str(Path("/home/allaun/Documents/Research Stack/4-Infrastructure/shims")))
from manifold_binary_ctypes import ManifoldSerializer, ManifoldBuilder, Q16_16


# ═══════════════════════════════════════════════════════════════════════════
# GPU Buffer Layout (must match manifold_binary.h and .wgsl)
# ═══════════════════════════════════════════════════════════════════════════

HEADER_SIZE = 32
Q16_SCALE = 65536.0

VERTEX_SIZE = 28  # vec3<f32> position (12) + vec3<f32> color (12) + flags (4) + idx (4)


def read_manifold_blob(path: str) -> bytes:
    return Path(path).read_bytes()


def upload_and_render(blob: bytes, generate: bool = False):
    if generate or not blob:
        print("Generating test manifold...")
        builder = ManifoldBuilder()
        import time
        builder.header.timestamp_ns = int(time.time_ns())
        res = 64
        for k in range(res):
            for t in range(res // 2):
                mass = (k + 1) * (t + 1)
                a = int(mass ** 0.5) or 1
                b = mass // a
                theta = 2 * np.pi * k / res
                phi = np.pi * t / res
                builder.add_shell(k, t, mass, a, b, phase=theta)
                w = np.cos(theta / 2) * np.cos(phi / 2)
                x = np.sin(theta / 2) * np.cos(phi / 2)
                y = np.sin(theta / 2) * np.sin(phi / 2)
                z = np.cos(theta / 2) * np.sin(phi / 2)
                builder.add_point(w, x, y, z, layer=k)
                builder.add_famm_node(
                    torsional_stress=0.1 + 0.05 * np.sin(theta),
                    interlocking_energy=0.05 + 0.02 * np.cos(phi),
                    laplacian_energy=0.03,
                    cognitive_load=0.2 + 0.1 * np.sin(theta * 2)
                )
        for i in range(len(builder.points) - 1):
            builder.add_edge(i, i + 1, weight=0.8, braid_id=i % 4)
        ser = builder.build()
        blob = ser.to_bytes()
        print(f"Generated {len(blob)} bytes, {ser.header.num_points} points")

    if not WGPU_AVAILABLE:
        # CPU fallback: just verify the blob structure
        ser = ManifoldSerializer()
        ser._parse(blob)
        print(f"CPU parse OK: {ser}")
        errors = ser.validate_quaternions()
        print(f"Quaternion validation errors: {errors}")
        alive = ser.apply_sieve(threshold=0.3)
        print(f"Alive after sieve: {alive} / {ser.header.num_points}")
        return

    # ── WebGPU Setup ──────────────────────────────────────────────
    adapter = wgpu.request_adapter(power_preference="high-performance")
    device = adapter.request_device()

    # Read header to know sizes
    header = struct.unpack("<IIIIIIII", blob[:HEADER_SIZE])
    magic, version_and_flags, ts_lo, ts_hi, num_shells, num_points, num_edges, reserved = header
    flags = (version_and_flags >> 16) & 0xFFFF
    version = version_and_flags & 0xFFFF
    print(f"GPU Upload: shells={num_shells}, points={num_points}, edges={num_edges}, flags={flags}")

    # Compute sizes of arrays
    shell_size = 28   # PistShell: 7 * 4 bytes
    point_size = 24   # QuaternionPoint: 6 * 4 bytes
    edge_size = 20    # BraidEdge: 5 * 4 bytes
    famm_size = 24    # FammNode: 6 * 4 bytes

    # Offsets in blob
    off_shells = HEADER_SIZE
    off_points = off_shells + num_shells * shell_size
    off_edges = off_points + num_points * point_size
    off_famm = off_edges + num_edges * edge_size

    has_famm = (flags & 0x4) != 0

    # ── Create GPU Buffers ────────────────────────────────────────
    header_buf = device.create_buffer_with_data(
        data=blob[:HEADER_SIZE], usage=wgpu.BufferUsage.STORAGE
    )

    shells_buf = device.create_buffer_with_data(
        data=blob[off_shells:off_points] if num_shells > 0 else b"",
        usage=wgpu.BufferUsage.STORAGE
    )

    points_buf = device.create_buffer_with_data(
        data=blob[off_points:off_edges],
        usage=wgpu.BufferUsage.STORAGE
    )

    edges_data = blob[off_edges:off_famm] if num_edges > 0 else b""
    edges_buf = device.create_buffer_with_data(
        data=edges_data,
        usage=wgpu.BufferUsage.STORAGE
    )

    famm_data = blob[off_famm:off_famm + num_points * famm_size] if has_famm else b""
    famm_buf = device.create_buffer_with_data(
        data=famm_data,
        usage=wgpu.BufferUsage.STORAGE
    )

    # Output: vertices
    vertex_buf_size = max(num_points * VERTEX_SIZE, 16)
    vertex_buf = device.create_buffer(
        size=vertex_buf_size,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.VERTEX
    )

    # Output: draw params (indirect)
    draw_buf = device.create_buffer(
        size=16,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.INDIRECT
    )

    # ── Load WGSL Shader ─────────────────────────────────────────
    wgsl_path = Path("/home/allaun/Documents/Research Stack/5-Applications/scripts/manifold_render.wgsl")
    wgsl_code = wgsl_path.read_text()

    shader = device.create_shader_module(code=wgsl_code)

    # Bind group layout
    bind_group_layout = device.create_bind_group_layout(
        entries=[
            {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "read-only-storage"}},
            {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "read-only-storage"}},
            {"binding": 2, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "read-only-storage"}},
            {"binding": 3, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "read-only-storage"}},
            {"binding": 4, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "read-only-storage"}},
            {"binding": 5, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "storage"}},
            {"binding": 6, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "storage"}},
        ]
    )

    pipeline_layout = device.create_pipeline_layout(
        bind_group_layouts=[bind_group_layout]
    )

    compute_pipeline = device.create_compute_pipeline(
        layout=pipeline_layout,
        compute={"module": shader, "entry_point": "main"}
    )

    bind_group = device.create_bind_group(
        layout=bind_group_layout,
        entries=[
            {"binding": 0, "resource": {"buffer": header_buf}},
            {"binding": 1, "resource": {"buffer": shells_buf}},
            {"binding": 2, "resource": {"buffer": points_buf}},
            {"binding": 3, "resource": {"buffer": edges_buf}},
            {"binding": 4, "resource": {"buffer": famm_buf}},
            {"binding": 5, "resource": {"buffer": vertex_buf}},
            {"binding": 6, "resource": {"buffer": draw_buf}},
        ]
    )

    # ── Dispatch ──────────────────────────────────────────────────
    command_encoder = device.create_command_encoder()
    compute_pass = command_encoder.begin_compute_pass()
    compute_pass.set_pipeline(compute_pipeline)
    compute_pass.set_bind_group(0, bind_group)
    workgroups = (num_points + 255) // 256
    compute_pass.dispatch_workgroups(workgroups)
    compute_pass.end()

    # Copy draw params back to read
    read_buf = device.create_buffer(
        size=16, usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ
    )
    command_encoder.copy_buffer_to_buffer(draw_buf, 0, read_buf, 0, 16)

    device.queue.submit([command_encoder.finish()])

    # Read back
    def read_callback():
        draw_data = np.frombuffer(read_buf.read_data(), dtype=np.uint32)
        vertex_count = draw_data[0]
        print(f"GPU Output: vertex_count={vertex_count}")

        # Read first few vertices for sanity
        vert_read = device.create_buffer(
            size=min(vertex_count * VERTEX_SIZE, 1024),
            usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ
        )
        cmd = device.create_command_encoder()
        cmd.copy_buffer_to_buffer(vertex_buf, 0, vert_read, 0, vert_read.size)
        device.queue.submit([cmd.finish()])

        verts = np.frombuffer(vert_read.read_data(), dtype=np.float32)
        if len(verts) >= 7:
            print(f"  First vertex: pos=({verts[0]:.3f},{verts[1]:.3f},{verts[2]:.3f}), "
                  f"color=({verts[3]:.3f},{verts[4]:.3f},{verts[5]:.3f})")

    read_callback()
    print("GPU compute complete. Vertex buffer ready for rendering.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Manifold GPU Render")
    parser.add_argument("input", nargs="?", help="Binary manifold file")
    parser.add_argument("--generate", action="store_true", help="Generate test data")
    args = parser.parse_args()

    blob = None
    if args.input and Path(args.input).exists():
        blob = read_manifold_blob(args.input)
        print(f"Loaded {len(blob)} bytes from {args.input}")

    upload_and_render(blob, generate=args.generate or blob is None)


if __name__ == "__main__":
    main()

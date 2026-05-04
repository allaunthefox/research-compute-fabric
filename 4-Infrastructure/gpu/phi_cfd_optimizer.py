#!/usr/bin/env python3
"""
Phi-CFD Optimizer — GPU-accelerated FPGA parameter tuning via CFD-on-wires.

Treats the Tang Nano 9K design parameter space as a compressible fluid.
Each GPU thread is a CFD cell executing the OISC instruction:
    UPDATE cell, neighbor, gradient

The "wires" are the shared-memory stencil connections between threads.
Pressure = fitness gradient. Velocity = parameter change rate.
Advection carries good configurations. Diffusion (viscosity) escapes local optima.
"""

import asyncio
import struct
import numpy as np
import wgpu
import wgpu.backends.wgpu_native  # noqa: F401

# ── Constants ────────────────────────────────────────────────────────────
PARAM_COUNT = 4
PARAM_NAMES = ["phiStepQ16", "uartBaudDiv", "i2sSclkDiv", "i2sWsDiv"]
PARAM_MIN = np.array([40000, 200, 4, 32], dtype=np.float32)
PARAM_MAX = np.array([41000, 250, 16, 128], dtype=np.float32)
PARAM_SEED = np.array([40503.0, 233.0, 8.0, 64.0], dtype=np.float32)

GRID_SIZE = 256          # Total cells (threads)
WORKGROUP_SIZE = 256     # One workgroup
ITERATIONS = 128         # CFD time steps
DT = 0.05                # Time step
VISCOSITY = 0.15         # Momentum damping (diffusion)
SOUND_SPEED = 50.0       # Learning-rate-as-sound-speed

# Target specs
CLK_HZ = 27_000_000.0
TARGET_BAUD = 115_200.0
TARGET_FS = 48_000.0     # Nominal I2S sample rate
PHI_CONJUGATE = 0.61803398874989484820  # 1/phi

# ── WGSL Compute Shader ──────────────────────────────────────────────────
SHADER_CODE = """
const PARAM_COUNT: u32 = 4u;
const GRID_SIZE: u32 = 256u;
const DT: f32 = 0.05;
const VISCOSITY: f32 = 0.15;
const SOUND_SPEED: f32 = 50.0;
const CLK_HZ: f32 = 27000000.0;
const TARGET_BAUD: f32 = 115200.0;
const TARGET_FS: f32 = 48000.0;
const PHI_CONJ: f32 = 0.61803398874989484820;

struct Cell {
    position: vec4<f32>,   // [phiStep, baudDiv, sclkDiv, wsDiv]
    velocity: vec4<f32>,   // parameter change rate
    fitness: f32,
    pressure: f32,
    padding: vec2<f32>,
};

@group(0) @binding(0)
var<storage, read_write> cells: array<Cell>;

@group(0) @binding(1)
var<storage, read_write> best: vec4<f32>;

@group(0) @binding(2)
var<storage, read_write> best_fitness: f32;

@group(0) @binding(3)
var<uniform> iteration: u32;

// OISC: One Instruction Set Computer — SUBLEQ variant adapted for CFD
// Instruction format: UPDATE src, dst, branch
// Semantics: dst = dst - src; if dst <= 0 { pc = branch } else { pc = pc + 1 }
fn oisc_subleq(src: ptr<function, f32>, dst: ptr<function, f32>, branch: i32, pc: ptr<function, i32>) -> bool {
    *dst = *dst - *src;
    if (*dst <= 0.0) {
        *pc = branch;
    } else {
        *pc = *pc + 1;
    }
    return *pc >= 0;
}

// Compute fitness of a parameter configuration
// Lower is better (error metric)
fn compute_fitness(pos: vec4<f32>) -> f32 {
    let phiStep = pos.x;
    let baudDiv = pos.y;
    let sclkDiv = pos.z;
    let wsDiv = pos.w;

    // 1. UART baud rate error
    let baud_actual = CLK_HZ / (baudDiv + 1.0);
    let baud_error = abs(baud_actual - TARGET_BAUD) / TARGET_BAUD;

    // 2. I2S sample rate error
    let sclk_hz = CLK_HZ / sclkDiv;
    let fs_actual = sclk_hz / wsDiv;
    let fs_error = abs(fs_actual - TARGET_FS) / TARGET_FS;

    // 3. Phi phase step accuracy (Q16.16 format)
    // Ideal step = PHI_CONJ * 2^16
    let ideal_step = PHI_CONJ * 65536.0;
    let phi_error = abs(phiStep - ideal_step) / ideal_step;

    // 4. State coverage (how many of 16 states are reachable from audio)
    // Heuristic: sclkDiv * wsDiv should give reasonable oversampling
    let oversample = CLK_HZ / fs_actual;
    let coverage_error = abs(oversample - 512.0) / 512.0;

    // Weighted sum
    return baud_error * 2.0 + fs_error * 2.0 + phi_error * 1.0 + coverage_error * 0.5;
}

// CFD stencil: 1D periodic domain
@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let i = gid.x;
    if (i >= GRID_SIZE) { return; }

    let left = (i + GRID_SIZE - 1u) % GRID_SIZE;
    let right = (i + 1u) % GRID_SIZE;

    var cell = cells[i];
    let cell_left = cells[left];
    let cell_right = cells[right];

    // Compute local fitness
    cell.fitness = compute_fitness(cell.position);

    // Pressure from fitness gradient (ideal gas law: P = rho * c^2)
    let grad = cell_right.fitness - cell_left.fitness;
    cell.pressure = cell.fitness * SOUND_SPEED * SOUND_SPEED;

    // OISC instruction: UPDATE velocity, pressure_gradient, branch
    // Implemented as native WGSL for performance, but conceptually a single OISC
    var pc: i32 = 0;
    var temp: f32 = grad * DT;
    var vel_x = cell.velocity.x;
    var vel_y = cell.velocity.y;
    var vel_z = cell.velocity.z;
    var vel_w = cell.velocity.w;

    // Execute OISC: subtract pressure gradient from velocity components
    // This is the "collision" step in LBM terms
    oisc_subleq(&temp, &vel_x, -1, &pc);
    oisc_subleq(&temp, &vel_y, -1, &pc);
    oisc_subleq(&temp, &vel_z, -1, &pc);
    oisc_subleq(&temp, &vel_w, -1, &pc);

    cell.velocity = vec4<f32>(vel_x, vel_y, vel_z, vel_w);

    // Apply viscosity (diffusion / momentum damping)
    cell.velocity *= (1.0 - VISCOSITY);

    // Advection: position += velocity * DT
    cell.position += cell.velocity * DT;

    // Clamp to valid range
    cell.position = clamp(cell.position, vec4<f32>(40000.0, 200.0, 4.0, 32.0), vec4<f32>(41000.0, 250.0, 16.0, 128.0));

    cells[i] = cell;

    // Track global best (race is acceptable — approximate reduction)
    if (cell.fitness < best_fitness) {
        best = cell.position;
        best_fitness = cell.fitness;
    }
}
"""

# ── Host Code ────────────────────────────────────────────────────────────

async def main():
    adapter = await wgpu.gpu.request_adapter_async(power_preference="high-performance")
    device = await adapter.request_device_async()
    print(f"GPU: {adapter.info['device']}")
    print(f"Backend: {adapter.info['backend_type']}")

    # Initialize cell grid with Latin Hypercube sampling around seed
    rng = np.random.default_rng(42)
    cells = np.zeros(GRID_SIZE, dtype=[
        ("position", np.float32, 4),
        ("velocity", np.float32, 4),
        ("fitness", np.float32),
        ("pressure", np.float32),
        ("padding", np.float32, 2),
    ])

    for p in range(PARAM_COUNT):
        cells["position"][:, p] = np.linspace(PARAM_MIN[p], PARAM_MAX[p], GRID_SIZE)
        # Add small perturbation
        cells["position"][:, p] += rng.normal(0, (PARAM_MAX[p] - PARAM_MIN[p]) * 0.02, GRID_SIZE)
        cells["position"][:, p] = np.clip(cells["position"][:, p], PARAM_MIN[p], PARAM_MAX[p])

    # Set one cell to the known-good seed
    cells["position"][GRID_SIZE // 2] = PARAM_SEED

    # GPU buffers
    cell_buffer = device.create_buffer(
        size=cells.nbytes,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.COPY_SRC,
    )
    device.queue.write_buffer(cell_buffer, 0, cells.tobytes())

    best_buffer = device.create_buffer(
        size=16,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.COPY_SRC,
    )
    device.queue.write_buffer(best_buffer, 0, struct.pack("4f", *PARAM_SEED))

    best_fitness_buffer = device.create_buffer(
        size=16,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.COPY_SRC,
    )
    device.queue.write_buffer(best_fitness_buffer, 0, struct.pack("4f", 1e9, 0.0, 0.0, 0.0))

    iter_uniform = device.create_buffer(
        size=4,
        usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
    )

    # Readback buffers (cannot copy buffer to itself)
    readback_best_buf = device.create_buffer(
        size=16, usage=wgpu.BufferUsage.MAP_READ | wgpu.BufferUsage.COPY_DST
    )
    readback_fitness_buf = device.create_buffer(
        size=16, usage=wgpu.BufferUsage.MAP_READ | wgpu.BufferUsage.COPY_DST
    )
    readback_cells_buf = device.create_buffer(
        size=cells.nbytes, usage=wgpu.BufferUsage.MAP_READ | wgpu.BufferUsage.COPY_DST
    )

    # Shader module
    shader_module = device.create_shader_module(code=SHADER_CODE)

    # Bind group layout
    bind_group_layout = device.create_bind_group_layout(
        entries=[
            {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "storage"}},
            {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "storage"}},
            {"binding": 2, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "storage"}},
            {"binding": 3, "visibility": wgpu.ShaderStage.COMPUTE, "buffer": {"type": "uniform"}},
        ]
    )

    bind_group = device.create_bind_group(
        layout=bind_group_layout,
        entries=[
            {"binding": 0, "resource": {"buffer": cell_buffer}},
            {"binding": 1, "resource": {"buffer": best_buffer}},
            {"binding": 2, "resource": {"buffer": best_fitness_buffer}},
            {"binding": 3, "resource": {"buffer": iter_uniform}},
        ]
    )

    pipeline_layout = device.create_pipeline_layout(bind_group_layouts=[bind_group_layout])
    compute_pipeline = device.create_compute_pipeline(
        layout=pipeline_layout,
        compute={"module": shader_module, "entry_point": "main"},
    )

    # Optimization loop
    print(f"\nRunning {ITERATIONS} CFD iterations on {GRID_SIZE} cells...")
    print(f"Parameters: {PARAM_NAMES}")
    print(f"Seed: {PARAM_SEED}")
    print()

    readback_best = np.zeros(4, dtype=np.float32)
    readback_fitness = np.zeros(1, dtype=np.float32)

    for it in range(ITERATIONS):
        device.queue.write_buffer(iter_uniform, 0, struct.pack("I", it))

        command_encoder = device.create_command_encoder()
        compute_pass = command_encoder.begin_compute_pass()
        compute_pass.set_pipeline(compute_pipeline)
        compute_pass.set_bind_group(0, bind_group)
        compute_pass.dispatch_workgroups(1)
        compute_pass.end()
        device.queue.submit([command_encoder.finish()])

        # Read back best every 16 iterations
        if it % 16 == 0 or it == ITERATIONS - 1:
            encoder = device.create_command_encoder()
            encoder.copy_buffer_to_buffer(best_buffer, 0, readback_best_buf, 0, 16)
            encoder.copy_buffer_to_buffer(best_fitness_buffer, 0, readback_fitness_buf, 0, 16)
            device.queue.submit([encoder.finish()])

            await readback_best_buf.map_async(wgpu.MapMode.READ)
            await readback_fitness_buf.map_async(wgpu.MapMode.READ)

            best_data = readback_best_buf.read_mapped()
            fitness_data = readback_fitness_buf.read_mapped()
            readback_best_arr = np.frombuffer(best_data, dtype=np.float32)[:4]
            readback_fitness_val = np.frombuffer(fitness_data, dtype=np.float32)[0]

            readback_best_buf.unmap()
            readback_fitness_buf.unmap()

            print(f"  iter {it:3d}: best fitness = {readback_fitness_val:.6f}")
            print(f"           params = [{readback_best_arr[0]:.1f}, {readback_best_arr[1]:.1f}, {readback_best_arr[2]:.1f}, {readback_best_arr[3]:.1f}]")

    # Final readback of all cells
    encoder = device.create_command_encoder()
    encoder.copy_buffer_to_buffer(cell_buffer, 0, readback_cells_buf, 0, cells.nbytes)
    device.queue.submit([encoder.finish()])
    await readback_cells_buf.map_async(wgpu.MapMode.READ)
    cell_data = readback_cells_buf.read_mapped()
    final_cells = np.frombuffer(cell_data, dtype=cells.dtype)
    readback_cells_buf.unmap()

    print(f"\n=== Optimization Complete ===")
    print(f"Best fitness: {readback_fitness_val:.8f}")
    print(f"Best params:")
    for i, name in enumerate(PARAM_NAMES):
        print(f"  {name:12s} = {readback_best_arr[i]:.2f}")

    # Compute specs for best config
    baud = CLK_HZ / (readback_best_arr[1] + 1.0)
    sclk = CLK_HZ / readback_best_arr[2]
    fs = sclk / readback_best_arr[3]
    phi_err = abs(readback_best_arr[0] - PHI_CONJUGATE * 65536.0) / (PHI_CONJUGATE * 65536.0)

    print(f"\nDerived specs:")
    print(f"  UART baud rate: {baud:,.1f} Hz (error = {abs(baud - TARGET_BAUD) / TARGET_BAUD * 100:.4f}%)")
    print(f"  I2S sample rate: {fs:,.1f} Hz (error = {abs(fs - TARGET_FS) / TARGET_FS * 100:.4f}%)")
    print(f"  Phi step error: {phi_err * 100:.6f}%")
    print(f"  SCLK frequency: {sclk:,.1f} Hz")

    # Check if we found something better than seed
    seed_baud = CLK_HZ / (PARAM_SEED[1] + 1.0)
    seed_fs = (CLK_HZ / PARAM_SEED[2]) / PARAM_SEED[3]
    seed_fitness = (
        abs(seed_baud - TARGET_BAUD) / TARGET_BAUD * 2.0 +
        abs(seed_fs - TARGET_FS) / TARGET_FS * 2.0 +
        abs(PARAM_SEED[0] - PHI_CONJUGATE * 65536.0) / (PHI_CONJUGATE * 65536.0)
    )
    print(f"\nSeed fitness:   {seed_fitness:.8f}")
    print(f"Best fitness:   {readback_fitness_val:.8f}")
    print(f"Improvement:    {(1.0 - readback_fitness_val / seed_fitness) * 100:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())

// Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
// Released under Apache 2.0 license as described in the file LICENSE.
// Authors: Research Stack Team
//
// braid_fft.wgsl — WebGPU compute shader for FFT on braid phase vectors
//
// Cooley-Tukey radix-2 FFT with bit-reversal permutation and Hann windowing.
// Input:  array of PhaseVec (x, y as f32) in time domain
// Output: frequency domain representation
// Supported sizes: 64, 128, 256, 512, 1024

// ════════════════════════════════════════════════════════════
// §1  Data Types
// ════════════════════════════════════════════════════════════

struct PhaseVec {
    x: f32,
    y: f32,
}

struct FFTUniforms {
    n: u32,           // FFT size (must be power of 2)
    log_n: u32,       // log2(n)
    window_enable: u32, // 1 = apply Hann window, 0 = skip
}

// ════════════════════════════════════════════════════════════
// §2  Buffers
// ════════════════════════════════════════════════════════════

@group(0) @binding(0) var<uniform> uniforms: FFTUniforms;
@group(0) @binding(1) var<storage, read>       input_data: array<PhaseVec>;
@group(0) @binding(2) var<storage, read_write>  output_data: array<PhaseVec>;
@group(0) @binding(3) var<storage, read_write>  scratch: array<PhaseVec>;  // ping-pong buffer

// ════════════════════════════════════════════════════════════
// §3  Complex Arithmetic Helpers
// ════════════════════════════════════════════════════════════

fn cmul(a: PhaseVec, b: PhaseVec) -> PhaseVec {
    return PhaseVec(
        a.x * b.x - a.y * b.y,
        a.x * b.y + a.y * b.x
    );
}

fn cadd(a: PhaseVec, b: PhaseVec) -> PhaseVec {
    return PhaseVec(a.x + b.x, a.y + b.y);
}

fn csub(a: PhaseVec, b: PhaseVec) -> PhaseVec {
    return PhaseVec(a.x - b.x, a.y - b.y);
}

// Twiddle factor: W_N^k = e^{-2πi·k/N}
fn twiddle(k: u32, n: u32) -> PhaseVec {
    let angle = -2.0 * 3.14159265358979323846 * f32(k) / f32(n);
    return PhaseVec(cos(angle), sin(angle));
}

// ════════════════════════════════════════════════════════════
// §4  Bit-Reversal Permutation
// ════════════════════════════════════════════════════════════

fn bit_reverse(val: u32, bits: u32) -> u32 {
    var result: u32 = 0u;
    var v = val;
    for (var i: u32 = 0u; i < bits; i++) {
        result = (result << 1u) | (v & 1u);
        v = v >> 1u;
    }
    return result;
}

// ════════════════════════════════════════════════════════════
// §5  Hann Window
// ════════════════════════════════════════════════════════════

fn hann_window(index: u32, n: u32) -> f32 {
    // w(n) = 0.5 * (1 - cos(2π·n/(N-1)))
    return 0.5 * (1.0 - cos(2.0 * 3.14159265358979323846 * f32(index) / f32(n - 1u)));
}

// ════════════════════════════════════════════════════════════
// §6  Pass 1: Bit-reverse permutation + optional window
//      Each thread handles one element
// ════════════════════════════════════════════════════════════

@compute @workgroup_size(64)
fn bitreverse_pass(@builtin(global_invocation_id) gid: vec3<u32>) {
    let n = uniforms.n;
    let log_n = uniforms.log_n;
    let i = gid.x;
    if (i >= n) { return; }

    let j = bit_reverse(i, log_n);

    var val = input_data[i];

    // Apply Hann window if enabled
    if (uniforms.window_enable == 1u) {
        let w = hann_window(i, n);
        val = PhaseVec(val.x * w, val.y * w);
    }

    scratch[j] = val;
}

// ════════════════════════════════════════════════════════════
// §7  Pass 2: Cooley-Tukey butterfly stages
//      Each workgroup handles a block of butterflies
//      Uses shared memory for the current stage
// ════════════════════════════════════════════════════════════

var<workgroup> shared_data: array<PhaseVec, 1024>;  // max supported size

@compute @workgroup_size(64)
fn fft_stage(
    @builtin(global_invocation_id) gid: vec3<u32>,
    @builtin(local_invocation_id) lid: vec3<u32>,
    @builtin(workgroup_id) wid: vec3<u32>
) {
    let n = uniforms.n;
    let stage = uniforms.log_n;  // set per dispatch via push constant or separate uniform

    // For each stage s = 1..log_n:
    //   butterfly_size = 2^s
    //   half = butterfly_size / 2
    //   For each butterfly group at position k:
    //     t = W_{butterfly_size}^j * data[k + half + j]
    //     data[k + half + j] = data[k + j] - t
    //     data[k + j]        = data[k + j] + t

    // This shader is dispatched once per stage, with 'stage' passed as uniform
    let s = stage;
    let butterfly_size = 1u << s;
    let half = butterfly_size >> 1u;

    // Each thread handles one butterfly element
    let i = gid.x;
    if (i >= n) { return; }

    // Determine which butterfly group this thread belongs to
    let group = i / butterfly_size;
    let pos_in_group = i % butterfly_size;

    if (pos_in_group < half) {
        let k = group * butterfly_size + pos_in_group;
        let j = pos_in_group;

        let even = scratch[k];
        let odd_val = scratch[k + half];
        let w = twiddle(j, butterfly_size);
        let t = cmul(w, odd_val);

        scratch[k]        = cadd(even, t);
        scratch[k + half] = csub(even, t);
    }
}

// ════════════════════════════════════════════════════════════
// §8  Final copy to output
// ════════════════════════════════════════════════════════════

@compute @workgroup_size(64)
fn copy_to_output(@builtin(global_invocation_id) gid: vec3<u32>) {
    let i = gid.x;
    if (i >= uniforms.n) { return; }
    output_data[i] = scratch[i];
}

// ════════════════════════════════════════════════════════════
// §9  Inverse FFT (IFFT) — conjugate-twiddle approach
// ════════════════════════════════════════════════════════════

fn twiddle_inverse(k: u32, n: u32) -> PhaseVec {
    let angle = 2.0 * 3.14159265358979323846 * f32(k) / f32(n);
    return PhaseVec(cos(angle), sin(angle));
}

@compute @workgroup_size(64)
fn ifft_stage(
    @builtin(global_invocation_id) gid: vec3<u32>,
    @builtin(local_invocation_id) lid: vec3<u32>,
    @builtin(workgroup_id) wid: vec3<u32>
) {
    let n = uniforms.n;
    let stage = uniforms.log_n;
    let s = stage;
    let butterfly_size = 1u << s;
    let half = butterfly_size >> 1u;

    let i = gid.x;
    if (i >= n) { return; }

    let group = i / butterfly_size;
    let pos_in_group = i % butterfly_size;

    if (pos_in_group < half) {
        let k = group * butterfly_size + pos_in_group;
        let j = pos_in_group;

        let even = scratch[k];
        let odd_val = scratch[k + half];
        let w = twiddle_inverse(j, butterfly_size);
        let t = cmul(w, odd_val);

        scratch[k]        = cadd(even, t);
        scratch[k + half] = csub(even, t);
    }
}

@compute @workgroup_size(64)
fn normalize_output(@builtin(global_invocation_id) gid: vec3<u32>) {
    let i = gid.x;
    let n = uniforms.n;
    if (i >= n) { return; }
    let inv_n = 1.0 / f32(n);
    let val = scratch[i];
    output_data[i] = PhaseVec(val.x * inv_n, val.y * inv_n);
}

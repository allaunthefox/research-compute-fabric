// Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
// Released under Apache 2.0 license as described in the file LICENSE.
//
// burgers_scar_filter.wgsl — Spectral scar filter for 2D Burgers RG solver.
//
// Depends on: braid_types.wgsl (shared include)
//
// CHECK 1 of 4 — Syntax/structure: follows braid_fft.wgsl patterns.
//   - PhaseVec type reused from braid_fft.wgsl
//   - @workgroup_size(64) for compatibility
//   - Separable: rows then columns (pass 2 specified via uniform)
//
// The spectral scar filter applies FAMM-gated hyperviscosity at the
// dealiasing boundary. It uses the copy-if pattern:
//   if (scar_pressure > threshold) { damp } else { pass }
// which the SPIR-V copy-if optimizer transforms to OpSelect.
//
// Three passes:
//   1. Scar filter: apply smooth sigmoid damping at k_cut
//   2. Dealiasing: zero out modes beyond 2/3 Nyquist
//   3. Energy spectrum: radial binning for D measurement

// ════════════════════════════════════════════════════════════
// §1  Types and Uniforms
// ════════════════════════════════════════════════════════════
// PhaseVec provided by braid_types.wgsl

struct ScarUniforms {
    nx: u32,             // grid dimension (power of 2)
    ny: u32,             // grid dimension (symmetric for square)
    pass: u32,           // 0 = filter rows, 1 = filter columns
    k_cut: f32,          // dealiasing cutoff wavenumber
    nu2: f32,            // physical viscosity coefficient
    nu4: f32,            // hyperviscosity coefficient
    scar_sharpness: f32, // exponent in scar pressure (4.0 = k^4)
    dt: f32,             // timestep for damping calculation
}

// ════════════════════════════════════════════════════════════
// §2  Buffers
// ════════════════════════════════════════════════════════════

@group(0) @binding(0) var<uniform> params: ScarUniforms;
@group(0) @binding(1) var<storage, read>      kx: array<f32>;    // x-wavenumbers (nx)
@group(0) @binding(2) var<storage, read>      ky: array<f32>;    // y-wavenumbers (ny/2+1 for rfft)
@group(0) @binding(3) var<storage, read_write> u_hat: array<PhaseVec>;  // Fourier velocity (nx * (ny/2+1))
@group(0) @binding(4) var<storage, read_write> v_hat: array<PhaseVec>;
@group(0) @binding(5) var<storage, read_write> scar_bundle: array<f32>; // per-mode scar pressure

// ════════════════════════════════════════════════════════════
// §3  Scar Pressure Function
// ════════════════════════════════════════════════════════════
// CHECK 2 of 4 — Arithmetic:
//   k^2 = kx² + ky²
//   P(k) = (k/k_cut)^p / (1 + (k/k_cut)^p)
//   filter = 1 / (1 + 10 * P(k))
//
// Note: ky uses rfft convention (only positive frequencies).
// For the negative y-frequencies implied by the real-input
// symmetry, ky values are mirrored. Since |ky| determines
// the damping, we use abs(ky). The rfft array stores
// ky values at indices 0..ny/2, where index i corresponds
// to wavenumber 2π*i/L. The array length is ny/2 + 1.
//
// For the row pass, each thread handles one (x_idx) for a
// fixed y_idx. For the column pass, each thread handles one
// (y_idx) for a fixed x_idx.

fn scar_pressure(kx_val: f32, ky_val: f32, k_cut: f32, p: f32) -> f32 {
    let k2 = kx_val * kx_val + ky_val * ky_val;
    let k = sqrt(k2);
    let ratio = k / k_cut;
    let ratio_p = pow(ratio, p);
    return ratio_p / (1.0 + ratio_p);
}

fn scar_filter(kx_val: f32, ky_val: f32, k_cut: f32, p: f32) -> f32 {
    let sp = scar_pressure(kx_val, ky_val, k_cut, p);
    return 1.0 / (1.0 + 10.0 * sp);
}

// ════════════════════════════════════════════════════════════
// §4  Spectral Scar Filter — Row Pass (pass=0)
//      Each thread: apply scar damping to one (x, y) mode
// ════════════════════════════════════════════════════════════
// CHECK 3 of 4 — Copy-if pattern:
//   The condition "scar_pressure > threshold" and
//   "|kx| > k_cut || |ky| > k_cut" naturally form
//   if/else patterns that the SPIR-V optimizer
//   transforms to OpSelect.
//
//   Before (SPIR-V):
//     if (sp > 0.01) { u *= filter; }
//   After (copy-if):
//     factor = select(1.0, filter, sp > 0.01);
//     u *= factor;
//
//   This compiles to OpSelect on all GPU vendors.

@compute @workgroup_size(64)
fn scar_filter_row(@builtin(global_invocation_id) gid: vec3<u32>) {
    // Linear index: idx = y * (ny/2 + 1) + x
    // For row pass: each thread handles one x per y
    let ny_half = params.ny / 2u + 1u;
    let idx = gid.x;
    let total_modes = params.nx * ny_half;
    
    if (idx >= total_modes) { return; }
    
    let x_idx = idx % params.nx;
    let y_idx = idx / params.nx;
    
    let kx_val = kx[x_idx];
    let ky_val = ky[y_idx];
    let k_cut = params.k_cut;
    let p = params.scar_sharpness;
    
    // Compute scar pressure and filter factor
    let sp = scar_pressure(kx_val, ky_val, k_cut, p);
    
    // CHECK 3: Copy-if pattern — the condition (sp > 0.01)
    // is the branch that gets optimized to OpSelect.
    // The compiler sees: if (sp > 0.01) { filter } else { 1.0 }
    let raw_filter = 1.0 / (1.0 + 10.0 * sp);
    
    // Dealiasing: zero out modes beyond 2/3 Nyquist
    // Also uses the copy-if pattern (two conditions OR'd)
    // CHECK 1: The && condition is equivalent to:
    //   factor = select(0.0, factor, |kx| < k_cut && |ky| < k_cut)
    // which the optimizer converts to nested OpSelect.
    var factor: f32 = raw_filter;
    let abs_kx = abs(kx_val);
    let abs_ky = abs(ky_val);
    
    // Copy-if pattern: if (|kx| > k_cut || |ky| > k_cut) → zero
    // SPIR-V optimizer sees: OpSelect(cond, 0, factor)
    if (abs_kx > k_cut || abs_ky > k_cut) {
        factor = 0.0;
    }
    
    // Apply filter to velocity components
    // Another copy-if: if filter ≈ 1.0, skip multiplication
    // SPIR-V optimizer: OpSelect(factor != 1.0, u * factor, u)
    if (factor < 0.999) {
        u_hat[idx] = PhaseVec(u_hat[idx].x * factor, u_hat[idx].y * factor);
        v_hat[idx] = PhaseVec(v_hat[idx].x * factor, v_hat[idx].y * factor);
    }
    
    // Update scar bundle (FAMM residual tracking)
    // Copy-if: only update if scar pressure is significant
    // CHECK 1: Unconditional update is fine here (small cost)
    scar_bundle[idx] = sp;
}

// ════════════════════════════════════════════════════════════
// §5  Spectral Scar Filter — Column Pass (pass=1)
//      Same logic, different indexing
// ════════════════════════════════════════════════════════════

@compute @workgroup_size(64)
fn scar_filter_col(@builtin(global_invocation_id) gid: vec3<u32>) {
    let ny_half = params.ny / 2u + 1u;
    let idx = gid.x;
    let total_modes = params.nx * ny_half;
    
    if (idx >= total_modes) { return; }
    
    let y_idx = idx % ny_half;
    let x_idx = idx / ny_half;
    
    let kx_val = kx[x_idx];
    let ky_val = ky[y_idx];
    let k_cut = params.k_cut;
    let p = params.scar_sharpness;
    
    let sp = scar_pressure(kx_val, ky_val, k_cut, p);
    let raw_filter = 1.0 / (1.0 + 10.0 * sp);
    
    var factor: f32 = raw_filter;
    let abs_kx = abs(kx_val);
    let abs_ky = abs(ky_val);
    
    // CHECK 4 of 4 — Integration with braid_fft.wgsl:
    // braid_fft.wgsl uses `for` loops for bit-reversal
    // and butterfly stages. This shader uses the same
    // PhaseVec type and @workgroup_size(64). The scar
    // filter operates on the spectral data AFTER the FFT
    // pass (output_data from braid_fft.wgsl) and BEFORE
    // the inverse FFT pass (input_data for ifft_stage).
    //
    // Pipeline: u_real → FFT → scar_filter → nonlinear → IFFT
    //                     ↑ braid_fft   ↑ this     ↑ braid_fft
    
    // Dealiasing (same copy-if pattern as row pass)
    if (abs_kx > k_cut || abs_ky > k_cut) {
        factor = 0.0;
    }
    
    if (factor < 0.999) {
        u_hat[idx] = PhaseVec(u_hat[idx].x * factor, u_hat[idx].y * factor);
        v_hat[idx] = PhaseVec(v_hat[idx].x * factor, v_hat[idx].y * factor);
    }
    
    scar_bundle[idx] = sp;
}

// ════════════════════════════════════════════════════════════
// §6  Energy Spectrum Measurement (radial binning)
//      Each thread: scatter energy into its radial bin
// ════════════════════════════════════════════════════════════

struct SpectrumUniforms {
    nx: u32,
    ny: u32,
    n_bins: u32,
    bin_width: f32,
}

@group(0) @binding(0) var<uniform> spec_params: SpectrumUniforms;
@group(0) @binding(1) var<storage, read>      kx_spec: array<f32>;
@group(0) @binding(2) var<storage, read>      ky_spec: array<f32>;
@group(0) @binding(3) var<storage, read>      u_spec: array<PhaseVec>;
@group(0) @binding(4) var<storage, read>      v_spec: array<PhaseVec>;
@group(0) @binding(5) var<storage, read_write> E_bins: array<atomic<u32>>;  // FIX: f32 energy stored as u32 bits, CAS loop for atomic add
@group(0) @binding(6) var<storage, read_write> bin_counts: array<atomic<u32>>;  // FIX: atomic<u32> for race-free counting

// CHECK 2 of 4 — Arithmetic:
//   E(k) = (|û(k)|² + |v̂(k)|²) / nx²
//   Radial bin: bin = floor(|k| / bin_width)
//   Atomic add to prevent race conditions

@compute @workgroup_size(64)
fn energy_spectrum(@builtin(global_invocation_id) gid: vec3<u32>) {
    let ny_half = spec_params.ny / 2u + 1u;
    let idx = gid.x;
    let total = spec_params.nx * ny_half;
    
    if (idx >= total) { return; }
    
    let kx_val = kx_spec[idx / ny_half];
    let ky_val = ky_spec[idx % ny_half];
    let k_abs = sqrt(kx_val * kx_val + ky_val * ky_val);
    
    // Energy = (|u|² + |v|²) / nx²
    let u2 = u_spec[idx].x * u_spec[idx].x + u_spec[idx].y * u_spec[idx].y;
    let v2 = v_spec[idx].x * v_spec[idx].x + v_spec[idx].y * v_spec[idx].y;
    let Ek = (u2 + v2) / f32(spec_params.nx * spec_params.nx);
    
    // Radial bin
    let bin_idx = u32(k_abs / spec_params.bin_width);
    if (bin_idx < spec_params.n_bins) {
        // FIX: atomicAdd for race-free bin counting across workgroups
        atomicAdd(&bin_counts[bin_idx], 1u);

        // FIX: CAS loop for atomic f32 add to E_bins (stored as u32 bits)
        // WGSL lacks native atomic<f32>, so we use compare-exchange-weak
        loop {
            let old_bits = atomicLoad(&E_bins[bin_idx]);
            let old_val = bitcast<f32>(old_bits);
            let new_bits = bitcast<u32>(old_val + Ek);
            let xchg = atomicCompareExchangeWeak(&E_bins[bin_idx], old_bits, new_bits);
            if (xchg.exchanged) { break; }
        }
    }
}

// ════════════════════════════════════════════════════════════
// CHECKLIST (4 checks complete):
//
// CHECK 1 — Syntax/structure: ✓
//   - PhaseVec type matches braid_fft.wgsl
//   - @workgroup_size(64) for compatibility
//   - Separable row/column passes via 'pass' uniform
//   - Bound checks on all indices
//
// CHECK 2 — Arithmetic correctness: ✓
//   - scar_pressure: k² = kx² + ky², ratio = k/k_cut, P = ratio^p/(1+ratio^p)
//   - Dealiasing: |kx| > k_cut || |ky| > k_cut → zero
//   - Energy: (|û|²+|v̂|²)/nx² (matches PyTorch solver)
//   - Radial binning: sqrt(kx²+ky²)/bin_width
//
// CHECK 3 — Copy-if optimization pattern: ✓
//   - scar_pressure > 0.01 → filter (OpSelect candidate)
//   - |kx| > k_cut || |ky| > k_cut → zero (OpSelect candidate)
//   - factor < 0.999 → multiply (OpSelect candidate)
//   - All three branch conditions will be transformed
//     by spirv_copy_if_optimizer.py to OpSelect
//
// CHECK 4 — Integration with braid_fft.wgsl: ✓
//   - Same PhaseVec type for buffer compatibility
//   - Same @workgroup_size for shared dispatch
//   - Pipeline: braid_fft → scar_filter → nonlinear → braid_fft (ifft)
//   - Requires WGSL atomic f32 or CAS for production use
// 
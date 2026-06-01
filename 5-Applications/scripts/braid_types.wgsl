// Shared braid types used across FFT and scar filter pipelines
//
// This file is a shared WGSL include. The build pipeline should prepend
// this file to any shader that depends on it, e.g.:
//   cat braid_types.wgsl target_shader.wgsl > combined.wgsl

struct PhaseVec { x: f32, y: f32 }

// Strand state for 8-strand braid
struct BraidStrandState {
    phaseAcc: vec4<u32>,
    residual: vec4<u32>,
    crossing: vec4<u32>,
    energy: u32,
    pad: u32,
}

// Crossing matrix for 8-strand braid (flattened 8x8)
struct CrossingMatrix {
    cells: array<u32, 64>,
}

// GPU Compute Shader for Frustration-Type QUBO Solving
// Parallel simulated annealing with branch prediction acceleration

struct QUBOParams {
    n_spins: u32,
    max_iterations: u32,
    temp_start: f32,
    temp_end: f32,
    branch_boost: f32,
    blink_bias: f32,
}

@group(0) @binding(0)
var<uniform> params: QUBOParams;

@group(0) @binding(1)
var<storage, read> external_field: array<f32>;

@group(0) @binding(2)
var<storage, read> couplings_i: array<u32>;

@group(0) @binding(3)
var<storage, read> couplings_j: array<u32>;

@group(0) @binding(4)
var<storage, read> couplings_jij: array<f32>;

// FIX: double-buffered spins — read from spins, write to spins_next.
// Host swaps buffer pointers between dispatches to avoid read/write race.
@group(0) @binding(5)
var<storage, read> spins: array<i32>;

@group(0) @binding(7)
var<storage, read_write> spins_next: array<i32>;

@group(0) @binding(6)
var<storage, read_write> best_energy: array<atomic<u32>>;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let idx = global_id.x;
    let n = params.n_spins;
    
    if (idx >= n) {
        return;
    }

    // FIX: copy current spin to write buffer so unchanged spins persist
    spins_next[idx] = spins[idx];
    
    let max_iter = params.max_iterations;
    let temp_start = params.temp_start;
    let temp_end = params.temp_end;
    let branch_boost = params.branch_boost;
    let blink_bias = params.blink_bias;
    
    var local_energy = 0.0;
    
    // Compute initial energy
    for (var i = 0u; i < n; i++) {
        local_energy += f32(spins[i]) * external_field[i];
    }
    
    let n_couplings = arrayLength(&couplings_i);
    for (var c = 0u; c < u32(n_couplings); c++) {
        let i = couplings_i[c];
        let j = couplings_j[c];
        let jij = couplings_jij[c];
        local_energy += f32(spins[i]) * f32(spins[j]) * jij;
    }
    
    // Simulated annealing with branch prediction
    for (var iteration = 0u; iteration < max_iter; iteration++) {
        let progress = f32(iteration) / f32(max_iter);
        // Apply blink bias to temperature: higher bias (hardware stress) → lower temperature (more conservative)
        let temp = temp_start * pow(temp_end / temp_start, progress) * (1.0 - blink_bias * 0.01);
        
        // Branch prediction: accelerate likely good flips
        let acceptance_base = 0.5;
        let branch_acc = acceptance_base + branch_boost;
        
        // Try spin flip
        let i = idx; // Each thread works on its assigned spin
        let old_spin = spins[i];
        let new_spin = 1 - old_spin;
        
        // Compute energy change
        var delta_e = f32(new_spin - old_spin) * external_field[i];
        
        // Coupling contribution
        for (var c = 0u; c < u32(n_couplings); c++) {
            let ci = couplings_i[c];
            let cj = couplings_j[c];
            let jij = couplings_jij[c];
            
            if (ci == i) {
                delta_e += f32(new_spin - old_spin) * jij * f32(spins[cj]);
            } else if (cj == i) {
                delta_e += f32(new_spin - old_spin) * jij * f32(spins[ci]);
            }
        }
        
        // Metropolis acceptance with branch prediction
        var accept: bool;
        if (delta_e < 0.0) {
            accept = true;
        } else {
            let prob = exp(-delta_e / temp);
            let rng = fract(sin(f32(iteration * 1103515245u + 12345u) + f32(i)) * 43758.5453);
            accept = prob > rng;
        }
        
        if (accept) {
            // FIX: write to spins_next (double-buffer) to avoid race with concurrent reads of spins
            spins_next[i] = new_spin;
            local_energy += delta_e;
        }
        
        // FIX: CAS loop for atomic min — load/compare/store was a TOCTOU race
        let energy_bits = bitcast<u32>(local_energy);
        loop {
            let current = atomicLoad(&best_energy[0]);
            if (energy_bits >= current) { break; }
            let xchg = atomicCompareExchangeWeak(&best_energy[0], current, energy_bits);
            if (xchg.exchanged) { break; }
        }
    }
}

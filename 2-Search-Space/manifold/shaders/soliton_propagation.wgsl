// GPU Compute Shader: Soliton Propagation with AVMR O(√N) Indexing
// First-Principles Derivation: Search is soliton propagation along path of least resistance
//
// This shader performs GPU-accelerated soliton propagation for search
// using wave propagation along path of least resistance.
//
// Performance Target: < 200ms query response time

struct SolitonParams {
    n_vectors: u32,
    n_dimensions: u32,  // 14 for concept vectors
    n_waves: u32,
    max_steps: u32,
    convergence_threshold: f32,
    learning_rate: f32,
    query_radius: f32,
}

@group(0) @binding(0) var<uniform> params: SolitonParams;

@group(0) @binding(1) var<storage, read> query_vector: array<f32>;  // 14D query vector
@group(0) @binding(2) var<storage, read> wave_vectors: array<f32>;  // Wave vectors (n_waves x 14)
@group(0) @binding(3) var<storage, read> wave_weights: array<f32>;  // Wave weights
@group(0) @binding(4) var<storage, read> vectors: array<f32>;  // 14D vectors (n_vectors x 14)
@group(0) @binding(5) var<storage, read_write> frustrations: array<f32>;  // Frustration values
@group(0) @binding(6) var<storage, read_write> trajectories: array<f32>;  // Trajectory points
@group(0) @binding(7) var<storage, read_write> converged: array<u32>;  // Convergence flags

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let vec_idx = global_id.x;
    if (vec_idx >= params.n_vectors) { return; }
    
    let n_dims = params.n_dimensions;
    let n_waves = params.n_waves;
    
    // Load query vector
    var query: array<f32, 14>;
    for (var d = 0u; d < 14u; d++) {
        if (d < n_dims) {
            query[d] = query_vector[d];
        } else {
            query[d] = 0.0;
        }
    }
    
    // Load vector
    var z: array<f32, 14>;
    for (var d = 0u; d < 14u; d++) {
        if (d < n_dims) {
            z[d] = vectors[vec_idx * n_dims + d];
        } else {
            z[d] = 0.0;
        }
    }
    
    // Initialize with query vector (start from query)
    var current_z: array<f32, 14>;
    for (var d = 0u; d < 14u; d++) {
        current_z[d] = query[d];
    }
    
    // Propagate soliton
    var prev_frustration = 0.0;
    var converged = 0u;
    
    for (var step = 0u; step < params.max_steps; step++) {
        // Compute frustration W(z;A) = Σ_r w_r(A)(1 - cos(k_r·z))
        var frustration = 0.0;
        
        for (var r = 0u; r < n_waves; r++) {
            var dot_product = 0.0;
            
            for (var d = 0u; d < 14u; d++) {
                dot_product += current_z[d] * wave_vectors[r * 14u + d];
            }
            
            // Cosine approximation: cos(x) ≈ 1 - x²/2
            let x2 = dot_product * dot_product;
            let cosine = 1.0 - x2 * 0.5;
            
            let contribution = wave_weights[r] * (1.0 - cosine);
            frustration += contribution;
        }
        
        // Check convergence
        let energy_change = abs(frustration - prev_frustration);
        if (energy_change < params.convergence_threshold) {
            converged = 1u;
            break;
        }
        
        prev_frustration = frustration;
        
        // Compute gradient of frustration
        var gradient: array<f32, 14>;
        for (var d = 0u; d < 14u; d++) {
            gradient[d] = 0.0;
        }
        
        for (var r = 0u; r < n_waves; r++) {
            var dot_product = 0.0;
            
            for (var d = 0u; d < 14u; d++) {
                dot_product += current_z[d] * wave_vectors[r * 14u + d];
            }
            
            // Derivative: sin(k·z) * k ≈ (k·z) * k (small angle approximation)
            let sine_approx = dot_product;
            
            for (var d = 0u; d < 14u; d++) {
                gradient[d] += wave_weights[r] * sine_approx * wave_vectors[r * 14u + d];
            }
        }
        
        // Gradient descent: z_new = z - learning_rate * gradient
        for (var d = 0u; d < 14u; d++) {
            current_z[d] = current_z[d] - params.learning_rate * gradient[d];
        }
        
        // Store trajectory point
        if (step < 100u) {  // Limit trajectory storage
            trajectories[vec_idx * 100u + step] = frustration;
        }
    }
    
    // Store final frustration
    frustrations[vec_idx] = prev_frustration;
    
    // Store convergence flag
    converged[vec_idx] = converged;
}

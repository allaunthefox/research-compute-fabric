// GPU Compute Shader: 14D → 2D Projection Rendering
// First-Principles Derivation: Files are n-space vectors, not locations
//
// This shader performs GPU-accelerated projection of 14D concept vectors
// to 2D coordinates for manifold navigation interface.
//
// Performance Target: 60 FPS projection rendering

struct ProjectionParams {
    n_vectors: u32,
    n_dimensions: u32,  // 14 for concept vectors
    projection_method: u32,  // 0=PCA, 1=tSNE, 2=UMAP, 3=ManifoldChart
    slice_axis_x: u32,  // Which axis to display on X
    slice_axis_y: u32,  // Which axis to display on Y
}

@group(0) @binding(0) var<uniform> params: ProjectionParams;

@group(0) @binding(1) var<storage, read> input_vectors: array<f32>;  // 14D vectors
@group(0) @binding(2) var<storage, read> projection_matrix: array<f32>;  // 14x2 projection matrix
@group(0) @binding(3) var<storage, read> mean_vector: array<f32>;  // 14D mean vector
@group(0) @binding(4) var<storage, read_write> output_points: array<vec2<f32>>;  // 2D output
@group(0) @binding(5) var<storage, read_write> output_confidence: array<f32>;  // Confidence scores

@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let idx = global_id.x;
    if (idx >= params.n_vectors) { return; }
    
    let n_dims = params.n_dimensions;
    
    // Load 14D vector
    var vector: array<f32, 14>;
    for (var d = 0u; d < 14u; d++) {
        if (d < n_dims) {
            vector[d] = input_vectors[idx * n_dims + d];
        } else {
            vector[d] = 0.0;
        }
    }
    
    // Center vector (subtract mean)
    var centered: array<f32, 14>;
    for (var d = 0u; d < 14u; d++) {
        centered[d] = vector[d] - mean_vector[d];
    }
    
    // Apply projection matrix (14x2 → 2D)
    var x_proj = 0.0;
    var y_proj = 0.0;
    
    if (params.projection_method == 3u) {
        // ManifoldChart: Direct slice
        x_proj = centered[params.slice_axis_x];
        y_proj = centered[params.slice_axis_y];
    } else {
        // PCA/tSNE/UMAP: Matrix multiplication
        for (var d = 0u; d < 14u; d++) {
            x_proj += centered[d] * projection_matrix[d * 2u];
            y_proj += centered[d] * projection_matrix[d * 2u + 1u];
        }
    }
    
    // Store output
    output_points[idx] = vec2<f32>(x_proj, y_proj);
    
    // Compute confidence (simplified reconstruction error)
    var reconstruction_error = 0.0;
    if (params.projection_method != 3u) {
        // Reconstruct (2D → 14D)
        var reconstructed: array<f32, 14>;
        for (var d = 0u; d < 14u; d++) {
            reconstructed[d] = x_proj * projection_matrix[d * 2u] + 
                              y_proj * projection_matrix[d * 2u + 1u] + 
                              mean_vector[d];
            
            let error = vector[d] - reconstructed[d];
            reconstruction_error += error * error;
        }
        
        reconstruction_error = sqrt(reconstruction_error);
    }
    
    // Convert error to confidence (lower error = higher confidence)
    let confidence = 1.0 / (1.0 + reconstruction_error);
    output_confidence[idx] = confidence;
}

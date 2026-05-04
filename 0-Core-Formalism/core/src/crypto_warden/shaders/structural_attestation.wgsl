// structural_attestation.wgsl
// Formal Source: tools/lean/Semantics/Semantics/StructuralAttestation.lean

struct StressVector {
    sigmaX: u32,
    sigmaY: u32,
    sigmaZ: u32,
    tauXY: u32,
    tauYZ: u32,
    tauZX: u32,
}

// 6-axis stress hashing: XOR sum of all stress components
fn mechanical_hash(v: StressVector) -> u32 {
    return v.sigmaX ^ v.sigmaY ^ v.sigmaZ ^ v.tauXY ^ v.tauYZ ^ v.tauZX;
}

@group(0) @binding(0) var<storage, read> stress_buffer: array<StressVector>;
@group(0) @binding(1) var<storage, read_write> hash_buffer: array<u32>;

// Compute leaf hashes for the Mechanical Merkle Tree
@compute @workgroup_size(64)
fn compute_leaf_hashes(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let idx = global_id.x;
    if (idx >= arrayLength(&stress_buffer)) {
        return;
    }
    hash_buffer[idx] = mechanical_hash(stress_buffer[idx]);
}

// Perform one level of Merkle Tree reduction
// Each invocation reduces two children into one parent
@compute @workgroup_size(64)
fn reduce_merkle_level(
    @builtin(global_invocation_id) global_id: vec3<u32>
) {
    let idx = global_id.x;
    let parent_idx = idx;
    let left_child = idx * 2u;
    let right_child = idx * 2u + 1u;

    if (left_child >= arrayLength(&hash_buffer)) {
        return;
    }

    let left_hash = hash_buffer[left_child];
    var right_hash = 0u;
    if (right_child < arrayLength(&hash_buffer)) {
        right_hash = hash_buffer[right_child];
    }

    // Root hash is XOR-sum of children's hashes as per mkNode in StructuralAttestation.lean
    hash_buffer[parent_idx] = left_hash ^ right_hash;
}

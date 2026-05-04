@group(0) @binding(0) var<storage, read> input: array<u32>;
@group(0) @binding(1) var<storage, read_write> output: array<u32>;

// AES S-Box as 64 u32s (256 bytes)
@group(0) @binding(2) var<storage, read> sbox: array<u32, 64>;

@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>, @builtin(num_workgroups) num_groups: vec3<u32>) {
    let idx = global_id.x + (global_id.y * num_groups.x * 256u);
    
    if (idx >= arrayLength(&input)) {
        return;
    }
    
    let word = input[idx];
    
    // Process 4 bytes at a time
    var result = 0u;
    for (var i = 0u; i < 4u; i = i + 1u) {
        let byte = (word >> (i * 8u)) & 0xFFu;
        // Access S-Box (4 bytes per u32)
        let sbox_idx = byte / 4u;
        let sbox_shift = (byte % 4u) * 8u;
        let sbox_val = (sbox[sbox_idx] >> sbox_shift) & 0xFFu;
        result = result | (sbox_val << (i * 8u));
    }
    
    output[idx] = result;
}

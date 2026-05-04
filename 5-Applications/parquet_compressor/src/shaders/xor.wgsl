@group(0) @binding(0) var<storage, read> input: array<u32>;
@group(0) @binding(1) var<storage, read_write> output: array<u32>;

@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>, @builtin(num_workgroups) num_groups: vec3<u32>) {
    // 2D dispatch aware index calculation
    let idx = global_id.x + (global_id.y * num_groups.x * 256u);
    
    if (idx >= arrayLength(&input)) {
        return;
    }
    
    let key = 0x1F1F1F1Fu; 
    output[idx] = input[idx] ^ key;
}

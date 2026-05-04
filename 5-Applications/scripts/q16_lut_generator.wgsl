// Q16_16 LUT Generator Shader
//
// This shader computes all combinations of Q16_16 operations and generates a lookup table.
// For each pair (a, b) in Q16_16 space (65,536² = 4,294,967,296 combinations), it computes:
//   - add(a, b)
//   - sub(a, b)
//   - mul(a, b)
//   - div(a, b) (when b != 0)
//   - max(a, b)
//   - min(a, b)
//   - neg(a)
//   - abs(a)
//
// The output is a packed LUT that can be used for fast hardware implementation.

struct LUTEntry {
    add_result: u32,
    sub_result: u32,
    mul_result: u32,
    div_result: u32,  // 0xFFFFFFFF if division by zero
    max_result: u32,
    min_result: u32,
    neg_result: u32,
    abs_result: u32,
}

@group(0) @binding(0) var<storage, read_write> lut: array<LUTEntry>;

const Q16_SPACE: u32 = 65536u;
const SCALE_FACTOR: u32 = 65536u;
const SIGN_BIT: u32 = 0x80000000u;
const TWO_POW_32: u32 = 0x100000000u;

// Q16_16 operations
fn q16_add(a: u32, b: u32) -> u32 {
    return a + b;
}

fn q16_sub(a: u32, b: u32) -> u32 {
    return a - b;
}

fn q16_mul(a: u32, b: u32) -> u32 {
    let prod = u64(a) * u64(b);
    return u32(prod >> 16u);
}

fn q16_div(a: u32, b: u32) -> u32 {
    if b == 0u {
        return 0xFFFFFFFFu;  // Division by zero marker
    }
    let numerator = u64(a) << 16u;
    return u32(numerator / u64(b));
}

fn q16_max(a: u32, b: u32) -> u32 {
    return select(a, b, a > b);
}

fn q16_min(a: u32, b: u32) -> u32 {
    return select(b, a, a > b);
}

fn q16_neg(a: u32) -> u32 {
    return 0u - a;
}

fn q16_abs(a: u32) -> u32 {
    let is_negative = (a & SIGN_BIT) != 0u;
    return select(a, q16_neg(a), is_negative);
}

// Convert linear index to (a, b) pair
fn linear_to_pair(idx: u32) -> vec2<u32> {
    let a = idx / Q16_SPACE;
    let b = idx % Q16_SPACE;
    return vec2<u32>(a, b);
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let idx = gid.x;
    let total_pairs = Q16_SPACE * Q16_SPACE;
    
    if idx >= total_pairs {
        return;
    }
    
    let pair = linear_to_pair(idx);
    let a = pair.x;
    let b = pair.y;
    
    // Compute all operations
    let entry = LUTEntry(
        add_result: q16_add(a, b),
        sub_result: q16_sub(a, b),
        mul_result: q16_mul(a, b),
        div_result: q16_div(a, b),
        max_result: q16_max(a, b),
        min_result: q16_min(a, b),
        neg_result: q16_neg(a),  // neg depends only on a
        abs_result: q16_abs(a),  // abs depends only on a
    );
    
    lut[idx] = entry;
}

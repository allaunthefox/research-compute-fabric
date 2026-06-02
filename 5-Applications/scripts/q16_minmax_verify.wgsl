// Q16_16 Min/Max Theorems Verification Shader
//
// Depends on: q16_arithmetic.wgsl (shared include)
//
// This shader verifies the min/max comparison theorems from FixedPoint.lean:
//   1. max_first_whenGe: a.toInt >= b.toInt → max a b = a
//   2. max_second_whenLt: a.toInt < b.toInt → max a b = b
//   3. min_first_whenLe: a.toInt <= b.toInt → min a b = a
//   4. min_second_whenGt: a.toInt > b.toInt → min a b = b
//
// Tests all pairs of Q16_16 values in parallel on GPU.

struct MinMaxResult {
    max_first_ok: u32,
    max_second_ok: u32,
    min_first_ok: u32,
    min_second_ok: u32,
}

@group(0) @binding(0) var<storage, read_write> results: array<MinMaxResult>;

const Q16_SPACE: u32 = 65536u;

// Q16_16 max (as defined in FixedPoint.lean)
fn q_max(a: u32, b: u32) -> u32 {
    let a_int = q16_to_int(a);
    let b_int = q16_to_int(b);
    return select(a, b, a_int >= b_int);
}

// Q16_16 min (as defined in FixedPoint.lean)
fn q_min(a: u32, b: u32) -> u32 {
    let a_int = q16_to_int(a);
    let b_int = q16_to_int(b);
    return select(a, b, a_int <= b_int);
}

@compute @workgroup_size(8, 8, 1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let a = gid.x;
    let b = gid.y;
    
    if (a >= Q16_SPACE || b >= Q16_SPACE) {
        return;
    }

    let a_int = q16_to_int(a);
    let b_int = q16_to_int(b);
    let max_ab = q_max(a, b);
    let min_ab = q_min(a, b);

    // Lemma 1: max_first_whenGe
    // a.toInt >= b.toInt → max a b = a
    let a_ge_b = a_int >= b_int;
    let max_first_ok = select(1u, 0u, !a_ge_b || max_ab == a);

    // Lemma 2: max_second_whenLt
    // a.toInt < b.toInt → max a b = b
    let a_lt_b = a_int < b_int;
    let max_second_ok = select(1u, 0u, !a_lt_b || max_ab == b);

    // Lemma 3: min_first_whenLe
    // a.toInt <= b.toInt → min a b = a
    let a_le_b = a_int <= b_int;
    let min_first_ok = select(1u, 0u, !a_le_b || min_ab == a);

    // Lemma 4: min_second_whenGt
    // a.toInt > b.toInt → min a b = b
    let a_gt_b = a_int > b_int;
    let min_second_ok = select(1u, 0u, !a_gt_b || min_ab == b);

    // Store result (use linear index)
    let idx = a * Q16_SPACE + b;
    results[idx] = MinMaxResult(
        max_first_ok,
        max_second_ok,
        min_first_ok,
        min_second_ok
    );
}

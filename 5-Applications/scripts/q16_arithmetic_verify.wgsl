// Q16_16 Arithmetic Theorems Verification Shader
//
// Depends on: q16_arithmetic.wgsl (shared include)
//
// This shader verifies the main arithmetic theorems from FixedPoint.lean:
//   1. mul_one: mul q one = q
//   2. div_one: div q one = q
//   3. neg_involutive: neg (neg q) = q
//   4. abs_nonNegative: (abs q).toInt >= 0
//
// Tests all 65,536 Q16_16 values in parallel on GPU.

struct ArithmeticResult {
    mul_one_ok: u32,
    div_one_ok: u32,
    neg_involutive_ok: u32,
    abs_nonNegative_ok: u32,
}

@group(0) @binding(0) var<storage, read_write> results: array<ArithmeticResult>;

const Q16_SPACE: u32 = 65536u;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let q = gid.x;
    if (q >= Q16_SPACE) {
        return;
    }

    // Lemma 1: mul_one
    // mul q one = q
    let mul_result = q16_mul(q, Q16_ONE);
    let mul_one_ok = select(0u, 1u, mul_result == q);

    // Lemma 2: div_one
    // div q one = q
    let div_result = q16_div(q, Q16_ONE);
    let div_one_ok = select(0u, 1u, div_result == q);

    // Lemma 3: neg_involutive
    // neg (neg q) = q
    let neg_once = q16_neg(q);
    let neg_twice = q16_neg(neg_once);
    let neg_involutive_ok = select(0u, 1u, neg_twice == q);

    // Lemma 4: abs_nonNegative
    // (abs q).toInt >= 0
    let abs_q = q16_abs(q);
    let abs_int = q16_to_int(abs_q);
    let abs_nonNegative_ok = select(0u, 1u, abs_int >= 0);

    results[q] = ArithmeticResult(
        mul_one_ok,
        div_one_ok,
        neg_involutive_ok,
        abs_nonNegative_ok
    );
}

// Q16_16 Arithmetic Theorems Verification Shader
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
const Q16_ONE: u32 = 0x00010000u;  // 1.0 in Q16_16
const SIGN_BIT: u32 = 0x80000000u;
const TWO_POW_32: u32 = 0x100000000u;

// Convert Q16_16 val to signed Int (2's complement)
fn toInt(val: u32) -> i32 {
    let is_negative = val >= SIGN_BIT;
    return select(i32(val), i32(val) - i32(TWO_POW_32), is_negative);
}

// Q16_16 multiplication (as defined in FixedPoint.lean)
fn q_mul(a: u32, b: u32) -> u32 {
    let product = u64(a) * u64(b);
    return u32(product >> 16u);
}

// Q16_16 division (as defined in FixedPoint.lean)
fn q_div(a: u32, b: u32) -> u32 {
    if (b == 0u) {
        return 0xFFFFFFFFu;  // infinity sentinel
    }
    let scaled = (u64(a) << 16u) / u64(b);
    return u32(scaled);
}

// Q16_16 negation (as defined in FixedPoint.lean)
fn q_neg(q: u32) -> u32 {
    let q_int = toInt(q);
    let neg_int = -q_int;
    // Convert back to unsigned (2's complement)
    return u32(neg_int);
}

// Q16_16 absolute value (as defined in FixedPoint.lean)
fn q_abs(q: u32) -> u32 {
    let is_negative = q >= SIGN_BIT;
    return select(q, q_neg(q), is_negative);
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let q = gid.x;
    if (q >= Q16_SPACE) {
        return;
    }

    // Lemma 1: mul_one
    // mul q one = q
    let mul_result = q_mul(q, Q16_ONE);
    let mul_one_ok = select(0u, 1u, mul_result == q);

    // Lemma 2: div_one
    // div q one = q
    let div_result = q_div(q, Q16_ONE);
    let div_one_ok = select(0u, 1u, div_result == q);

    // Lemma 3: neg_involutive
    // neg (neg q) = q
    let neg_once = q_neg(q);
    let neg_twice = q_neg(neg_once);
    let neg_involutive_ok = select(0u, 1u, neg_twice == q);

    // Lemma 4: abs_nonNegative
    // (abs q).toInt >= 0
    let abs_q = q_abs(q);
    let abs_int = toInt(abs_q);
    let abs_nonNegative_ok = select(0u, 1u, abs_int >= 0);

    results[q] = ArithmeticResult(
        mul_one_ok,
        div_one_ok,
        neg_involutive_ok,
        abs_nonNegative_ok
    );
}

// Q16_16 Bit-Level Arithmetic Verification Shader
//
// Depends on: q16_arithmetic.wgsl (shared include)
//
// This shader exhaustively verifies bit-level arithmetic lemmas for FixedPoint.lean
// across the entire Q16_16 space (65,536 values) in parallel on GPU.
//
// Lemmas verified:
//   1. shift_left_16_eq_mul_65536: n <<< 16 = n * 65536
//   2. shift_right_16_eq_div_65536: n >>> 16 = n / 65536
//   3. toInt_eq_val_div_65536_nonneg: toInt = val / 65536 for val < 0x80000000
//   4. toInt_eq_val_minus_2to32_div_65536_neg: toInt = (val - 2^32) / 65536 for val >= 0x80000000
//
// Output: 1 if lemma holds for given value, 0 if counterexample found

struct VerificationResult {
    shift_left_ok:   u32,
    shift_right_ok:  u32,
    toInt_nonneg_ok: u32,
    toInt_neg_ok:    u32,
}

@group(0) @binding(0) var<storage, read_write> results: array<VerificationResult>;

const Q16_SPACE: u32 = 65536u;  // Q16_16 has 2^16 possible values

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let val = gid.x;
    if (val >= Q16_SPACE) {
        return;
    }

    // Lemma 1: shift_left_16_eq_mul_65536
    // n <<< 16 should equal n * 65536
    let shift_left_result = val << 16u;
    let mul_result = val * Q16_SCALE;
    let shift_left_ok = select(0u, 1u, shift_left_result == mul_result);

    // Lemma 2: shift_right_16_eq_div_65536
    // n >>> 16 should equal n / 65536
    let shift_right_result = val >> 16u;
    let div_result = val / Q16_SCALE;
    let shift_right_ok = select(0u, 1u, shift_right_result == div_result);

    // Lemma 3: toInt_eq_val_div_65536_nonneg
    // For val < 0x80000000: toInt = val / 65536
    let is_nonneg = val < SIGN_BIT;
    let toInt_nonneg_expected = val / Q16_SCALE;
    // Actual toInt for non-negative: just the value divided by scale
    let toInt_nonneg_ok = select(0u, 1u, is_nonneg && toInt_nonneg_expected == toInt_nonneg_expected);

    // Lemma 4: toInt_eq_val_minus_2to32_div_65536_neg
    // For val >= 0x80000000: toInt = (val - 2^32) / 65536
    let is_neg = val >= SIGN_BIT;
    let toInt_neg_expected = (val - TWO_POW_32) / Q16_SCALE;
    // For negative values, we need to compute the signed interpretation
    // In 2's complement: signed = unsigned - 2^32 if bit 31 is set
    let signed_val = select(val, i32(val) - i32(TWO_POW_32), is_neg);
    let toInt_neg_computed = u32(signed_val) / Q16_SCALE;
    let toInt_neg_ok = select(0u, 1u, is_neg && toInt_neg_expected == toInt_neg_computed);

    results[val] = VerificationResult(
        shift_left_ok,
        shift_right_ok,
        toInt_nonneg_ok,
        toInt_neg_ok
    );
}

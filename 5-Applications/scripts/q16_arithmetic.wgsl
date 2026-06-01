// Q16_16 fixed-point arithmetic — shared include
//
// This file is a shared WGSL include. The build pipeline should prepend
// this file to any shader that depends on it, e.g.:
//   cat q16_arithmetic.wgsl target_shader.wgsl > combined.wgsl
//
// Scale: 2^16 = 65536

const Q16_SCALE: u32 = 65536u;
const Q16_ONE: u32 = 0x00010000u;
const SIGN_BIT: u32 = 0x80000000u;
const TWO_POW_32: u32 = 0x100000000u;

// Extract sign bit as i32 (WGSL: u32 -> bool)
fn is_neg(v: u32) -> bool {
    return (v & SIGN_BIT) != 0u;
}

// Convert unsigned Q16_16 to signed integer
fn q16_to_int(v: u32) -> i32 {
    return bitcast<i32>(v);
}

// Convert signed integer to unsigned Q16_16
fn int_to_q16(v: i32) -> u32 {
    return bitcast<u32>(v);
}

// Q16_16 multiplication: (a * b) >> 16
fn q16_mul(a: u32, b: u32) -> u32 {
    let a_signed = q16_to_int(a);
    let b_signed = q16_to_int(b);
    let product = i64(a_signed) * i64(b_signed);
    let result = i32(product >> 16);
    return bitcast<u32>(result);
}

// Q16_16 division: (a << 16) / b
fn q16_div(a: u32, b: u32) -> u32 {
    let a_signed = q16_to_int(a);
    let b_signed = q16_to_int(b);
    let num = i64(a_signed) << 16;
    let result = i32(num / i64(b_signed));
    return bitcast<u32>(result);
}

// Q16_16 negation
fn q16_neg(a: u32) -> u32 {
    return int_to_q16(-q16_to_int(a));
}

// Q16_16 absolute value
fn q16_abs(a: u32) -> u32 {
    let s = q16_to_int(a);
    return select(a, q16_neg(a), is_neg(a));
}

// Q16_16 addition (saturating)
fn q16_add(a: u32, b: u32) -> u32 {
    let result = q16_to_int(a) + q16_to_int(b);
    return int_to_q16(result);
}

// Q16_16 subtraction (saturating)
fn q16_sub(a: u32, b: u32) -> u32 {
    let result = q16_to_int(a) - q16_to_int(b);
    return int_to_q16(result);
}

// Q16_16 maximum
fn q16_max(a: u32, b: u32) -> u32 {
    return select(b, a, q16_to_int(a) > q16_to_int(b));
}

// Q16_16 minimum
fn q16_min(a: u32, b: u32) -> u32 {
    return select(b, a, q16_to_int(a) < q16_to_int(b));
}

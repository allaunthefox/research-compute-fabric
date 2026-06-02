// ── Q16_16 Fixed-Point Arithmetic Verification Shader ───────────────────
//
// Depends on: q16_arithmetic.wgsl (shared include)
//
// Each workgroup verifies one theorem across N test vectors.
// Theorems are indexed by workgroup_id; each invocation tests one vector.

// Q16_16 is a UInt32 where 1.0 = 0x00010000 = 65536
// Positive: [0x00000000, 0x7FFFFFFF], Negative: [0x80000000, 0xFFFFFFFF]

struct TestVector {
  a: u32,
  b: u32,
  expected: u32,
}

struct TheoremBatch {
  theorem_id: u32,
  count: u32,
  padding: u32,
  padding2: u32,
}

struct TheoremResult {
  theorem_id: u32,
  passed: u32,  // 0 = fail, 1 = pass
  total: u32,
  failed: u32,
}

@group(0) @binding(0) var<storage, read> vectors: array<TestVector>;
@group(0) @binding(1) var<storage, read> batches: array<TheoremBatch>;
@group(0) @binding(2) var<storage, read_write> results: array<TheoremResult>;

// ── Q16_16 Arithmetic (matches FixedPoint.lean) ─────────────────────────
// Note: q16_mul, q16_div, q16_neg, q16_to_int come from q16_arithmetic.wgsl shared include.
// q16_add and q16_sub are saturating variants defined locally.

fn q16_add(a: u32, b: u32) -> u32 {
  let s: u32 = a + b;
  // Positive + positive overflow -> maxVal
  if (a < 0x80000000u && b < 0x80000000u && s >= 0x80000000u) {
    return 0x7FFFFFFFu;
  }
  // Negative + negative underflow -> minVal
  if (a >= 0x80000000u && b >= 0x80000000u && s < 0x80000000u) {
    return 0x80000000u;
  }
  return s;
}

fn q16_sub(a: u32, b: u32) -> u32 {
  let d: u32 = a - b;
  // Positive - negative overflow -> maxVal
  if (a < 0x80000000u && b >= 0x80000000u && d >= 0x80000000u) {
    return 0x7FFFFFFFu;
  }
  // Negative - positive underflow -> minVal
  if (a >= 0x80000000u && b < 0x80000000u && d < 0x80000000u) {
    return 0x80000000u;
  }
  return d;
}

// ── Theorem Verification Kernels ─────────────────────────────────────────

fn check_zero_mul(idx: u32) -> bool {
  let v = vectors[idx];
  // zero * a = zero
  let result = q16_mul(0u, v.a);
  return result == 0u;
}

fn check_mul_zero(idx: u32) -> bool {
  let v = vectors[idx];
  // a * zero = zero
  let result = q16_mul(v.a, 0u);
  return result == 0u;
}

fn check_add_zero(idx: u32) -> bool {
  let v = vectors[idx];
  // a + zero = a
  let result = q16_add(v.a, 0u);
  return result == v.a;
}

fn check_zero_add(idx: u32) -> bool {
  let v = vectors[idx];
  // zero + a = a
  let result = q16_add(0u, v.a);
  return result == v.a;
}

fn check_sub_self(idx: u32) -> bool {
  let v = vectors[idx];
  // a - a = zero
  let result = q16_sub(v.a, v.a);
  return result == 0u;
}

fn check_one_mul(idx: u32) -> bool {
  let v = vectors[idx];
  // one * a = a  (one = 0x00010000)
  let result = q16_mul(0x00010000u, v.a);
  return result == v.a;
}

fn check_mul_one(idx: u32) -> bool {
  let v = vectors[idx];
  // a * one = a  (one = 0x00010000)
  let result = q16_mul(v.a, 0x00010000u);
  return result == v.a;
}

fn check_add_comm(idx: u32) -> bool {
  let v = vectors[idx];
  // a + b = b + a
  let r1 = q16_add(v.a, v.b);
  let r2 = q16_add(v.b, v.a);
  return r1 == r2;
}

fn check_neg_involutive(idx: u32) -> bool {
  let v = vectors[idx];
  // -(-a) = a
  let neg1 = q16_neg(v.a);
  let neg2 = q16_neg(neg1);
  return neg2 == v.a;
}

fn check_sub_via_neg(idx: u32) -> bool {
  let v = vectors[idx];
  // a - b = a + (-b)
  let sub_result = q16_sub(v.a, v.b);
  let via_neg = q16_add(v.a, q16_neg(v.b));
  return sub_result == via_neg;
}

// ── Main Dispatch ────────────────────────────────────────────────────────

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let batch_idx = gid.x;
  let local_idx = gid.y;

  if (batch_idx >= arrayLength(&batches)) {
    return;
  }

  let batch = batches[batch_idx];

  if (local_idx >= batch.count) {
    return;
  }

  let vec_idx = local_idx;
  var pass: bool = false;

  // Dispatch by theorem_id
  switch (batch.theorem_id) {
    case 0u: { pass = check_zero_mul(vec_idx); }
    case 1u: { pass = check_mul_zero(vec_idx); }
    case 2u: { pass = check_add_zero(vec_idx); }
    case 3u: { pass = check_zero_add(vec_idx); }
    case 4u: { pass = check_sub_self(vec_idx); }
    case 5u: { pass = check_one_mul(vec_idx); }
    case 6u: { pass = check_mul_one(vec_idx); }
    case 7u: { pass = check_add_comm(vec_idx); }
    case 8u: { pass = check_neg_involutive(vec_idx); }
    case 9u: { pass = check_sub_via_neg(vec_idx); }
    default: { pass = true; }
  }

  // Atomic increment failure count
  if (!pass) {
    let old = atomicAdd(&results[batch_idx].failed, 1u);
  }
  // Set passed flag if any invocation succeeded (we use global atomic for count)
  // The host checks results[batch_idx].failed == 0
}

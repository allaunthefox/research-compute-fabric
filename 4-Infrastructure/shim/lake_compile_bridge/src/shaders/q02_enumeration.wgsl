// ── Q0_2 Exhaustive Enumeration Verification Shader ───────────────
// Each workgroup verifies one Q0_2 theorem across all 4 Q0_2 values
// (16 pairs for binary operations).
//
// Q0_2 is a 2-bit fixed-point type with 4 values:
//   0       → 0x00000000
//   0.25    → 0x00004000
//   0.5     → 0x00008000
//   0.75    → 0x0000C000
//
// Theorem IDs:
//   10: q0_2_mul_self_nonneg — ∀ a ∈ Q0_2, (a*a).toInt ≥ 0
//   11: q0_2_mul_nonneg      — ∀ a,b ∈ Q0_2, (a*b).toInt ≥ 0
//   12: q0_2_add_nonneg      — ∀ a,b ∈ Q0_2, (a+b).toInt ≥ 0

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
  passed: u32,
  total: u32,
  failed: u32,
}

@group(0) @binding(0) var<storage, read> vectors: array<TestVector>;
@group(0) @binding(1) var<storage, read> batches: array<TheoremBatch>;
@group(0) @binding(2) var<storage, read_write> results: array<TheoremResult>;

// ── Q0_2 Constants ─────────────────────────────────────────────────

const Q0_2_VALUES: array<u32, 4> = array<u32, 4>(
  0x00000000u,
  0x00004000u,
  0x00008000u,
  0x0000C000u,
);

// ── Q16_16 Arithmetic (matches FixedPoint.lean) ─────────────────────

fn q16_add(a: u32, b: u32) -> u32 {
  let s: u32 = a + b;
  if (a < 0x80000000u && b < 0x80000000u && s >= 0x80000000u) {
    return 0x7FFFFFFFu;
  }
  if (a >= 0x80000000u && b >= 0x80000000u && s < 0x80000000u) {
    return 0x80000000u;
  }
  return s;
}

fn q16_mul(a: u32, b: u32) -> u32 {
  let prod: u64 = u64(a) * u64(b);
  return u32(prod >> 16u);
}

fn q16_to_int(a: u32) -> i32 {
  if (a >= 0x80000000u) {
    return i32(a) - 0x100000000i;
  }
  return i32(a);
}

// ── Q0_2 Verification Kernels ───────────────────────────────────────

fn check_q0_2_mul_self_nonneg(idx: u32) -> bool {
  let a = Q0_2_VALUES[idx];
  let result = q16_mul(a, a);
  return q16_to_int(result) >= 0i;
}

fn check_q0_2_mul_nonneg(idx: u32) -> bool {
  let ai = idx / 4u;
  let bi = idx % 4u;
  let a = Q0_2_VALUES[ai];
  let b = Q0_2_VALUES[bi];
  let result = q16_mul(a, b);
  return q16_to_int(result) >= 0i;
}

fn check_q0_2_add_nonneg(idx: u32) -> bool {
  let ai = idx / 4u;
  let bi = idx % 4u;
  let a = Q0_2_VALUES[ai];
  let b = Q0_2_VALUES[bi];
  let result = q16_add(a, b);
  return q16_to_int(result) >= 0i;
}

// ── Main Dispatch ───────────────────────────────────────────────────

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

  var pass: bool = false;

  switch (batch.theorem_id) {
    case 10u: { pass = check_q0_2_mul_self_nonneg(local_idx); }
    case 11u: { pass = check_q0_2_mul_nonneg(local_idx); }
    case 12u: { pass = check_q0_2_add_nonneg(local_idx); }
    default: { pass = true; }
  }

  if (!pass) {
    atomicAdd(&results[batch_idx].failed, 1u);
  }
}

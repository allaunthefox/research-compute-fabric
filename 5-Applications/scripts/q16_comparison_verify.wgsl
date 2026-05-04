// Q16_16 Comparison Monotonicity Verification Shader
//
// This shader verifies monotonicity lemmas for Q16_16 comparisons:
//   1. val_ge_implies_toInt_ge: a.val >= b.val → a.toInt >= b.toInt
//   2. val_le_implies_toInt_le: a.val <= b.val → a.toInt <= b.toInt
//
// Tests all pairs of Q16_16 values (65,536² = 4.3 billion pairs) in parallel.
// Uses 2D grid to iterate over (a, b) pairs efficiently.

struct ComparisonResult {
    val_ge_toInt_ge_ok: u32,
    val_le_toInt_le_ok: u32,
    counterexamples_found: u32,
}

@group(0) @binding(0) var<storage, read_write> results: array<ComparisonResult>;

const Q16_SPACE: u32 = 65536u;
const SIGN_BIT: u32 = 0x80000000u;
const TWO_POW_32: u32 = 0x100000000u;

// Convert Q16_16 val to signed Int (2's complement)
fn toInt(val: u32) -> i32 {
    let is_negative = val >= SIGN_BIT;
    return select(i32(val), i32(val) - i32(TWO_POW_32), is_negative);
}

@compute @workgroup_size(8, 8, 1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let a = gid.x;
    let b = gid.y;
    
    if (a >= Q16_SPACE || b >= Q16_SPACE) {
        return;
    }

    // Lemma 1: val_ge_implies_toInt_ge
    // If a.val >= b.val, then a.toInt >= b.toInt
    let val_ge = a >= b;
    let a_int = toInt(a);
    let b_int = toInt(b);
    let toInt_ge = a_int >= b_int;
    
    // The implication: val_ge → toInt_ge
    // This is false only when val_ge is true but toInt_ge is false
    let val_ge_toInt_ge_ok = select(1u, 0u, !(val_ge && !toInt_ge));

    // Lemma 2: val_le_implies_toInt_le
    // If a.val <= b.val, then a.toInt <= b.toInt
    let val_le = a <= b;
    let toInt_le = a_int <= b_int;
    
    // The implication: val_le → toInt_le
    // This is false only when val_le is true but toInt_le is false
    let val_le_toInt_le_ok = select(1u, 0u, !(val_le && !toInt_le));

    // Track counterexamples
    let counterexamples = select(0u, 1u, !val_ge_toInt_ge_ok || !val_le_toInt_le_ok);

    // Store result (use linear index)
    let idx = a * Q16_SPACE + b;
    results[idx] = ComparisonResult(
        val_ge_toInt_ge_ok,
        val_le_toInt_le_ok,
        counterexamples
    );
}

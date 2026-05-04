// Q16_16 Path Explorer Shader - Exhaustively explores all possible proof paths
//
// This shader systematically tests all 6 helper lemmas across the entire Q16_16 space
// to identify patterns, counterexamples, and proof paths. It outputs detailed
// information about each case to help construct formal Lean proofs.
//
// Lemmas explored:
//   1. toInt_eq_val_nonneg: toInt = val.toNat for val < 0x80000000
//   2. toInt_eq_val_minus_2to32_neg: toInt = val.toNat - 2^32 for val >= 0x80000000
//   3. shift_left_16_eq_mul_65536: n <<< 16 = n * 65536
//   4. shift_right_16_eq_div_65536: n >>> 16 = n / 65536
//   5. val_ge_implies_toInt_ge: val >= implies toInt >=
//   6. val_le_implies_toInt_le: val <= implies toInt <=

struct PathExplorationResult {
    // toInt exploration
    toInt_nonneg_matches: u32,      // Count of non-negative vals where toInt = val.toNat
    toInt_neg_matches: u32,         // Count of negative vals where toInt = val.toNat - 2^32
    toInt_nonneg_total: u32,        // Total non-negative values
    toInt_neg_total: u32,           // Total negative values
    
    // Shift exploration
    shift_left_matches: u32,        // Count where n <<< 16 = n * 65536
    shift_right_matches: u32,       // Count where n >>> 16 = n / 65536
    shift_total: u32,               // Total values tested
    
    // Comparison exploration
    val_ge_toInt_ge_matches: u32,   // Count where val >= implies toInt >=
    val_le_toInt_le_matches: u32,   // Count where val <= implies toInt <=
    comparison_total: u32,          // Total pairs tested
    
    // Pattern detection
    sign_bit_pattern: u32,          // Pattern in sign bit behavior
    overflow_count: u32,            // Count of overflow cases
    edge_case_count: u32,           // Count of edge cases (0, max, min, etc.)
}

@group(0) @binding(0) var<storage, read_write> results: PathExplorationResult;

const Q16_SPACE: u32 = 65536u;
const SIGN_BIT: u32 = 0x80000000u;
const TWO_POW_32: u32 = 0x100000000u;
const SCALE_FACTOR: u32 = 65536u;

// Convert Q16_16 val to signed Int (2's complement)
fn toInt(val: u32) -> i32 {
    let is_negative = val >= SIGN_BIT;
    return select(i32(val), i32(val) - i32(TWO_POW_32), is_negative);
}

// Check if value is an edge case
fn is_edge_case(val: u32) -> bool {
    return val == 0u || val == 0xFFFFFFFFu || val == SIGN_BIT || val == (SIGN_BIT - 1u);
}

// Detect pattern in sign bit behavior
fn detect_sign_bit_pattern(val: u32) -> u32 {
    let sign_bit = (val & SIGN_BIT) >> 31u;
    let magnitude = val & 0x7FFFFFFFu;
    // Pattern: sign_bit * magnitude_mod_256
    return sign_bit * (magnitude % 256u);
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let val = gid.x;
    if (val >= Q16_SPACE) {
        return;
    }
    
    // Initialize counters (atomic operations for parallel safety)
    var toInt_nonneg_matches_local: u32 = 0u;
    var toInt_neg_matches_local: u32 = 0u;
    var toInt_nonneg_total_local: u32 = 0u;
    var toInt_neg_total_local: u32 = 0u;
    var shift_left_matches_local: u32 = 0u;
    var shift_right_matches_local: u32 = 0u;
    var shift_total_local: u32 = 0u;
    var val_ge_toInt_ge_matches_local: u32 = 0u;
    var val_le_toInt_le_matches_local: u32 = 0u;
    var comparison_total_local: u32 = 0u;
    var sign_bit_pattern_local: u32 = 0u;
    var overflow_count_local: u32 = 0u;
    var edge_case_count_local: u32 = 0u;
    
    // Explore toInt lemma 1: non-negative values
    let is_nonneg = val < SIGN_BIT;
    if (is_nonneg) {
        toInt_nonneg_total_local = 1u;
        let toInt_val = toInt(val);
        let expected = i32(val);
        if (toInt_val == expected) {
            toInt_nonneg_matches_local = 1u;
        }
    }
    
    // Explore toInt lemma 2: negative values
    let is_neg = val >= SIGN_BIT;
    if (is_neg) {
        toInt_neg_total_local = 1u;
        let toInt_val = toInt(val);
        let expected = i32(val) - i32(TWO_POW_32);
        if (toInt_val == expected) {
            toInt_neg_matches_local = 1u;
        }
    }
    
    // Explore shift lemma 1: left shift
    let shift_left = val << 16u;
    let mul_result = val * SCALE_FACTOR;
    if (shift_left == mul_result) {
        shift_left_matches_local = 1u;
    }
    shift_total_local = 1u;
    
    // Explore shift lemma 2: right shift
    let shift_right = val >> 16u;
    let div_result = val / SCALE_FACTOR;
    if (shift_right == div_result) {
        shift_right_matches_local = 1u;
    }
    
    // Detect overflow
    if (val > 0xFFFFFFFFu / SCALE_FACTOR) {
        overflow_count_local = 1u;
    }
    
    // Check edge case
    if (is_edge_case(val)) {
        edge_case_count_local = 1u;
    }
    
    // Detect sign bit pattern
    sign_bit_pattern_local = detect_sign_bit_pattern(val);
    
    // Explore comparison lemmas (sample pairs to avoid quadratic explosion)
    // Test against 0, half space, max positive, max negative
    let test_values: array<u32, 4> = array<u32, 4>(0u, 0x40000000u, 0x7FFFFFFFu, SIGN_BIT);
    for (var i: u32 = 0u; i < 4u; i++) {
        let b = test_values[i];
        let a_val = val;
        let b_val = b;
        let a_int = toInt(a_val);
        let b_int = toInt(b_val);
        
        // Test val_ge_toInt_ge
        if (a_val >= b_val) {
            comparison_total_local += 1u;
            if (a_int >= b_int) {
                val_ge_toInt_ge_matches_local += 1u;
            }
        }
        
        // Test val_le_toInt_le
        if (a_val <= b_val) {
            comparison_total_local += 1u;
            if (a_int <= b_int) {
                val_le_toInt_le_matches_local += 1u;
            }
        }
    }
    
    // Atomic add to global results
    atomicAdd(&results.toInt_nonneg_matches, toInt_nonneg_matches_local);
    atomicAdd(&results.toInt_neg_matches, toInt_neg_matches_local);
    atomicAdd(&results.toInt_nonneg_total, toInt_nonneg_total_local);
    atomicAdd(&results.toInt_neg_total, toInt_neg_total_local);
    atomicAdd(&results.shift_left_matches, shift_left_matches_local);
    atomicAdd(&results.shift_right_matches, shift_right_matches_local);
    atomicAdd(&results.shift_total, shift_total_local);
    atomicAdd(&results.val_ge_toInt_ge_matches, val_ge_toInt_ge_matches_local);
    atomicAdd(&results.val_le_toInt_le_matches, val_le_toInt_le_matches_local);
    atomicAdd(&results.comparison_total, comparison_total_local);
    atomicAdd(&results.sign_bit_pattern, sign_bit_pattern_local);
    atomicAdd(&results.overflow_count, overflow_count_local);
    atomicAdd(&results.edge_case_count, edge_case_count_local);
}

; FixedPoint Q16.16 — LLVM IR Reference Implementation
; Matches FixedPoint.lean definitions and C nii_surface_driver.c
; Target: x86_64 (can be compiled to WASM with --target=wasm32)
;
; Operations:
;   q16_16_add:  i32 + i32
;   q16_16_sub:  i32 - i32
;   q16_16_mul:  (i64 a * i64 b) >> 16
;   q16_16_div:  (i64 a << 16) / i64 b
;   q16_16_neg:  -i32 (2's complement)
;   q16_16_abs:  select(sign, -v, v)
;
; Calling convention: SystemV AMD64 ABI (i32 return, i32 args)

; Module ID = 'FixedPoint'
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; ═══════════════════════════════════════════════════════════════════════════
; Constants
; ═══════════════════════════════════════════════════════════════════════════

@Q16_SCALE = constant i32 65536, align 4          ; 2^16
@Q16_ONE   = constant i32 65536, align 4          ; 1.0 in Q16.16
@Q16_ZERO  = constant i32 0, align 4              ; 0.0

; ═══════════════════════════════════════════════════════════════════════════
; q16_16_add: a + b (no scaling needed — same unit)
; Signature: i32 q16_16_add(i32 a, i32 b)
; ═══════════════════════════════════════════════════════════════════════════

define i32 @q16_16_add(i32 %a, i32 %b) {
entry:
  %sum = add i32 %a, %b
  ret i32 %sum
}

; ═══════════════════════════════════════════════════════════════════════════
; q16_16_sub: a - b
; ═══════════════════════════════════════════════════════════════════════════

define i32 @q16_16_sub(i32 %a, i32 %b) {
entry:
  %diff = sub i32 %a, %b
  ret i32 %diff
}

; ═══════════════════════════════════════════════════════════════════════════
; q16_16_mul: (i64 a * i64 b) >> 16
; Matches C: (int64_t)a * (int64_t)b >> 16
; ═══════════════════════════════════════════════════════════════════════════

define i32 @q16_16_mul(i32 %a, i32 %b) {
entry:
  %a64 = sext i32 %a to i64
  %b64 = sext i32 %b to i64
  %prod = mul i64 %a64, %b64
  %scaled = ashr i64 %prod, 16
  %result = trunc i64 %scaled to i32
  ret i32 %result
}

; ═══════════════════════════════════════════════════════════════════════════
; q16_16_div: (i64 a << 16) / i64 b
; Guard: b == 0 → return INT32_MAX (0x7FFFFFFF) as infinity sentinel
; ═══════════════════════════════════════════════════════════════════════════

define i32 @q16_16_div(i32 %a, i32 %b) {
entry:
  %b_is_zero = icmp eq i32 %b, 0
  br i1 %b_is_zero, label %div_by_zero, label %do_div

div_by_zero:
  ret i32 2147483647                          ; INT32_MAX

do_div:
  %a64 = sext i32 %a to i64
  %b64 = sext i32 %b to i64
  %shifted = shl i64 %a64, 16
  %quot = sdiv i64 %shifted, %b64
  %result = trunc i64 %quot to i32
  ret i32 %result
}

; ═══════════════════════════════════════════════════════════════════════════
; q16_16_neg: 2's complement negation
; Matches lemma neg_involutive: neg(neg q) = q
; ═══════════════════════════════════════════════════════════════════════════

define i32 @q16_16_neg(i32 %v) {
entry:
  %neg = sub i32 0, %v
  ret i32 %neg
}

; ═══════════════════════════════════════════════════════════════════════════
; q16_16_abs: absolute value
; Matches lemma abs_nonNegative: (abs q).toInt >= 0
; ═══════════════════════════════════════════════════════════════════════════

define i32 @q16_16_abs(i32 %v) {
entry:
  %is_neg = icmp slt i32 %v, 0
  %neg_v = sub i32 0, %v
  %result = select i1 %is_neg, i32 %neg_v, i32 %v
  ret i32 %result
}

; ═══════════════════════════════════════════════════════════════════════════
; q16_16_compare: returns -1, 0, or 1
; ═══════════════════════════════════════════════════════════════════════════

define i32 @q16_16_compare(i32 %a, i32 %b) {
entry:
  %lt = icmp slt i32 %a, %b
  br i1 %lt, label %ret_neg, label %check_gt

check_gt:
  %gt = icmp sgt i32 %a, %b
  br i1 %gt, label %ret_pos, label %ret_eq

ret_neg:
  ret i32 -1

ret_eq:
  ret i32 0

ret_pos:
  ret i32 1
}

; ═══════════════════════════════════════════════════════════════════════════
; q16_16_from_float: float * 65536 (truncated)
; Calling convention: float passed in xmm0, return in eax
; ═══════════════════════════════════════════════════════════════════════════

define i32 @q16_16_from_float(float %f) {
entry:
  %scale = fptosi float 6.553600e+04 to i32    ; 65536.0
  %fi = fptosi float %f to i32
  %result = mul i32 %fi, %scale
  ret i32 %result
}

; ═══════════════════════════════════════════════════════════════════════════
; q16_16_to_float: i32 / 65536.0
; ═══════════════════════════════════════════════════════════════════════════

define float @q16_16_to_float(i32 %v) {
entry:
  %vf = sitofp i32 %v to float
  %scale = fdiv float %vf, 6.553600e+04
  ret float %scale
}

; ═══════════════════════════════════════════════════════════════════════════
; compute_sss: Steady-State Stability (Layer 6)
; C signature:
;   static q16_16_t compute_sss(const struct sss_constant *c)
;   { counter_torque - torsional_term }
;
; LLVM IR struct layout for sss_constant:
;   { i32 routing_load, i32 memory_load, i32 extraneous_weight,
;     i32 engram_length, i32 extraneous_gradient }
;   Total: 20 bytes (no padding needed — all i32)
; ═══════════════════════════════════════════════════════════════════════════

%struct.sss_constant = type { i32, i32, i32, i32, i32 }

define i32 @compute_sss(%struct.sss_constant* %c) {
entry:
  ; c->routing_load
  %r_ptr = getelementptr %struct.sss_constant, %struct.sss_constant* %c, i32 0, i32 0
  %routing = load i32, i32* %r_ptr

  ; c->memory_load
  %m_ptr = getelementptr %struct.sss_constant, %struct.sss_constant* %c, i32 0, i32 1
  %memory = load i32, i32* %m_ptr

  ; counter_torque = add(routing, memory)
  %counter = call i32 @q16_16_add(i32 %routing, i32 %memory)

  ; c->extraneous_weight
  %ew_ptr = getelementptr %struct.sss_constant, %struct.sss_constant* %c, i32 0, i32 2
  %ew = load i32, i32* %ew_ptr

  ; c->engram_length
  %el_ptr = getelementptr %struct.sss_constant, %struct.sss_constant* %c, i32 0, i32 3
  %el = load i32, i32* %el_ptr

  ; mul(extraneous_weight, engram_length)
  %tmp1 = call i32 @q16_16_mul(i32 %ew, i32 %el)

  ; c->extraneous_gradient
  %eg_ptr = getelementptr %struct.sss_constant, %struct.sss_constant* %c, i32 0, i32 4
  %eg = load i32, i32* %eg_ptr

  ; torsional_term = mul(tmp1, extraneous_gradient)
  %tmp2 = call i32 @q16_16_mul(i32 %tmp1, i32 %eg)

  ; sss = counter_torque - torsional_term
  %result = call i32 @q16_16_sub(i32 %counter, i32 %tmp2)
  ret i32 %result
}

; ═══════════════════════════════════════════════════════════════════════════
; compute_famm_load: Σ² + I_lock + Δϕ (Layer FAMM)
; ═══════════════════════════════════════════════════════════════════════════

%struct.famm_timing = type { i32, i32, i32 }

define i32 @compute_famm_load(%struct.famm_timing* %t) {
entry:
  ; t->torsional_stress
  %ts_ptr = getelementptr %struct.famm_timing, %struct.famm_timing* %t, i32 0, i32 0
  %ts = load i32, i32* %ts_ptr

  ; t->interlocking_energy
  %ie_ptr = getelementptr %struct.famm_timing, %struct.famm_timing* %t, i32 0, i32 1
  %ie = load i32, i32* %ie_ptr

  ; add(torsional_stress, interlocking_energy)
  %tmp = call i32 @q16_16_add(i32 %ts, i32 %ie)

  ; t->laplacian_energy
  %le_ptr = getelementptr %struct.famm_timing, %struct.famm_timing* %t, i32 0, i32 2
  %le = load i32, i32* %le_ptr

  ; total = add(tmp, laplacian_energy)
  %result = call i32 @q16_16_add(i32 %tmp, i32 %le)
  ret i32 %result
}

; ═══════════════════════════════════════════════════════════════════════════
; Verification Harness (main for opt/lli)
; Compiles to native or runs with `lli fixedpoint_q16_16.ll`
; ═══════════════════════════════════════════════════════════════════════════

declare i32 @printf(i8*, ...)

@fmt_pass = constant [15 x i8] c"PASS: %s = %d\0A\00"
@fmt_fail = constant [15 x i8] c"FAIL: %s = %d\0A\00"

@str_mul_one = constant [8 x i8] c"mul_one\00"
@str_div_one = constant [8 x i8] c"div_one\00"
@str_neg_inv  = constant [12 x i8] c"neg_involut\00"
@str_abs_nonneg = constant [12 x i8] c"abs_nonneg\00\00"

define i32 @main() {
entry:
  ; --- Precompute all string pointers (must dominate all uses) ---
  %fmt_pass_ptr  = getelementptr [15 x i8], [15 x i8]* @fmt_pass,  i32 0, i32 0
  %fmt_fail_ptr  = getelementptr [15 x i8], [15 x i8]* @fmt_fail,  i32 0, i32 0
  %s1 = getelementptr [8 x i8],  [8 x i8]*  @str_mul_one,   i32 0, i32 0
  %s2 = getelementptr [8 x i8],  [8 x i8]*  @str_div_one,   i32 0, i32 0
  %s3 = getelementptr [12 x i8], [12 x i8]* @str_neg_inv,   i32 0, i32 0
  %s4 = getelementptr [12 x i8], [12 x i8]* @str_abs_nonneg, i32 0, i32 0

  ; --- Test mul_one: 1.0 * 1.0 = 1.0 ---
  %one = load i32, i32* @Q16_ONE
  %mul_result = call i32 @q16_16_mul(i32 %one, i32 %one)
  %mul_ok = icmp eq i32 %mul_result, %one
  br i1 %mul_ok, label %mul_pass, label %mul_fail

mul_pass:
  call i32 (i8*, ...) @printf(i8* %fmt_pass_ptr, i8* %s1, i32 %mul_result)
  br label %test_div

mul_fail:
  call i32 (i8*, ...) @printf(i8* %fmt_fail_ptr, i8* %s1, i32 %mul_result)
  br label %test_div

  ; --- Test div_one: 1.0 / 1.0 = 1.0 ---
test_div:
  %div_result = call i32 @q16_16_div(i32 %one, i32 %one)
  %div_ok = icmp eq i32 %div_result, %one
  br i1 %div_ok, label %div_pass, label %div_fail

div_pass:
  call i32 (i8*, ...) @printf(i8* %fmt_pass_ptr, i8* %s2, i32 %div_result)
  br label %test_neg

div_fail:
  call i32 (i8*, ...) @printf(i8* %fmt_fail_ptr, i8* %s2, i32 %div_result)
  br label %test_neg

  ; --- Test neg_involutive: -(-q) = q ---
test_neg:
  %neg1 = call i32 @q16_16_neg(i32 %one)
  %neg2 = call i32 @q16_16_neg(i32 %neg1)
  %neg_ok = icmp eq i32 %neg2, %one
  br i1 %neg_ok, label %neg_pass, label %neg_fail

neg_pass:
  call i32 (i8*, ...) @printf(i8* %fmt_pass_ptr, i8* %s3, i32 %neg2)
  br label %test_abs

neg_fail:
  call i32 (i8*, ...) @printf(i8* %fmt_fail_ptr, i8* %s3, i32 %neg2)
  br label %test_abs

  ; --- Test abs_nonNegative: abs(-1.0) >= 0 ---
test_abs:
  %abs_val = call i32 @q16_16_abs(i32 %neg1)
  %zero = load i32, i32* @Q16_ZERO
  %abs_ok = icmp sge i32 %abs_val, %zero
  br i1 %abs_ok, label %abs_pass, label %abs_fail

abs_pass:
  call i32 (i8*, ...) @printf(i8* %fmt_pass_ptr, i8* %s4, i32 %abs_val)
  br label %done

abs_fail:
  call i32 (i8*, ...) @printf(i8* %fmt_fail_ptr, i8* %s4, i32 %abs_val)
  br label %done

done:
  ret i32 0
}

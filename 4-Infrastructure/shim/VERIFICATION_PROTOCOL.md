# F01-F12 Verification Protocol

## Layer 1: Mathematical Verification (Wolfram Alpha)

**Every equation verified against Wolfram Alpha:**

```
Input: 121.567 * 65536
Wolfram: 7,967,421.952
Rounded: 7,967,422
Q16.16: 0x0079.9120
```

**Required for each F01-F12:**
- Closed-form solution where available
- Numerical test with 3+ input sets
- Edge cases (zero, infinity, singularities)
- Document Wolfram query in comment

---

## Layer 2: Computational Verification (Lean 4)

**Every `def` requires:**

```lean
def encodeWavelength (λ : Q16_16) : Q16_16 := ...

#eval encodeWavelength (Q16_16.ofFloat 121.567)
-- Expected: 0x0079.9120
-- Wolfram verified: 121.567 * 65536 = 7,967,422
```

**Every `def` requires theorem:**

```lean
theorem encodeWavelength_total (λ : Q16_16) : 
  ∃ result, encodeWavelength λ = result := by 
  simp [encodeWavelength]
```

**Build must pass:**
```bash
cd 0-Core-Formalism/lean/Semantics && lake build
```

---

## Layer 3: Determinism Verification

**Test: Same inputs → Same outputs (always)**

```python
def test_determinism():
    for i in range(1000):
        result = f01_encode(121.567)
        assert result == 0x0079.9120
```

**Failure modes:**
- Non-deterministic: Reject
- Undefined behavior: Reject
- Platform-dependent: Reject

---

## Layer 4: Symbolic Stripping Verification

**Test: Remove all semantic content, verify computation**

```
Original: encode_hydrogen_wavelength(λ)
Stripped: N_7 = floor(N_0 * 65536 + 32768) / 65536

Test: N_0 = 121.567 → N_7 = 0x0079.9120
Pass: Computation identical with/without names
```

**Required:** 100% pass rate on adversarial stripping test.

---

## Layer 5: Property-Based Testing

**QuickCheck-style random testing:**

```lean
theorem encode_roundtrip (λ : Q16_16) (h : λ ≥ 0) :
  |decode (encode λ) - λ| < 0.0001 := by 
  -- Property: encode then decode ≈ original
```

**Test properties:**
- Roundtrip (encode→decode ≈ original)
- Monotonicity (x < y → f(x) < f(y))
- Boundedness (output in valid range)
- Idempotence (f(f(x)) = f(x) where applicable)

---

## Layer 6: Cross-Implementation Verification

**Two independent implementations:**

1. **Lean 4** (canonical): `0-Core-Formalism/lean/Semantics/`
2. **Python** (reference): `4-Infrastructure/shim/validation/`

**Verify bit-identical outputs:**

```python
def test_cross_impl():
    for input_val in test_vectors:
        lean_result = lean_call(input_val)
        py_result = python_call(input_val)
        assert lean_result == py_result  # Bit-identical
```

---

## Layer 7: Statistical Verification (6.5σ)

**For claims with statistical component:**

```
Claim: Compression ratio > baseline
Test: 1000 random inputs
Mean: μ, Std: σ
Achieved: x = 6.5σ above baseline?
Required: Yes for 6.5σ claim
```

**Standard:** 6.5σ = 99.999999992% confidence  
**Minimum:** 5σ = 99.9999427% confidence  
**Below 5σ:** REJECT

---

## Verification Checklist per FXX

| Layer | Test | Pass Criteria | Status |
|-------|------|---------------|--------|
| 1 | Wolfram Alpha | 3+ numerical cases verified | ☐ |
| 2 | Lean #eval | All public functions have #eval | ☐ |
| 3 | Totality theorem | Every `def` has totality proof | ☐ |
| 4 | Determinism | 1000 iterations, identical outputs | ☐ |
| 5 | Symbolic stripping | Passes adversarial test | ☐ |
| 6 | Property tests | Roundtrip, monotonicity, bounds | ☐ |
| 7 | Cross-impl | Bit-identical with Python shim | ☐ |
| 8 | Statistical | 6.5σ where applicable | ☐ |
| 9 | Lake build | `lake build` passes | ☐ |
| 10 | No sorry | Zero `sorry` in code | ☐ |

**All 10 must pass for VALIDATED status.**

---

## Automated Verification Script

```bash
#!/bin/bash
# verify_fxx.sh

FXX=$1

echo "Verifying $FXX..."

# Layer 2: Lean build
cd 0-Core-Formalism/lean/Semantics
if ! lake build; then
    echo "FAIL: lake build"
    exit 1
fi

# Layer 4: Adversarial stripping
if ! python3 4-Infrastructure/shim/adversarial_symbolic_stripping.py --test $FXX; then
    echo "FAIL: symbolic stripping"
    exit 1
fi

# Layer 6: Cross-implementation
if ! python3 4-Infrastructure/shim/cross_verify.py --lean $FXX; then
    echo "FAIL: cross-implementation"
    exit 1
fi

echo "PASS: $FXX verified"
```

---

## Best Verification: Compositional

**Verify components, compose to system:**

```
F01 verified + F02 verified + ... + F12 verified
    ↓
Compose: F01∘F02∘...∘F12
    ↓
Verify composition: Master equation
```

**Do not:** Verify only final output  
**Do:** Verify each FXX independently, then verify composition

---

## Summary

**Best verification = 10-layer compositional checking:**

1. Wolfram Alpha (math)
2. Lean #eval (compute)
3. Totality theorems (total functions)
4. Determinism (1000 iterations)
5. Symbolic stripping (no semantic deps)
6. Property-based (random testing)
7. Cross-implementation (bit-identical)
8. Statistical (6.5σ)
9. Lake build (compiles)
10. No sorry (proven correct)

**10/10 required for publication.**

Current F01-F12 status: 0/10

---

**Document ID:** VERIFICATION-PROTOCOL-2026-05-06  
**Standard:** 10-layer compositional verification  
**Target:** 100% pass rate for all F01-F12  
**Current:** 0% — blocked on F01-F12 formalization

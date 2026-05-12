**1. YES/NO VERDICT TABLE**

| Question | Verdict | Notes |
|----------|---------|-------|
| Q1: Internal consistency of canonical arithmetic? | YES | All computed values match the spec and Lean receipt. |
| Q2: Is K=7 invalid as a selective threshold? | YES | FPR ≈94.57% under random-permutation null. |
| Q3: Is K=21 defensible for ~5% FPR? | YES (with caveats) | Strict `>21`: 3.05% FPR. Inclusive `>=21`: 5.43% FPR (slightly above 5%). |
| Q4: Does prime-gap signal survive corrected threshold? | YES (severely attenuated) | Strict `>21`: 38 fires (0.0038% of windows). Inclusive `>=21`: 190 fires (0.019%). Original `>7`: 86,565 fires (8.66%). |
| Q5: Is the provided conclusion appropriately worded? | YES | Correctly states original was artifact, surviving fires are rare candidate motifs, not general phenomenon. |
| Q6: Is the fusion rule correct for intended semantics? | YES | `braid(t→t+1)` AND `sigma_q(t+1)` AND `D_q(t+1)` correctly targets turbulent transition into collapsed arrival window. |

---

**2. ARITHMETIC RECHECK**

- **Crossing count**: `dense_rank(A)=[0,2,1,0,2,1,0,1]`, `dense_rank(B)=[2,1,0,2,1,0,1,2]`. 12 crossings verified.
- **D₂**: `sum p² = 22/64 = 0.34375`. `D₂ = -log(0.34375)/log(8) ≈ 0.5135`.
- **σ_q (Hurst)**: MSD(1)=64/7≈9.143, MSD(2)=8, MSD(4)=10. OLS slope=0.0646, `σ_q=0.0323`.
- **Kendall SD**: Variance = `8×7×21/72 = 16.3333`, SD = `√16.3333 = 4.04145`.
- **Exact tail probabilities** (W=8, 40320 permutations):
  - `P(count>7) = 38129/40320 ≈ 0.9457`
  - `P(count>21) = 1230/40320 ≈ 0.0305`
  - `P(count>=21) = 2191/40320 ≈ 0.0543`
- **All values match** the canonical spec and Lean receipt.

---

**3. STATISTICAL INTERPRETATION**

- **K=7 threshold**: HEURISTIC and non-selective (94.57% FPR under random permutations). Using it as a braid component in a triple condition does not control false positives.
- **K=21 threshold**: HEURISTIC calibration to ~5% FPR under random-permutation null. Strict `>21` yields 3.05% FPR; inclusive `>=21` yields 5.43% FPR.
- **σ_q and D₂ thresholds**: `σ_c=0.4` and `D_c=0.7` are HEURISTIC. `σ_q=0.0323` is a DETERMINISTIC WINDOW FEATURE (n=8 is too short for reliable Hurst estimation).
- **Prime-gap data**: The random-permutation null is not appropriate for prime gaps (ties, non-uniform marginal distribution, local dependence). Therefore, the FPRs above are not reliable for prime gaps.

---

**4. PRIME-GAP SIGNAL VERDICT**

- **Original signal (`cross>7`)**: 86,565 fires in 999,991 windows (8.66%). This high rate is expected given the 94.57% FPR of the braid component alone.
- **Corrected strict (`cross>21`)**: 38 fires (0.0038%). **Survives but extremely rare**.
- **Corrected inclusive (`cross>=21`)**: 190 fires (0.019%). **Survives but rare**.
- **Interpretation**: The original claim of common firing on prime gaps was an artifact of the non-selective K=7. The corrected thresholds reduce fires by factors of ~2,300 (strict) and ~450 (inclusive). Surviving windows are candidate structured motifs (e.g., alternating patterns) but do not support a general entropy-collapse phenomenon.

---

**5. FUSION-RULE VERDICT**

- **Rule**: `braid(t→t+1) AND sigma_q(window t+1) AND D_q(window t+1)`
- **Intended semantics**: Detect turbulent transition (braid) into a window that is already collapsed (low σ_q and D₂). Using `window t` for σ_q/D₂ would detect collapse in the departure window, which could fire early.
- **Verdict**: The rule correctly implements the intended semantics.

---

**6. FAILURE MODES**

1. **Tied ranks**: Dense ranking excludes ties, but the permutation null assumes distinct values. Prime gaps have ties (e.g., many gaps of 2). This invalidates the permutation FPR.
2. **Overlapping sliding windows**: Windows overlap by 7 points, violating independence assumptions. Multiple testing corrections are non-trivial.
3. **Prime-gap marginal distribution**: Gaps are not uniformly distributed (e.g., even gaps except 1, high frequency of 2). The random-permutation null is inappropriate.
4. **Local dependence**: Prime gaps exhibit local patterns (e.g., twin primes, gap chains). The braid crossing statistic assumes independent permutations.
5. **Using permutation-tail FPR on non-permutation data**: The 5% FPR threshold is derived under a random-permutation null, which does not hold for prime gaps. Actual FPR unknown.
6. **Multiple testing**: Testing ~1 million overlapping windows without correction inflates family-wise error rate.

---

**7. NEXT VALIDATION TESTS**

1. **Permutation test on prime gaps**:
   - **Method**: For each window pair, shuffle the 8 gap values within each window independently (preserving marginal distribution but breaking local structure). Compute the number of fires under the corrected threshold.
   - **Expected**: If the observed fires (38 strict, 190 inclusive) are within the 95% percentile of the permutation distribution, the signal is consistent with chance.
2. **Block bootstrap test**:
   - **Method**: Resample blocks of prime gaps (block length >8) to preserve local dependence. Compute firing rates.
   - **Expected**: If the observed firing rate is not significantly higher than bootstrap rates, the signal may be due to dependence.
3. **Non-overlapping windows**:
   - **Method**: Use non-overlapping windows (t=0,8,16,...) to reduce dependence.
   - **Expected**: If fires remain rare, strengthens signal; if they disappear, suggests overlapping-window artifact.
4. **Synthetic data with same marginal distribution**:
   - **Method**: Generate i.i.d. sequences from the empirical gap distribution (first 1M primes). Compute firing rate.
   - **Expected**: If observed fires exceed synthetic fires, suggests structure beyond marginal distribution.
5. **Adjust for multiple testing**:
   - **Method**: Apply Bonferroni or Šidák correction to the per-window threshold (e.g., `alpha = 0.05 / 999,991`).
   - **Expected**: The corrected threshold becomes more stringent (K>21). If fires persist, they are more significant.

---

**8. CANONICAL SPEC PATCHES**

Add these explicit warnings and clarifications to the canonical spec:

1. **Thresholds are heuristic**:
   "K=21, σ_c=0.4, D_c=0.7 are calibrated to a white-noise random-permutation null. They do not guarantee a 5% FPR for non-permutation data (e.g., prime gaps)."

2. **Window features are not estimators**:
   "σ_q (Hurst) and D₂ computed on n=8 are DETERMINISTIC WINDOW FEATURES, not statistically reliable long-series estimators. Do not report confidence intervals or p-values."

3. **Prime-gap null mismatch**:
   "Prime gaps violate the random-permutation null due to ties, non-uniform marginal distribution, and local dependence. Permutation-based FPRs are not applicable."

4. **Multiple testing**:
   "Sliding windows overlap, violating independence. Family-wise error rate is uncontrolled. Any claimed signal must survive multiple-testing correction."

5. **Fusion rule clarification**:
   "The fusion rule uses `sigma_q(window t+1)` and `D_q(window t+1)` to detect collapse in the arrival window, not
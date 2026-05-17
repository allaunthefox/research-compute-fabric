# Corrected Arithmetic Specification — Entropy-Collapse Detector

**Date:** 2026-05-11  
**Status:** Self-verified in Python. All numbers computed exactly. No model dependency.

---

## Verified Results (pen-and-paper checkable)

### Component 1: Braid Crossing Count

| Quantity | Value |
|---|---|
| A = [2, 6, 4, 2, 6, 4, 2, 4] | — |
| B = [6, 4, 2, 6, 4, 2, 4, 6] | — |
| dense_rank(A) | [0, 2, 1, 0, 2, 1, 0, 1] |
| dense_rank(B) | [2, 1, 0, 2, 1, 0, 1, 2] |
| **Crossing count** | **12** |
| Max possible (W=8) | C(8,2) = 28 |
| K=7 (raw): 12 > 7 | FIRES — but ~94.6% FPR on white noise |
| K=21 (raw): 12 ≤ 21 | DOES NOT FIRE — ~3.05% strict FPR |

**Tie rule:** dense ranking — equal values get equal rank. Phantom crossings between tied elements are excluded.

**Operation:** For pair (i,j), count as crossing iff sign(rank_A[i]-rank_A[j]) ≠ sign(rank_B[i]-rank_B[j]), with sign(0) = 0 (ties excluded from counting).

---

### Component 2: Sigma_q / Hurst Exponent

| Quantity | Value |
|---|---|
| Series x | [2, 6, 4, 2, 6, 4, 2, 6] |
| MSD(1) | 64/7 ≈ 9.143 |
| MSD(2) | 48/6 = 8.000 |
| MSD(4) | 40/4 = 10.000 |
| OLS slope (2H) | 0.0646 |
| **H = σ_q** | **0.0323** |
| σ_c = 0.4 | 0.0323 < 0.4 → COLLAPSED |

**Physical meaning:** H=0.032 is EXTREMELY anti-persistent. The series oscillates perfectly (2→6→4→2→6→4→2→6). Every large step is followed by reversal. The system is forced — it cannot explore freely.

**WARNING:** n=8 is too short for a statistically robust Hurst estimate. This value is a deterministic window feature, not a reliable long-series estimate. Use only as a local indicator within the sliding window framework.

---

### Component 3: D_q — Rényi D_2

| Quantity | Value |
|---|---|
| Series x | [2, 6, 4, 2, 6, 4, 2, 6] |
| Value counts | {2: 3, 4: 2, 6: 3} |
| Probabilities | [3/8, 2/8, 3/8] |
| Σp² | 9/64 + 4/64 + 9/64 = **22/64 = 0.34375** |
| D_2 = -log(0.34375)/log(8) | **0.5135** |
| D_c = 0.7 (heuristic) | 0.5135 < 0.7 → BELOW → collapsed |

**D_c = 1.2 is a DEFINITION MISMATCH** for 1D Rényi D_2 (bounded [0,1]). The correct D_c for this estimator must be in [0,1]. D_c = 0.7 is a plausible heuristic threshold; label as calibrated, not derived.

---

### Component 4: False Positive Rate — Kendall Tau Distance

For two independent uniform random permutations of {0..7}:

| K | P(count > K) exact | P(count ≥ K) exact |
|---|---|---|
| 7 | 38129/40320 = **94.57%** | — |
| 14 | 18242/40320 = **45.24%** | 22078/40320 = **54.76%** |
| 21 | 1230/40320 = **3.05%** | 2191/40320 = **5.43%** |
| 22 | 628/40320 = **1.56%** | 1230/40320 = 3.05% |

**Mean = 14, Variance = 8×7×21/72 = 1176/72 = 16.3333, SD = 4.04145**

The LLM-reported SD of 4.7 is WRONG. The correct SD is sqrt(16.3333) = 4.04145.

**Implication:** K=7 alone is not selective (~95% FPR). The triple condition works because σ_q and D_q must ALSO fire simultaneously — the braid component is a necessary but not sufficient condition.

---

## Corrected Invariant Parameters

| Parameter | Correct Value | Notes |
|---|---|---|
| K | 21 (strict >) or 20 (≥ convention) | For ~5% FPR on white noise, W=8 |
| σ_c | 0.4 | Below random walk baseline (0.5). Crossing = forced reversals. |
| D_c | 0.7 (heuristic) | For 1D Rényi D_2. Label as calibrated, not derived. |
| τ | substrate-specific | Only free parameter per substrate. |

---

## Most Common Implementation Mistakes

1. **Using argsort instead of dense_rank for ties.** argsort breaks ties by position, creating phantom crossings. Unit test: `assert dense_rank([2,4,2,6]) == [0,1,0,2]`.

2. **Mixing log bases in OLS.** Must use same base (log2) for both x and y axes. The base cancels in the ratio, but only if consistent.

3. **Forgetting the /2 in H = slope/2.** The OLS slope is 2H, not H. Missing the /2 doubles the exponent.

4. **Using D_c = 1.2 with 1D Rényi D_2.** Impossible — bounded by 1. Use D_c ∈ [0,1] or switch to a different D_q estimator.

5. **Treating n=8 Hurst as statistically reliable.** It is a deterministic window feature only. Do not report confidence intervals or p-values.

---

## Fusion Rule

Triple condition fires when:  
`braid(t→t+1)` AND `σ_q(window t+1)` AND `D_q(window t+1)`

Rationale: detect whether the system has ARRIVED in a collapsed state (t+1) while the transition was turbulent. Using window t instead leads to early false positives.

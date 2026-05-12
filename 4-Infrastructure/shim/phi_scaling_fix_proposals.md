# Φ-Scaling Equation Fix Proposals

## Test Results Summary

| Test | Status | Error | Issue |
|------|--------|-------|-------|
| LTEE Fitness | FAIL | 133.45% | Square-root scaling too aggressive |
| Drake's Rule | FAIL | 60.61% | Per-genome rate assumption wrong |
| Fractal Dimension | PASS | 5.06% | Works well - keep as is |
| Sampling Coincidence | PARTIAL | 7.67% | Close but not exact |

## Proposed Fixes

### Fix 1: LTEE Fitness Trajectory

**Problem**: Simple square-root scaling `P ∝ S^{1/2}` overpredicts fitness dramatically at higher mutation counts (237.5% error at 50,000 generations).

**Root Cause**: LTEE exhibits stronger diminishing returns than simple square-root due to:
- Clonal interference (multiple beneficial mutations compete)
- Resource limitation (carrying capacity 500M cells, 25 mg/L glucose)
- Epistatic interactions (negative epistasis between mutations)
- Mutation rate evolution (mutator strains appear)

**Proposed Fix**: Replace square-root with a selected response family that incorporates epistatic interference:

```
P = C_domain · (S / (K + S))^α · lambda_phi^{D_f} · B_gate
```

where:
- `K` = half-saturation constant (epistatic interference strength)
- `α` = scaling exponent (fit to data, likely < 0.5)
- This is a Michaelis-Menten type saturating function

**Alternative**: Use logarithmic scaling with epistatic correction:

```
P = C_domain · log(1 + β·S) · lambda_phi^{D_f} · B_gate
```

where:
- `β` = epistatic interference coefficient
- Logarithmic scaling naturally gives diminishing returns

**Expected Improvement**: Logarithmic or saturating functions should capture the observed LTEE fitness trajectory more accurately than simple power law.

**Model-selection update**: A local response-family sweep found:

```
best tested LTEE response:
  hill_saturation
  avg_error = 0.40604904495100724%
  K = 200
  hill = 0.5

nearest logarithmic response:
  log_mutations
  avg_error = 0.48125216224193257%
  beta = 0.31622776601683794
```

This keeps logarithmic scaling as a serious natural-law candidate, but not a
forced answer. The updated rule is to select among logarithmic, low-exponent,
Michaelis-Menten, and Hill/saturation responses by measured error,
complexity penalty, and held-out validation.

Natural logarithmic-law rationale:

```
Weber-Fechner perception       -> bounded response to broad stimulus range
Benford distributions          -> multiplicative growth over log intervals
logarithmic spirals            -> self-similar growth under scale
Boltzmann / Shannon entropy    -> log accessible states
cooling / decay thresholds     -> logarithmic time-to-threshold equations
```

Compression / transfold implication:

```
logs are admissible when a domain compresses multiplicative scale,
state multiplicity, or threshold response into a bounded observable
```

### Fix 2: Drake's Rule

**Problem**: Per-genome rate assumption fails across taxa. Model works for E. coli (reference) but fails dramatically for larger organisms (100% error for humans).

**Root Cause**: The corrected Drake's rule states:
- Per-genome mutation rate (U) is approximately bounded across taxa
- Per-site mutation rate (μ) scales roughly inversely with genome size: μ ∝ 1/G
- The simple Φ-scaling model doesn't capture this inverse relationship

**Proposed Fix**: Incorporate genome-size dependence explicitly:

```
U_genome = C_domain · lambda_phi^{D_f} · B_gate (bounded, ~0.001-100 per genome)
μ_site = U_genome / G (inverse scaling with genome size)
```

**Additional Factors**:
- Generation time (g): Longer-lived organisms have fewer cell divisions
- Population size (Ne): Larger populations have stronger selection on mutation rate
- DNA repair efficiency (R): Eukaryotes have better repair than bacteria
- Metabolic rate (M): Higher metabolic rate → more oxidative damage

**Full Model**:

```
U_genome = C_domain · lambda_phi^{D_f} · B_gate · (g/g_ref)^{-1} · (Ne/Ne_ref)^{-1/2}
μ_site = U_genome / G · R · M
```

**Expected Improvement**: Incorporating generation time, population size, and DNA repair should capture the observed variation across taxa.

### Fix 3: Fractal Dimension (No Change)

**Status**: PASS - 5.06% error

**Keep as is**: The predicted D_f = log(2)/log(Φ) ≈ 1.44042 matches empirical genetic network data well. This is the strongest validated component of the Φ-scaling framework.

**Recommendation**: Use this as the core validated prediction. Treat other scaling relationships as requiring domain-specific refinement.

### Fix 4: Sampling Coincidence (Treat as Coincidence)

**Status**: PARTIAL - 7.67% error

**Recommendation**: Treat 30·Φ^6 ≈ 538 vs 500 generations as a candidate scale coincidence, not a derived Nyquist rate. Do not claim it as a prediction.

**Reason**: The 7.67% error is within "close coincidence" range but not precise enough to claim as a derived result.

## Unified Refined Model

### Core Validated Component

```
D_f = log(2)/log(Φ) ≈ 1.44042 (fractal dimension of genetic networks)
```

### LTEE Fitness Model (Refined)

```
Fitness =
  C_domain
  · response_family(mutations; θ)
  · lambda_phi^{D_f}
  · exp(-gamma·DeltaE_eff/kT)
```

where:
- `response_family` = selected from log, low-exponent power, Michaelis-Menten, or Hill/saturation candidates
- `θ` = fitted response parameters
- `lambda_phi^{D_f}` = fractal gain (4 if lambda_phi = Φ², 2 if lambda_phi = Φ)
- `DeltaE_eff` = incremental metabolic barrier (not total bond energy)

### Mutation Rate Model (Refined)

```
U_genome = C_domain · lambda_phi^{D_f} · B_gate · (g/g_ref)^{-1} · (Ne/Ne_ref)^{-1/2}
μ_site = U_genome / G
```

where:
- `g` = generation time (years)
- `Ne` = effective population size
- `B_gate` = binding gate for DNA repair efficiency
- `G` = genome size

### General Form

```
P = C_domain · f(S) · lambda_phi^{D_f} · B_gate
```

where:
- `f(S)` = domain-specific response function selected by receipt, not assumed
- `lambda_phi^{D_f}` = fractal gain (validated)
- `B_gate` = binding/admissibility gate (domain-specific barrier)
- `C_domain` = domain normalization (fit to data)

## Implementation Plan

1. **Fit LTEE response-family models** to Wiser et al. 2013 data
2. **Fit Drake's rule model** with generation time and population size
3. **Validate fractal dimension** on additional genetic networks
4. **Treat sampling coincidence** as coincidence, not prediction
5. **Update SIGNAL_ANALYSIS_GENETIC_IMPLICATIONS.md** with refined models
6. **Create Lean formalization** of refined models

## Key Insight

The Φ-scaling framework provides a **topological prior** (fractal dimension) that is validated, but **power-law scaling** requires domain-specific refinement. The fractal dimension D_f = log(2)/log(Φ) ≈ 1.44042 is the robust, universal prediction. Evolutionary dynamics (fitness, mutation rates) require organism-specific parameters beyond simple Φ-scaling.

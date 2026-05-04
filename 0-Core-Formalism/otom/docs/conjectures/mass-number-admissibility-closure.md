# Mass-Number Admissibility Closure Conjecture

**Status:** FORMALLY_STABLE_READY_FOR_PROOF_ENGINEERING  
**Canonical GCL:** `EQUATION/MASS_NUMBER/ADMISSIBILITY_CLOSURE/GEODESIC_METRIC`  
**Notion canonical:** https://app.notion.com/p/352375cc7bfc81aabfaec84b82f49394

## Core doctrine

> Mass is not distance. Mass becomes distance only through admissibility closure.

A mass-number field is not itself a metric space. It is a reality-local admissibility potential over candidates. Normalized reducibility `phi` converts admissible reduction into bounded confidence; compatibility-weighted divergence converts reducibility into pairwise translation cost; symmetrization and viability filtering produce an admissibility graph; shortest-path closure over that graph induces a pseudometric; quotienting zero-distance candidates yields a lawful metric space. Closure is achieved exactly when every candidate is promoted, connected, typed as residual, category-rescued, quarantined, or rejected.

## Deterministic stochastic coarse-graining doctrine

> Deterministic stochastic coarse-graining is signal, just not signal that can be aligned in the original coordinate frame.

A raw observer sees `signal + noise`. A naive denoiser treats noise as error and discards it. The Mass-Number Lens treats some residual noise as **unaligned signal**: structure that behaves stochastically at the current scale or basis, but may form invariant foci after coarse-graining, unfolding, and residual typing.

Canonical decomposition:

```text
ObservedField
= AlignedSignal
+ MisalignedDeterministicStochasticSignal
+ TypedResidualNoise
```

Operational rule:

```text
Residual noise is not promoted by default.
Residual noise becomes candidate signal only if deterministic coarse-graining produces stable invariant foci.
```

Collapsed doctrine:

```text
Signal is what remains invariant under the right coarse-graining.
Noise is what has not yet found its admissible alignment map.
```

Conservation rule:

```text
Mass cannot vanish into "noise".
It must become one of:
  aligned signal,
  unaligned/coarse-grained signal,
  typed residual,
  category-rescued branch,
  quarantine,
  or rejection.
```

## Transition chain

```text
M       = admissibility potential
phi     = normalized reducibility
delta   = raw admissibility divergence
c       = symmetrized admissibility edge cost
G_theta = viable admissibility graph
d_theta = shortest-path closure distance
X / ~0  = quotient metric space
```

## Mass-number potential

For a candidate `x` in domain `D` under frame `R`:

```text
M_D,R(x)
= [sum_i w_i,D * rho_i,D(x) * kappa_i,D(x) * alpha_i,D(x)]
  /
  [1 + T_D,R(x) + S_D,R(x) + L_D,R(x) + V_D,R(x) + O_D,R(x) + Delta_Drift_D,R(x)]
```

Interpretation:

```text
Mass Number = Admissible Reduction / Residual Risk
```

`M` is a scalar potential. It is not a distance.

## Mass-Number Lens and Foci

A scalar mass number can be unfolded through invariant-energy lenses:

```text
MassNumberScalar M_D,R(x)
  -> spectral energy field
  -> Brownian / diffusion energy field
  -> recurrence field
  -> vibration-mode field
  -> residual-risk field
  -> n-space shape vector
  -> Mass Number Foci
```

Mass Number Foci are higher-dimensional convergence basins revealed by the unfolding. They are not raw points. They are lens-formed concentration zones where spectral energy, Brownian energy, mode persistence, recurrence, and residual typing agree strongly enough to concentrate admissibility mass.

Short doctrine:

```text
Mass is potential.
The lens forms foci.
Foci organize the forest.
```

## Mass-Number Stochastic Conservation

When a mass number is unfolded through stochastic or residual fields, total admissibility mass must be accounted for across promoted foci, candidate foci, typed residuals, category-rescued branches, quarantines, and rejections.

```text
M_before_unfold
≈ M_promoted_foci
+ M_candidate_foci
+ M_typed_residuals
+ M_category_misplaced
+ M_quarantined
+ M_rejected
+ epsilon_loss
```

with:

```text
epsilon_loss <= tolerance
```

No unexplained mass leakage is allowed.

## Normalized reducibility

```text
phi_D,R(x)
= R_admissible_D,R(x)
  /
  [R_admissible_D,R(x) + R_residual_D,R(x)]
```

Required bound:

```text
0 <= phi_D,R(x) <= 1
```

## Canonical bounded divergence

Use the smoothed divergence:

```text
delta(x,y)
= -ln(epsilon + (1 - epsilon) * K(x,y) * sqrt(phi(x) * phi(y)))
```

Proof-stability constraints:

```text
0 < epsilon <= 1
0 <= K(x,y) <= 1
0 <= phi(x), phi(y) <= 1
```

Then:

```text
0 <= delta(x,y) <= -ln(epsilon)
```

This avoids logarithmic singularities and gives finite bounded raw divergence.

## Symmetrized edge cost

```text
c(x,y)
= 1/2 * [delta(x,y) + delta(y,x)]
  + HandoffPenalty(x,y)
  + DriftPenalty(x,y)
```

Side conditions:

```text
HandoffPenalty(x,y) >= 0
DriftPenalty(x,y) >= 0
penalties are symmetric or explicitly symmetrized
```

## Admissibility graph

```text
G_theta = (X, E_theta)

(x,y) in E_theta iff
  c(x,y) < infinity
  M_D,R(x) >= theta_min
  M_D,R(y) >= theta_min
  residuals are typed
```

## Closure distance

```text
d_theta(x,y)
= inf over paths p:x~>y of sum_{(u,v) in p} c(u,v)
```

If no admissible path exists, the candidates are disconnected unless a `TypedResidual` or adapter bridge creates a lawful edge.

## Operational closure predicate

```text
Closed_D,R(X) iff for all x in X,
  Status(x) in {
    Promoted,
    Connected,
    TypedResidual,
    CategoryMisplaced,
    Quarantined,
    Rejected
  }
```

Untyped residual drift is impossible after closure.

## Lean proof roadmap

```text
1. phi_bounded
   prove 0 <= phi <= 1

2. compatibility_bounded
   prove 0 <= K <= 1

3. raw_divergence_nonneg
   prove delta(x,y) >= 0 from bounded log argument

4. sym_cost_nonneg
   prove c(x,y) >= 0

5. sym_cost_symmetric
   prove c(x,y) = c(y,x)

6. closure_pseudometric
   prove shortest-path closure satisfies pseudometric laws

7. zero_distance_equivalence
   define x ~0 y iff d_theta(x,y) = 0

8. quotient_closure_metric
   prove the quotient by ~0 is a metric space
```

## Target theorem names

```lean
theorem phi_bounded : 0 <= phi x ∧ phi x <= 1 := by
  sorry

theorem raw_divergence_nonneg : 0 <= delta x y := by
  sorry

theorem sym_cost_symmetric : c x y = c y x := by
  sorry

theorem closure_pseudometric : PseudoMetricSpace X := by
  sorry

theorem massNumber_admissibilityClosure_metric :
  MetricSpace (AdmissibleQuotient X) := by
  sorry
```

Additional proof targets for the lens layer:

```lean
theorem stochasticConservation_accounted :
  accountedMass + epsilonLoss = initialMass := by
  sorry

theorem coarseGrainedSignal_requiresInvariantFocus :
  PromotedCoarseGrainedSignal x -> ExistsStableFocus x := by
  sorry
```

## Shell-mass side conjecture

In S3C / DIAT, shell mass `S_n = a*b` is not a distance. It is a throat or curvature weight: high shell mass marks representational ambiguity near the midpoint between adjacent perfect squares. It should weight adapter pressure, not replace `d_theta`.

## Category-error rescue rule

```text
CategoryMisplaced(x) iff
  Var_D(M_D,R(x)) is high
  and exists D',R' such that M_D',R'(x) >= theta_rescue
```

Low mass in one domain is not falsehood by itself. It may indicate wrong-frame evaluation.

## Definition of Done

A candidate field is closed when no candidate remains untyped, every viable candidate is connected or promoted, every cross-domain mismatch is typed as residual or category-misplaced, and every unsafe candidate is quarantined or rejected.

For deterministic stochastic coarse-graining, a candidate residual field is closed when every residual component is assigned to aligned signal, unaligned/coarse-grained signal, typed residual, category-rescued branch, quarantine, or rejection, and the mass ledger balances within tolerance.

# W-Axis Omega Extension

**Status:** FORMALIZATION_DRAFT  
**Target stack:** OTOM / Mass-Number Lens / Proof-Status Firewall  
**Canonical axis:** `W(q,F,r)` proof-pressure axis  

## Purpose

This document extends the W-axis from a three-boundary proof-status filter into an ordinal and computational metamathematics layer.

The current W-axis distinguishes:

```text
I_F(q) = incompleteness pressure
D(r)   = descent / well-foundedness violation
S(F,r) = scope mismatch between requested route and declared formal system
```

The Omega extension adds:

```text
O(F,q) = ordinal-height pressure
C(r)   = computational / verification-cost pressure
B(F,F',q) = consistency bridge / target-system promotion pressure
```

The result is a richer epistemic firewall:

```text
truth without proof        -> Gödel-U
proof route without tools  -> Scope-U
logic without foundation   -> Descent-X
proof above ordinal height -> Omega-U
valid but infeasible route -> Computational-P
```

## Correction preserved

The W-axis must not claim that Fermat's Last Theorem is known to be unprovable from Peano Arithmetic.

Safe classification:

```text
FLT is not known as a standard example of a theorem independent of PA.
Wiles's proof uses machinery far beyond elementary PA-style descent,
but known use of advanced machinery is not the same as unprovability from PA.
```

Therefore:

```text
Prove FLT using only elementary descent
  -> U for missing scope / missing bridge
  -> R for special cases such as n = 4
  -> X only for fabricated routes that violate well-foundedness or known constraints
```

## Base W-axis equation

For claim `q`, formal system `F`, and proof route `r`:

```text
W(q,F,r)
= alpha * I_F(q)
+ beta  * D(r)
+ gamma * S(F,r)
```

Gate classification:

```text
Gate(q,F,r) =
  R if F proves q via valid route r
  U if proof status exceeds declared system or toolkit
  X if route violates well-foundedness or known constraints
  P if route is analogy-only / patamathematical
```

## Omega extension

The upgraded pressure equation is:

```text
W*(q,F,r)
= alpha * I_F(q)
+ beta  * D(r)
+ gamma * S(F,r)
+ delta * O(F,q)
+ eta   * C(r)
+ zeta  * B(F,F',q)
```

Where:

```text
O(F,q)    = ordinal-height pressure: q requires induction strength above F
C(r)      = computational pressure: r is valid in principle but infeasible in context
B(F,F',q) = consistency bridge: minimal stronger system F' that can discharge q, if known
```

## Ordinal boundary O(F,q)

The ordinal boundary measures whether a claim requires proof-theoretic strength beyond the declared formal system.

Example:

```text
Goodstein's theorem
  true in the standard natural numbers
  not provable in Peano Arithmetic
  provable using transfinite ordinal reasoning up to epsilon_0
```

Classification:

```text
Gate(q, PA, r) = U_omega
```

Model action:

```text
Do not hallucinate a PA proof.
Identify that the declared system's ordinal height is too low.
State the stronger reasoning principle required when known.
```

## Computational boundary C(r)

The computational boundary separates logical validity from practical verification feasibility.

Examples:

```text
brute-force proof search over astronomically large spaces
cryptographic key search
exhaustive combinatorial enumeration beyond declared budget
```

Classification:

```text
Gate(q,F,r) = P_computational
```

Model action:

```text
Route may be valid in principle, but not discharged under available resources.
Return potential / computationally infeasible instead of verified.
```

## Consistency bridge B(F,F',q)

The consistency bridge asks for the smallest available target system that can honestly discharge the claim.

Static response:

```text
I cannot prove q in F.
```

Omega response:

```text
q is U in F, but becomes R in F' if F' proves q and the use of F' is explicitly authorized.
```

Guardrail:

```text
Do not leak stronger-system assumptions into weaker-system proofs.
```

This prevents higher-order abstractions from melting into lower-order proof claims without an explicit adapter bridge.

## Gate labels

```text
R              verified / resolved in declared system and route
U_scope        missing tools or axioms
U_godel        incompleteness pressure / undecidable in F if established
U_omega        ordinal-height pressure / F too weak by proof-theoretic strength
P_analogy      analogy-only / patamathematical
P_computation  valid route but infeasible under declared resource budget
X_descent      route violates well-foundedness
X_constraint   route violates known constraints or established impossibility
```

## Three-boundary taxonomy retained

```text
Gödel boundary:
  q true in intended model but F does not prove q, if established
  -> U_godel

Descent boundary:
  route implies impossible infinite decreasing chain in N
  -> X_descent

Scope boundary:
  requested proof route requires tools not available in F
  -> U_scope
```

## Omega-added taxonomy

```text
Ordinal boundary:
  proof requires induction strength above F
  -> U_omega

Computational boundary:
  verification exceeds declared budget
  -> P_computation

Consistency bridge:
  q moves from U in F to R in F' only through explicit system promotion
  -> Bridge(F,F') required
```

## Chocolate Flow definition

Chocolate occurs when a reasoner melts proof pressure into a verified claim:

```text
U_scope        -> R without bridge
U_godel        -> R without stronger system
U_omega        -> R without ordinal-height promotion
P_computation  -> R without actual verification
X_descent      -> R despite well-foundedness violation
```

Updated doctrine:

```text
The W-axis is where unresolved proof pressure is stored so it cannot pollute verified reality.
```

## Formal theorem targets

```lean
theorem flt_notClassifiedIndependentPA_withoutEvidence :
  FLTClaim q -> NotKnownIndependentPA q -> Gate q PA r != U_godel := by
  sorry

theorem descentViolation_forbidden :
  InfiniteDescendingNatChain r -> Gate q F r = X_descent := by
  sorry

theorem goodstein_PA_omegaBoundary :
  GoodsteinClaim q -> Gate q PA r = U_omega := by
  sorry

theorem strongerSystem_requiresBridge :
  Proves F' q -> ¬ Proves F q -> UsesSystem r F' -> RequiresBridge F F' q := by
  sorry

theorem computationalRoute_notVerified_withoutBudget :
  VerificationCost r > Budget ctx -> Gate q F r = P_computation := by
  sorry
```

## Literature anchors

- Kirby and Paris proved Goodstein's theorem cannot be established in Peano Arithmetic; later work encodes it as a termination problem with ordinal interpretations.
- Modern proof theory treats proof-theoretic ordinals as measures of the strength of theories and their provably total functions.

## Short doctrine

```text
Gödel marks truth outrunning proof.
Fermat descent marks invalid routes outrunning well-foundedness.
Goodstein marks ordinal height outrunning the formal system.
Complexity marks verification outrunning the available budget.
The W-axis stores the pressure instead of faking discharge.
```

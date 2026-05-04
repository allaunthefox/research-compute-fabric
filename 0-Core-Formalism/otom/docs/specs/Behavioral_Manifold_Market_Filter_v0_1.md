# Behavioral Manifold Market Filter v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This is a research filter specification, not a trading system and not financial advice. The goal is to discover behavioral equivalences across heterogeneous systems by embedding them into a common manifold and ranking matches by distance, binding, turbulence, and adapter explanation.

---

## 1. Core thesis

Humans classify by nouns:

```text
shipping containers
DNA sequencing
grandmother’s cookies
semiconductors
market assets
protocols
```

The behavioral manifold classifies by operators:

```text
input stock
→ constrained transformation
→ queue / bottleneck
→ quality or error filter
→ output delivery
→ lagged feedback
→ regime shift
```

The filter asks:

> Do two objects instantiate the same behavioral operator, even if their ontology labels are different?

This is the usable market idea. It does not claim that different things are identical. It claims that different things can share invariant dynamics.

---

## 2. Core object

Each observed object becomes a 31-dimensional fixed-point vector:

```text
MarketPoint(asset, window) : Fin 31 → Q16_16
```

The object may be:

```text
equity
commodity
index
currency
supply-chain node
biological pipeline
food batch process
network protocol
```

The ontology label is metadata. It is not the primary metric.

---

## 3. Five behavioral blocks

The 31 coordinates are grouped as:

```text
0–5     Identity
6–12    Conservation
13–18   Transformation
19–24   Scaling
25–30   Dynamics
```

### 3.1 Identity

What is the object right now?

Candidate market features:

```text
regime label
liquidity state
volatility state
margin state
inventory state
balance-sheet stress state
```

### 3.2 Conservation

What is preserved or constrained?

Candidate market features:

```text
money flow persistence
volume persistence
supply/demand balance
inventory balance
capital constraint
working-capital pressure
throughput conservation
```

### 3.3 Transformation

How does input become output?

Candidate market features:

```text
lead-lag behavior
factor-to-return conversion
news-to-price conversion
input-cost to margin conversion
queue-to-revenue conversion
production throughput
```

### 3.4 Scaling

How does behavior change with size, time, or load?

Candidate market features:

```text
elasticity
capacity curve
margin scaling
volatility scaling
network effect strength
power-law behavior
```

### 3.5 Dynamics

How does it move?

Candidate market features:

```text
momentum
mean reversion
acceleration
drawdown behavior
shock response
regime transition probability
instability / turbulence
```

---

## 4. Prototype library v0.1

Each prototype is also a 31-dimensional fixed-point vector:

```text
PrototypePoint : Fin 31 → Q16_16
```

Initial prototypes:

```text
batch bottleneck
inventory glut
supply squeeze
demand shock
margin compression
capacity expansion
regulatory delay
quality failure
commodity pass-through
platform/network effect
```

A prototype is a behavioral shape, not a sector tag.

Example:

```text
batch bottleneck =
high conservation constraint
high transformation delay
high queue sensitivity
high scaling nonlinearity
medium/high dynamics instability
low ontology dependence
```

---

## 5. Distance

The primary comparison operator is weighted behavioral distance:

```text
d(M_a, Q) = Σ_i w_i · domainWeight(i) · |M_a[i] - Q[i]|
```

Where:

```text
M_a = market point for asset/object a
Q   = query prototype
w_i = coordinate weight
domainWeight(i) = block-level weight
```

Interpretation:

```text
low distance  = behavioral similarity
high distance = behavioral mismatch
```

This is the central inversion: the filter does not ask whether two things share a sector. It asks whether their behavioral vectors are close.

---

## 6. Binding

Binding measures persistence of the match across rolling windows.

For windows:

```text
older → previous → current
```

Define instability:

```text
I = |d_current - d_previous| + |d_previous - d_older|
```

Fixed-point binding proxy:

```text
B = 1 / (1 + I)
```

Interpretation:

```text
high binding = repeatable structure
low binding  = noisy coincidence
```

A one-window match is not trusted. A persistent match is more meaningful.

---

## 7. Turbulence

Turbulence is unresolved mismatch.

In v0.1:

```text
τ = distance instability + ontology mismatch penalty
```

Expanded later:

```text
τ =
  distance instability
+ ontology/behavior mismatch
+ geodesic error
+ regime curvature
+ adapter failure
```

Interpretation:

```text
low turbulence  = clean behavioral match
medium turbulence = interesting tension
high turbulence = unresolved or unstable equivalence
```

Important rule:

> Turbulence is not automatically noise. It may be where a new adapter wants to form.

---

## 8. Score

The conceptual score is:

```text
S(a,Q) = exp(-d(M_a,Q)/σ) · B(M_a)/(1 + τ(M_a,Q))
```

The hot-path Q16.16 version avoids exp/log:

```text
S_q16(a,Q) = B / (1 + d + τ)
```

Interpretation:

```text
higher score = closer, more stable, less turbulent match
```

The score is a filter/ranking signal only. It is not a buy/sell/hold signal.

---

## 9. Filter gate

A candidate passes only if all gates pass:

```text
distance   ≤ distanceMax
binding    ≥ bindingMin
turbulence ≤ turbulenceMax
```

The score alone is insufficient.

Recommended initial gate logic:

```text
PASS:
  low distance
  high binding
  low/medium turbulence

WATCH:
  low distance
  medium binding
  high turbulence

REJECT:
  high distance
  low binding
  high turbulence
```

---

## 10. Adapter explanation

The filter should explain matches through adapter paths.

Example:

```text
shipping containers
↔ capacity bottleneck + queue depth + delivery lag
↔ DNA sequencing
```

Or:

```text
grandmother’s cookies
↔ batch throughput + ingredient constraint + oven capacity + demand spike
↔ semiconductor fabs
```

The result should not merely say:

```text
A is similar to B
```

It should say:

```text
A is similar to B through adapter C
```

Output schema:

```text
source object
target prototype
adapter prototype
distance
binding
turbulence
claim state
explanation
```

---

## 11. Encoder responsibilities

The Lean module assumes the encoder has already converted raw data into Q16.16 coordinates.

The external encoder may use:

```text
returns
volume
volatility
spread/liquidity
drawdown
correlation to factors
news/event embeddings
fundamental ratios
inventory metrics
supply-chain metrics
lead-time data
commodity input prices
```

Encoder output:

```text
MarketPoint(asset, rolling_window)
```

The first implementation can be Python. The formal interface should remain Q16.16.

---

## 12. Evidence discipline

Every result receives a claim state:

```text
BEAUTIFUL_PROVISIONAL
CALIBRATED_ENGINEERING_DELTA
REVIEWED
```

### BEAUTIFUL_PROVISIONAL

Allowed when:

```text
shape match exists
no statistical validation yet
no Lean/evidence receipt
```

### CALIBRATED_ENGINEERING_DELTA

Allowed when:

```text
rolling backtest exists
baseline comparison exists
false-positive rate estimated
parameters and data provenance recorded
```

### REVIEWED

Allowed when:

```text
theorems/proofs or independent review exist
benchmark receipts exist
method survives adversarial tests
```

---

## 13. Minimal v0.1 build

### Step 1 — Encoder

Build:

```text
raw market window → Fin 31 → Q16_16
```

### Step 2 — Prototype library

Create ten manually seeded prototype vectors.

### Step 3 — Distance engine

Compute:

```text
d(M_a, Q)
```

### Step 4 — Binding engine

Compute:

```text
B = 1 / (1 + distance instability)
```

### Step 5 — Turbulence engine

Compute:

```text
τ = instability + mismatch penalty
```

### Step 6 — Filter result

Return:

```text
asset
window
matched prototype
distance
binding
turbulence
score
adapter explanation
claim state
```

---

## 14. Non-goals

This v0.1 does not:

```text
predict prices directly
make trading recommendations
claim causal certainty
replace econometric validation
use sector labels as truth
use Float in the formal hot path
```

---

## 15. Strongest formulation

The filter is not claiming:

> Everything is secretly the same.

It is claiming:

> Different objects can instantiate the same behavioral operator.

That is the rigorous version.

The purpose of the manifold is to find those operators before ordinary ontology notices them.

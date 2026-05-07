# Adaptive Material Math Application Map

Status: candidate integration map

Purpose: identify where the locally adaptive flip-tile / fractal-hair /
MXene-scroll concept can pay rent elsewhere in the Research Stack math.

## Core Transfer

The shared primitive is:

```text
2D controllable surface
  -> local tension / strain / charge imbalance
  -> curl, flip, extend, branch, or lock
  -> 1D path, contact, channel, or route
```

That maps directly onto several existing stack surfaces:

```text
surface state -> local transition -> routed path -> receipt
```

The concept should be treated as a finite local state machine first, not as
unbounded morphing material.

## Best Application Targets

| Target | Existing surface | How the material concept applies | First test |
|---|---|---|---|
| DynamicCanal | `Semantics.DynamicCanal` | A canal section is like a scrollable sheet: pressure/stress/mismatch decides whether a lane stays flat, narrows, curls into a throat, or ruptures. | Add `curlBias = stress * mismatch / capacity` as a candidate canal classifier. |
| COUCH | `CouchFilterNormalization`, `COUCH_EQUATION.md` | Near-critical flip tiles are physical COUCH oscillators: coupling, damping, hysteresis, and boundary avoidance decide whether a patch changes shape. | Treat `CriticalMargin` as a COUCH hysteresis gate and sweep it against `F_COUCH`. |
| Charged-Mass Braid Sieve | `charged_mass_braid_sieve.md`, braid shifters | Fractal hairs and scrolls are path-sensitive: repeated contact/rotation separates stable grip from scar, residue, or discharge. | Model hair engagement as `M(t+1) = M(t) + contact_gain - release_risk`. |
| Waveprobe | `waveprobe_qubo_spec.tex`, `Semantics.Waveprobe` | A flip-tile field is a local selection kernel: choose the tile/hair state with highest overlap to terrain/contact history. | Add contact-state QUBO features: adhesion, release, heat, fatigue, contamination. |
| Soliton / void chasing | Soliton docs, `SolitonTensor`, `SolitonLighthouse` | A deformation wave through tiles is a soliton-like front; it chases low-risk contact basins and avoids scars. | Track tile-state fronts as discrete waves over a patch lattice. |
| Morphic DSP | `MORPHIC_DSP_CONCEPT.md` | Flip-tile material is the physical analogue of virtual morphic DSP: fixed cells, changing local mode, receipt-gated collapse. | Reuse `BoundaryState`: independent, merged, split, fluid for tile patches. |
| PIST / N-Shell | `PIST`, `GENSIS`, shifter scripts | Hair branch depth and tile orientation can be encoded as shell coordinates with mass-preserving local moves. | Encode `{tile, hair_depth, orientation}` as a PIST coordinate packet. |
| Hutter / compression | Hutter and manifold compression scripts | Scroll/hair states are adaptive dictionaries for physical/contact patterns: reuse successful morphology memes as compressed route priors. | Compare repeated terrain/contact traces with and without morphology-meme reuse. |
| Cotranslational folding | `CodonPeptideConsistency.lean`, `codon_rl_v2_summary.md` | "Structure through time before geometry" mirrors tile/hair extension: local sequence of flips matters before final shape. | Treat tile updates as exposure windows `W_t`, not a static final geometry. |
| Neural type eigenvector coverage | `NEURAL_TYPE_EIGENVECTOR_COVERAGE.md` | Biological morphology features can rank which hair/tile patterns are plausible and efficient. | Add gecko/cilia/setae/skin texture features as external coverage nodes. |
| Recursive branch cuts | `recursive_branch_cut_self_similarity.md` | Scroll formation is a finite, materials-grounded branch cut: flat sheet crosses a curvature threshold and commits to a new topology. | Use scroll onset as a concrete branch-cut analogy with no cosmology claim. |
| Structural eFuse / SDR void hash | Semi-jack, patent/CAD, verification docs | SLS tubules, magnetic labyrinths, doped matrices, and piezo/ME capsules turn structural state into measurable RF/flux/electrical receipts. | Classify healthy vs failed tubule states using `VoidHash`, `flux_delta`, and `PercolationMargin`. |

## Specific Equations To Try

### 1. Scroll Bias For DynamicCanal

```text
ScrollBias(section) =
  stress
  * mismatch
  * pressure
  / (1 + capacity + heat)
```

Interpretation:

| Regime | Meaning |
|---|---|
| low bias | flat transport; keep lane/canal unchanged. |
| medium bias | local curl; narrow into directed route. |
| high bias | throat candidate; use receipt gate. |
| extreme bias | rupture/quarantine. |

### 2. Hair Contact Mass For Braid Sieve

```text
ContactMass(t+1) =
  ContactMass(t)
  + adhesion_gain
  + microhook_gain
  - release_risk
  - fouling_risk
  - damage_risk
```

Promotion:

```text
promote_contact iff
  ContactMass >= contact_floor
  and release_risk <= release_ceiling
  and heat <= heat_ceiling
```

### 3. Tile-State QUBO For Waveprobe

```text
Q_ij =
  terrain_match_i * terrain_match_j
  + release_compat_i_j
  - heat_conflict_i_j
  - fatigue_conflict_i_j
```

The selected state maximizes:

```text
x^T Q x
```

subject to:

```text
detachability_ok
heat_ok
critical_margin_ok
```

### 4. COUCH Critical Margin

```text
PatchPressure =
  F_COUCH
  + U_rot
  + ContactAuthority
  - CriticalMarginPenalty
  - DamageRisk
```

Interpretation:

| Output | Action |
|---|---|
| local | use current tile/hair meme. |
| atlas | search morphology atlas. |
| reject | hold/scar/quarantine. |

### 5. Cotranslational Tile Windows

```text
SkinState_t = update(SkinState_{t-1}, TileWindow_t)
```

Where:

```text
TileWindow_t = (tile_{t-k}, ..., tile_t)
```

This mirrors the codon result:

```text
local updates influence structure through time before final geometry
```

## What To Avoid

Do not claim:

- graphene or MXene scrolls are already proven robot skin components
- nanoscale effects carry the main load
- the material changes shape for free
- a gecko anchor solves all surfaces
- a scroll analogy proves N-space equations

Allowed claim:

```text
layered microstructured surfaces provide a grounded model for local
state transitions, contact multiplication, and 2D-to-1D routing under strain
```

## Immediate Next Artifact

The cleanest next implementation is a small JSONL schema:

```json
{"kind":"tile_state","id":"tile:0:0","phase":"near_critical","hair_depth":2,"orientation":3}
{"kind":"contact_event","tile":"tile:0:0","terrain":"rough","adhesion":0.61,"release_risk":0.12,"heat":0.04}
{"kind":"transition","src":"tile:0:0:flat","dst":"tile:0:0:hair_extend","receipt":"sensor-window-hash"}
```

Then run:

1. COUCH pressure scoring over tile states.
2. Waveprobe/QUBO selection over candidate contact memes.
3. FAMM scar storage for failed release, fouling, or heat events.

## Recovered Session Material Addendum

See `RecoveredSessionMaterialConcepts.md` for the recovered material cluster
from the local chat transcript: MXene nanoscrolls, charge-flow shaping,
resonant SLS tubules, conductive valence matrices, magnetic labyrinths,
magnetoelectric laminate capsules, piezo alerts, ferrite/carbon SLS doping, and
SDR resonant void readout.

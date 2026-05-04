# Burgers Harmonic Peeling — Witness Grammar Verification

**Commit title:** `docs: add witness grammar verification from Burgers harmonic peeling`

**One-line law:**
> FNWH decompiles fields into witness grammars; Burgers non-linearity traps the expansion; BEC collapse regularizes the singularity; crystallization bounds the field; phonon draining clears the residual; Brillouin zones forbid the chaos.

## 1. Burgers Toy → WitnessGrammar Mapping

```
S(x) = sin(x) + 0.3 sin(2x) + 0.1 sin(3x)
```

| Role      | ν   | a     | Lean Mapping                         |
|-----------|-----|-------|--------------------------------------|
| Carrier   | 1.0 | 1.0   | `WitnessRole.carrier`  → BHOCS      |
| Texture 1 | 2.0 | 0.3   | `WitnessRole.texture`  → FAMM       |
| Texture 2 | 3.0 | 0.1   | `WitnessRole.texture`  → FAMM       |

Implemented in `WitnessGrammar.capacityConstrainedBatchTransformer`.

## 2. Key Mathematical Results

| Result | Equation | Role in Stack |
|--------|----------|---------------|
| Viscosity stiffening | `ν_eff = ν_0 (1 + Ω)` | Trapping mechanism |
| Quantum pressure | `Q_eff = (1 + κ Ω) Q` | Singularity regularization |
| Stiffening factor | `κ = 0.3547` (35.47%) | Global bound safety margin |
| Solidification | `E_eff = E_0 (1 + κ Ω)` | Phase transition to crystal |
| Phonon drain | `Γ_drain ∝ Ω²` | Residual energy dissipation |
| Brillouin bound | `\|∇u\| ≤ ℏ k_max / m` | Gradient ceiling |
| Dispersion | `ω(k) = c_s k √(1 + κ Ω(k))` | Band gap / noise forbidden |

## 3. Module Connections

- `WitnessGrammar.lean` — stores ν/a/φ/role decomposition
- `CoulombComplexity.lean` — polarity from amplitude sign (carrier +, texture −)
- `SigmaGate` — confidence scoring on grammar match quality
- `BHOCS` — commits carrier-witness nodes
- `FAMM` — drains texture-witness stress energy

## 4. What Remains Theoretical

- Full BEC/GPE collapse proof (requires `ℏ` and `m` in simulation units)
- Brillouin zone enforcement as explicit lattice constraint
- Phonon drain as time-step dissipative term in NBody state update
- Young's modulus tensor from stiffening in 3D manifold coordinates

Source research log: `/home/allaun/Downloads/mathholes.md`

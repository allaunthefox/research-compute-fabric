# Witness Grammar Specification

## One-Line Law

> FNWH decompiles fields into witness grammars; Equation Sniffers compare those grammars; the market filter searches for shared behavioral operators, not shared nouns.

## What is a Witness Grammar?

A **Witness Grammar** is the finite symbolic source code recovered from a field.
It stores the active witnesses, their amplitudes / frequencies / phases, their routing roles, and a residual receipt.

From the Burgers/FNWH visual verification:

```
S(x) = sin(x) + 0.3 sin(2x) + 0.1 sin(3x)
```

yields the finite witness grammar:

| Role      | ν (frequency) | a (amplitude) | phase |
|-----------|---------------|---------------|-------|
| Carrier   | 1.0           | 1.0           | 0     |
| Texture 1 | 2.0           | 0.3           | 0     |
| Texture 2 | 3.0           | 0.1           | 0     |

## Pipeline

```
Raw field
  → FNWH peeling
  → WitnessGrammar
  → EquationSniffer
  → route suggestion
  → MassNumberField
  → BHOCS / FAMM
```

Equation Sniffers do not inspect raw data directly; they **sniff witness grammars**.

## Equation Sniffer Input (YAML prototype)

```yaml
EquationSnifferInput:
  grammar:
    - role: Carrier
      v: 1.0
      a: 1.0
    - role: Texture
      v: 2.0
      a: 0.3
    - role: Texture
      v: 3.0
      a: 0.1
  residual:
    energy: 0
    status: CLOSED
```

## Market-Data Bridge

The market version applies the same pipeline to ontologically unrelated systems:

```
price / volume / news / fundamental stream
  → rolling signal field
  → witness grammar
  → behavioral operator class
  → filter score
```

### Asset field example

```
S_a(t) = return carrier + volatility texture + liquidity basin + residual stress
```

Witness grammar:

| Component | Role               |
|-----------|--------------------|
| Carrier   | market regime      |
| Texture   | volatility shock   |
| Basin     | macro drift        |
| Residual  | unexplained risk   |

## Market Filter Prototype

**Behavioral class:** `capacity_constrained_batch_transformer`

This class unifies:

- shipping containers
- DNA sequencing
- grandmother's cookies
- semiconductor fabs
- clinical labs
- warehouses
- bakeries
- ports

**First test:** Can the manifold cluster ontologically unrelated things by shared operational dynamics?

**Filter score:**

```
S(a, Q) = exp(-d(M_a, Q) / σ) · B(M_a) / (1 + τ(M_a, Q))
```

Where:

| Symbol | Meaning                     |
|--------|----------------------------|
| M_a    | witness / manifold point for asset a |
| Q      | query prototype (behavioral class)   |
| d      | behavioral distance         |
| B      | binding / pattern stability |
| τ      | turbulence / unresolved mismatch     |
| σ      | distance temperature        |

High score = asset behaves like the query pattern.  
Low score = asset does not match or is too turbulent.

## Commit Note

This spec documents the verified Burgers-harmonic peeling transition from visual proof to executable primitive. The next step is real-data validation, not more theory.

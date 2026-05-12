# Underverse Zero Layer

Status: `ADMIT_EXPLICIT_ACCOUNTING_LAYER`

Claim boundary: this document makes the neutral closure layer explicit. It does
not claim a physical mirror universe, anti-baryonic observation, negative mass,
genus-3 theorem, cosmology fit, compression gain, or hardware readiness.

## Definition

The zero layer is the neutral accounting boundary between observable accounting
and Underverse/complement accounting.

```text
O_visible = measured or promoted visible-side ledger
U_under   = hidden, failed, inverse, complement, or residual ledger
U_sink    = typed sink, loss, annihilation, or sidecar ledger

U0 closes iff O_visible + U_under + U_sink = 0
```

The point is to stop the model from silently assuming balance. If the terms do
not recompute to zero, the zero-layer claim fails and the residual must be
routed to a typed Underverse lane.

## Genus-3 Zero-Charge Assumption

The model may choose a genus-3 chart, but zero charge is not implied by the
chart. It must be declared and receipted:

```text
chart = genus3
genus = 3
net_charge = 0
replay_receipt_present = true
```

The Lean fixture encodes this as:

```text
observableCharge + underverseCharge + sinkCharge = 0
```

and admits the genus-3 event only when replay evidence is present.

## Lanes

| Lane | Terminal | Use |
|---|---|---|
| `U0_CLOSURE` | `ADMIT_U0_CLOSURE` | Observable, Underverse, and sink terms replay to exact neutral closure. |
| `U0_HOLD_MISSING_RECEIPT` | `HOLD_U0_REPLAY` | Terms appear balanced, but replay evidence is missing. |
| `U0_REJECT_NONZERO_CHARGE` | `REJECT_U0_NONZERO` | Claimed zero event recomputes to nonzero charge. |
| `U0_GENUS3_ZERO_CHARGE` | `ADMIT_GENUS3_ZERO_CHARGE` | Genus-3 chart declares and receipts zero net charge explicitly. |

## Lean Surface

```text
0-Core-Formalism/lean/Semantics/Semantics/Core/UnderverseZeroLayer.lean
```

The minimal fixtures are:

```text
genus3BalancedFixture     -> ADMIT genus-3 zero-charge event
missingReplayFixture      -> HOLD because replay receipt is missing
nonzeroChargeFixture      -> REJECT because net charge is nonzero
```

## Non-Claims

- `U0` is not a hidden physical layer.
- `U0` is not a free variable for unexplained effects.
- `U0` does not prove genus-3 topology.
- `U0` does not prove a mirror universe.
- `U0` does not prove anti-baryonic matter.
- `U0` does not promote cosmology, compression, or hardware claims.

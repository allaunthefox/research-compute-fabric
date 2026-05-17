# Anti-Baryonic Underverse Categories

Status: `HOLD_ACCOUNTING_CATEGORIES`

Claim boundary: these categories add typed Underverse accounting lanes for
anti-baryonic complements and candidate residues. They do not claim observed
anti-baryonic matter, negative mass, mirror matter, baryogenesis closure, dark
matter identity, or a cosmology fit.

## Why Add Them

The CPT mirror prior introduced a useful separation:

```text
U_total = U_visible + U_mirror
```

That makes anti-baryonic bookkeeping worth separating from generic mirror-world
or hidden-sector language. Anti-baryonic matter has specific sign/accounting
questions: baryon-number sign, charge conjugation, annihilation/loss channels,
and visible-side imbalance.

## Categories

| Variant | Terminal | Use |
|---|---|---|
| `U_ANTI_BARYONIC_COMPLEMENT` | `HOLD_ANTI_BARYONIC_ACCOUNTING` | A hidden or complement ledger lane is needed to represent charge/baryon-number-reversed accounting. |
| `U_ANTI_BARYONIC_CANDIDATE` | `HOLD_ANTI_BARYONIC_OBSERVATION` | A local observation or model residue looks compatible with an anti-baryonic term, but has not passed source, uncertainty, background, and replay checks. |
| `U_ANTI_BARYONIC_SINK` | `HOLD_ANTI_BARYONIC_SINK` | A visible baryonic imbalance requires an explicit sink, annihilation/loss channel, or complement function before interpretation. |

## Accounting Kernel

```text
B_visible = baryonic visible-side accounting term
B_anti    = anti-baryonic complement or candidate term
B_sink    = typed loss / annihilation / complement sink

B_total = B_visible + B_anti + B_sink
```

The useful gate is not whether `B_anti` is present as a story. The useful gate
is whether it is typed, capacity-bounded, source-backed, and replayable.

## Promotion Requirements

An anti-baryonic lane may only promote out of HOLD when all of these exist:

```text
source identity
observer frame
baryon-number sign convention
charge/conjugation convention
annihilation or loss policy
capacity bound
background/null model
receipt hash
replay path
```

## Explicit Non-Claims

- Anti-baryonic matter has not been observed by this repo.
- The lane is not negative mass.
- The lane does not prove a mirror universe.
- The lane does not close baryogenesis.
- The lane does not identify dark matter or dark energy.
- The lane does not promote any Research Stack cosmology model.

## Integration

These categories extend:

```text
shared-data/data/underverse_variant_accounting/underverse_variant_accounting.md
6-Documentation/tiddlywiki-local/wiki/tiddlers/Underverse Variant Accounting.tid
```

They are intentionally additive. The generated Underverse registry root is not
rewritten by hand; registry regeneration needs to recompute the root and receipt.

# Autonomous Speedrun Harness Gate

## Purpose

Integrate the Prime Intellect `auto-nanoGPT` lesson into the FAMM stack as an autonomous research harness.

This gate models a long-running research loop as a receipt-bearing search machine:

```text
AGENTS.md / rules
→ goal.md / target invariant
→ plan.md / mutable frontier
→ THREAD.md / durable mission memory
→ variant logs / delta stream
→ run logs / experiment receipts
→ pruning rounds / Warden cleanup
→ source refresh / drift gate
→ statistical receipt
```

## Source boundary

The Prime Intellect run is an external reference pattern, not a dependency. The article describes agents iterating on the nanoGPT speedrun optimizer track, using a markdown harness with durable working memory and run logs. It also documents failure modes: local-loop grinding, insufficient upstream refresh, premature stopping, and weak novelty without external/public-record scaffolding.

This gate imports the **harness architecture**, not any benchmark-specific optimizer claim.

## Core stack

```text
Builder-Judge-Warden
→ Autonomous Speedrun Harness
→ Experiment Delta-DAG
→ FAMM Scar Ledger
→ Source Refresh Warden
→ Statistical Receipt
```

## FAMM object

```math
\mathfrak C_{\mathrm{AutoHarness}}
=
A_{16}(u_{\mathrm{run}})
\otimes
[
\Sigma_{\mathrm{goal}}
+
\Sigma_{\mathrm{plan}}
+
\Sigma_{\mathrm{thread}}
+
\Sigma_{\mathrm{variant}}
+
\Sigma_{\mathrm{run}}
+
\Sigma_{\mathrm{source}}
+
\Sigma_{\mathrm{scar}}
+
\Sigma_{\mathrm{stats}}
+
\Sigma_{\mathrm{receipt}}
]
```

## 16D autonomous harness state

```math
X_{\mathrm{harness}}
=
[
\nu,
g,
p,
t,
v,
r,
s,
\mu,
z,
\Delta,
\Omega,
R,
I,
C,
\rho,
\pi
]
```

| Axis | Meaning |
|---:|---|
| 0 | NUVMAP run/frontier address |
| 1 | goal / target invariant |
| 2 | plan/frontier state |
| 3 | durable thread memory |
| 4 | variant / hypothesis stack |
| 5 | run-result metric |
| 6 | source-refresh freshness |
| 7 | semantic mass / promise pressure |
| 8 | recurrence / local-loop detector |
| 9 | delta-memory / experiment lineage |
| 10 | FAMM scar pressure |
| 11 | residual / validation gap |
| 12 | invariant / benchmark-rule overlap |
| 13 | route cost / compute cost |
| 14 | receipt strength / statistical validity |
| 15 | projection / report gauge |

## Builder-Judge-Warden mapping

| Role | Harness behavior |
|---|---|
| Builder | proposes optimizer, schedule, initialization, or search-policy mutation |
| Judge | checks benchmark rules, target metric, seeds/statistical noise floor, and reproducibility |
| Warden | blocks stale loops, rule violations, overfit/seed hacking, premature pruning, stale upstream source, and unsupported novelty claims |

## Experiment delta edge

```math
\nu_t
\xrightarrow{\Delta e_t}
\nu_{t+1}
```

```text
Δe_t = {
  idea_hash,
  patch_hash,
  config_hash,
  run_id,
  seed_set,
  metric_delta,
  compute_cost,
  receipt_hash
}
```

## Source Refresh Warden Gate

Long autonomous runs must periodically refresh source-of-truth state:

```text
upstream PRs
leaderboard / records
paper notes
previous best local stack
external benchmark rule changes
```

If source freshness exceeds a threshold:

```math
S_{\mathrm{stale}}>\Theta_{\mathrm{source}}
\Rightarrow
\mathrm{WARDEN\_BLOCK}
```

## Coarsening failed ideas

```text
failed idea
→ residual measured
→ scar written
→ local basin coarsened
→ future fine search downweighted
→ reopened only if new evidence/source refresh changes the boundary
```

## Statistical receipt

A run is not promoted by a single attractive metric. It must carry a statistical receipt:

```text
multi-seed result
noise-floor margin
rule compliance
reproducibility status
run-log hash
patch/config hash
```

## Stack placement

```text
MARKOVJUNIOR_16D_PIST_REWRITE_SHIM
→ AUTO_NANOGPT_AUTONOMOUS_RESEARCH_HARNESS_GATE
→ BJW_GEODESIC_CLEANUP
→ NUVMAP_DELTA_DAG
→ FAMM_SCAR_LEDGER
→ SOURCE_REFRESH_WARDEN_GATE
→ STATISTICAL_RECEIPT
```

## No-drift boundary

This gate does not claim autonomous agents can discover truth alone. It models the surrounding harness needed for useful autonomous search: durable memory, receipts, source refresh, pruning, coarsening, and statistical validation.

## Project sentence

The Autonomous Speedrun Harness Gate turns long-running agent research into a FAMM-compatible search machine: Builder proposes mutations, Judge validates statistical receipts, Warden blocks stale or invalid loops, failed ideas become coarsened scar basins, and every experiment becomes a Delta-DAG edge with replayable provenance.

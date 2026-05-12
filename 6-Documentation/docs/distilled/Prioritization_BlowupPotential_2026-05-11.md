# Prioritization — Given Blowup Potential from Minimal Tests

**Date:** 2026-05-11
**Query:** What to prioritize given detector fires correctly on primes with zero calibration
**Source:** deepseek-v4-pro:cloud

---

## Recommended 8-Week Sequence

| Week | Action |
|------|--------|
| 1–2 | Mathematical blowup characterization: systematic test suite, map firing boundaries, confirm K/σ_c/D_c invariance |
| 2–3 | Crypto shortcut: one on-chain market (ETH/USDC Uniswap or Aave), compare firing to known stress events |
| 3–4 | Internal tech report: write up results, check if any parameter tuning needed |
| 4–6 | Starling murmuration deep dive: Cavagna 3D trajectory data, validate against predator attacks/roosting |
| 6–8 | Draft preprint: math + crypto + starling → arXiv |
| 8+ | Historical prose pipeline: subsistence observer records, expand to cattle/fish/rat datasets |

---

## Priority 1: Mathematical Characterization First (days, not weeks)

**The prime gap result is the most leveraged finding.** It fired with zero calibration on a domain the detector was never designed for. Before applying to biology or finance, characterize what CLASS of sequences the detector fires on.

Test suite to run:
- Random uniform → should be silent
- Random walk / Brownian noise → high σ_q, no collapse
- Periodic (sine, constant gap) → silent or low firing
- Chaotic (logistic map, Lorenz discretized) → intermediate
- Fibonacci mod n, digits of π, Copeland-Erdős, Thue-Morse
- Twin prime gaps only, prime gaps by range
- Primes in arithmetic progressions

**Why first:** Gives a falsification boundary. Know exactly what the detector CAN and CANNOT see before touching noisier domains. Prevents overinterpretation. Takes days, not months.

---

## Priority 2: Crypto Fast Track (parallel with math characterization)

**Fastest feedback loop.** Blockchain data is live, machine-readable, constraint math is explicit.

- Pick one pool: ETH/USDC Uniswap v3 or Aave lending
- Extract: tick liquidity, liquidation events, funding rates, trade sizes
- Set τ = block time or event time
- Find firing clusters → compare against known crashes, squeezes, governance attacks

**Not the final validation — use as stress test.** If fires on manipulated adversarial data at meaningful points, robustness confirmed. If fails, learn limitations early.

---

## Priority 3: Depth vs Breadth Resolution

Breadth first across math + crypto is SAFE because you're actively testing invariance. The math characterization will reveal whether K, σ_c, D_c need substrate-specific tuning before you touch biology.

After math + crypto: go deep on **starling murmurations (Cavagna data)** because:
- Already numerical (3D trajectories) — no extraction pipeline
- Known critical phenomenon with studied order-disorder transition
- Can directly compare to predator attack / roosting timestamps
- Cleaner than historical prose anecdotes

---

## Priority 4: Historical Prose Pipeline (weeks 8+)

Build AFTER math + crypto results are in hand. You'll know exactly what features to extract and how to discretize them. Don't build the pipeline for a signal you don't yet fully trust.

Schema when built:
```
{ timestamp: uint32, activity: enum{grazing,resting,milling,agitated,fleeing}, cohesion: enum{scattered,loose,tight} }
```

---

## Publication Sequencing

| Stage | Timing | Content |
|---|---|---|
| Internal tech report | Now | Prime gap result + math blowup plan. Establishes priority. |
| Preprint (arXiv) | Weeks 6-8 | Math characterization + crypto case + starling. Stakes claim, invites feedback. |
| Full paper | Months 3-4 | All three domains. Three-domain package (math, adversarial human, biological) is hard to dismiss. |

**Do not publish prematurely.** The cross-domain substrate-invariance claim is bold. It needs math + one adversarial system + one clean biological system minimum before submission to high-impact venue.

---

## Key Insight from DeepSeek

> "The prime gap test is your canary in the coal mine — it's telling you this is bigger than you thought. Characterize that first, then let the applications flow from a position of mathematical certainty."

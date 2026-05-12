# Blockchain as Hardcoded Human Math — Vortex Signal Architecture

**Date:** 2026-05-11
**Query:** On-chain data sources for HCMMR vortex detection; composite eigenmass pipeline
**Source:** deepseek-v4-pro:cloud

---

## Core Insight

On-chain primitives are not just data — they are the literal encoding of adversarial intent.
Every AMM curve, liquidation threshold, and funding rate formula is a commitment to a specific
gain-seeking behavior, executed deterministically. This makes them ideal for the HCMMR vortex
detector, which thrives on explicit, mathematically crisp boundaries.

---

## 1. AMM Invariant Curves as Eigenmass Surfaces

**Concentrated liquidity (Uniswap v3) is a piecewise hyperbola with tick boundaries.**

Each tick `i` → price `p_i = 1.0001^i`. Liquidity `L` active only when `P ∈ [p_i, p_{i+1})`.
Marginal depth (eigenmass) is stepwise, not smooth.

```
M_AMM(P) = Σ_{ticks i active at P} L_i * w(P, p_i, p_{i+1})
```

**Each tick range is a distinct HCMMR depth level:**
- Each tick has its own `σ_q` (computed from historical vol within that tick range)
- Tick crossings are braid generators: upward crossing = `σ_i`, downward = `σ_i⁻¹`
- High crossing-frequency tick ranges → high `σ_q` → complex braid word → vortex signal

**Q16_16 implementation:**
- Fixed-point array of tick liquidity indexed by tick index
- Update active tick set on each new block
- Record tick-crossing events as braid generators incrementally

---

## 2. Liquidation Cascades as Programmed Vortexes

For each open position `j`: health factor `H_j = (collateral_j × price_collateral × LT_j) / debt_j`
Liquidatable when `H_j < 1`.

**Eigenmass distribution `ρ(H, P)`:**
- For each position: compute liquidation price `P_liq = debt_j / (collateral_j × LT_j)`
- Eigenmass at `P` = total collateral of positions with `P_liq ≈ P`
- The distribution is the density of that mass

**Vortex precursor signals:**
- Heavy-tailed `ρ` near `H=1` → cascade imminent
- `σ_q` of mass-weighted mean H collapses as positions cluster near H=1
- Braid word = sequence of liquidations as price drops through each `P_liq` in order
  → braid becomes highly tangled (many crossings, short price interval) just before cascade

**Concrete pipeline:**
- Ingest all open positions from Aave/Compound (subgraph or events)
- Build histogram `M(P)` = sum of collateral with `P_liq ∈ [P, P+ΔP]`
- Track `⟨H⟩` and its variance; sharp variance drop + `M(P)` spike = vortex precursor
- Braid trigger: non-trivial crossing number when sequencing through `P_liq` levels

---

## 3. MEV Mempool as a Braid

Mempool transactions = strands. Reorderings = crossings in `B_n`.

- Sandwich attack = braid word `σ_i σ_{i+1} σ_i⁻¹`
- Eigenmass = total MEV value extractable
- Braid word complexity (crossing number, topological entropy) = MEV opportunity size

**Vortex signal `(P, T, C)` adapted for MEV:**
- `P` = price level of most contested pool
- `T` = braid crossing count per second
- `C` = eigenmass (MEV profit) concentration in single dominant opportunity

**Implementation:**
- Stream mempool via `txpool` RPC
- Insert each tx into braid word by current ordering (gas price, nonce)
- Sliding window of last N txns, compute crossing number as inversion count
- Q16_16 for value calculations

---

## 4. Funding Rates as Eigenmass Damping

Funding rate `F = clamp( (mark - index) / index / period, -cap, cap )`
Acts as mean-reversion force on the eigenmass:

```
dM±/dt = ... - λ × F × M±
```

**Integration:**
- F > 0 (perps above spot): dampens `M+`, amplifies `M-`
- Vortex forms when F is pinned at cap for extended period → large imbalance → violent unwind
- `σ_q` of funding rate time series collapses before vortex (rate oscillates with decreasing amplitude)
- Funding rate sign changes = braid crossings; rapid series of flips = high crossing braid word

**Q16_16 integration:**
- Poll funding rates every minute from exchange APIs
- `M_damped = M_raw × (1 - κ × |F|)` with tuned `κ`
- Feed `M_damped` into composite eigenmass surface

---

## 5. Minimum Viable Cross-Domain Signal Pipeline

**Composite eigenmass:**
```
M_total(P) = α₁ × M_CEX(P) + α₂ × M_AMM(P) + α₃ × M_liq(P) + α₄ × M_MEV(P)
```

Weights `α_i` dynamically adjusted by `D_q` of each source's recent activity
(higher `D_q` → richer microstructure → more weight).

**Directional split:**
- CEX: bids → M+, asks → M-
- AMM: symmetric; bias from cumulative swap direction in last N blocks
- Liquidations: always M- (sell-side pressure)
- MEV: directionally assigned by arbitrage direction

**Funding damping:**
```
M±_damped = M± × D(t),  D(t) = 1 - κ × |F|
```

**Data ingestion:**
1. CEX order books (Binance/Kraken/Bybit) at 100ms → `M_CEX(P)`
2. Uniswap v3 events (Swap/Mint/Burn) → tick liquidity map → `M_AMM(P)`
3. Aave/Compound events (Deposit/Borrow/Repay/Liquidate) → `M_liq(P)`
4. txpool mempool → braid crossing count `B(t)` + MEV value → `M_MEV(P)`
5. Perp funding rates → damping `D(t)`

**Vortex detection (triple condition):**
1. Braid crossing count exceeds threshold (from price-level crossings of `M_total`)
2. `σ_q` of composite eigenmass collapses below critical value (RGFlow on M_total time series)
3. Fractal dimension `D_q` of `M_total(P)` drops sharply (multi-fractal → near 1 = intent concentrating)

**Implementation spec:**
- Single event loop: WebSocket (CEX) + Ethereum JSON-RPC subscriptions (blocks, mempool) + periodic REST (funding, lending)
- All state in Q16_16 fixed-point arrays (price grid at 0.01% resolution, tick AMM state, liq histogram)
- Braid tracker: circular buffer of last 256 price-level crossings, reduced braid word computed on each update
- RGFlow: `σ_q` and `μ_q` on composite eigenmass time series per price level, sliding window of 1024 samples
- Alert when triple condition met → emit `(P, T, C)` via ZeroMQ socket

---

## Key Mapping Summary

| On-chain primitive | HCMMR object | Signal mechanism |
|---|---|---|
| Uniswap v3 tick boundary | Depth-activation threshold | Tick crossing = braid generator |
| Liquidation health factor | Eigenmass `ρ(H, P)` | H→1 variance collapse = vortex precursor |
| MEV sandwich in mempool | Braid word `σ_i σ_{i+1} σ_i⁻¹` | Crossing count spike = MEV opportunity |
| Funding rate formula | Eigenmass damping `λF` | Rate at cap + oscillation collapse = unwind |
| CEX order book depth | `M_CEX(P)` surface | Liquidity wall erosion = D_q transition |

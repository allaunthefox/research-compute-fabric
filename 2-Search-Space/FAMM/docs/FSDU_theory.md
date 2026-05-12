# FAMM Scar Differential Update (FSDU)

> **Source:** ChatGPT session `6a000496-f338-83ea-80f5-353913c68a50`
> **Date:** 2026-05-09
> **Status:** Lean build surface active — theorem layer checks, Q16 proof debt HOLD
> **Build receipt:** `shared-data/data/stack_solidification/fsdu_q16_build_receipt_2026-05-10.json`

---

## 1  Premise

Classical pathfinding algorithms are not separate solvers. They are
**projections of a single reconfigurable traversal manifold**. The first
expanded Lean surface tracks the nine core modes named in the current fixture:

```text
A*
Dijkstra
Greedy Best-First
BFS
DFS
Bidirectional BFS
Weighted A*
Recursive Backtrack
Wall Follower
```

The broader theory treats additional search methods as optional projection
families that can be admitted later when they have a receipt, a failure mode,
and a role in the ahead/behind scar update.

Every solve leaves a *scar* — residual geometry that rewrites the graph
metric at every scale, making the full object fractal.

---

## 2  Core Object

The state manifold at time $t$:

$$
\mathcal{S}_t = (G,\; w_t,\; h_t,\; \rho_t,\; \tau_t,\; R_t)
$$

| Symbol    | Meaning                                      |
|-----------|----------------------------------------------|
| $G$       | graph / maze topology                        |
| $w_t$     | current edge cost field                      |
| $h_t$     | heuristic potential field                    |
| $\rho_t$  | visitation / density / pressure field        |
| $\tau_t$  | traversal memory / braid trace               |
| $R_t$     | residual error from prior solves             |

Each algorithm is a **mode** over the same priority field:

$$
Q_m(v) =
\begin{cases}
\text{depth}(v)         & \text{BFS}     \\
-\text{depth}(v)        & \text{DFS}     \\
g(v)                    & \text{Dijkstra}\\
g(v)+h(v)               & \text{A}^*     \\
h(v)                    & \text{Greedy Best-First}\\
g(v)+\omega h(v)        & \text{Weighted A}^*\\
\min(d_f(v),d_b(v))     & \text{Bidirectional BFS}\\
\text{stack\_depth}(v) + \beta\,\text{backtrack}(v)
                         & \text{Recursive Backtrack}\\
\text{wall\_contact}(v)+\kappa\,\text{turn}(v)
                         & \text{Wall Follower}
\end{cases}
$$

The merged solver is a weighted field:

$$
Q(v) =
\alpha_B\, Q_{BFS}(v)
+ \alpha_D\, Q_{DFS}(v)
+ \alpha_J\, Q_{Dijkstra}(v)
+ \alpha_A\, Q_{A^*}(v)
+ \alpha_G\, Q_{Greedy}(v)
+ \alpha_{BB}\, Q_{BidirectionalBFS}(v)
+ \alpha_{WA}\, Q_{WeightedA^*}(v)
+ \alpha_{RB}\, Q_{RecursiveBacktrack}(v)
+ \alpha_{WF}\, Q_{WallFollower}(v)
+ \lambda\, R_t(v)
$$

## 2.1  Solver Mode Atlas

The phrase "all possible options" is treated as an extensible atlas. The Lean
core should stay finite; the atlas can keep adding modes as candidate
chiralities.

### Core fixture modes

| Mode | Geometry | Best use | Scar risk |
|---|---|---|---|
| `A*` | cost plus goal curvature | admissible route when heuristic is trustworthy | stale heuristic scars |
| `Dijkstra` | isotropic cost-pressure relaxation | stable weighted graph with no strong heuristic | expensive wave scars |
| `Greedy Best-First` | pure attractor collapse | fast scout toward visible goal | false attractor scars |
| `BFS` | uniform expanding wavefront | unweighted reachability / shortest edge count | frontier blow-up |
| `DFS` | tunneling strand | narrow passage discovery | deep dead-end scars |
| `Bidirectional BFS` | two-front closure | known start and goal in unweighted graph | midpoint mismatch scars |
| `Weighted A*` | inflated goal curvature | speed-biased near-admissible route | suboptimality debt |
| `Recursive Backtrack` | constructive DFS with rollback | maze generation / exhaustive local structure | oscillation scars |
| `Wall Follower` | boundary contour trace | local embodied navigation | loop and island scars |

### Additional atlas families

| Family | Examples | Stack role |
|---|---|---|
| Heuristic graph search | IDA*, RBFS, SMA*, Fringe Search, Beam Search | bounded-memory or bounded-width goal search |
| Incremental replanning | LPA*, D*, D* Lite, Anytime Repairing A* | changing-map repair modes |
| Geometry-aware line-of-sight | Theta*, Lazy Theta*, Any-angle A* | shortcut/ray admissibility modes |
| Grid acceleration | Jump Point Search, HPA*, contraction hierarchies | static-grid speedups |
| Weighted graph relaxation | Bellman-Ford, Johnson, Floyd-Warshall | negative-edge / all-pairs / baseline maps |
| Sampling planners | RRT, RRT*, PRM, BIT* | continuous-space run-ahead scouts |
| Local motion policies | Bug algorithms, potential fields, vector fields | embodied wall/contact/gradient following |
| Stochastic/metaheuristic | Ant colony, simulated annealing, tabu search, genetic search | noisy scout swarms and FAMM exploration |
| Tree/game search | MCTS, minimax/alpha-beta | adversarial or uncertain branch allocation |
| Learned/index search | HNSW, ANN graph walks, learned heuristics | retrieval-space pathfinding and cache routing |

Admission rule:

```text
new solver mode may enter the atlas when it declares:
  Q_m(v) or equivalent selection law
  what alert increases its weight
  what alert decreases its weight
  what scar it tends to create
  what receipt can replay its committed segment
```

---

## 3  Dual-Map Structure

The system maintains **two deforming maps**:

| Map   | Name              | Scars accumulate from                          |
|-------|-------------------|------------------------------------------------|
| $M^a$ | Ahead / Probe map | false corridors, bad heuristics, noisy attractors |
| $M^b$ | Behind / Commit map | stale receipts, overtrusted paths, delayed corrections |

The **scar differential** is the control signal:

$$
\Delta S_t = S^a_t - S^b_t
$$

This is **FAMM pressure**: the tension between speculative and committed reality.

---

## 4  Run-Ahead Probe Architecture

```
ahead probes  = scouts / wavefront feelers / speculative braids
behind probes = consolidators / receipt builders / admissibility checkers
```

Alert taxonomy from ahead probes:

| Alert                    | Behind-probe response                   |
|--------------------------|-----------------------------------------|
| `EDGE_COST_CHANGED`     | increase Dijkstra/A* weight             |
| `HEURISTIC_BIAS_FAILED` | reduce Greedy/A* heuristic trust        |
| `CORRIDOR_COLLAPSED`    | increase BFS wave sampling              |
| `DEAD_END_CONFIRMED`    | raise residual penalty                  |
| `SHORTCUT_OPENED`       | spawn new attractor basin               |
| `LOOP_PRESSURE_RISING`  | increase DFS strand penetration         |
| `GOAL_FIELD_WARPED`     | slow commit rate, increase receipts     |
| `GOAL_KNOWN_AND_STABLE` | increase Bidirectional BFS              |
| `TIME_BUDGET_TIGHT`     | increase Weighted A* / Beam Search      |
| `BOUNDARY_CONTACT_HIGH` | increase Wall Follower / Bug modes      |
| `ROLLBACK_PRODUCTIVE`   | increase Recursive Backtrack            |
| `MAP_CHANGES_INCREMENTALLY` | increase LPA* / D* family HOLD sidecar |
| `OPEN_CONTINUOUS_SPACE` | increase RRT/PRM family HOLD sidecar    |

---

## 5  The Adaptive Equation

### Full state

$$
X_t = (M^a_t,\; M^b_t,\; S^a_t,\; S^b_t,\; \Theta_t)
$$

### Expanded update

$$
\begin{aligned}
A_t &= \mathcal{P}_{\Theta_t}(M^a_t)
\\[4pt]
\Delta S_t &= S^a_t - S^b_t
\\[4pt]
\Theta_{t+1} &=
\Pi_{\Delta}\!\left[
  (1-\eta)\,\Theta_t + \eta \cdot \mathcal{T}(A_t, R_t, \Delta S_t)
\right]
\\[4pt]
S^a_{t+1} &= \lambda_a\, S^a_t + \phi_a(A_t, R_t)
\\[4pt]
S^b_{t+1} &= \lambda_b\, S^b_t + \phi_b(C_t, R_t, \Delta S_t)
\\[4pt]
M^a_{t+1} &= \mathcal{R}_a(M^a_t,\, A_t,\, S^a_{t+1},\, \Theta_{t+1})
\\[4pt]
M^b_{t+1} &= \mathcal{R}_b(M^b_t,\, C_t,\, S^b_{t+1},\, \Theta_{t+1})
\end{aligned}
$$

Where the current Lean fixture surface is:

$$
\Theta_t =
(\alpha_{BFS},\alpha_{DFS},\alpha_{Dijkstra},\alpha_{A^*},\alpha_{Greedy},
\alpha_{BiBFS},\alpha_{WA^*},\alpha_{RB},\alpha_{WF})
$$

The wider atlas can be projected into this finite basis until a new mode earns
its own formal field. For example, IDA* can initially lower into the A*/DFS
subspace, while D* Lite can lower into the A*/incremental-repair sidecar.

$\Pi_{\Delta}$ projects back onto the simplex ($\alpha_i \ge 0$, $\sum \alpha_i = 1$).

### Commitment gate

$$
C_t =
\begin{cases}
\operatorname{Commit}(M^b_t, A_t, \Theta_{t+1}),
  & \lVert \Delta S_t \rVert_W \le \epsilon \\[4pt]
\varnothing,
  & \lVert \Delta S_t \rVert_W > \epsilon
\end{cases}
$$

### Compact canonical form

$$
\boxed{
X_{t+1}
=
\operatorname{Adm}_{\epsilon}\!\left[
  \operatorname{FAMM}_{\eta,\lambda}\!\left(
    X_t,\; A_t,\; R_t,\; \Delta S_t
  \right)
\right]
}
$$

subject to the **bounded scar divergence invariant**:

$$
\boxed{\lVert S^a_t - S^b_t \rVert_W \le \epsilon}
$$

for any committed segment.

---

## 6  Damping

$$
\Theta_{t+1} = (1-\eta)\,\Theta_t + \eta\,\Delta(A_t, R_t)
$$

| $\eta$ | Behavior                        |
|--------|---------------------------------|
| Low    | Stable, slow learner            |
| High   | Fast, twitchy, possibly chaotic |

**Rule:** Don't let the scout braid yank the whole manifold unless the alert has enough mass.

---

## 7  Braid Interpretation

| Concept         | Braid analogue                    |
|-----------------|-----------------------------------|
| Ahead strand    | Explores unstable possibility     |
| Behind strand   | Commits stable geometry           |
| Alert crossing  | Changes traversal chirality       |
| Receipt closure | Proves committed segment belongs  |

Full cycle:

```
PROBE → ALERT → RETUNE → COMMIT → RECEIPT → RESEED
```

---

## 8  Guarantees

The guarantee moves from *fixed-graph optimality* to:

> **No committed path segment is accepted under a stale topology receipt.**

More precisely:

> No path segment is committed when the speculative scar field and
> committed scar field have diverged beyond admissible FAMM tolerance.

The solver is not trying to become scar-free.
A scar-free solver has learned nothing.
The invariant is: **scars may accumulate, but unbounded scar divergence is forbidden.**

---

## 9  Connection to Existing Stack

| FSDU concept              | Existing FAMM module                    |
|---------------------------|-----------------------------------------|
| Solver mixture $\Theta$   | `DelayHeuristic` in `FAMM_hyperheuristic.lean` |
| Performance scoring       | `scoreHeuristic` / `evaluateHeuristic`  |
| Heuristic switching       | `shouldSwitchHeuristic`                 |
| Crystallized LUT          | `FAMMLut` / `FAMMLutEntry`              |
| Out-of-bounds fail-closed | `hyperHeuristic_outOfBounds_fails`      |
| Switch monotonicity       | `switchCount_monotone`                  |

The FSDU extends the existing hyper-heuristic by adding:
1. **Dual maps** (ahead/behind) instead of a single bank
2. **Scar fields** instead of simple performance history
3. **Scar differential** as the commitment gate
4. **Run-ahead probe alerts** driving tactic switching
5. **BFS/DFS/A*/Dijkstra/Greedy/Bidirectional/Weighted/Backtrack/Wall modes**
   alongside the existing greedy/frustration/mass/adaptive heuristics

## 10  Formalization Status

The Lean surface currently lives at:

```text
2-Search-Space/FAMM/FAMM_FSDU.lean
```

Current checked commands:

```text
lake build Semantics.FixedPoint
lake build Semantics.FAMM
lake env lean /home/allaun/Documents/Research\ Stack/2-Search-Space/FAMM/FAMM_FSDU.lean
lake build Semantics
```

All four commands pass as of the 2026-05-10 receipt.

Claim boundary:

```text
FSDU compiles and local theorem replay works.
Q16_16 signed arithmetic is active.
Q16_16 algebra closure still has HOLD(q16-proof) axioms for signed UInt32 reconstruction.
```

So FSDU is not yet a fully axiom-free proof surface. It is a build-checked
integration surface with explicit low-level proof debt.

---

## 11  Naming

| Short          | Full                                              |
|----------------|---------------------------------------------------|
| **FSDU**       | FAMM Scar Differential Update                     |
| **BraidFront** | Braid-front search with dual-map scar control     |
| **FFS**        | Fractal Frontier Search                           |

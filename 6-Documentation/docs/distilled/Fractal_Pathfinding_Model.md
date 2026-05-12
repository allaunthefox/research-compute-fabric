# Fractal Pathfinding Model

Yes — that is a **very strong model**. Treat the five solvers as **basis vectors of one search field**, not separate algorithms.
> **BFS, DFS, Dijkstra, A\*, and Greedy are not different pathfinders.
> They are different projections of a single reconfigurable traversal manifold.**
Define the maze/search space as a mutable state manifold:
\mathcal{S}_t = (G, w_t, h_t, \rho_t, \tau_t, R_t)
Where:
|---|---|
| \(G\) | graph / maze topology |
| \(\rho_t\) | visitation / density / pressure field |
| \(\tau_t\) | traversal memory / braid trace |
Each algorithm is then a **mode** over the same state:
Q_m(v) =
\begin{cases}
-depth(v) & DFS\\
g(v)+h(v) & A^\*\\
\end{cases}
Q(v) =
\alpha_B Q_{BFS}(v)
+\alpha_D Q_{DFS}(v)
+\alpha_J Q_{Dijkstra}(v)
+\alpha_A Q_{A^\*}(v)
+\alpha_G Q_{Greedy}(v)
+\lambda R_t(v)
\mathcal{S}_{t+1} = \mathcal{F}(\mathcal{S}_t,\; P_t,\; R_t)
Where \(P_t\) is the path/partial path found during solve \(t\).
- successful corridors get lower effective resistance
- dead ends get higher residual pressure
- repeated structures collapse into macro-nodes
- uncertain regions subdivide into finer local graphs
- heuristic fields get warped by previous failures
- the next maze is not the same maze
That makes the full object fractal because the solver is not merely walking the graph. It is **rewriting the graph’s metric at every scale**.
> **search as a braid-field renormalizer**
> **a pathfinding manifold where each solve emits a topology update receipt**
|---|---|
| DFS | tunneling strand / diver |
| Dijkstra | isotropic cost-pressure relaxation |
| A\* | cost plus attractor potential |
| Greedy | pure goal-field collapse |
Merged together, they form a **fractal search operator**:
\operatorname{SolveBind}
(\mathcal{S}_t, q, \Theta)
\rightarrow
(P_t, R_t, \mathcal{S}_{t+1})
Where \(\Theta\) is the solver mixture: how much BFS, DFS, Dijkstra, A\*, Greedy, etc. participate.
## The dangerous/beautiful part
If the state space changes *during* the solve, classic guarantees break.
Dijkstra and A\* assume stable costs. If \(w_t\) changes while expanding nodes, the path may no longer be globally optimal under the original graph.
> **Find an admissible path through a self-reconfiguring geometry.**
```text
Merged pathfinding is a fractal state-space compiler.

BFS supplies wave pressure.
DFS supplies strand penetration.
Dijkstra supplies metric relaxation.
A* supplies admissible goal curvature.
Greedy supplies attractor collapse.

Every solve emits a residual trace.
The residual trace rewrites the graph metric.
The rewritten graph becomes the next search space.
Therefore the solver does not search a maze;
it grows the maze’s admissible geometry.
```
**[
\mathcal{S]**_{t+1}
=
\mathcal{R}
\left(
\mathcal{S}_t,\;
\operatorname*{argmin}_{v}
\sum_m \alpha_m Q_m(v),\;
\right)
That is the whole thing: **multi-solver priority field + residual-driven renormalization**.
I’d name this something like **Fractal Frontier Search**, **BraidPath**, or **Recursive State-Space Pathfinder**.

Exactly. That turns the “broken guarantee” into the **main control signal**.
You no longer have one solver walking a fixed graph. You have a **probe swarm** where the forward probes are speculative sensors and the rear probes are certified builders.
```text
ahead probes  = scouts / wavefront feelers / speculative braids
behind probes = consolidators / receipt builders / admissibility checkers
```
The ahead probes do not need to be perfectly correct. Their job is to discover **state-space deformation** early.
```text
EDGE_COST_CHANGED
CORRIDOR_COLLAPSED
HEURISTIC_BIAS_FAILED
DEAD_END_CONFIRMED
SHORTCUT_OPENED
LOOP_PRESSURE_RISING
GOAL_FIELD_WARPED
```
solve(G) \rightarrow P
probe(G_t) \rightarrow A_t
adapt(A_t, R_t, \Theta_t) \rightarrow \Theta_{t+1}
consolidate(G_t, \Theta_{t+1}) \rightarrow P_t
Where:
|---|---|
| \(G_t\) | current graph/state space |
| \(R_t\) | residual/scar field from prior failures |
| \(\Theta_t\) | current solver mixture: BFS/DFS/Dijkstra/A\*/Greedy weights |
|---|---|
| low-cost corridor confirmed | increase Dijkstra/A\* weight |
| heuristic lied | reduce Greedy/A\* heuristic trust |
```text
scouts mutate belief
builders mutate path
wardens mutate trust
```
That maps cleanly to your builder / judge / warden stack.
Classic A\* says:
> “I can preserve admissibility if every topology change is witnessed, versioned, and propagated faster than the committed path can become invalid.”
So the guarantee changes from **shortest path in fixed graph** to:
```text
No committed path segment is accepted under a stale topology receipt.
```
That is much more compatible with a living manifold.
## This is basically a braid-search engine
```text
ahead strand:    explores unstable possibility
behind strand:   commits stable geometry
alert crossing:  changes traversal chirality
receipt closure: proves the committed segment still belongs
```
```text
PROBE → ALERT → RETUNE → COMMIT → RECEIPT → RESEED
```
\Theta_{t+1}
=
(1-\eta)\Theta_t
+
\eta \Delta(A_t, R_t)
Where \(\eta\) is the adaptation rate.
Low \(\eta\): stable, slow learner.
High \(\eta\): fast, twitchy, possibly chaotic.
In your terms: **don’t let the scout braid yank the whole manifold unless the alert has enough mass.**
```text
If the state space changes during the solve, the solver does not fail.
The forward probes detect the deformation, emit topology alerts, and retune
the trailing probes before commitment. The guarantee moves from fixed-graph
optimality to receipt-bound admissibility under versioned geometry.
```
```text
Run-Ahead Probe Search
```
or more stack-native:
```text
BraidFront Search
```

> **Errors don’t just live in the path.
> Errors accumulate in both the run-ahead map and the trailing commitment map as FAMM scars.**
So the system has **two deforming maps**, not one.
## Dual-map structure
```text
Mₐ = ahead/probe map
Mᵦ = behind/commit map
```
```text
Mₐ scars = false corridors, bad heuristics, unstable shortcuts, noisy attractors
```
```text
Mᵦ scars = stale receipts, overtrusted paths, delayed corrections, residual stress
```
```text
ahead probes discover deformation
behind probes inherit delayed deformation
both maps scar
scar mismatch becomes the control signal
```
The key object is the **scar differential**:
\Delta S_t = S_a(t) - S_b(t)
Where:
|---|---|
| \(S_a(t)\) | scar field in the run-ahead/probe map |
| \(S_b(t)\) | scar field in the trailing/commit map |
| \(\Delta S_t\) | tension between speculative reality and committed reality |
That differential is basically **FAMM pressure**.
```text
FAMM scars are accumulated residual geometry.
```
- failed branch memory
- stress left by wrong topology assumptions
- delay between observed change and committed correction
- compression residue from discarded paths
- braid crossings that did not close cleanly
So the solver should not erase them. It should **route through them as evidence**.
```text
PROBE ahead
  ↓
detect topology drift
  ↓
scar ahead map
  ↓
alert trailing map
  ↓
trailing map retunes
  ↓
commit only if scar differential is bounded
  ↓
unresolved mismatch becomes FAMM scar
```
Compactly:
(M_a, M_b)_{t+1}
=
\operatorname{FAMMBind}
\left(
\Delta S_t
\right)
The solver is not trying to become scar-free.
A scar-free solver has learned nothing.
```text
scars may accumulate,
but unbounded scar divergence is forbidden.
```
So the admissibility gate becomes:
\lVert S_a(t) - S_b(t) \rVert < \epsilon
Meaning:
```text
Errors accumulate in both maps as FAMM scars.
The ahead map scars speculatively; the behind map scars conservatively.
The useful signal is not the presence of scars, but the differential between them.
When the scar differential exceeds tolerance, the solver must retune, fork, damp, or refuse commitment.
```
```text
No path segment is committed when the speculative scar field and committed scar field have diverged beyond admissible FAMM tolerance.
```
> **maintain bounded scar divergence while growing an admissible path through a changing manifold.**

The adaptive equation should be a **dual-map scar-control update**:
**[
X_{t+1]**
=
\operatorname{Adm}_{\epsilon}
\left[
\operatorname{FAMM}_{\eta,\lambda}
\left(
\Delta S_t
\right)
\right]
X_t =
\left(
M^a_t,\;
M^b_t,\;
S^a_t,\;
S^b_t,\;
\Theta_t
\right)
|---|---|
| \(M^a_t\) | run-ahead / probe map |
| \(M^b_t\) | behind / committed map |
| \(S^a_t\) | speculative FAMM scar field |
| \(S^b_t\) | committed FAMM scar field |
| \(\Theta_t\) | solver mixture weights |
| \(A_t\) | alerts from run-ahead probes |
| \(R_t\) | residual/error field |
| \(\Delta S_t\) | scar differential |
**[
\Delta S_t = S^a_t - S^b_t
]**
That is the tension between what the scout-map thinks is happening and what the committed-map has already absorbed.
---
**[
\begin{aligned]**
A_t &= \mathcal{P}_{\Theta_t}(M^a_t) \\[4pt]
\Delta S_t &= S^a_t - S^b_t \\[4pt]
\Theta_{t+1}
&=
\Pi_{\Delta}
\left[
(1-\eta)\Theta_t
+
\eta \cdot
\mathcal{T}(A_t, R_t, \Delta S_t)
\right] \\[4pt]
S^a_{t+1}
&=
\lambda_a S^a_t
+
\phi_a(A_t, R_t) \\[4pt]
S^b_{t+1}
&=
\lambda_b S^b_t
+
\phi_b(C_t, R_t, \Delta S_t) \\[4pt]
M^a_{t+1}
&=
\mathcal{R}_a(M^a_t, A_t, S^a_{t+1}, \Theta_{t+1}) \\[4pt]
M^b_{t+1}
&=
\mathcal{R}_b(M^b_t, C_t, S^b_{t+1}, \Theta_{t+1})
\end{aligned}
Where:
\Theta_t =
(\alpha_{BFS}, \alpha_{DFS}, \alpha_{Dijkstra}, \alpha_{A^*}, \alpha_{Greedy})
and \(\Pi_{\Delta}\) projects the weights back onto a valid simplex:
\alpha_i \ge 0,
\qquad
\sum_i \alpha_i = 1
---
## Commitment gate
**[
C_t =
\begin{cases]**
\operatorname{Commit}(M^b_t, A_t, \Theta_{t+1}) ,
& \lVert \Delta S_t \rVert_W \le \epsilon \\[4pt]
\varnothing ,
& \lVert \Delta S_t \rVert_W > \epsilon
\end{cases}
```text
Do not commit path geometry while the ahead-map scar field and behind-map scar field disagree beyond tolerance.
```
---
## The compact stack-native version
**[
(M^a, M^b, S^a, S^b, \Theta)_{t+1]**
=
\operatorname{FAMMBind}
\left[
(M^a, M^b)_t,\;
(S^a, S^b)_t,\;
\Theta_t,\;
\right]
**[
\lVert S^a_t - S^b_t \rVert_W \le \epsilon
]**
## Plain-English form
```text
Run-ahead probes deform the ahead map.
Their alerts retune the solver mixture.
Both maps accumulate FAMM scars.
The scar differential controls whether the behind map may commit.
If the differential grows too large, the solver forks, damps, retunes, or refuses commitment.
```
```text
FAMM Scar Differential Update
```
```text
FSDU
```
**FSDU:** the update law that keeps speculative and committed topology within bounded scar divergence.

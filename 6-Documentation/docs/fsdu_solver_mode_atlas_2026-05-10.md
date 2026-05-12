# FSDU Solver Mode Atlas

Status: `CANDIDATE_SOLVER_BASIS`

Claim boundary: this is a solver-mode atlas for the FAMM Scar Differential
Update surface. It is not a claim that every algorithm has been implemented,
benchmarked, or proven equivalent. It defines how traversal algorithms enter
the adaptive mixture as bounded projection modes.

Theory anchor:

```text
2-Search-Space/FAMM/docs/FSDU_theory.md
```

Lean anchor:

```text
2-Search-Space/FAMM/FAMM_FSDU.lean
```

## Core Fixture Modes

The current finite Lean fixture uses nine modes:

| Mode | Geometry | Use | Scar risk |
|---|---|---|---|
| A* | cost plus goal curvature | admissible heuristic route | stale heuristic |
| Dijkstra | isotropic cost relaxation | weighted graph baseline | expensive wavefront |
| Greedy Best-First | goal attractor collapse | fast scout | false attractor |
| BFS | expanding wavefront | unweighted reachability | frontier blow-up |
| DFS | tunneling strand | narrow/deep passage | dead-end depth |
| Bidirectional BFS | two-front closure | known start and goal | midpoint mismatch |
| Weighted A* | inflated heuristic | speed-biased route | suboptimality debt |
| Recursive Backtrack | constructive DFS with rollback | local exhaustive structure | oscillation |
| Wall Follower | boundary contour trace | embodied/local wall navigation | loop/island trap |

## Extended Atlas

Additional modes can be lowered into the finite basis until they earn their own
formal field.

| Family | Examples | Initial lowering |
|---|---|---|
| bounded-memory heuristic | IDA*, RBFS, SMA* | A* + DFS |
| bounded-width heuristic | Beam Search, Fringe Search | Greedy + Weighted A* |
| incremental replanning | LPA*, D*, D* Lite, ARA* | A* + scar repair sidecar |
| line-of-sight | Theta*, Lazy Theta*, Any-angle A* | A* + ray shortcut sidecar |
| grid acceleration | Jump Point Search, HPA* | A* + cached symmetry sidecar |
| weighted relaxation | Bellman-Ford, Johnson, Floyd-Warshall | Dijkstra + baseline map |
| continuous sampling | RRT, RRT*, PRM, BIT* | DFS + random scout sidecar |
| local embodied | Bug algorithms, potential fields | Wall Follower + Greedy |
| stochastic/metaheuristic | ant colony, simulated annealing, tabu, genetic | Greedy + FAMM exploration |
| game/tree search | MCTS, minimax, alpha-beta | DFS + receipt branching |
| retrieval graph | HNSW, ANN walks, learned heuristics | Greedy + Dijkstra |

## Admission Rule

Each new mode needs:

```text
selection law Q_m(v)
weight-increase alert
weight-decrease alert
scar type it tends to create
receipt shape for committed segments
negative control or failure case
```

If those are missing, the mode remains an atlas note rather than a formal field.

## FSDU Control Law

```text
X_t = (M_a, M_b, S_a, S_b, Theta)
DeltaS_t = S_a - S_b
commit allowed iff ||DeltaS_t|| <= epsilon
```

The solver atlas only changes `Theta`. It does not change the commitment rule.

## Keeper Distinction

Classic pathfinding asks:

```text
which algorithm finds the best path on this graph?
```

FSDU asks:

```text
which mixture keeps speculative and committed scars bounded
while the graph itself may be changing?
```

That is the important expansion. The algorithm name is not the truth source.
The replay receipt and bounded scar differential are.

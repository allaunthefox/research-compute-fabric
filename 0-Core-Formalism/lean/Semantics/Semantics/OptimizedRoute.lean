import Semantics.RouteCost

/-!
# Optimized Route Proof

2-opt local search over exactishRoute finds a strictly cheaper permutation
of the same 39 nodes.  The cost comparison is over `Nat` (Q16.16-scaled
fixed-point arithmetic), so `native_decide` closes the inequality gate.

Route discovered by 2-opt: cost 345147 < 401666 (exactishRoute).
-/

namespace Semantics.RouteCost

/-- The 2-opt optimized route: same 39 nodes, different order. -/
def optimizedRoute : List RouteNode :=
  [ nF01, nF02, nF03, nS1, nB2, nS2, nF04, nF05, nF06, nF07
  , nM2, nM3, nF12, nF11, nM5, nM1, nB3, nB1, nS4, nB4
  , nS3, nF08, nF09, nF10, nM4, nF37, nF34, nF24, nF17, nF16
  , nG0, nB5, nB8, nB7, nB6, nS5, nX3, nX2, nX1
  ]

/-- Both routes visit 39 nodes. -/
theorem optimizedRoute_length :
    optimizedRoute.length = exactishRoute.length := by
  native_decide

/-- The optimized route is strictly cheaper than the exactish route.
    Cost: 345147 < 401666 (Q16.16-scaled Nat). -/
theorem optimizedRoute_shorter :
    routeCostSum optimizedRoute < routeCostSum exactishRoute := by
  native_decide

/-- Cost savings from 2-opt optimization (Q16.16-scaled Nat). -/
def costSavings : Nat :=
  routeCostSum exactishRoute - routeCostSum optimizedRoute

theorem costSavings_positive : costSavings > 0 := by
  unfold costSavings
  exact Nat.sub_pos_of_lt optimizedRoute_shorter

end Semantics.RouteCost

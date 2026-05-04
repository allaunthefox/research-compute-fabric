/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

Tactics.lean — Custom proof automation for the Sovereign Informatic Manifold
-/

import Lean

namespace Semantics.Tactics

/-- 
Tactic to automatically prove well-formedness for ProbDist.
Goal: `counts.size = B ∧ total > 0`
Usage: `wf := by by_prob_dist`
-/
macro "by_prob_dist" : tactic => 
  `(tactic| (
    constructor <;> (first | simpa | exact lt_of_lt_of_le Nat.zero_lt_one (Nat.le_max_right _ 1))
  ))

end Semantics.Tactics

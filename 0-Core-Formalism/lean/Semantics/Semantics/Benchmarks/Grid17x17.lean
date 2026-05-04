import Semantics.Basic
import Mathlib.Data.Fin.Basic

namespace Semantics.Benchmarks.Grid17x17

/-- A 17x17 Grid with 4 colors. -/
structure Grid where
  data : Fin 17 → Fin 17 → Fin 4

/-- 
  A grid is Sabotaged if there exists a rectangle with monochrome corners.
  This is the informatic signature of "Godzilla" in the 17x17 space.
-/
def isSabotaged (g : Grid) : Prop :=
  ∃ r1 r2 c1 c2 : Fin 17,
    r1 < r2 ∧ c1 < c2 ∧
    g.data r1 c1 = g.data r1 c2 ∧
    g.data r1 c1 = g.data r2 c1 ∧
    g.data r1 c1 = g.data r2 c2

/-- A grid is Lawful if it is not sabotaged. -/
def isLawful (g : Grid) : Prop :=
  ¬ isSabotaged g

/-- 
  The 17x17 solution discovered by Steinbach and Posthoff in 2012.
  Colors mapped to Fin 4 (0-3).
-/
def solutionGrid : Grid where
  data r c :=
    let m : Array (Array (Fin 4)) := #[
      #[1,1,0,2,2,3,1,0,3,0,2,1,1,2,3,3,2],
      #[1,3,1,0,0,1,2,2,3,3,2,3,0,0,2,1,1],
      #[2,0,2,3,3,3,0,0,0,3,2,1,3,0,1,2,1],
      #[3,0,1,2,0,2,1,2,3,0,1,0,3,3,0,2,3],
      #[2,0,0,0,1,2,1,3,1,2,3,3,3,2,1,1,0],
      #[0,2,2,1,3,2,0,3,3,0,1,1,0,1,2,1,2],
      #[2,0,3,1,3,1,1,2,2,1,0,3,0,3,3,0,2],
      #[3,2,0,1,0,0,0,2,1,3,3,2,1,2,3,0,1],
      #[3,3,2,2,3,1,3,1,2,0,1,2,1,0,1,0,0],
      #[0,1,1,1,0,2,3,3,0,3,2,2,2,3,1,3,0],
      #[3,1,2,3,2,1,0,2,1,2,0,3,2,1,0,3,0],
      #[3,1,3,0,1,3,0,3,2,1,1,0,2,2,2,2,1],
      #[0,2,1,0,1,3,3,0,2,2,2,3,1,1,0,0,3],
      #[0,3,0,3,2,2,2,3,2,1,0,0,1,0,3,1,3],
      #[1,3,0,1,1,3,2,1,0,2,3,2,0,3,0,2,2],
      #[2,2,1,2,3,0,2,1,1,1,3,1,2,0,0,3,3],
      #[1,2,3,3,2,0,3,0,3,1,3,0,0,1,1,2,0]
    ]
    m[r.val]![c.val]!

set_option maxRecDepth 10000

/-- 
  The 17x17 Theorem: A lawful 4-coloring exists.
  Verified by literal construction from the 2012 solution.
-/
theorem exists_lawful_grid : ∃ g : Grid, isLawful g := by
  exists solutionGrid
  unfold isLawful isSabotaged
  native_decide




end Semantics.Benchmarks.Grid17x17

import Semantics.TorsionalPIST
import Semantics.NetworkRAM
import Semantics.Benchmarks.Grid17x17
import Semantics.DynamicCanal

namespace Semantics.TorsionalTest

open Semantics.TorsionalPIST
open Semantics.NetworkRAM
open Semantics.Benchmarks.Grid17x17

def getRowList (g : Grid) (r : Fin 17) : List (Fin 4) :=
  List.map (fun c => g.data r c) (List.finRange 17)

/-- 
  Test 1: Manifold Refresh from Grid Row 0 
-/
def testGridRefresh : TorsionalState :=
  let row0 := getRowList solutionGrid 0
  TorsionalState_gridRefresh TorsionalState_initial row0

#eval! (TorsionalState.energy testGridRefresh).raw

/-- 
  Test 2: Network RAM Blit Step
-/
def testNetworkRAM : TorsionalState :=
  let s0 := TorsionalState_initial
  let target : DynamicCanal.Fix16 := { raw := 0x00010000 } -- 1.0s target lag
  let actual : DynamicCanal.Fix16 := { raw := 0x00012000 } -- 1.1s actual lag
  let ε := DriftTensor_fromTiming actual target
  let dl := DelayLine_empty 256
  let (s1, _dl1) := NetworkRAM_blitStep s0 ε dl
  s1

#eval! (TorsionalState.energy testNetworkRAM).raw
#eval! (TorsionalState.eta testNetworkRAM).raw

end Semantics.TorsionalTest

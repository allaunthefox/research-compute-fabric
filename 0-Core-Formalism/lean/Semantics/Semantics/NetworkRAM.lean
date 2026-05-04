import Semantics.Quaternion
import Semantics.Adaptation
import Semantics.FixedPoint
import Semantics.DynamicCanal
import Semantics.TorsionalPIST

namespace Semantics.NetworkRAM

/-- 
  DriftTensor (ε_TCP): The software interface to network lag.
-/
structure DriftTensor where
  jitter : DynamicCanal.Fix16
  lag    : DynamicCanal.Fix16
  salt   : DynamicCanal.Fix16
  deriving Repr, DecidableEq

/-- 
  DelayLine: The physical substrate of 'Network RAM'.
-/
structure DelayLine where
  slots : Array Semantics.TorsionalPIST.TorsionalState
  size  : Nat
  deriving Repr, DecidableEq

def DriftTensor_fromTiming (actual target : DynamicCanal.Fix16) : DriftTensor :=
  let delta := if actual.raw > target.raw then DynamicCanal.Fix16.sub actual target else DynamicCanal.Fix16.sub target actual
  let jitter := DynamicCanal.Fix16.div delta target
  let salt := DynamicCanal.Fix16.mul jitter { raw := 0x00008000 }
  { jitter := jitter, lag := delta, salt := salt }

def DelayLine_empty (n : Nat) : DelayLine :=
  { slots := (List.replicate n Semantics.TorsionalPIST.TorsionalState_initial).toArray
  , size := n }

def DelayLine_readAt (dl : DelayLine) (ε : DriftTensor) : Semantics.TorsionalPIST.TorsionalState :=
  let addr := (DriftTensor.lag ε).raw.toNat % dl.size
  dl.slots[addr]!

def DelayLine_writeAt (dl : DelayLine) (ε : DriftTensor) (s : Semantics.TorsionalPIST.TorsionalState) : DelayLine :=
  let addr := (DriftTensor.lag ε).raw.toNat % dl.size
  { dl with slots := dl.slots.set! addr s }

def NetworkRAM_blitStep (M_k : Semantics.TorsionalPIST.TorsionalState) (ε : DriftTensor) (dl : DelayLine) 
    : Semantics.TorsionalPIST.TorsionalState × DelayLine :=
  let _prev_s := DelayLine_readAt dl ε
  let salted_eta := DynamicCanal.Fix16.add (Semantics.TorsionalPIST.TorsionalState.eta M_k) (DriftTensor.jitter ε)
  let M_salted := { M_k with eta := salted_eta }
  let next_M := Semantics.TorsionalPIST.TorsionalState_torsionalBetaStep M_salted (DriftTensor.lag ε)
  let next_dl := DelayLine_writeAt dl ε next_M
  (next_M, next_dl)

end Semantics.NetworkRAM

import Semantics.FixedPoint
import Semantics.CompressionMechanicsBridge

namespace Semantics.CompressionControl

open Semantics
open Semantics.CompressionMechanicsBridge

/--
Local ENE-style control flag.
-/
inductive ControlFlag
  | Red
  | White
  | Blue
deriving Repr, Inhabited, DecidableEq

/--
Proof-layer control state over an already constructed substrate witness.
This captures the archive's strongest reusable idea: confidence-guided,
cache-aware pruning over canonicalized states.
-/
structure ControlState where
  substrate : SubstrateWitness
  confidence : Q16_16
  cacheSeen : Bool
  pruned : Bool
deriving Repr, Inhabited

/--
Low-confidence threshold for pruning.
-/
def confidenceThreshold : Q16_16 := Q16_16.one

/--
ENE manifold thresholds reused locally to avoid unrelated scaffold dependencies.
-/
def redThreshold : Q16_16 := Q16_16.ofInt 4
def blueThreshold : Q16_16 := Q16_16.ofInt 10

/--
Confidence update: convex-style blend of previous confidence and current score.
This remains in the proof layer as a bounded fixed-point update.
-/
def updateConfidence (previous score alpha : Q16_16) : Q16_16 :=
  Q16_16.add
    (Q16_16.mul alpha previous)
    (Q16_16.mul (Q16_16.sub Q16_16.one alpha) score)

/--
Assign an ENE-style flag from the control confidence.
-/
def getControlFlag (state : ControlState) : ControlFlag :=
  if Q16_16.lt state.confidence redThreshold then .Red
  else if Q16_16.lt state.confidence blueThreshold then .White
  else .Blue

/--
Canonicalization witness: a state is canonicalized when either it is already
cached or its substrate witness is admissible.
-/
def canonicalized (state : ControlState) : Bool :=
  state.cacheSeen || substrateAdmissible state.substrate

/--
Pruning law from the archive: prune if already pruned, if confidence is below
threshold, or if the substrate witness is not admissible.
-/
def pruneDecision (state : ControlState) : Bool :=
  state.pruned ||
    Q16_16.lt state.confidence confidenceThreshold ||
    !(substrateAdmissible state.substrate)

/--
Local update step for confidence only.
-/
def localUpdate (state : ControlState) (score alpha : Q16_16) : ControlState :=
  { state with confidence := updateConfidence state.confidence score alpha }

/--
Cache update stage.
-/
def cacheUpdate (state : ControlState) (seen : Bool) : ControlState :=
  { state with cacheSeen := seen }

/--
Canonicalization stage. This does not alter state data; it exposes whether the
state is admissible for reuse.
-/
def canonicalize (state : ControlState) : ControlState :=
  state

/--
Pruning stage.
-/
def prune (state : ControlState) : ControlState :=
  { state with pruned := pruneDecision state }

/--
Composed control step:
`Prune ∘ Canonicalize ∘ CacheUpdate ∘ LocalUpdate`
-/
def controlStep (state : ControlState) (score alpha : Q16_16) (seen : Bool) : ControlState :=
  prune (canonicalize (cacheUpdate (localUpdate state score alpha) seen))

/--
Control admissibility requires a substrate-admissible witness, canonicalized
state, and no prune decision.
-/
def controlAdmissible (state : ControlState) : Bool :=
  substrateAdmissible state.substrate &&
    canonicalized state &&
    !pruneDecision state

/--
Cached states are canonicalized by definition.
-/
theorem cachedCanonicalized (state : ControlState)
  (h : state.cacheSeen = true) :
  canonicalized state = true := by
  simp [canonicalized, h]

/--
Pruning stage sets the `pruned` bit exactly to the prune decision.
-/
theorem pruneSetsPruned (state : ControlState) :
  (prune state).pruned = pruneDecision state := by
  rfl

/--
If the substrate is admissible and confidence is at least the threshold, a
fresh unpruned uncached state will not be pruned.
-/
theorem highConfidenceAdmissibleNotPruned
  (state : ControlState)
  (hSub : substrateAdmissible state.substrate = true)
  (hConf : Q16_16.lt state.confidence confidenceThreshold = false)
  (hFresh : state.pruned = false) :
  pruneDecision state = false := by
  simp [pruneDecision, hSub, hConf, hFresh]

/--
If a state is marked as seen in the cache, it is canonicalized.
-/
theorem seenCacheCanonicalized
  (state : ControlState) :
  canonicalized (cacheUpdate state true) = true := by
  simp [cacheUpdate, canonicalized]

def sampleControlState : ControlState :=
  { substrate := sampleSubstrateWitness
  , confidence := blueThreshold
  , cacheSeen := false
  , pruned := false }

def sampleControlStep : ControlState :=
  controlStep sampleControlState blueThreshold Q16_16.one true

#eval getControlFlag sampleControlState
#eval canonicalized sampleControlState
#eval pruneDecision sampleControlState
#eval controlAdmissible sampleControlState
#eval canonicalized (cacheUpdate sampleControlState true)
#eval sampleControlStep.pruned

end Semantics.CompressionControl

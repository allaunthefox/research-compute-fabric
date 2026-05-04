import ExtensionScaffold.Compression.CellCore
import ExtensionScaffold.Compression.SignalPolicy

namespace ExtensionScaffold.Compression.Metatyping

open Semantics
open ExtensionScaffold.Compression.CellCore
open ExtensionScaffold.Compression.PriorityGossip
open ExtensionScaffold.Compression.SignalPolicy

/--
Visibility: Defines the locality or structural clarity of a path.
-/
inductive Visibility where
  | hidden
  | obscured
  | clear
  | crystalline
  deriving Repr, BEq, DecidableEq

def visibilityScore : Visibility -> Q16_16
  | .hidden      => Q16_16.ofFloat 0.1
  | .obscured    => Q16_16.ofFloat 0.5
  | .clear       => Q16_16.one
  | .crystalline => Q16_16.ofInt 2

/--
Coherence: The inverse of noise (N).
Calculated as 1 / (1 + noise).
-/
def signalCoherence (s : SignalSample) : Q16_16 :=
  Q16_16.div Q16_16.one (Q16_16.add Q16_16.one s.value)

/--
MetaState: The accumulator for the Metatyping Invariant (sigma).
-/
structure MetaState where
  sigma : Q16_16
  deriving Repr

/--
MetaStep: The per-transition update for the Metatyping Equation.
sigma_t+1 = sigma_t + (gain * coherence * visibility)
-/
def metaStep
  (p : GossipPayload)
  (signal : SignalSample)
  (vis : Visibility)
  (m : MetaState) : MetaState :=
  let gain := priorityScore p
  let coherence := signalCoherence signal
  let visibility := visibilityScore vis
  let delta := Q16_16.mul (Q16_16.mul gain coherence) visibility
  { sigma := Q16_16.add m.sigma delta }

/--
MetaAccumulate: Fold over a route to compute the trajectory quality.
This is the executable form of the Path Integral: ∮ bind
-/
def metaAccumulate
  (ps : Array GossipPayload)
  (signalOf : GossipPayload -> SignalSample)
  (visOf : GossipPayload -> Visibility) : MetaState :=
  ps.foldl
    (fun m p => metaStep p (signalOf p) (visOf p) m)
    { sigma := Q16_16.zero }

/--
Bindable: Only accumulate structurally valid transitions.
This gates the Metatyping Invariant by the Substrate's lawfulness.
-/
def bindable (p : GossipPayload) (c : LocalSignature) : Bool :=
  p.sig == c

/--
Route Quality Analysis:
Good routes exceed a specific threshold of accumulated sigma.
-/
def isGoodRoute (m : MetaState) (threshold : Q16_16) : Bool :=
  Q16_16.ge m.sigma threshold

def isPromotable (m : MetaState) : Bool :=
  Q16_16.gt m.sigma (Q16_16.ofInt 10)

end ExtensionScaffold.Compression.Metatyping

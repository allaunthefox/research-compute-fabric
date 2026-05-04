import Mathlib.Data.Fin.Basic
import Mathlib.Data.Int.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic
import Semantics.MorphicNeuralNetwork
import Semantics.NeurodivergentPatternLUT
import Semantics.Genome18

/-!
# Abelian Sandpile Routing

This module isolates the algebraic core of the proposed "Millennium problem as
routing" framing.  A neural sandpile state is represented as an integer-valued
chip/load assignment over a finite neuron set.  A firing/toppling at one neuron
is a routing operator induced by a fixed redistribution matrix.

The key fact is the abelian law: for a fixed routing matrix, toppling neuron `u`
and then neuron `v` gives the same state as toppling `v` and then `u`.  This is
the finite routing invariant that larger proof surfaces can use for confluence,
certificate checking, and "route = proof" search.
-/

namespace Semantics.AbelianSandpileRouting

open Finset
open Semantics.NeurodivergentPatternLUT

deriving instance Repr for Semantics.Genome18

instance : Inhabited Semantics.Genome18 :=
  ⟨Semantics.Genome18.default⟩

/-- A finite neural sandpile state: integer load at each neuron. -/
abbrev NeuralSandpileState (n : Nat) := Fin n → Int

/-- A routing matrix; `routing source target` is load sent from `source` to `target`. -/
abbrev RoutingMatrix (n : Nat) := Fin n → Fin n → Int

/--
Closed encoding set for neuronal profiles.  These constructors are intentionally
finite and explicit: route selection can case-split over the complete profile
surface instead of falling back to string tags.
-/
inductive NeuronalProfile where
  | pyramidalExcitatory
  | fastSpikingInterneuron
  | martinottiInterneuron
  | chandelierInterneuron
  | basketInterneuron
  | thalamocorticalRelay
  | reticularThalamic
  | granuleCell
  | purkinjeCell
  | dopaminergicModulator
  | serotonergicModulator
  | cholinergicModulator
  | noradrenergicModulator
  | sensoryProjection
  | motorProjection
  | astrocyteCoupledSupport
  | neurotypicalRouting
  | autismEnhancedPattern
  | adhdFlexibleAttention
  | combinedCompensatory
  | adaptiveSecurityScan
  | adaptiveCodeReview
  | adaptiveSustainedFocus
  | adaptiveSignalDetection
  | adaptiveFaultTolerance
  deriving Repr, Inhabited, BEq, DecidableEq

/-- Coarse neuronal family used for morphic routing pressure. -/
inductive NeuronalFamily where
  | excitatory
  | inhibitory
  | modulatory
  | sensoryMotor
  | support
  | compensatory
  | adaptive
  deriving Repr, Inhabited, BEq, DecidableEq

/-- The complete profile encoding list used by table-driven tooling. -/
def allNeuronalProfiles : List NeuronalProfile := [
  .pyramidalExcitatory,
  .fastSpikingInterneuron,
  .martinottiInterneuron,
  .chandelierInterneuron,
  .basketInterneuron,
  .thalamocorticalRelay,
  .reticularThalamic,
  .granuleCell,
  .purkinjeCell,
  .dopaminergicModulator,
  .serotonergicModulator,
  .cholinergicModulator,
  .noradrenergicModulator,
  .sensoryProjection,
  .motorProjection,
  .astrocyteCoupledSupport,
  .neurotypicalRouting,
  .autismEnhancedPattern,
  .adhdFlexibleAttention,
  .combinedCompensatory,
  .adaptiveSecurityScan,
  .adaptiveCodeReview,
  .adaptiveSustainedFocus,
  .adaptiveSignalDetection,
  .adaptiveFaultTolerance
]

/-- Map each profile to the nearest existing neurodivergent/adaptive pattern. -/
def profilePattern : NeuronalProfile → NeurodivergentPattern
  | .neurotypicalRouting => mkNeurotypicalPattern
  | .autismEnhancedPattern => mkAutismPattern
  | .adhdFlexibleAttention => mkADHDPattern
  | .combinedCompensatory => mkCombinedPattern
  | .adaptiveSecurityScan => mkAdaptivePattern .securityScan
  | .adaptiveCodeReview => mkAdaptivePattern .codeReview
  | .adaptiveSustainedFocus => mkAdaptivePattern .sustainedFocus
  | .adaptiveSignalDetection => mkAdaptivePattern .signalDetection
  | .adaptiveFaultTolerance => mkAdaptivePattern .faultTolerance
  | .pyramidalExcitatory => mkNeurotypicalPattern
  | .fastSpikingInterneuron => mkAdaptivePattern .faultTolerance
  | .martinottiInterneuron => mkAdaptivePattern .codeReview
  | .chandelierInterneuron => mkAdaptivePattern .faultTolerance
  | .basketInterneuron => mkAdaptivePattern .faultTolerance
  | .thalamocorticalRelay => mkAdaptivePattern .signalDetection
  | .reticularThalamic => mkAdaptivePattern .sustainedFocus
  | .granuleCell => mkAdaptivePattern .signalDetection
  | .purkinjeCell => mkAdaptivePattern .codeReview
  | .dopaminergicModulator => mkADHDPattern
  | .serotonergicModulator => mkAdaptivePattern .sustainedFocus
  | .cholinergicModulator => mkAdaptivePattern .securityScan
  | .noradrenergicModulator => mkAdaptivePattern .securityScan
  | .sensoryProjection => mkAdaptivePattern .signalDetection
  | .motorProjection => mkNeurotypicalPattern
  | .astrocyteCoupledSupport => mkAdaptivePattern .faultTolerance

/-- Profile family projection for downstream routing policies. -/
def profileFamily : NeuronalProfile → NeuronalFamily
  | .pyramidalExcitatory | .thalamocorticalRelay | .granuleCell => .excitatory
  | .fastSpikingInterneuron | .martinottiInterneuron | .chandelierInterneuron
  | .basketInterneuron | .reticularThalamic | .purkinjeCell => .inhibitory
  | .dopaminergicModulator | .serotonergicModulator | .cholinergicModulator
  | .noradrenergicModulator => .modulatory
  | .sensoryProjection | .motorProjection => .sensoryMotor
  | .astrocyteCoupledSupport => .support
  | .neurotypicalRouting | .autismEnhancedPattern | .adhdFlexibleAttention
  | .combinedCompensatory => .compensatory
  | .adaptiveSecurityScan | .adaptiveCodeReview | .adaptiveSustainedFocus
  | .adaptiveSignalDetection | .adaptiveFaultTolerance => .adaptive

/-- Morphic routing mode chosen from how close the current state is to the target. -/
inductive MorphicRoutingMode where
  | exploitLocal
  | exploreAtlas
  | rejectDivergent
  deriving Repr, Inhabited, BEq, DecidableEq

/-- Nat absolute distance. -/
def natAbsDiff (a b : Nat) : Nat :=
  if a ≤ b then b - a else a - b

/-- Distance-to-target selector: close routes exploit, middle routes explore, far routes reject. -/
def selectMorphicMode (distance closeRadius farRadius : Nat) : MorphicRoutingMode :=
  if distance ≤ closeRadius then
    .exploitLocal
  else if farRadius ≤ distance then
    .rejectDivergent
  else
    .exploreAtlas

/-- Bridge the morphic mode into the existing MNN routing action vocabulary. -/
def morphicModeToAction : MorphicRoutingMode → RoutingAction
  | .exploitLocal => .local
  | .exploreAtlas => .atlas
  | .rejectDivergent => .reject

/--
Profile-aware morphic route selection.  The profile supplies the compensatory
weight from the full neuronal encoding set; closeness to target supplies the
local/explore/reject routing pressure.
-/
structure ProfileRoutingDecision where
  profile : NeuronalProfile
  family : NeuronalFamily
  mode : MorphicRoutingMode
  action : RoutingAction
  distanceToTarget : Nat
  compensatoryWeight : UInt16
  deriving Repr, Inhabited

/-- Clamp a natural number into the 3-bit forest bin range `[0, 7]`. -/
def bin8OfNat (n : Nat) : Fin 8 :=
  ⟨min n 7, by omega⟩

/--
Equation-forest signals used to refine the morphic route.  These are the six
Genome18 axes from `EQUATION_FOREST_INDEX.md`, kept as natural summaries at the
surface and clamped into `Fin 8` at the hardware/LUT boundary.
-/
structure ForestRouteSignals where
  routingLoad : Nat
  verificationPressure : Nat
  connectance : Nat
  compressionResidue : Nat
  effectiveSample : Nat
  fitnessProxy : Nat
  deriving Repr, Inhabited

/-- Convert forest signals into the canonical Genome18 address state. -/
def forestGenome (signals : ForestRouteSignals) : Semantics.Genome18 :=
  { muBin := bin8OfNat signals.routingLoad
  , rhoBin := bin8OfNat signals.verificationPressure
  , cBin := bin8OfNat signals.connectance
  , mBin := bin8OfNat signals.compressionResidue
  , neBin := bin8OfNat signals.effectiveSample
  , sigmaBin := bin8OfNat signals.fitnessProxy }

/--
Default forest projection from a profile and distance.  This folds the forest
street map into the route decision:
- F11/F12: distance and compensatory weight shape routing load/verification
- F08-F10: profile family shapes connectance
- F01-F03: distance and profile shape compression/sample/fitness bins
-/
def forestSignalsForProfile (profile : NeuronalProfile) (distance : Nat) :
    ForestRouteSignals :=
  let pattern := profilePattern profile
  let compBin := pattern.routing.compensationFactor.toNat / 8192
  let routingLoad := min 7 (distance / 8 + compBin)
  let verificationPressure :=
    match profileFamily profile with
    | .support => 7
    | .adaptive => 6
    | .compensatory => 5
    | .inhibitory => 5
    | .modulatory => 4
    | .excitatory => 3
    | .sensoryMotor => 3
  let connectance :=
    match profileFamily profile with
    | .excitatory => 5
    | .inhibitory => 6
    | .modulatory => 4
    | .sensoryMotor => 4
    | .support => 7
    | .compensatory => 6
    | .adaptive => 6
  let compressionResidue := min 7 (distance / 16)
  let effectiveSample :=
    match profileFamily profile with
    | .support => 7
    | .compensatory => 6
    | .adaptive => 6
    | _ => 4
  let fitnessProxy := if distance ≤ 5 then 7 else if distance ≤ 40 then 5 else 2
  { routingLoad := routingLoad
  , verificationPressure := verificationPressure
  , connectance := connectance
  , compressionResidue := compressionResidue
  , effectiveSample := effectiveSample
  , fitnessProxy := fitnessProxy }

/-- Forest-calibrated decision surface with its Genome18 address. -/
structure ForestProfileRoutingDecision extends ProfileRoutingDecision where
  forestSignals : ForestRouteSignals
  genome : Semantics.Genome18
  forestAddress : Nat
  deriving Repr, Inhabited

/--
Refine the distance-only morphic mode with the equation forest.  Extreme routing
load with weak verification rejects; close routes with enough verification stay
local; everything else goes to atlas exploration.
-/
def refineModeWithForest
    (baseMode : MorphicRoutingMode) (signals : ForestRouteSignals) : MorphicRoutingMode :=
  if signals.routingLoad ≥ 7 ∧ signals.verificationPressure ≤ 3 then
    .rejectDivergent
  else
    match baseMode with
    | .exploitLocal =>
        if signals.verificationPressure ≥ 4 then .exploitLocal else .exploreAtlas
    | .exploreAtlas => .exploreAtlas
    | .rejectDivergent => .rejectDivergent

/-- Forest refinement preserves close/local routing when verification is strong. -/
theorem refineModeWithForest_close_verified
    {signals : ForestRouteSignals}
    (hLoad : ¬ (signals.routingLoad ≥ 7 ∧ signals.verificationPressure ≤ 3))
    (hVerify : signals.verificationPressure ≥ 4) :
    refineModeWithForest .exploitLocal signals = .exploitLocal := by
  simp [refineModeWithForest, hLoad, hVerify]

/-- Select a profile-aware route decision from current/target scalar summaries. -/
def chooseProfileRoute
    (profile : NeuronalProfile) (current target closeRadius farRadius : Nat) :
    ProfileRoutingDecision :=
  let distance := natAbsDiff current target
  let mode := selectMorphicMode distance closeRadius farRadius
  let pattern := profilePattern profile
  { profile := profile
  , family := profileFamily profile
  , mode := mode
  , action := morphicModeToAction mode
  , distanceToTarget := distance
  , compensatoryWeight := pattern.routing.compensatoryWeight }

/-- Select a profile-aware route, then refine it through the equation forest. -/
def chooseForestProfileRoute
    (profile : NeuronalProfile) (current target closeRadius farRadius : Nat) :
    ForestProfileRoutingDecision :=
  let distance := natAbsDiff current target
  let base := chooseProfileRoute profile current target closeRadius farRadius
  let signals := forestSignalsForProfile profile distance
  let mode := refineModeWithForest base.mode signals
  let genome := forestGenome signals
  { profile := base.profile
  , family := base.family
  , mode := mode
  , action := morphicModeToAction mode
  , distanceToTarget := base.distanceToTarget
  , compensatoryWeight := base.compensatoryWeight
  , forestSignals := signals
  , genome := genome
  , forestAddress := genome.addr }

/-- Every forest-refined profile route has a valid 18-bit Genome address. -/
theorem chooseForestProfileRoute_address_range
    (profile : NeuronalProfile) (current target closeRadius farRadius : Nat) :
    (chooseForestProfileRoute profile current target closeRadius farRadius).forestAddress < 262144 := by
  simp [chooseForestProfileRoute]
  exact Semantics.Genome18.addr_range _

theorem selectMorphicMode_close
    {distance closeRadius farRadius : Nat} (h : distance ≤ closeRadius) :
    selectMorphicMode distance closeRadius farRadius = .exploitLocal := by
  simp [selectMorphicMode, h]

theorem selectMorphicMode_far
    {distance closeRadius farRadius : Nat}
    (hClose : ¬ distance ≤ closeRadius) (hFar : farRadius ≤ distance) :
    selectMorphicMode distance closeRadius farRadius = .rejectDivergent := by
  simp [selectMorphicMode, hClose, hFar]

theorem chooseProfileRoute_close_action
    (profile : NeuronalProfile) {current target closeRadius farRadius : Nat}
    (h : natAbsDiff current target ≤ closeRadius) :
    (chooseProfileRoute profile current target closeRadius farRadius).action = RoutingAction.local := by
  simp [chooseProfileRoute, selectMorphicMode_close h, morphicModeToAction]

theorem allNeuronalProfiles_nonempty : allNeuronalProfiles.length = 25 := by
  native_decide

/-- Total load emitted by a source neuron under the routing matrix. -/
def emittedLoad {n : Nat} (routing : RoutingMatrix n) (source : Fin n) : Int :=
  ∑ target : Fin n, routing source target

/-- The signed load delta caused by toppling one source neuron. -/
def toppleDelta {n : Nat} (routing : RoutingMatrix n) (source target : Fin n) : Int :=
  routing source target - if target = source then emittedLoad routing source else 0

/-- Fire/topple one neuron according to a fixed routing matrix. -/
def topple {n : Nat}
    (routing : RoutingMatrix n) (source : Fin n) (state : NeuralSandpileState n) :
    NeuralSandpileState n :=
  fun target => state target + toppleDelta routing source target

/-- A route certificate is an ordered list of neurons to topple. -/
abbrev RouteCertificate (n : Nat) := List (Fin n)

/-- Execute a route certificate against a starting sandpile state. -/
def runRoute {n : Nat}
    (routing : RoutingMatrix n) (start : NeuralSandpileState n)
    (route : RouteCertificate n) : NeuralSandpileState n :=
  route.foldl (fun state source => topple routing source state) start

/-- Total load in the sandpile state. -/
def totalLoad {n : Nat} (state : NeuralSandpileState n) : Int :=
  ∑ site : Fin n, state site

/-- Toppling preserves total load over the finite neuron set. -/
theorem totalLoad_topple {n : Nat}
    (routing : RoutingMatrix n) (source : Fin n) (state : NeuralSandpileState n) :
    totalLoad (topple routing source state) = totalLoad state := by
  simp [totalLoad, topple, toppleDelta, emittedLoad, Finset.sum_add_distrib,
    Finset.sum_sub_distrib]

/--
The abelian sandpile routing law: two one-step topplings commute.

This is the algebraic heart of treating a hard search problem as a routing
problem over a sandpile neuron set.
-/
theorem topple_commute {n : Nat}
    (routing : RoutingMatrix n) (u v : Fin n) (state : NeuralSandpileState n) :
    topple routing u (topple routing v state) =
      topple routing v (topple routing u state) := by
  ext target
  simp [topple, add_assoc, add_left_comm, add_comm]

/-- Adjacent independent certificate swaps do not change the routed state. -/
theorem runRoute_pair_swap {n : Nat}
    (routing : RoutingMatrix n) (u v : Fin n) (state : NeuralSandpileState n) :
    runRoute routing state [u, v] = runRoute routing state [v, u] := by
  simpa [runRoute] using (topple_commute routing v u state)

/--
A compact statement of the challenge surface: a route proof must carry a
certificate plus a theorem that executing it reaches the claimed target state.
-/
structure RoutingProof {n : Nat} (routing : RoutingMatrix n)
    (start target : NeuralSandpileState n) where
  route : RouteCertificate n
  reachesTarget : runRoute routing start route = target

/-- Any routing proof certifies equality between the executed route and target. -/
theorem routingProof_sound {n : Nat}
    {routing : RoutingMatrix n} {start target : NeuralSandpileState n}
    (proof : RoutingProof routing start target) :
    runRoute routing start proof.route = target :=
  proof.reachesTarget

end Semantics.AbelianSandpileRouting

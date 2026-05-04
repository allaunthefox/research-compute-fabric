import Semantics.FixedPoint

namespace Semantics.Tape

/-! # Topological Tape Machine
Ported from `infra/access_control/topological_tape_machine.py`.
Pure state transition core only — all I/O (sqlite, JSON, hashlib, time)
is deleted per the formalization boundary.
-/

/-- Ternary clock modes / transition regimes. -/
inductive ControlMode
  | accumulate
  | commit
  | divergence
  | heatSink
deriving Repr, BEq, DecidableEq

/-- Minimal invariant vector I = (o, a, p, t). -/
structure InvariantVector where
  occupancy : Q16_16
  adjacency : Q16_16
  path      : Q16_16
  trust     : Q16_16
deriving Repr, DecidableEq

/-- Survival mask for morphism validity. -/
structure InvariantMask where
  occupancySurvives : Bool
  adjacencySurvives : Bool
  pathSurvives      : Bool
  trustSurvives     : Bool
deriving Repr, DecidableEq

namespace InvariantVector

def toMask (inv : InvariantVector) (thresholds : InvariantVector) : InvariantMask :=
  { occupancySurvives := Q16_16.ge inv.occupancy thresholds.occupancy
  , adjacencySurvives := Q16_16.ge inv.adjacency thresholds.adjacency
  , pathSurvives      := Q16_16.ge inv.path      thresholds.path
  , trustSurvives     := Q16_16.ge inv.trust     thresholds.trust }

def survives (inv : InvariantVector) (required : InvariantMask) (thresholds : InvariantVector) : Bool :=
  let mask := toMask inv thresholds
  (!required.occupancySurvives || mask.occupancySurvives) &&
  (!required.adjacencySurvives || mask.adjacencySurvives) &&
  (!required.pathSurvives      || mask.pathSurvives)      &&
  (!required.trustSurvives     || mask.trustSurvives)

end InvariantVector

/-- Minimal lawful-formation event. -/
structure BraidEvent where
  eventId           : String
  parentIds         : List String
  stateCommitment   : String
  domain            : String
  timestamp         : Nat
  structuralValidity : Bool
  crossingSignature : String
deriving Repr, DecidableEq

/-- Ordered witness structure B = (e_1, e_2, ..., e_n). -/
structure BraidTrace where
  events : List BraidEvent
deriving Repr, DecidableEq

namespace BraidTrace

def empty : BraidTrace := ⟨[]⟩

def append (bt : BraidTrace) (e : BraidEvent) : BraidTrace :=
  { events := e :: bt.events }

def lastCommitment (bt : BraidTrace) : Option String :=
  match bt.events with
  | [] => none
  | e :: _ => some e.stateCommitment

/-- Stage 1: local braid validity. -/
def isValid (bt : BraidTrace) (durabilityThreshold : Nat) : Bool :=
  bt.events.length ≥ durabilityThreshold &&
  bt.events.all (λ e => e.structuralValidity)

end BraidTrace

/-- Primary machine object S = (μ, I, B, σ, c, h) with KOT accounting.
KOT fields use Rat because physical constants (e.g. 2.9e-21 J) are outside Q16_16 range. -/
structure TapeState where
  mode            : ControlMode
  invariants      : InvariantVector
  braid           : BraidTrace
  confidence      : Q16_16
  kotAccumulated  : Rat
  kotYieldProjected : Rat
deriving Repr, DecidableEq

namespace TapeState

def default : TapeState := {
  mode := ControlMode.accumulate,
  invariants := { occupancy := Q16_16.zero, adjacency := Q16_16.zero,
                  path := Q16_16.zero, trust := Q16_16.zero },
  braid := BraidTrace.empty,
  confidence := Q16_16.zero,
  kotAccumulated := 0,
  kotYieldProjected := 0
}

/-- Basic stability: occupancy and confidence above 0.5. -/
def isStable (s : TapeState) : Bool :=
  let half := Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 2)
  Q16_16.ge s.invariants.occupancy half && Q16_16.ge s.confidence half

end TapeState

/-- Kinetic Operation Token ledger entry.
Rat is used for physical constants outside Q16_16 range. -/
structure KOTLedger where
  subregisterId  : String
  joulesTotal    : Rat
  landauerFloor  : Rat
  landauerRatio  : Rat
  etaTotal       : Rat
  kotTotal       : Rat
  decision       : String
deriving Repr, DecidableEq

/-- Budget envelope for KOT. -/
structure KOTBudget where
  authorized : Rat
  consumed   : Rat
deriving Repr, DecidableEq

namespace KOTBudget

def empty (auth : Rat) : KOTBudget := { authorized := auth, consumed := 0 }

def canAfford (b : KOTBudget) (cost : Rat) : Bool :=
  b.consumed + cost ≤ b.authorized

def spend (b : KOTBudget) (entry : KOTLedger) : KOTBudget :=
  { b with consumed := b.consumed + entry.kotTotal }

/-- Economic viability evaluation. -/
def evaluateEconomics (b : KOTBudget) (projectedYield : Rat) (gasThreshold : Rat) : String :=
  if projectedYield < b.consumed then "PAUSE"
  else if b.consumed > 0 && (b.consumed / projectedYield) > gasThreshold then "PAUSE"
  else if b.consumed ≥ b.authorized then "KILL"
  else "CONTINUE"

end KOTBudget

/-- Pure topological tape machine state. -/
structure TapeMachine where
  budget         : KOTBudget
  thresholds     : InvariantVector
  lambdaWeights  : List (String × Rat)
  tape           : List TapeState
deriving Repr, DecidableEq

namespace TapeMachine

def empty : TapeMachine := {
  budget := KOTBudget.empty 0,
  thresholds := { occupancy := Q16_16.ofInt 0, adjacency := Q16_16.ofInt 0,
                  path := Q16_16.ofInt 0, trust := Q16_16.ofInt 0 },
  lambdaWeights := [("+", 1.2), ("0", 1.0), ("-", 0.8)],
  tape := []
}

/-- Genesis threshold = 1 event; descendant threshold = 2 events. -/
def validBraid (braid : BraidTrace) (isGenesis : Bool) : Bool :=
  let threshold := if isGenesis then 1 else 2
  braid.isValid threshold

/-- Stage 2: morphism validity.
State must be stable, invariants must survive, and no silent vanish. -/
def validMorphism (tm : TapeMachine) (state : TapeState) : Bool :=
  if !state.isStable then false else
  let required := { occupancySurvives := true, adjacencySurvives := true,
                    pathSurvives := false, trustSurvives := false }
  if !state.invariants.survives required tm.thresholds then false else
  -- No silent vanish: not all invariants may be zero simultaneously
  let allZero := state.invariants.occupancy == Q16_16.zero &&
                 state.invariants.adjacency == Q16_16.zero &&
                 state.invariants.path == Q16_16.zero &&
                 state.invariants.trust == Q16_16.zero
  !allZero

/-- Acceptance predicate: braid AND morphism must hold. -/
def accept (tm : TapeMachine) (state : TapeState) : Bool :=
  let isGenesis := tm.tape.isEmpty
  validBraid state.braid isGenesis && validMorphism tm state

/-- Simplified structure compression.
Python version called PBACSContextCompressor; here we keep only the pure contract. -/
def compressStructure (data : List UInt8) : List UInt8 :=
  -- Formalization boundary: compression is an external oracle.
  -- The tape machine only requires that the result fits the invariant predicates.
  data

/-- Compute invariants from structure.
Placeholder faithful to the Python shape but using Q16_16 ratios. -/
def computeInvariants (data : List UInt8) : InvariantVector :=
  let len := data.length
  let unique := (List.foldl (λ acc x => if acc.contains x then acc else acc ++ [x]) [] data).length
  let entropy : Float := if len == 0 then 0.0 else Nat.toFloat unique / len.toFloat
  -- Placeholder: map entropy to Q16_16 bounded in [0,1]
  let entropyQ := Q16_16.ofFloat entropy
  let occupancy := Q16_16.max (Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 2))
                      (Q16_16.min Q16_16.one (Q16_16.ofFloat (len.toFloat / 100.0)))
  { occupancy := occupancy
  , adjacency := Q16_16.max (Q16_16.div (Q16_16.ofInt 1) (Q16_16.ofInt 2)) entropyQ
  , path      := Q16_16.ofFloat 0.7
  , trust     := Q16_16.ofFloat 0.8 }

/-- Compute confidence score. -/
def computeConfidence (_data : List UInt8) : Q16_16 :=
  Q16_16.ofFloat 0.75

/-- Apply control-mode transition law. -/
def applyTransitionLaw (state : TapeState) : TapeState :=
  if state.isStable && state.mode == ControlMode.accumulate then
    { state with mode := ControlMode.commit }
  else
    state

/-- Simulated energy measurement.
In production this comes from hardware/JEDEC. -/
def measureEnergy (data : List UInt8) (mode : ControlMode) : Rat :=
  let len := data.length
  let baseEnergy : Rat := (232 : Rat) / (10^16 : Rat) * (len : Rat)
  let modeMultiplier : Rat := match mode with
    | .accumulate => 1.5
    | .commit     => 1.0
    | .divergence => 0.8
    | .heatSink   => 1.0
  baseEnergy * modeMultiplier

/-- Calculate KOT for operation. -/
def accountKot (tm : TapeMachine) (state : TapeState) (mode : ControlMode) : KOTLedger :=
  let joules := measureEnergy [] mode
  let etaIso : List (String × Rat) := [("rw", 0.9), ("locality", 0.85),
                                        ("batch", 0.95), ("throughput", 0.88)]
  let etaTotal := etaIso.foldl (λ acc (_, v) => acc * v) 1.0
  let landauerFloor : Rat := 2.9e-21
  let landauerRatio := if landauerFloor > 0 then joules / landauerFloor else 0
  let modeStr := match mode with
    | .accumulate => "+"
    | .commit     => "0"
    | .divergence => "-"
    | .heatSink   => "!"
  let lambdaMode := match tm.lambdaWeights.lookup modeStr with | some v => v | none => 1.0
  let kot := lambdaMode * landauerRatio * etaTotal
  let entry := { subregisterId := ""
               , joulesTotal := joules
               , landauerFloor := landauerFloor
               , landauerRatio := landauerRatio
               , etaTotal := etaTotal
               , kotTotal := kot
               , decision := "CONTINUE" }
  let newBudget := tm.budget.spend entry
  let decision := KOTBudget.evaluateEconomics newBudget state.kotYieldProjected (1 / 10 : Rat)
  { entry with decision := decision }

/-- Form a new tape state from normalized input. -/
def formState (tm : TapeMachine) (data : List UInt8) (contextType : String) : TapeState :=
  let compressed := compressStructure data
  let invariants := computeInvariants compressed
  let confidence := computeConfidence compressed
  let parentCommitment := match tm.tape with
    | _ :: _ => "prev_state"
    | [] => "genesis"
  let event1 : BraidEvent := {
    eventId := "event_" ++ parentCommitment ++ "_" ++ contextType,
    parentIds := [parentCommitment],
    stateCommitment := "commit_" ++ contextType,
    domain := contextType,
    timestamp := tm.tape.length,
    structuralValidity := true,
    crossingSignature := "genesis"
  }
  let braid1 := BraidTrace.empty.append event1
  let braid2 := if !tm.tape.isEmpty then
    let event2 : BraidEvent := {
      eventId := "durability_" ++ contextType,
      parentIds := [event1.eventId],
      stateCommitment := "durability_commit",
      domain := contextType ++ "_witness",
      timestamp := tm.tape.length + 1,
      structuralValidity := true,
      crossingSignature := "valid"
    }
    braid1.append event2
  else
    braid1
  let baseState := { TapeState.default with
    invariants := invariants,
    confidence := confidence,
    braid := braid2
  }
  let transitioned := applyTransitionLaw baseState
  let kotEntry := accountKot tm transitioned transitioned.mode
  { transitioned with kotAccumulated := kotEntry.kotTotal }

/-- Ingest: single entry point. Returns new state and updated machine. -/
def ingest (tm : TapeMachine) (data : List UInt8) (contextType : String) : Option (TapeState × TapeMachine) :=
  let state := formState tm data contextType
  if accept tm state then
    some (state, { tm with tape := state :: tm.tape })
  else
    none

end TapeMachine

end Semantics.Tape

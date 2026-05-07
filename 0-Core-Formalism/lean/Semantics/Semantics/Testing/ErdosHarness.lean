namespace Semantics.Testing.ErdosHarness

/-!
ErdosHarness.lean

A finite, executable harness for Erdős-style four-primitive experiments.

The point of this file is deliberately modest: it does not prove the
Erdős-Gyárfás or Erdős-Selfridge conjectures.  It formalizes the promotion
gate that prevents a diagnostic boolean from becoming a theorem claim without
an explicit receipt-bearing witness packet.
-/

structure Edge where
  u : Nat
  v : Nat
  deriving Repr, DecidableEq

structure CycleCount where
  length : Nat
  count : Nat
  deriving Repr, DecidableEq

inductive ExperimentStatus where
  | finiteSmokePass
  | detectorAnomaly
  | verifiedCounterexampleCertificate
  | invalidPacket
  deriving Repr, DecidableEq

def edgeInBounds (n : Nat) (e : Edge) : Bool :=
  e.u < n && e.v < n

def edgeNotLoop (e : Edge) : Bool :=
  e.u != e.v

def normalizedEdge (e : Edge) : Edge :=
  if e.u ≤ e.v then e else { u := e.v, v := e.u }

def listHasDup [DecidableEq α] : List α → Bool
  | [] => false
  | x :: xs => xs.contains x || listHasDup xs

def simpleGraphEdges (n : Nat) (edges : List Edge) : Bool :=
  edges.all (fun e => edgeInBounds n e && edgeNotLoop e) &&
    !listHasDup (edges.map normalizedEdge)

def degreeOf (edges : List Edge) (vertex : Nat) : Nat :=
  (edges.filter (fun e => e.u == vertex || e.v == vertex)).length

def computedDegreeSequence (n : Nat) (edges : List Edge) : List Nat :=
  (List.range n).map (degreeOf edges)

def minNatList : List Nat → Nat
  | [] => 0
  | x :: xs => xs.foldl Nat.min x

def isPow2 (n : Nat) : Bool :=
  n > 0 && n &&& (n - 1) == 0

def powerTwoCycleLengthsUpTo (n : Nat) : List Nat :=
  (List.range (n + 1)).filter (fun k => 3 ≤ k && isPow2 k)

def countForLength (counts : List CycleCount) (length : Nat) : Nat :=
  match counts.find? (fun c => c.length == length) with
  | some c => c.count
  | none => 0

def allCheckedPowerLengthsAbsent (checked : List Nat) (counts : List CycleCount) : Bool :=
  checked.all (fun k => countForLength counts k == 0)

structure GyarfasPacket where
  graphId : String
  n : Nat
  edges : List Edge
  degreeSequence : List Nat
  minDegree : Nat
  checkedLengths : List Nat
  cyclesFoundByLength : List CycleCount
  independentVerifier : Bool
  edgeReceipt : String
  deriving Repr

def GyarfasPacket.graphModelSane (p : GyarfasPacket) : Bool :=
  simpleGraphEdges p.n p.edges

def GyarfasPacket.degreeReceiptMatches (p : GyarfasPacket) : Bool :=
  let ds := computedDegreeSequence p.n p.edges
  p.degreeSequence == ds && p.minDegree == minNatList ds

def GyarfasPacket.checkedAllPowerLengths (p : GyarfasPacket) : Bool :=
  p.checkedLengths == powerTwoCycleLengthsUpTo p.n

def GyarfasPacket.hasReceipt (p : GyarfasPacket) : Bool :=
  !p.edgeReceipt.isEmpty

/--
A packet is a certified finite counterexample candidate only if it carries
the full graph model, full power-of-two length coverage, no found cycles at
those lengths, an independent verifier bit, and a nonempty receipt.
-/
def GyarfasPacket.certifiedCounterexampleCandidate (p : GyarfasPacket) : Bool :=
  p.graphModelSane &&
    p.degreeReceiptMatches &&
    p.minDegree >= 3 &&
    p.checkedAllPowerLengths &&
    allCheckedPowerLengthsAbsent p.checkedLengths p.cyclesFoundByLength &&
    p.independentVerifier &&
    p.hasReceipt

def classifyGyarfasPacket (p : GyarfasPacket) : ExperimentStatus :=
  if !p.graphModelSane || !p.degreeReceiptMatches || !p.hasReceipt then
    .invalidPacket
  else if p.certifiedCounterexampleCandidate then
    .verifiedCounterexampleCertificate
  else
    .detectorAnomaly

def localBadGyarfasPacket : GyarfasPacket :=
  { graphId := "local-run-n10-seed0-summary-only"
    n := 10
    edges := []
    degreeSequence := [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
    minDegree := 5
    checkedLengths := []
    cyclesFoundByLength := []
    independentVerifier := false
    edgeReceipt := "" }

theorem local_bad_gyarfas_is_not_certified :
    localBadGyarfasPacket.certifiedCounterexampleCandidate = false := by
  native_decide

theorem local_bad_gyarfas_is_invalid_packet :
    classifyGyarfasPacket localBadGyarfasPacket = .invalidPacket := by
  native_decide

def diagnosticOnlyGyarfasPacket : GyarfasPacket :=
  { graphId := "local-run-diagnostic-summary"
    n := 10
    edges := [
      {u := 0, v := 1}, {u := 1, v := 2}, {u := 2, v := 3},
      {u := 3, v := 4}, {u := 4, v := 0}
    ]
    degreeSequence := [2, 2, 2, 2, 2, 0, 0, 0, 0, 0]
    minDegree := 0
    checkedLengths := [4, 8]
    cyclesFoundByLength := [{ length := 4, count := 0 }, { length := 8, count := 0 }]
    independentVerifier := false
    edgeReceipt := "sha256:diagnostic" }

theorem diagnostic_gyarfas_stays_anomaly :
    classifyGyarfasPacket diagnosticOnlyGyarfasPacket = .detectorAnomaly := by
  native_decide

structure CoveringSystemPacket where
  candidateId : String
  moduli : List Nat
  residues : List Nat
  coverageWindow : Nat
  uncoveredResidues : List Nat
  independentVerifier : Bool
  candidateReceipt : String
  deriving Repr

def allOdd (xs : List Nat) : Bool :=
  xs.all (fun x => x % 2 == 1)

def allGreaterThanOne (xs : List Nat) : Bool :=
  xs.all (fun x => x > 1)

def pairShapeMatches (p : CoveringSystemPacket) : Bool :=
  p.moduli.length == p.residues.length

def CoveringSystemPacket.hasReceipt (p : CoveringSystemPacket) : Bool :=
  !p.candidateReceipt.isEmpty

def CoveringSystemPacket.isOddCoveringViolationCandidate (p : CoveringSystemPacket) : Bool :=
  pairShapeMatches p &&
    allGreaterThanOne p.moduli &&
    allOdd p.moduli &&
    !listHasDup p.moduli &&
    p.uncoveredResidues.isEmpty &&
    p.independentVerifier &&
    p.hasReceipt

def classifySelfridgePacket (p : CoveringSystemPacket) : ExperimentStatus :=
  if !pairShapeMatches p || !p.hasReceipt then
    .invalidPacket
  else if p.isOddCoveringViolationCandidate then
    .verifiedCounterexampleCertificate
  else
    .finiteSmokePass

def localSelfridgeSmokePacket : CoveringSystemPacket :=
  { candidateId := "local-selfridge-finite-smoke"
    moduli := [3, 5, 7]
    residues := [0, 1, 2]
    coverageWindow := 100
    uncoveredResidues := [4, 8, 11]
    independentVerifier := false
    candidateReceipt := "sha256:finite-smoke" }

theorem selfridge_smoke_is_not_proof :
    localSelfridgeSmokePacket.isOddCoveringViolationCandidate = false := by
  native_decide

theorem selfridge_smoke_classifies_as_finite_smoke :
    classifySelfridgePacket localSelfridgeSmokePacket = .finiteSmokePass := by
  native_decide

def gyarfasPrimitiveMap : List (String × String) :=
  [ ("rho", "edge/min-degree density")
  , ("spectral", "adjacency spectrum C = UΛU^T")
  , ("shear", "degree deformation G = A^T A")
  , ("packet", "cycle witness or Gamma_fail receipt") ]

def selfridgePrimitiveMap : List (String × String) :=
  [ ("rho", "residue/modulus coverage density")
  , ("spectral", "covering overlap spectrum C = UΛU^T")
  , ("shear", "even/odd modulus balance G = A^T A")
  , ("packet", "covering-system witness receipt") ]

#eval classifyGyarfasPacket localBadGyarfasPacket
#eval classifyGyarfasPacket diagnosticOnlyGyarfasPacket
#eval classifySelfridgePacket localSelfridgeSmokePacket
#eval gyarfasPrimitiveMap
#eval selfridgePrimitiveMap

end Semantics.Testing.ErdosHarness

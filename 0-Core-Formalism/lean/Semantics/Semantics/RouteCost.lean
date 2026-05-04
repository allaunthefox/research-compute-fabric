namespace Semantics.RouteCost

/-!
# Equation Route Cost

Finite, Q16.16-scaled route scoring for the first compressed equation graph.
The JSON and CSV artifacts are serialization witnesses; this Lean module is the
source of truth for the edge-cost computation.
-/

abbrev Cost := UInt32

def qZero : Nat := 0
def qEighth : Nat := 8192
def qQuarter : Nat := 16384
def qHalf : Nat := 32768
def qOne : Nat := 65536

inductive FoundationKernel
  | f01 | f02 | f03 | f04 | f05 | f06 | f07 | f08 | f09 | f10 | f11 | f12
  deriving Repr, DecidableEq, BEq

inductive Street
  | entropyCompression
  | thermodynamicAdmissibility
  | geometricMotion
  | cognitiveRoutingLoad
  | diatAvmrS3cBridge
  deriving Repr, DecidableEq, BEq

inductive TopologyLayer
  | topologyState
  | rotationalAlignment
  | spatialProximity
  | completeCoupling
  | throatCondition
  | nonEuclideanRouteDistance
  deriving Repr, DecidableEq, BEq

inductive SubstrateStage
  | opcodeGas
  | witness
  | attest
  deriving Repr, DecidableEq, BEq

inductive ProofBurden
  | audited
  | formal
  | executable
  | empirical
  | unresolved
  deriving Repr, DecidableEq, BEq

inductive FailureRisk
  | low
  | medium
  | high
  deriving Repr, DecidableEq, BEq

inductive NodeRole
  | foundation
  | street
  | bridge
  | gwlTopology
  | fammMemory
  | substrate
  deriving Repr, DecidableEq, BEq

structure RouteNode where
  id : Nat
  code : String
  label : String
  role : NodeRole
  kernel : Option FoundationKernel
  street : Option Street
  topology : Option TopologyLayer
  substrate : Option SubstrateStage
  proof : ProofBurden
  risk : FailureRisk
  throat : Bool
  fammMemory : Bool
  deriving Repr

def FoundationKernel.index : FoundationKernel → Nat
  | .f01 => 1 | .f02 => 2 | .f03 => 3 | .f04 => 4
  | .f05 => 5 | .f06 => 6 | .f07 => 7 | .f08 => 8
  | .f09 => 9 | .f10 => 10 | .f11 => 11 | .f12 => 12

def FoundationKernel.street : FoundationKernel → Street
  | .f01 | .f02 | .f03 => .entropyCompression
  | .f04 | .f05 | .f06 | .f07 => .thermodynamicAdmissibility
  | .f08 | .f09 | .f10 => .geometricMotion
  | .f11 | .f12 => .cognitiveRoutingLoad

def TopologyLayer.index : TopologyLayer → Nat
  | .topologyState => 0
  | .rotationalAlignment => 1
  | .spatialProximity => 2
  | .completeCoupling => 3
  | .throatCondition => 4
  | .nonEuclideanRouteDistance => 5

def SubstrateStage.index : SubstrateStage → Nat
  | .opcodeGas => 0
  | .witness => 1
  | .attest => 2

def proofBurdenCost : ProofBurden → Nat
  | .audited => qZero
  | .formal => qEighth
  | .executable => qQuarter
  | .empirical => qHalf
  | .unresolved => qOne

def failureRiskCost : FailureRisk → Nat
  | .low => qZero
  | .medium => qQuarter
  | .high => qOne

def natAbsDiff (a b : Nat) : Nat :=
  if a < b then b - a else a - b

def optEq {α : Type} [BEq α] (a b : Option α) : Bool :=
  match a, b with
  | some x, some y => x == y
  | none, none => true
  | _, _ => false

def knownBridge (a b : Street) : Bool :=
  (a == .entropyCompression && b == .cognitiveRoutingLoad) ||
  (a == .cognitiveRoutingLoad && b == .entropyCompression) ||
  (a == .entropyCompression && b == .thermodynamicAdmissibility) ||
  (a == .thermodynamicAdmissibility && b == .entropyCompression) ||
  (a == .thermodynamicAdmissibility && b == .cognitiveRoutingLoad) ||
  (a == .cognitiveRoutingLoad && b == .thermodynamicAdmissibility) ||
  (a == .geometricMotion && b == .cognitiveRoutingLoad) ||
  (a == .cognitiveRoutingLoad && b == .geometricMotion) ||
  (a == .diatAvmrS3cBridge && b == .geometricMotion) ||
  (a == .geometricMotion && b == .diatAvmrS3cBridge) ||
  (a == .diatAvmrS3cBridge && b == .entropyCompression) ||
  (a == .entropyCompression && b == .diatAvmrS3cBridge)

def resolvedStreet (n : RouteNode) : Option Street :=
  match n.street, n.kernel with
  | some s, _ => some s
  | none, some k => some k.street
  | none, none => none

def kernelDistance (a b : RouteNode) : Nat :=
  if a.id == b.id then qZero else
  match a.kernel, b.kernel with
  | some x, some y =>
      if x == y then qZero
      else if x.street == y.street then qQuarter
      else qOne
  | none, none => qHalf
  | _, _ => qHalf

def streetTransitionCost (a b : RouteNode) : Nat :=
  if a.id == b.id then qZero else
  match resolvedStreet a, resolvedStreet b with
  | some x, some y =>
      if x == y then qZero
      else if knownBridge x y then qQuarter
      else qOne
  | none, none => qHalf
  | _, _ => qHalf

def gwlTopologyDistance (a b : RouteNode) : Nat :=
  if a.id == b.id then qZero else
  match a.topology, b.topology with
  | some x, some y =>
      let d := natAbsDiff x.index y.index
      if d == 0 then qZero else if d == 1 then qQuarter else qHalf
  | none, none => qZero
  | _, _ => qHalf

def substrateExecutionCost (a b : RouteNode) : Nat :=
  if a.id == b.id then qZero else
  match a.substrate, b.substrate with
  | some x, some y =>
      let d := natAbsDiff x.index y.index
      if d == 0 then qZero else if d == 1 then qEighth else qQuarter
  | none, none => qZero
  | _, _ => qHalf

def proofObligationCost (a b : RouteNode) : Nat :=
  if a.id == b.id then qZero else
  Nat.max (proofBurdenCost a.proof) (proofBurdenCost b.proof)

def failureRisk (a b : RouteNode) : Nat :=
  if a.id == b.id then qZero else
  Nat.max (failureRiskCost a.risk) (failureRiskCost b.risk)

def throatBonus (a b : RouteNode) : Nat :=
  if a.throat || b.throat then qHalf else qZero

def fammMemoryBonus (a b : RouteNode) : Nat :=
  if a.fammMemory && b.fammMemory then qHalf
  else if a.fammMemory || b.fammMemory then qQuarter
  else qZero

def weighted (weight component : Nat) : Nat :=
  (weight * component) / 100

def routeCostNat (a b : RouteNode) : Nat :=
  if a.id == b.id then qZero else
    let positive :=
      weighted 20 (kernelDistance a b) +
      weighted 14 (streetTransitionCost a b) +
      weighted 16 (gwlTopologyDistance a b) +
      weighted 12 (substrateExecutionCost a b) +
      weighted 14 (proofObligationCost a b) +
      weighted 14 (failureRisk a b)
    let bonus :=
      weighted 5 (throatBonus a b) +
      weighted 5 (fammMemoryBonus a b)
    positive - bonus

def routeCost (a b : RouteNode) : Cost :=
  UInt32.ofNat (routeCostNat a b)

def mkNode
    (id : Nat) (code label : String) (role : NodeRole)
    (kernel : Option FoundationKernel) (street : Option Street)
    (topology : Option TopologyLayer) (substrate : Option SubstrateStage)
    (proof : ProofBurden) (risk : FailureRisk)
    (throat fammMemory : Bool) : RouteNode :=
  { id, code, label, role, kernel, street, topology, substrate, proof, risk, throat, fammMemory }

def nF01 := mkNode 1 "F01" "Shannon_Entropy_Calculation" .foundation (some .f01) none none none .executable .low false false
def nF02 := mkNode 2 "F02" "Information_Content_Measurement" .foundation (some .f02) none none none .executable .low false false
def nF03 := mkNode 3 "F03" "Hierarchical_Entropy_Decomposition" .foundation (some .f03) none none none .formal .low false false
def nF04 := mkNode 4 "F04" "Thermodynamic_Efficiency_Limit" .foundation (some .f04) none none none .formal .low false false
def nF05 := mkNode 5 "F05" "Computation_Energy_Bound" .foundation (some .f05) none none none .formal .low false false
def nF06 := mkNode 6 "F06" "Energy_Balance_Threshold" .foundation (some .f06) none none none .executable .low false false
def nF07 := mkNode 7 "F07" "Maxwell_Demon_Recovery" .foundation (some .f07) none none none .formal .medium false false
def nF08 := mkNode 8 "F08" "Riemannian_Distance_Calculation" .foundation (some .f08) none none none .formal .low false false
def nF09 := mkNode 9 "F09" "Geodesic_Connection_Coefficients" .foundation (some .f09) none none none .formal .low false false
def nF10 := mkNode 10 "F10" "Single_Step_Geodesic_Integration" .foundation (some .f10) none none none .executable .low false false
def nF11 := mkNode 11 "F11" "Aggregate_Load_Combination" .foundation (some .f11) none none none .executable .low false false
def nF12 := mkNode 12 "F12" "Intrinsic_to_Total_Ratio" .foundation (some .f12) none none none .executable .low false false

def nS1 := mkNode 13 "S1" "Entropy_Compression_Street" .street none (some .entropyCompression) none none .formal .low false false
def nS2 := mkNode 14 "S2" "Thermodynamic_Admissibility_Street" .street none (some .thermodynamicAdmissibility) none none .formal .low false false
def nS3 := mkNode 15 "S3" "Geometric_Motion_Street" .street none (some .geometricMotion) none none .formal .low false false
def nS4 := mkNode 16 "S4" "Cognitive_Routing_Load_Street" .street none (some .cognitiveRoutingLoad) none none .formal .low false false
def nS5 := mkNode 17 "S5" "DIAT_AVMR_S3C_Bridge_Street" .street none (some .diatAvmrS3cBridge) none none .formal .low false false

def nB1 := mkNode 18 "B1" "Entropy_Load_Bridge" .bridge none (some .cognitiveRoutingLoad) none none .formal .low false false
def nB2 := mkNode 19 "B2" "Entropy_Landauer_Bridge" .bridge none (some .thermodynamicAdmissibility) none none .formal .low false false
def nB3 := mkNode 20 "B3" "Energy_Routing_Bridge" .bridge none (some .cognitiveRoutingLoad) none none .formal .low false false
def nB4 := mkNode 21 "B4" "Geometry_Routing_Bridge" .bridge none (some .geometricMotion) none none .formal .low false false
def nB5 := mkNode 22 "B5" "DIAT_Geometry_Bridge" .bridge none (some .diatAvmrS3cBridge) none none .formal .low false false
def nB6 := mkNode 23 "B6" "AVMR_Entropy_Bridge" .bridge none (some .diatAvmrS3cBridge) none none .formal .low false false
def nB7 := mkNode 24 "B7" "S3C_Codec_Bridge" .bridge none (some .diatAvmrS3cBridge) none none .formal .low false false
def nB8 := mkNode 25 "B8" "PIST_Surface_Bridge" .bridge none (some .diatAvmrS3cBridge) none none .formal .low false false

def nG0 := mkNode 26 "G00" "GWL_Topology_State" .gwlTopology none (some .diatAvmrS3cBridge) (some .topologyState) none .formal .low false false
def nF16 := mkNode 27 "F16" "Rotational_Alignment" .gwlTopology none (some .geometricMotion) (some .rotationalAlignment) none .executable .low false false
def nF17 := mkNode 28 "F17" "Spatial_Proximity" .gwlTopology none (some .geometricMotion) (some .spatialProximity) none .executable .low false false
def nF24 := mkNode 29 "F24" "Complete_Coupling_5Factor" .gwlTopology none (some .geometricMotion) (some .completeCoupling) none .formal .low false false
def nF34 := mkNode 30 "F34" "Throat_Condition" .gwlTopology none (some .diatAvmrS3cBridge) (some .throatCondition) none .formal .low true false
def nF37 := mkNode 31 "F37" "Non_Euclidean_Route_Distance" .gwlTopology none (some .geometricMotion) (some .nonEuclideanRouteDistance) none .formal .low false false

def nM1 := mkNode 32 "M01" "FAMM_Frustration_Memory" .fammMemory none (some .cognitiveRoutingLoad) none none .executable .low false true
def nM2 := mkNode 33 "M02" "Prior_Route_Pain" .fammMemory none (some .cognitiveRoutingLoad) none none .empirical .medium false true
def nM3 := mkNode 34 "M03" "Stable_Basin_Prior" .fammMemory none (some .cognitiveRoutingLoad) none none .empirical .low false true
def nM4 := mkNode 35 "M04" "Delay_Mass_Memory" .fammMemory none (some .geometricMotion) none none .executable .low false true
def nM5 := mkNode 36 "M05" "FAMM_Access_Bonus" .fammMemory none (some .cognitiveRoutingLoad) none none .executable .low false true

def nX1 := mkNode 37 "X01" "Topology_ISA_Opcode_Gas" .substrate none none none (some .opcodeGas) .executable .low false false
def nX2 := mkNode 38 "X02" "Substrate_VM_Witness" .substrate none none none (some .witness) .audited .low false false
def nX3 := mkNode 39 "X03" "Substrate_VM_Attestation" .substrate none none none (some .attest) .audited .low false false

def nodes : List RouteNode :=
  [ nF01, nF02, nF03, nF04, nF05, nF06, nF07, nF08, nF09, nF10, nF11, nF12
  , nS1, nS2, nS3, nS4, nS5
  , nB1, nB2, nB3, nB4, nB5, nB6, nB7, nB8
  , nG0, nF16, nF17, nF24, nF34, nF37
  , nM1, nM2, nM3, nM4, nM5
  , nX1, nX2, nX3
  ]

def exactishRoute : List RouteNode :=
  [ nF01, nF02, nF03, nB7, nB6, nS5, nF11, nF12, nG0, nF16, nF17, nF24, nF34, nF37
  , nM1, nM2, nM3, nM4, nM5, nX1, nX2, nX3
  , nB1, nS1, nB2, nF05, nF04, nS2, nF06, nF07, nB3
  , nB4, nS3, nF08, nF09, nF10, nB5, nB8, nS4
  ]

def roleName : NodeRole → String
  | .foundation => "foundation"
  | .street => "street"
  | .bridge => "bridge"
  | .gwlTopology => "gwl_topology"
  | .fammMemory => "famm_memory"
  | .substrate => "substrate"

def streetName : Street → String
  | .entropyCompression => "entropy_compression"
  | .thermodynamicAdmissibility => "thermodynamic_admissibility"
  | .geometricMotion => "geometric_motion"
  | .cognitiveRoutingLoad => "cognitive_routing_load"
  | .diatAvmrS3cBridge => "diat_avmr_s3c_bridge"

def proofName : ProofBurden → String
  | .audited => "audited"
  | .formal => "formal"
  | .executable => "executable"
  | .empirical => "empirical"
  | .unresolved => "unresolved"

def riskName : FailureRisk → String
  | .low => "low"
  | .medium => "medium"
  | .high => "high"

def optString (x : Option String) : String :=
  match x with
  | some s => "\"" ++ s ++ "\""
  | none => "null"

def kernelName : FoundationKernel → String
  | .f01 => "F01" | .f02 => "F02" | .f03 => "F03" | .f04 => "F04"
  | .f05 => "F05" | .f06 => "F06" | .f07 => "F07" | .f08 => "F08"
  | .f09 => "F09" | .f10 => "F10" | .f11 => "F11" | .f12 => "F12"

def topologyName : TopologyLayer → String
  | .topologyState => "gwl_topology_state"
  | .rotationalAlignment => "rotational_alignment"
  | .spatialProximity => "spatial_proximity"
  | .completeCoupling => "complete_coupling"
  | .throatCondition => "throat_condition"
  | .nonEuclideanRouteDistance => "non_euclidean_route_distance"

def substrateName : SubstrateStage → String
  | .opcodeGas => "opcode_gas"
  | .witness => "witness"
  | .attest => "attest"

def boolJson (b : Bool) : String :=
  if b then "true" else "false"

def nodeJson (n : RouteNode) : String :=
  "{" ++
  "\"id\":" ++ toString n.id ++ "," ++
  "\"code\":\"" ++ n.code ++ "\"," ++
  "\"label\":\"" ++ n.label ++ "\"," ++
  "\"role\":\"" ++ roleName n.role ++ "\"," ++
  "\"kernel\":" ++ optString (n.kernel.map kernelName) ++ "," ++
  "\"street\":" ++ optString ((resolvedStreet n).map streetName) ++ "," ++
  "\"topology\":" ++ optString (n.topology.map topologyName) ++ "," ++
  "\"substrate\":" ++ optString (n.substrate.map substrateName) ++ "," ++
  "\"proof\":\"" ++ proofName n.proof ++ "\"," ++
  "\"risk\":\"" ++ riskName n.risk ++ "\"," ++
  "\"throat\":" ++ boolJson n.throat ++ "," ++
  "\"famm_memory\":" ++ boolJson n.fammMemory ++
  "}"

def joinLines : List String → String
  | [] => ""
  | [x] => x
  | x :: xs => x ++ "\n" ++ joinLines xs

def matrixRowsFrom (left right : List RouteNode) : List String :=
  match left with
  | [] => []
  | a :: rest =>
      let rows := right.map fun b =>
        let c := routeCostNat a b
        a.code ++ "," ++ b.code ++ "," ++ toString c ++ "," ++ toString (c / 655) ++ "e-2"
      rows ++ matrixRowsFrom rest right

def csvMatrixRows : List String :=
  "from,to,cost_q16_16,cost_decimal_hint" :: matrixRowsFrom nodes nodes

def routeCodesJson (xs : List RouteNode) : String :=
  "[" ++ String.intercalate "," (xs.map fun n => "\"" ++ n.code ++ "\"") ++ "]"

def routeCostSum : List RouteNode → Nat
  | [] => 0
  | [_] => 0
  | a :: b :: rest => routeCostNat a b + routeCostSum (b :: rest)

def compressedSupernodesJson : String :=
  "{\n" ++
  "  \"foundation_kernels\": " ++ routeCodesJson [nF01,nF02,nF03,nF04,nF05,nF06,nF07,nF08,nF09,nF10,nF11,nF12] ++ ",\n" ++
  "  \"core_streets\": " ++ routeCodesJson [nS1,nS2,nS3,nS4,nS5] ++ ",\n" ++
  "  \"bridge_nodes\": " ++ routeCodesJson [nB1,nB2,nB3,nB4,nB5,nB6,nB7,nB8] ++ ",\n" ++
  "  \"gwl_topology\": " ++ routeCodesJson [nG0,nF16,nF17,nF24,nF34,nF37] ++ ",\n" ++
  "  \"famm_memory\": " ++ routeCodesJson [nM1,nM2,nM3,nM4,nM5] ++ ",\n" ++
  "  \"substrate_execution\": " ++ routeCodesJson [nX1,nX2,nX3] ++ "\n" ++
  "}\n"

def exactRouteJson : String :=
  "{\n" ++
  "  \"route_kind\": \"exactish_seed_route\",\n" ++
  "  \"node_count\": " ++ toString exactishRoute.length ++ ",\n" ++
  "  \"total_cost_q16_16\": " ++ toString (routeCostSum exactishRoute) ++ ",\n" ++
  "  \"route\": " ++ routeCodesJson exactishRoute ++ "\n" ++
  "}\n"

def localClusterRoutesJsonl : String :=
  joinLines [
    "{\"cluster\":\"foundation_kernels\",\"route\":" ++ routeCodesJson [nF01,nF02,nF03,nF11,nF12,nF08,nF09,nF10,nF04,nF05,nF06,nF07] ++ "}",
    "{\"cluster\":\"core_streets\",\"route\":" ++ routeCodesJson [nS1,nS5,nS4,nS3,nS2] ++ "}",
    "{\"cluster\":\"bridge_nodes\",\"route\":" ++ routeCodesJson [nB7,nB6,nB1,nB2,nB3,nB4,nB5,nB8] ++ "}",
    "{\"cluster\":\"gwl_topology\",\"route\":" ++ routeCodesJson [nG0,nF16,nF17,nF24,nF34,nF37] ++ "}",
    "{\"cluster\":\"famm_memory\",\"route\":" ++ routeCodesJson [nM1,nM2,nM3,nM4,nM5] ++ "}",
    "{\"cluster\":\"substrate_execution\",\"route\":" ++ routeCodesJson [nX1,nX2,nX3] ++ "}"
  ] ++ "\n"

def witnessReport : String :=
  "# Route Witness Report\n\n" ++
  "Scope: first compressed 39-node graph from the updated route-cost model.\n\n" ++
  "Cost model: D(i,j)=alpha*kernel + beta*street + gamma*GWL topology + delta*substrate + epsilon*proof + zeta*risk - eta*throat - theta*FAMM memory. All components are Q16.16-scaled UInt32 values computed in Lean.\n\n" ++
  "Recovered bridge test: entropy/compression enters routing through B7/B6, reaches F11/F12, crosses GWL topology through F16/F17/F24/F34/F37, then enters FAMM memory and substrate witness/attest.\n\n" ++
  "High-pain regions: empirical FAMM priors still carry medium risk; substrate entry remains costly when jumping directly from non-substrate nodes; thermodynamic nodes connect cleanly through B2/B3 but still need stronger Lean proof witnesses.\n\n" ++
  "Main road: " ++ String.intercalate " -> " (exactishRoute.map (fun n => n.code)) ++ "\n"

theorem routeCostTotal (a b : RouteNode) :
    ∃ c, routeCost a b = c := by
  exact ⟨routeCost a b, rfl⟩

theorem routeCostSelfZero (a : RouteNode) :
    routeCostNat a a = 0 := by
  unfold routeCostNat qZero
  simp

#eval (routeCost nF01 nF02).toNat -- expected: 5569
#eval (routeCost nF34 nF37).toNat -- expected: 10975

def writeArtifacts : IO Unit := do
  IO.FS.writeFile "../../../data/unified_equation_nodes.jsonl" (joinLines (nodes.map nodeJson) ++ "\n")
  IO.FS.writeFile "../../../data/unified_route_distance_matrix.csv" (joinLines csvMatrixRows ++ "\n")
  IO.FS.writeFile "../../../data/compressed_supernodes.json" compressedSupernodesJson
  IO.FS.writeFile "../../../data/exact_supernode_route.json" exactRouteJson
  IO.FS.writeFile "../../../data/local_cluster_routes.jsonl" localClusterRoutesJsonl
  IO.FS.writeFile "../../../data/route_witness_report.md" witnessReport

end Semantics.RouteCost

def main : IO Unit :=
  Semantics.RouteCost.writeArtifacts

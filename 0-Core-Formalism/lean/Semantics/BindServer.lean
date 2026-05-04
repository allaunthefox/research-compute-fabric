import Semantics.Bind
import Semantics.FixedPoint
import Semantics.Physics.Boundary
import Semantics.Physics.Conservation
import Semantics.Physics.BindPhysics
import Lean.Data.Json

namespace BindServer

open Lean Semantics Semantics.Physics

-- ============================================================================
-- JSON helpers
-- ============================================================================

def jsonObj (fields : List (String × Json)) : Json :=
  Json.mkObj fields

@[inline]
def q16_16_of_float (f : Float) : UInt32 :=
  if f.isNaN || f ≥ 32768.0 then 0xFFFFFFFF
  else if f ≤ -32768.0 then 0x80000000
  else (f * 65536.0).floor.toUInt32

@[inline]
def q16_16_to_float (u : UInt32) : Float :=
  let signed : Int := if u ≥ 0x80000000 then (Int.ofNat (u.toUInt64.toNat) - 0x100000000) else Int.ofNat (u.toUInt64.toNat)
  Float.ofInt signed / 65536.0

@[inline]
def jsonToQ16_16 (j : Json) : Except String Q16_16 :=
  match j.getNum? with
  | .ok n => .ok (Q16_16.ofFloat n.toFloat)
  | .error _ => match j.getInt? with
    | .ok n => .ok (Q16_16.ofInt n)
    | .error e => .error e

def parseQ16_16Dict (j : Json) : Except String (List (String × Q16_16)) := do
  let obj ← j.getObj?
  obj.toList.mapM (fun (k, v) => do let q ← jsonToQ16_16 v; return (k, q))

def parseQ16_16List (j : Json) : Except String (List Q16_16) := do
  let arr ← match j.getArr? with
    | .ok a => .ok a
    | .error _ => do
        let obj ← j.getObjVal? "state_vector"
        obj.getArr?
  arr.toList.mapM jsonToQ16_16

@[inline]
def parseString (j : Json) : Except String String :=
  j.getStr?

-- Quantity kind parsing
@[inline]
def parseQuantityKind (s : String) : QuantityKind :=
  match s with
  | "charge" => .charge
  | "mass" => .mass
  | "spin" => .spin
  | "energy" => .energy
  | "momentum" => .momentum
  | "baryonNumber" => .baryonNumber
  | "leptonNumber" => .leptonNumber
  | _ => .charge

-- Simplified particle kind aliases for the bridge API
@[inline]
def parseParticleKind (s : String) : Except String ParticleKind :=
  match s with
  | "electron" => .ok (.lepton .electron false)
  | "positron" => .ok (.lepton .electron true)
  | "photon" => .ok (.gauge .photon)
  | "proton" => .ok (.hadron .proton)
  | "neutron" => .ok (.hadron .neutron)
  | "neutrino" => .ok (.lepton .eNeutrino false)
  | "up_quark" => .ok (.quark .up .red false)
  | "down_quark" => .ok (.quark .down .blue false)
  | _ => .error s!"Unknown particle kind: {s}"

def parseQuantity (k : String) (v : Json) : Except String Quantity := do
  let n ← v.getInt?
  return { kind := parseQuantityKind k, value := n }

def parseQuantities (j : Json) : Except String (List Quantity) := do
  let obj ← j.getObj?
  obj.toList.mapM (fun (k, v) => parseQuantity k v)

def parseParticle (j : Json) : Except String Particle := do
  let kindJson ← j.getObjVal? "kind"
  let kindStr ← parseString kindJson
  let kind ← parseParticleKind kindStr
  let quantities ← match j.getObjVal? "quantities" with
    | .ok q => parseQuantities q
    | .error _ => .ok []
  return { kind := kind, quantities := quantities }

def parseParticles (j : Json) : Except String (List Particle) := do
  -- Allow either a direct array or {"particles": [...]}
  let arr ← match j.getArr? with
    | .ok a => .ok a
    | .error _ => do
        let obj ← j.getObjVal? "particles"
        obj.getArr?
  arr.toList.mapM parseParticle

-- Float fallback: try JsonNumber first, then Int
@[inline]
def jsonToFloat (j : Json) : Except String Float :=
  match j.getNum? with
  | .ok n => .ok n.toFloat
  | .error _ => match j.getInt? with
    | .ok n => .ok (Float.ofInt n)
    | .error e => .error e

def parseFloatDict (j : Json) : Except String (List (String × Float)) := do
  let obj ← j.getObj?
  obj.toList.mapM (fun (k, v) => do let f ← jsonToFloat v; return (k, f))

def parseFloatList (j : Json) : Except String (List Float) := do
  -- Allow either a direct array or {"state_vector": [...]}
  let arr ← match j.getArr? with
    | .ok a => .ok a
    | .error _ => do
        let obj ← j.getObjVal? "state_vector"
        obj.getArr?
  arr.toList.mapM jsonToFloat

-- ============================================================================
-- Cost functions implemented in Lean (Q16.16 fixed-point)
-- ============================================================================

@[inline]
def euclideanCost (left right : List Q16_16) : UInt32 :=
  let n := max left.length right.length
  let a := left ++ List.replicate (n - left.length) Q16_16.zero
  let b := right ++ List.replicate (n - right.length) Q16_16.zero
  let sumSq := (List.zip a b).foldl (fun acc (x, y) => Q16_16.add acc (Q16_16.mul (Q16_16.sub x y) (Q16_16.sub x y))) Q16_16.zero
  (Q16_16.sqrt sumSq).val

@[inline]
def klCost (left right : List (String × Float)) : UInt32 :=
  -- log requires fixed-point lookup table or series expansion.
  -- Keeping Float computation until Q16.16 log is implemented.
  let total := left.foldl (fun acc (k, p) =>
    let q := match right.lookup k with | some v => v | none => 1e-12
    if p > 0.0 then acc + p * (Float.log (p / max q 1e-12)) else acc
  ) 0.0
  q16_16_of_float total

@[inline]
def thermodynamicCost (left right :List (String × Q16_16)) : UInt32 :=
  let entropyL := match left.lookup "entropy" with | some v => v | none => Q16_16.zero
  let entropyR := match right.lookup "entropy" with | some v => v | none => Q16_16.zero
  let temp := match left.lookup "temperature" with | some v => v | none => Q16_16.ofNat 300
  let deltaS := Q16_16.sub entropyL entropyR
  let kB := Q16_16.ofFloat 8.617e-5  -- Boltzmann constant in Q16.16
  (Q16_16.abs (Q16_16.mul (Q16_16.mul deltaS temp) kB)).val

@[inline]
def controlCost (left right : List (String × Q16_16)) : UInt32 :=
  let obs := match left.lookup "observation" with | some v => v | none => Q16_16.zero
  let target := match right.lookup "setpoint" with | some v => v | none => Q16_16.zero
  (Q16_16.abs (Q16_16.sub obs target)).val

@[inline]
def geodesicCost (left right : List Q16_16) (metric : Metric) : UInt32 :=
  if metric.tensor == "identity" then
    euclideanCost left right
  else
    let n := max left.length right.length
    let a := left ++ List.replicate (n - left.length) Q16_16.zero
    let b := right ++ List.replicate (n - right.length) Q16_16.zero
    let scale := Q16_16.add Q16_16.one ⟨metric.cost⟩
    let torsionPenalty := Q16_16.mul ⟨metric.torsion⟩ (Q16_16.ofFloat (3.1415926535 / 8.0))
    let indices := List.range a.length
    let dist := (List.zip a indices).foldl (fun acc (x, i) =>
      let y := b.getD i Q16_16.zero
      let delta := Q16_16.mul (Q16_16.sub x y) scale
      let torsion := Q16_16.mul torsionPenalty (Q16_16.sin (Q16_16.ofInt i))
      Q16_16.add acc (Q16_16.add (Q16_16.mul delta delta) (Q16_16.mul torsion torsion))
    ) Q16_16.zero
    (Q16_16.sqrt dist).val

-- ============================================================================
-- Request / Response
-- ============================================================================

instance : Lean.FromJson UInt32 where
  fromJson? j := match j.getNat? with | .ok n => .ok n.toUInt32 | .error e => .error e

instance : Lean.ToJson UInt32 where
  toJson u := Json.num (Lean.JsonNumber.fromNat u.toNat)

structure BindRequest where
  metricKind : String
  left : Json
  right : Json
  useHistory : Bool := false
  historyLen : Nat := 0
  historyCost : UInt32 := 0x00000000
  historyTorsion : UInt32 := 0x00000000
deriving FromJson, ToJson

structure BindResponse where
  cost : UInt32
  lawful : Bool
  leftInvariant : String
  rightInvariant : String
  traceHash : String
  metricTensor : String
  metricTorsion : UInt32
  metricHistoryLen : Nat
deriving ToJson

@[inline]
def buildMetric (req : BindRequest) : Metric :=
  if req.useHistory && req.historyLen >= 2 then
    { cost := req.historyCost, tensor := req.metricKind, torsion := req.historyTorsion, reference := s!"nlocal_from_{req.historyLen}_binds", history_len := req.historyLen }
  else
    { cost := 0x00000000, tensor := req.metricKind, torsion := 0x00000000, reference := "euclidean_baseline", history_len := req.historyLen }

@[inline]
def genericInvariant (j : Json) : String :=
  j.compress

-- ============================================================================
-- Handlers
-- ============================================================================

def handlePhysical (req : BindRequest) : Except String BindResponse := do
  let leftParticles ← parseParticles req.left
  let rightParticles ← parseParticles req.right
  let metric := buildMetric req
  let invL := particleInvariant leftParticles
  let invR := particleInvariant rightParticles
  let b := physicalBindEval leftParticles rightParticles metric
  return {
    cost := b.cost,
    lawful := b.lawful,
    leftInvariant := invL,
    rightInvariant := invR,
    traceHash := b.witness.trace_hash,
    metricTensor := metric.tensor,
    metricTorsion := metric.torsion,
    metricHistoryLen := metric.history_len
  }

def handleInformational (req : BindRequest) : Except String BindResponse := do
  let leftDict ← parseFloatDict req.left
  let rightDict ← parseFloatDict req.right
  let metric := buildMetric req
  let cost := klCost leftDict rightDict
  let invL := genericInvariant req.left
  let invR := genericInvariant req.right
  let lawful := invL == invR
  return {
    cost := cost,
    lawful := lawful,
    leftInvariant := invL,
    rightInvariant := invR,
    traceHash := if lawful then s!"lawful:{invL}={invR}" else "unlawful",
    metricTensor := metric.tensor,
    metricTorsion := metric.torsion,
    metricHistoryLen := metric.history_len
  }

def handleGeometric (req : BindRequest) : Except String BindResponse := do
  let leftVec ← parseQ16_16List req.left
  let rightVec ← parseQ16_16List req.right
  let metric := buildMetric req
  let cost := geodesicCost leftVec rightVec metric
  let invL := genericInvariant req.left
  let invR := genericInvariant req.right
  let lawful := invL == invR
  return {
    cost := cost,
    lawful := lawful,
    leftInvariant := invL,
    rightInvariant := invR,
    traceHash := if lawful then s!"lawful:{invL}={invR}" else "unlawful",
    metricTensor := metric.tensor,
    metricTorsion := metric.torsion,
    metricHistoryLen := metric.history_len
  }

def handleThermodynamic (req : BindRequest) : Except String BindResponse := do
  let leftDict ← parseQ16_16Dict req.left
  let rightDict ← parseQ16_16Dict req.right
  let metric := buildMetric req
  let cost := thermodynamicCost leftDict rightDict
  let invL := genericInvariant req.left
  let invR := genericInvariant req.right
  let lawful := invL == invR
  return {
    cost := cost,
    lawful := lawful,
    leftInvariant := invL,
    rightInvariant := invR,
    traceHash := if lawful then s!"lawful:{invL}={invR}" else "unlawful",
    metricTensor := metric.tensor,
    metricTorsion := metric.torsion,
    metricHistoryLen := metric.history_len
  }

def handleControl (req : BindRequest) : Except String BindResponse := do
  let leftDict ← parseQ16_16Dict req.left
  let rightDict ← parseQ16_16Dict req.right
  let metric := buildMetric req
  let cost := controlCost leftDict rightDict
  let invL := genericInvariant req.left
  let invR := genericInvariant req.right
  let lawful := invL == invR
  return {
    cost := cost,
    lawful := lawful,
    leftInvariant := invL,
    rightInvariant := invR,
    traceHash := if lawful then s!"lawful:{invL}={invR}" else "unlawful",
    metricTensor := metric.tensor,
    metricTorsion := metric.torsion,
    metricHistoryLen := metric.history_len
  }

def handleRequest (req : BindRequest) : Except String BindResponse :=
  match req.metricKind with
  | "physical" => handlePhysical req
  | "informational" => handleInformational req
  | "geometric" | "riemannian" => handleGeometric req
  | "thermodynamic" => handleThermodynamic req
  | "control" => handleControl req
  | _ => .error s!"Unknown metric kind: {req.metricKind}"

-- ============================================================================
-- Batch handlers
-- ============================================================================

structure BindBatchRequest where
  requests : List BindRequest
deriving FromJson

structure BindBatchResponse where
  results : List BindResponse
deriving ToJson

def handleBatchRequest (req : BindBatchRequest) : BindBatchResponse :=
  { results := req.requests.map (fun r => match handleRequest r with | .ok resp => resp | .error e => {
      cost := 0xFFFFFFFF,
      lawful := false,
      leftInvariant := "",
      rightInvariant := "",
      traceHash := s!"error:{e}",
      metricTensor := "",
      metricTorsion := 0x00000000,
      metricHistoryLen := 0
    }) }

-- ============================================================================
-- I/O Loop
-- ============================================================================

partial def serve : IO Unit := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  let line ← stdin.getLine
  if line.isEmpty || line == "\n" then
    return ()
  match Json.parse line with
  | .error e =>
    stdout.putStrLn (Json.compress (jsonObj [("error", Json.str e)]))
    stdout.flush
  | .ok j =>
    -- Dispatch: if "requests" field exists, treat as batch; else single
    let isBatch := match j.getObjVal? "requests" with | .ok _ => true | .error _ => false
    if isBatch then
      match fromJson? j with
      | .error e =>
        stdout.putStrLn (Json.compress (jsonObj [("error", Json.str e)]))
        stdout.flush
      | .ok batchReq =>
        let batchResp := handleBatchRequest batchReq
        stdout.putStrLn (Json.compress (toJson batchResp))
        stdout.flush
    else
      match fromJson? j with
      | .error e =>
        stdout.putStrLn (Json.compress (jsonObj [("error", Json.str e)]))
        stdout.flush
      | .ok req =>
        match handleRequest req with
        | .error e =>
          stdout.putStrLn (Json.compress (jsonObj [("error", Json.str e)]))
          stdout.flush
        | .ok resp =>
          stdout.putStrLn (Json.compress (toJson resp))
          stdout.flush
  serve

end BindServer

def main : IO Unit := BindServer.serve

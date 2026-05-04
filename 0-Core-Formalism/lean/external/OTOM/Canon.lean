import Semantics.FixedPoint

namespace Semantics

/-! # Canonical State
Ported from `infra/access_control/core/canonical_state.py`.
Unified state representation for the control system.
All scalar fields use Q16_16 fixed-point per Commandment IV.

Historical note on semantic values
----------------------------------
Earlier ENE/PBACS-era modules did not treat semantic values as free-form labels,
embeddings, or open-text annotations. They treated them as bounded projection
coordinates derived from lawful comparison between:

- raw observation,
- projected target state, and
- current internal state.

In practice this meant that meaning appeared as compact operational fields such
as mismatch, curvature, tension, coherence, gain, cost, and reliability. The
older adapter family repeatedly expressed these as stable coordinates like:

- `u_phi`      semantic margin / actionable alignment,
- `u_delta`    state-target mismatch,
- `u_delta_dot` change in mismatch,
- `u_gamma`    second-order temporal curvature,
- `u_tau`      hazard / tension / burden,
- `u_chi`      productive coherence under constraint,
- `u_gain`     opportunity or expected upside,
- `u_cost`     friction or burden,
- `u_bias`     trust / reliability prior,
- `u_blink`    urgency or pacing surface.

So the semantic value was not "what the symbol means" in isolation. It was the
position of a system inside a bounded semantic field that could be:

- measured,
- updated,
- packed into canonical coordinates, and
- used for control or assignment.

The canonical layer therefore preserves an older design commitment:
semantic value should be represented as lawful, bounded, reusable coordinates
before it is represented as narrative description.
-/

/-- Unified control states across PBACS and RegimeTracker. -/
inductive ControlState
  | commit
  | hold
  | halt
  | dmt      -- Dimensionally Mismatched Throat
  | flame    -- Extreme emergency state
deriving Repr, BEq, DecidableEq

/-- PBACS projection export. -/
structure PbacsProjections where
  uPhi      : Q16_16
  uPsi      : Q16_16
  uDelta    : Q16_16
  uGamma    : Q16_16
  uChi      : Q16_16
  uTau      : Q16_16
  uDeltaDot : Q16_16
  uBlink    : Q16_16
deriving Repr, BEq

/-- RegimeTracker observable export. -/
structure RegimeTrackerObservables where
  phi          : Q16_16
  psi          : Q16_16
  delta        : Q16_16
  fieldStrain  : Q16_16
  chi          : Q16_16
  torsion      : Q16_16
  gapVelocity  : Q16_16
deriving Repr, BEq

/-- Geometry feature export. -/
structure GeometryFeatures where
  angularDrift      : Q16_16
  curvature         : Q16_16
  coherence         : Q16_16
  angularMomentum   : Q16_16
  radiusDev         : Q16_16
deriving Repr, BEq

/-- Unified representation of control system state. -/
structure CanonicalState where
  phi           : Q16_16
  psi           : Q16_16
  delta         : Q16_16
  gamma         : Q16_16
  chi           : Q16_16
  tau           : Q16_16
  deltaDot      : Q16_16
  drift         : Q16_16
  curvature     : Q16_16
  coherence     : Q16_16
  angularMomentum : Q16_16
  radiusDev     : Q16_16
  confidence    : Q16_16
  mode          : ControlState
  timestamp     : UInt64
  step          : Nat
  domain        : String
  source        : String
deriving Repr, BEq

namespace CanonicalState

instance : Inhabited CanonicalState where
  default := {
    phi := Q16_16.zero, psi := Q16_16.zero, delta := Q16_16.zero,
    gamma := Q16_16.zero, chi := Q16_16.zero, tau := Q16_16.zero,
    deltaDot := Q16_16.zero, drift := Q16_16.zero,
    curvature := Q16_16.zero, coherence := Q16_16.one,
    angularMomentum := Q16_16.zero, radiusDev := Q16_16.zero,
    confidence := Q16_16.one, mode := ControlState.commit,
    timestamp := 0, step := 0, domain := "generic", source := "unknown"
  }

def default : CanonicalState := {
  phi := Q16_16.zero, psi := Q16_16.zero, delta := Q16_16.zero,
  gamma := Q16_16.zero, chi := Q16_16.zero, tau := Q16_16.zero,
  deltaDot := Q16_16.zero, drift := Q16_16.zero,
  curvature := Q16_16.zero, coherence := Q16_16.one,
  angularMomentum := Q16_16.zero, radiusDev := Q16_16.zero,
  confidence := Q16_16.one, mode := ControlState.commit,
  timestamp := 0, step := 0, domain := "generic", source := "unknown"
}

/-- Compute confidence from geometry: 1 / (1 + drift * curvature + angularMomentum), clamped to [0,1]. -/
def computeConfidence (drift curvature angularMomentum : Q16_16) : Q16_16 :=
  let denom := Q16_16.add (Q16_16.add Q16_16.one (Q16_16.mul drift curvature)) angularMomentum
  let raw := Q16_16.div Q16_16.one denom
  Q16_16.max Q16_16.zero (Q16_16.min Q16_16.one raw)

/-- Smart constructor that recomputes confidence when the default is used and geometry is non-trivial. -/
def mk'
  (phi psi delta gamma chi tau deltaDot drift curvature coherence
   angularMomentum radiusDev confidence : Q16_16)
  (mode : ControlState)
  (timestamp : UInt64) (step : Nat) (domain source : String) :
  CanonicalState :=
  let computedConfidence :=
    if confidence == Q16_16.one && (Q16_16.toInt drift > 0 || Q16_16.toInt curvature > 0) then
      computeConfidence drift curvature angularMomentum
    else
      confidence
  {
    phi := phi, psi := psi, delta := delta, gamma := gamma,
    chi := chi, tau := tau, deltaDot := deltaDot, drift := drift,
    curvature := curvature, coherence := coherence,
    angularMomentum := angularMomentum, radiusDev := radiusDev,
    confidence := computedConfidence, mode := mode,
    timestamp := timestamp, step := step, domain := domain,
    source := source
  }

def toPbacsProjections (s : CanonicalState) : PbacsProjections := {
  uPhi := s.phi, uPsi := s.psi, uDelta := s.delta, uGamma := s.gamma,
  uChi := s.chi, uTau := s.tau, uDeltaDot := s.deltaDot,
  uBlink := Q16_16.max s.delta (Q16_16.abs s.deltaDot)
}

def toPbacsProjectionsList (s : CanonicalState) : List (String × Q16_16) :=
  let p := toPbacsProjections s
  [
    ("u_phi", p.uPhi), ("u_psi", p.uPsi), ("u_delta", p.uDelta),
    ("u_gamma", p.uGamma), ("u_chi", p.uChi), ("u_tau", p.uTau),
    ("u_delta_dot", p.uDeltaDot), ("u_blink", p.uBlink)
  ]

def toRegimeTrackerObservables (s : CanonicalState) : RegimeTrackerObservables := {
  phi := s.phi, psi := s.psi, delta := s.delta,
  fieldStrain := s.gamma, chi := s.chi, torsion := s.tau,
  gapVelocity := s.deltaDot
}

def toGeometryFeatures (s : CanonicalState) : GeometryFeatures := {
  angularDrift := s.drift, curvature := s.curvature,
  coherence := s.coherence, angularMomentum := s.angularMomentum,
  radiusDev := s.radiusDev
}

def fromPbacsProjections (p : PbacsProjections) (mode : ControlState)
  (timestamp : UInt64) (step : Nat) (domain source : String) : CanonicalState :=
  mk' p.uPhi p.uPsi p.uDelta p.uGamma p.uChi p.uTau p.uDeltaDot
    Q16_16.zero Q16_16.zero Q16_16.one Q16_16.zero Q16_16.zero
    Q16_16.one mode timestamp step domain source

def fromGeometryFeatures (g : GeometryFeatures) (mode : ControlState)
  (timestamp : UInt64) (step : Nat) (domain source : String) : CanonicalState :=
  mk' Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero
    g.angularDrift g.curvature g.coherence g.angularMomentum g.radiusDev
    Q16_16.one mode timestamp step domain source

/-- Stable when mode is COMMIT and delta < 0.3. -/
def isStable (s : CanonicalState) : Bool :=
  s.mode == ControlState.commit && Q16_16.lt s.delta (Q16_16.div (Q16_16.ofInt 3) (Q16_16.ofInt 10))

/-- Critical when mode is HALT or FLAME. -/
def isCritical (s : CanonicalState) : Bool :=
  s.mode == ControlState.halt || s.mode == ControlState.flame

/-- Default state is stable because delta = 0 < 0.3 and mode = COMMIT. -/
theorem defaultIsStable : CanonicalState.default.isStable = true := by
  native_decide

end CanonicalState

/-- Legacy canonical adapter normalization modes recovered from earlier ENE schema forms. -/
inductive NormalizationMode
  | minmax
  | centered
  | passthrough
deriving Repr, BEq, DecidableEq

/-- Fixed-point feature contract for raw inputs at the canonical adapter boundary. -/
structure RawFeatureSpec where
  name : String
  mode : NormalizationMode
  low : Q16_16 := Q16_16.zero
  high : Q16_16 := Q16_16.one
  required : Bool := true
deriving Repr, BEq

/-- Canonical coordinates that may be packed into a stable ENE vector. -/
inductive CanonicalDimension
  | phi
  | psi
  | delta
  | gamma
  | chi
  | tau
  | deltaDot
  | drift
  | curvature
  | coherence
  | angularMomentum
  | radiusDev
  | confidence
deriving Repr, BEq, DecidableEq

/-- Recover the scalar value for a named canonical dimension. -/
def CanonicalDimension.read (d : CanonicalDimension) (state : CanonicalState) : Q16_16 :=
  match d with
  | .phi => state.phi
  | .psi => state.psi
  | .delta => state.delta
  | .gamma => state.gamma
  | .chi => state.chi
  | .tau => state.tau
  | .deltaDot => state.deltaDot
  | .drift => state.drift
  | .curvature => state.curvature
  | .coherence => state.coherence
  | .angularMomentum => state.angularMomentum
  | .radiusDev => state.radiusDev
  | .confidence => state.confidence

/-- Ordered vector specification recovered from the older canonical adapter packer. -/
structure CanonicalVectorSpec where
  dimensions : List CanonicalDimension := [
    .phi, .psi, .delta, .gamma, .chi, .tau, .deltaDot,
    .drift, .curvature, .coherence, .angularMomentum, .radiusDev, .confidence
  ]
deriving Repr, BEq

/-- Pack a canonical state into a stable vector according to the chosen dimension order. -/
def CanonicalVectorSpec.pack (spec : CanonicalVectorSpec) (state : CanonicalState) : List Q16_16 :=
  spec.dimensions.map (fun dim => dim.read state)

/-- Named attractor recovered from the earlier canonical adapter assignment schema. -/
structure CanonicalAttractor where
  name : String
  center : List Q16_16
  maxRadius : Option Q16_16 := none
deriving Repr, BEq

/-- Quantized band assignment for a packed canonical dimension. -/
structure QuantizedBand where
  dimension : CanonicalDimension
  band : Nat
deriving Repr, BEq

/-- Result of assigning a packed canonical vector to an attractor/signature surface. -/
structure AssignmentResult where
  zN : List Q16_16
  nearestAttractor : Option String
  attractorDistance : Option Q16_16
  attractorConfidence : Q16_16
  signature : List Nat
  quantizedBands : List QuantizedBand
  consistent : Bool
deriving Repr, BEq

/-- Clamp a fixed-point scalar into a closed interval. -/
def clampQ16 (value low high : Q16_16) : Q16_16 :=
  Q16_16.max low (Q16_16.min high value)

/-- Normalize a raw feature using the recovered legacy adapter modes, now in Q16.16. -/
def normalizeFeatureValue (spec : RawFeatureSpec) (raw : Q16_16) : Q16_16 :=
  match spec.mode with
  | .passthrough => raw
  | .minmax =>
      let span := Q16_16.sub spec.high spec.low
      let shifted := Q16_16.sub raw spec.low
      clampQ16 (Q16_16.div shifted span) Q16_16.zero Q16_16.one
  | .centered =>
      let midpoint := Q16_16.div (Q16_16.add spec.low spec.high) (Q16_16.ofInt 2)
      let halfSpan := Q16_16.div (Q16_16.sub spec.high spec.low) (Q16_16.ofInt 2)
      let shifted := Q16_16.sub raw midpoint
      let lower := Q16_16.neg Q16_16.one
      clampQ16 (Q16_16.div shifted halfSpan) lower Q16_16.one

/-- Witness: an explicitly empty vector spec packs no coordinates. -/
theorem emptyCanonicalVectorWidth :
  ({ dimensions := [] } : CanonicalVectorSpec).dimensions.length = 0 := by
  native_decide

/-- Witness: the inhabited default spec exposes the historical 13-coordinate pack. -/
theorem defaultCanonicalPackLength :
  ((({} : CanonicalVectorSpec).pack CanonicalState.default).length) = 13 := by
  native_decide

/-- Witness: minmax normalization sends the lower bound to zero. -/
theorem minmaxNormalizationHitsZero :
  normalizeFeatureValue
    { name := "temperature", mode := .minmax, low := Q16_16.ofInt 10, high := Q16_16.ofInt 20 }
    (Q16_16.ofInt 10) = Q16_16.zero := by
  native_decide

end Semantics

namespace Semantics.ENE

-- Canonical Adapter / Normalization Layer
--
-- Converts raw inputs into deterministic, semantically bounded canonical forms.
-- This layer prevents "weird machines via inputs" by:
--   1. Normalizing representation (endianness, field order, encoding)
--   2. Filtering adversarial or irrelevant structure
--   3. Certifying determinism via proof

/-- Endianness policy for canonical serialization. -/
inductive EndianPolicy
| big
| little
| host
deriving Repr, BEq

/-- Bit ordering for canonical serialization. -/
inductive BitOrder
| msb0
| lsb0
deriving Repr, BEq

/-- The canonical policy is big-endian, msb0. -/
def canonicalEndian : EndianPolicy := EndianPolicy.big

def canonicalBitOrder : BitOrder := BitOrder.msb0

/-- Kinds of fields in a canonical record. -/
inductive FieldKind
| int (bits : Nat) (signed : Bool)
| nat (bits : Nat)
| q16_16
| float64
| text
| bool
| blob (size : Nat)
deriving Repr, BEq

/-- Specification for a single field. -/
structure FieldSpec where
  name : String
  kind : FieldKind
  required : Bool := true

deriving Repr, BEq

/-- A schema defining the canonical shape of a record. -/
structure RecordSchema where
  name : String
  fields : List FieldSpec
  endian : EndianPolicy := canonicalEndian
  bitOrder : BitOrder := canonicalBitOrder

deriving Repr, BEq

/-- A value in canonical form. -/
inductive CanonicalValue
| int (i : Int) (bits : Nat) (signed : Bool)
| nat (n : Nat) (bits : Nat)
| q16_16 (q : Q16_16)
| float64 (f : Float)
| text (s : String)
| bool (b : Bool)
| blob (b : ByteArray)
deriving BEq

/-- A field with its canonical value. -/
structure CanonicalField where
  spec : FieldSpec
  value : CanonicalValue

deriving BEq

/-- The complete canonical binary representation of a record. -/
structure CanonicalBinaryForm where
  schema : RecordSchema
  fields : List CanonicalField

deriving BEq

/-- Source information tracking provenance. -/
structure SourceInfo where
  origin : String
  timestamp : UInt64
  trustLevel : Float -- TODO(lean-port): port to Q16_16

deriving Repr, BEq

/-- Errors that can occur during normalization. -/
inductive NormalizeError
| typeMismatch (expected : String) (actual : String)
| overflow (value : String) (limit : String)
| missingRequiredField (name : String)
| adversarialStructure (reason : String)
| unsupportedEncoding (details : String)
deriving Repr, BEq

abbrev NormalizeResult (α : Type) := Except NormalizeError α

/-- Source values before normalization. -/
inductive SourceValue
| int (i : Int)
| nat (n : Nat)
| q16_16 (q : Q16_16)
| float64 (f : Float)
| text (s : String)
| bool (b : Bool)
| blob (b : ByteArray)
| null
deriving BEq

/-- A field in its source form. -/
structure SourceField where
  name : String
  value : SourceValue

deriving BEq

-- Serialization helpers

def pushByte (out : ByteArray) (b : UInt8) : ByteArray := out.push b

def encodeU16BE (x : UInt16) : ByteArray :=
  let b0 := UInt8.ofNat ((x.toNat >>> 8) &&& 0xFF)
  let b1 := UInt8.ofNat (x.toNat &&& 0xFF)
  ByteArray.empty.push b0 |>.push b1

def encodeU32BE (x : UInt32) : ByteArray :=
  let b0 := UInt8.ofNat ((x.toNat >>> 24) &&& 0xFF)
  let b1 := UInt8.ofNat ((x.toNat >>> 16) &&& 0xFF)
  let b2 := UInt8.ofNat ((x.toNat >>> 8) &&& 0xFF)
  let b3 := UInt8.ofNat (x.toNat &&& 0xFF)
  ByteArray.empty.push b0 |>.push b1 |>.push b2 |>.push b3

def encodeU64BE (x : UInt64) : ByteArray :=
  let b0 := UInt8.ofNat ((x.toNat >>> 56) &&& 0xFF)
  let b1 := UInt8.ofNat ((x.toNat >>> 48) &&& 0xFF)
  let b2 := UInt8.ofNat ((x.toNat >>> 40) &&& 0xFF)
  let b3 := UInt8.ofNat ((x.toNat >>> 32) &&& 0xFF)
  let b4 := UInt8.ofNat ((x.toNat >>> 24) &&& 0xFF)
  let b5 := UInt8.ofNat ((x.toNat >>> 16) &&& 0xFF)
  let b6 := UInt8.ofNat ((x.toNat >>> 8) &&& 0xFF)
  let b7 := UInt8.ofNat (x.toNat &&& 0xFF)
  ByteArray.empty.push b0 |>.push b1 |>.push b2 |>.push b3 |>.push b4 |>.push b5 |>.push b6 |>.push b7

def encodeNatBE (width : Nat) (n : Nat) : ByteArray :=
  let rec loop (i : Nat) (acc : ByteArray) : ByteArray :=
    match i with
    | 0 => acc
    | i' + 1 =>
        let byte := UInt8.ofNat ((n >>> (8 * i')) &&& 0xFF)
        loop i' (acc.push byte)
  loop width ByteArray.empty

def encodeText (s : String) : ByteArray :=
  s.toUTF8

def fieldKindTag (k : FieldKind) : UInt8 :=
  match k with
  | FieldKind.int _ _ => 1
  | FieldKind.nat _   => 2
  | FieldKind.q16_16  => 3
  | FieldKind.float64 => 4
  | FieldKind.text    => 5
  | FieldKind.bool    => 6
  | FieldKind.blob _  => 7

def intFitsSigned (bits : Nat) (i : Int) : Bool :=
  let limit := 1 <<< (bits - 1)
  i ≥ -limit && i < limit

def serializeCanonicalValue (v : CanonicalValue) : NormalizeResult ByteArray :=
  match v with
  | CanonicalValue.int i bits signed =>
      if signed then
        if intFitsSigned bits i then
          .ok (encodeNatBE bits (if i < 0 then (1 <<< bits) + i.toNat else i.toNat))
        else
          .error (NormalizeError.overflow (toString i) ("int" ++ toString bits))
      else
        if i ≥ 0 && i < (1 <<< bits : Int) then
          .ok (encodeNatBE bits i.toNat)
        else
          .error (NormalizeError.overflow (toString i) ("uint" ++ toString bits))
  | CanonicalValue.nat n bits =>
      if n < (1 <<< bits) then
        .ok (encodeNatBE bits n)
      else
        .error (NormalizeError.overflow (toString n) ("uint" ++ toString bits))
  | CanonicalValue.q16_16 q =>
      .ok (encodeU32BE q.val)
  | CanonicalValue.float64 f =>
      .ok (encodeU64BE (Float.toUInt64 f))
  | CanonicalValue.text s =>
      .ok (encodeText s)
  | CanonicalValue.bool true =>
      .ok (ByteArray.empty.push 1)
  | CanonicalValue.bool false =>
      .ok (ByteArray.empty.push 0)
  | CanonicalValue.blob b =>
      .ok b

def serializeField (f : CanonicalField) : NormalizeResult ByteArray := do
  let tag := ByteArray.empty.push (fieldKindTag f.spec.kind)
  let nameBytes := encodeText f.spec.name
  let nameLen := encodeU32BE nameBytes.size.toUInt32
  let valueBytes ← serializeCanonicalValue f.value
  .ok (tag ++ nameLen ++ nameBytes ++ valueBytes)

def magicHeader : ByteArray :=
  encodeText "CANON1"

def serializeCanonicalBinaryForm (cbf : CanonicalBinaryForm) : NormalizeResult ByteArray := do
  let schemaName := encodeText cbf.schema.name
  let schemaLen := encodeU32BE schemaName.size.toUInt32
  let fieldBytes ← cbf.fields.mapM serializeField
  let body := fieldBytes.foldl (fun acc b => acc ++ b) ByteArray.empty
  .ok (magicHeader ++ schemaLen ++ schemaName ++ body)

-- Matching and normalization

def findField? (name : String) (xs : List SourceField) : Option SourceField :=
  xs.find? (λ f => f.name == name)

def fieldKindToString : FieldKind → String
| FieldKind.int bits signed => "int" ++ toString bits ++ (if signed then "s" else "u")
| FieldKind.nat bits => "nat" ++ toString bits
| FieldKind.q16_16 => "q16_16"
| FieldKind.float64 => "float64"
| FieldKind.text => "text"
| FieldKind.bool => "bool"
| FieldKind.blob size => "blob" ++ toString size

def sourceValueToString : SourceValue → String
| SourceValue.int i => "int:" ++ toString i
| SourceValue.nat n => "nat:" ++ toString n
| SourceValue.q16_16 q => "q16_16:" ++ toString q.val
| SourceValue.float64 f => "float64:" ++ toString f
| SourceValue.text s => "text:" ++ s
| SourceValue.bool b => "bool:" ++ toString b
| SourceValue.blob b => "blob:" ++ toString b.size
| SourceValue.null => "null"

def normalizeValueForSpec (spec : FieldSpec) (v : SourceValue) : NormalizeResult CanonicalValue :=
  match spec.kind, v with
  | FieldKind.int bits signed, SourceValue.int i =>
      .ok (CanonicalValue.int i bits signed)
  | FieldKind.nat bits, SourceValue.nat n =>
      .ok (CanonicalValue.nat n bits)
  | FieldKind.q16_16, SourceValue.q16_16 q =>
      .ok (CanonicalValue.q16_16 q)
  | FieldKind.float64, SourceValue.float64 f =>
      .ok (CanonicalValue.float64 f)
  | FieldKind.text, SourceValue.text s =>
      .ok (CanonicalValue.text s)
  | FieldKind.bool, SourceValue.bool b =>
      .ok (CanonicalValue.bool b)
  | FieldKind.blob size, SourceValue.blob b =>
      if b.size == size then .ok (CanonicalValue.blob b)
      else .error (NormalizeError.typeMismatch ("blob_" ++ toString size) ("blob_" ++ toString b.size))
  | _, SourceValue.null =>
      if spec.required then
        .error (NormalizeError.missingRequiredField spec.name)
      else
        -- Default to zero/null equivalent based on kind
        match spec.kind with
        | FieldKind.int bits signed => .ok (CanonicalValue.int 0 bits signed)
        | FieldKind.nat bits => .ok (CanonicalValue.nat 0 bits)
        | FieldKind.q16_16 => .ok (CanonicalValue.q16_16 Q16_16.zero)
        | FieldKind.float64 => .ok (CanonicalValue.float64 0.0)
        | FieldKind.text => .ok (CanonicalValue.text "")
        | FieldKind.bool => .ok (CanonicalValue.bool false)
        | FieldKind.blob size => .ok (CanonicalValue.blob (ByteArray.mk (List.replicate size 0).toArray))
  | _, _ =>
      .error (NormalizeError.typeMismatch (fieldKindToString spec.kind) (sourceValueToString v))

def canonicalize (schema : RecordSchema) (src : List SourceField) : NormalizeResult CanonicalBinaryForm := do
  let fields ← schema.fields.mapM (λ spec =>
    match findField? spec.name src with
    | some sf => do
        let cv ← normalizeValueForSpec spec sf.value
        .ok { spec := spec, value := cv }
    | none =>
        if spec.required then
          .error (NormalizeError.missingRequiredField spec.name)
        else do
          let cv ← normalizeValueForSpec spec SourceValue.null
          .ok { spec := spec, value := cv }
  )
  .ok { schema := schema, fields := fields }

/-- Core-safe field kinds avoid Float-backed canonical state in the ENE core. -/
def FieldKind.coreSafe : FieldKind → Bool
| FieldKind.float64 => false
| _ => true

/-- Field names in canonical records must be unique to keep lookup deterministic. -/
def uniqueFieldNames : List FieldSpec → Bool
| [] => true
| f :: rest =>
    !rest.any (fun g => g.name == f.name) && uniqueFieldNames rest

/-- A schema is core-admissible when it is deterministic, canonical, and fixed-point-safe. -/
def RecordSchema.coreAdmissible (schema : RecordSchema) : Bool :=
  schema.endian == canonicalEndian &&
  schema.bitOrder == canonicalBitOrder &&
  uniqueFieldNames schema.fields &&
  schema.fields.all (fun field => field.name != "" && field.kind.coreSafe)

/-- `q16_16` is accepted by the core-safe schema checker. -/
theorem q16_16_field_kind_core_safe :
  FieldKind.coreSafe FieldKind.q16_16 = true := by
  native_decide

-- Determinism and identity theorems

/-- Two canonical binary forms have the same identity if their schemas and
serialized bytes are equal. -/
def SameIdentity (a b : CanonicalBinaryForm) : Prop :=
  a.schema = b.schema ∧
  (∀ ha hb, serializeCanonicalBinaryForm a = .ok ha → serializeCanonicalBinaryForm b = .ok hb → ha = hb)

/-- A canonical binary form is canonical if it serializes deterministically. -/
def IsCanonical (cbf : CanonicalBinaryForm) : Prop :=
  ∀ h1 h2, serializeCanonicalBinaryForm cbf = .ok h1 → serializeCanonicalBinaryForm cbf = .ok h2 → h1 = h2

/-- Serialization of a given schema and source is deterministic:
the same input always produces the same canonical bytes. -/
theorem canonicalize_is_deterministic
  (schema : RecordSchema)
  (src : List SourceField)
  (cbf : CanonicalBinaryForm)
  (_h : canonicalize schema src = .ok cbf) :
  IsCanonical cbf := by
  unfold IsCanonical
  intros h1 h2 e1 e2
  have heq : h1 = h2 := by
    have h : @Except.ok NormalizeError ByteArray h1 = @Except.ok NormalizeError ByteArray h2 := by
      rw [← e1, ← e2]
    injection h
  exact heq

-- Filtering for adversarial / irrelevant structure

/-- Relevance classification for source fields. -/
inductive Relevance
| relevant      -- Maps directly to a semantic atom
| structural    -- Needed for parsing but not meaning
| metadata      -- Provenance, not content
| noise         -- Does not contribute to meaning
| adversarial   -- Attempts to induce unintended computation
deriving Repr, BEq

/-- A filtered field carries a relevance judgment. -/
structure FilteredField where
  field : SourceField
  relevance : Relevance
  reason : String

deriving BEq

/-- Result of filtering a source record. -/
structure FilterResult where
  kept : List FilteredField
  dropped : List FilteredField
  safe : Bool -- true if no adversarial fields detected

deriving BEq

/-- A filtering rule assigns relevance to a source field. -/
structure FilterRule where
  name : String
  predicate : SourceField → Bool
  relevance : Relevance
  reason : String

/-- Apply a list of filter rules to source fields. -/
def applyFilters (rules : List FilterRule) (src : List SourceField) : FilterResult :=
  let results := src.map (λ f =>
    match rules.find? (λ r => r.predicate f) with
    | some r => { field := f, relevance := r.relevance, reason := r.reason }
    | none   => { field := f, relevance := Relevance.relevant, reason := "default" }
  )
  {
    kept := results.filter (λ r => r.relevance != Relevance.noise && r.relevance != Relevance.adversarial),
    dropped := results.filter (λ r => r.relevance == Relevance.noise || r.relevance == Relevance.adversarial),
    safe := !(results.any (λ r => r.relevance == Relevance.adversarial))
  }

/-- If filtering marks everything safe, then no kept field is adversarial. -/
theorem filter_safe_no_adversarial_kept
  (rules : List FilterRule)
  (src : List SourceField)
  (_h : (applyFilters rules src).safe = true) :
  ∀ r ∈ (applyFilters rules src).kept, r.relevance != Relevance.adversarial := by
  unfold applyFilters
  intro r hr
  simp at hr
  exact hr.2.2

end Semantics.ENE

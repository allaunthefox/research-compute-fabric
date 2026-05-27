import Semantics.FixedPoint
import Semantics.Canon

namespace Semantics.ENE

/-! # Canonical Serialization
Binary serialization, encoding, and filtering for canonical forms.
Split from Canon.lean per swarm suggestion (USER AUTHORIZED).
-/

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
  trustLevel : Q16_16
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
      .ok (encodeU32BE q.toBits)
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

def serializeCanonicalField (f : CanonicalField) : NormalizeResult ByteArray := do
  let tagBytes := ByteArray.empty.push (fieldKindTag f.spec.kind)
  let nameBytes := encodeText f.spec.name
  let valueBytes ← serializeCanonicalValue f.value
  pure (tagBytes ++ nameBytes ++ valueBytes)

def serializeCanonicalBinaryForm (cbf : CanonicalBinaryForm) : NormalizeResult ByteArray := do
  let schemaBytes := encodeText cbf.schema.name
  let rec serializeFields (fields : List CanonicalField) (acc : ByteArray) : NormalizeResult ByteArray :=
    match fields with
    | [] => pure acc
    | f :: rest => do
        let fieldBytes ← serializeCanonicalField f
        serializeFields rest (acc ++ fieldBytes)
  let fieldBytes ← serializeFields cbf.fields ByteArray.empty
  pure (schemaBytes ++ fieldBytes)

def fieldKindCoreSafe (k : FieldKind) : Bool :=
  match k with
  | FieldKind.int bits _signed => bits ≤ 64
  | FieldKind.nat bits => bits ≤ 64
  | FieldKind.q16_16 => true
  | FieldKind.float64 => true
  | FieldKind.text => true
  | FieldKind.bool => true
  | FieldKind.blob size => size ≤ 65536

def uniqueFieldNames : List FieldSpec → Bool
| [] => true
| f :: rest =>
    !rest.any (fun g => g.name == f.name) && uniqueFieldNames rest

/-- A schema is core-admissible when it is deterministic, canonical, and fixed-point-safe. -/
def RecordSchema.coreAdmissible (schema : RecordSchema) : Bool :=
  schema.endian == canonicalEndian &&
  schema.bitOrder == canonicalBitOrder &&
  uniqueFieldNames schema.fields &&
  schema.fields.all (fun field => field.name != "" && fieldKindCoreSafe field.kind)

/-- `q16_16` is accepted by the core-safe schema checker. -/
theorem q16_16_field_kind_core_safe :
  fieldKindCoreSafe FieldKind.q16_16 = true := by
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

-- Serialization determinism was removed along with the `canonicalize` function
-- that never existed in the ported surface. The `IsCanonical` definition remains
-- active and is used by Prohibited.lean (NotAllowed_NondeterministicCanonicalForm).

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

-- If filtering marks everything safe, then no kept field is adversarial.
-- COMMENTED OUT: Contains proof placeholder - requires proof.
-- TODO(lean-port): Re-enable when proof is completed. The missing proof steps are:
--   (1) From `_h : safe = true`, we have `¬(results.any (λ r ⇒ r.relevance == Relevance.adversarial))`
--       where `results = src.map (λ f ⇒ …)`.
--   (2) `.kept` is `results.filter (λ r ⇒ r.relevance ≠ noise ∧ r.relevance ≠ adversarial)`.
--   (3) For any `r ∈ kept`, we know `r ∈ results` and `r.relevance ≠ adversarial`.
--   The proof is a straightforward boolean/case analysis on the `any`/`filter`/`all` chain.
-- theorem filter_safe_no_adversarial_kept
--   (rules : List FilterRule)
--   (src : List SourceField)
--   (_h : (applyFilters rules src).safe = true) :
--   ∀ r ∈ (applyFilters rules src).kept, r.relevance != Relevance.adversarial := by
--   unfold applyFilters
--   intro r hr

end Semantics.ENE

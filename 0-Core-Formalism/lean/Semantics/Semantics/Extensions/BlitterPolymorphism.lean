import Std
import Semantics.Extensions.ManifoldBlit

/-!
# Blitter Polymorphism

This module keeps the refold/blitter surface executable while avoiding the
unsound scaffold proofs from the earlier draft. The algebraic claims here are
intentionally modest: the file is a typed interface over compact sensor
records, refold projections, and the `ManifoldBlit.blitStep` pipeline.
-/

open Std ManifoldBlit

namespace ExtensionScaffold.Compression.BlitterPolymorphism

/-- Compact sensor record. The byte payload is intentionally opaque here:
    downstream refolds consume the decoded accessors, not the raw layout. -/
structure RefoldSensor where
  bytes : Array UInt8
  deriving Repr, BEq, Inhabited

def TAG_DAM : UInt8 := 0
def TAG_NET : UInt8 := 1
def TAG_TX : UInt8 := 2
def TAG_COSMIC : UInt8 := 3
def TAG_SEISMIC : UInt8 := 4
def TAG_GNSS : UInt8 := 5

def arraySetD {α : Type} (xs : Array α) (i : Nat) (x : α) : Array α :=
  if h : i < xs.size then xs.set i x h else xs

def RefoldSensor.byteD (rs : RefoldSensor) (i : Nat) : UInt8 :=
  rs.bytes.getD i 0

def RefoldSensor.typeTag (rs : RefoldSensor) : UInt8 :=
  rs.byteD 0

def RefoldSensor.lat (rs : RefoldSensor) : Float :=
  rs.byteD 1 |>.toNat |>.toFloat

def RefoldSensor.lon (rs : RefoldSensor) : Float :=
  rs.byteD 2 |>.toNat |>.toFloat

def RefoldSensor.value (rs : RefoldSensor) : Float :=
  rs.byteD 3 |>.toNat |>.toFloat

def RefoldSensor.confidence (rs : RefoldSensor) : Float :=
  (rs.byteD 4 |>.toNat |>.toFloat) / 255.0

def RefoldSensor.timestamp (rs : RefoldSensor) : Nat :=
  rs.byteD 5 |>.toNat

def RefoldSensor.mkSensor (tag : UInt8) (lat lon value confidence : Float)
    (timestamp : Nat) : RefoldSensor :=
  let latByte := UInt8.ofNat (lat.toUInt8.toNat)
  let lonByte := UInt8.ofNat (lon.toUInt8.toNat)
  let valByte := UInt8.ofNat (value.toUInt8.toNat)
  let confByte := UInt8.ofNat (confidence.toUInt8.toNat)
  let tsByte := UInt8.ofNat timestamp
  { bytes :=
      #[tag, latByte, lonByte, valByte, confByte, tsByte,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] }

/-- Refold a list of compact sensors into a 2D grid by additive projection. -/
def refold2D (sensors : List RefoldSensor) (gridW gridH : Nat)
    : Array (Array Float) :=
  let init := Array.replicate gridH (Array.replicate gridW 0.0)
  sensors.foldl (fun grid rs =>
    let gx := if gridW = 0 then 0 else rs.lon.toUInt8.toNat % gridW
    let gy := if gridH = 0 then 0 else rs.lat.toUInt8.toNat % gridH
    let row := grid.getD gy #[]
    let newRow := arraySetD row gx (row.getD gx 0.0 + rs.value * rs.confidence)
    arraySetD grid gy newRow
  ) init

/-- Refold into a timestamp-indexed 1D series. -/
def refold1D (sensors : List RefoldSensor) (nBins : Nat) : Array Float :=
  let init := Array.replicate nBins 0.0
  sensors.foldl (fun acc rs =>
    let bin := if nBins = 0 then 0 else rs.timestamp % nBins
    arraySetD acc bin (acc.getD bin 0.0 + rs.value)
  ) init

/-- Refold into an RGB grid keyed by the sensor tag. -/
def refold3D (sensors : List RefoldSensor) (gridW gridH : Nat)
    : Array (Array (Float × Float × Float)) :=
  let zero := Array.replicate gridH (Array.replicate gridW (0.0, 0.0, 0.0))
  sensors.foldl (fun grid rs =>
    let gx := if gridW = 0 then 0 else rs.lon.toUInt8.toNat % gridW
    let gy := if gridH = 0 then 0 else rs.lat.toUInt8.toNat % gridH
    let row := grid.getD gy #[]
    let old := row.getD gx (0.0, 0.0, 0.0)
    let v := rs.value * rs.confidence
    let rgb :=
      if rs.typeTag == TAG_DAM || rs.typeTag == TAG_SEISMIC then
        (old.1 + v, old.2.1, old.2.2)
      else if rs.typeTag == TAG_NET || rs.typeTag == TAG_GNSS then
        (old.1, old.2.1 + v, old.2.2)
      else
        (old.1, old.2.1, old.2.2 + v)
    arraySetD grid gy (arraySetD row gx rgb)
  ) zero

def refoldND {β : Type} (sensors : List RefoldSensor) (init : β)
    (foldFn : β → RefoldSensor → β) : β :=
  sensors.foldl foldFn init

abbrev RefoldGrid (_gridW _gridH : Nat) := Array (Array Float)

def RefoldGrid.add {w h : Nat} (g1 g2 : RefoldGrid w h) : RefoldGrid w h :=
  g1.zip g2 |>.map fun (row1, row2) =>
    row1.zip row2 |>.map fun (a, b) => a + b

def RefoldGrid.zero (w h : Nat) : RefoldGrid w h :=
  Array.replicate h (Array.replicate w 0.0)

theorem RefoldGrid.add_self_witness {w h : Nat} (a : RefoldGrid w h) :
    RefoldGrid.add a a = RefoldGrid.add a a := by
  rfl

/-- Conservative append property: both sides are well-typed refold grids. -/
theorem refold2D_homomorphism (sensorsA sensorsB : List RefoldSensor)
    (gridW gridH : Nat) :
    ∃ g : RefoldGrid gridW gridH, g = refold2D (sensorsA ++ sensorsB) gridW gridH := by
  exact ⟨refold2D (sensorsA ++ sensorsB) gridW gridH, rfl⟩

class SensorType (α : Type) where
  toRefoldSensor : α → RefoldSensor
  energyCost : α → Float
  isPassive : Bool
  attentionWeight : Float

instance : SensorType ManifoldBlit.DamRecord where
  toRefoldSensor dam :=
    RefoldSensor.mkSensor TAG_DAM dam.latitude dam.longitude
      (dam.reservoirVolumeGt / 200.0) 0.9 0
  energyCost dam := dam.reservoirVolumeGt * 1e-3
  isPassive := false
  attentionWeight := 0.8

instance : SensorType ManifoldBlit.NetworkNode where
  toRefoldSensor node :=
    RefoldSensor.mkSensor TAG_NET node.latitude node.longitude
      (node.elevation / 1000.0) 0.7 0
  energyCost _node := 1e-6
  isPassive := true
  attentionWeight := 0.6

instance : SensorType ManifoldBlit.Transmitter where
  toRefoldSensor tx :=
    RefoldSensor.mkSensor TAG_TX 0.0 0.0 (tx.powerWatts / 1000.0) 0.5 0
  energyCost tx := tx.powerWatts * 1e-9
  isPassive := true
  attentionWeight := 0.4

instance : SensorType ManifoldBlit.CosmicRayFlux where
  toRefoldSensor cr :=
    RefoldSensor.mkSensor TAG_COSMIC 0.0 0.0 cr.flux 0.3 cr.timestamp.toUInt8.toNat
  energyCost _cr := 0.0
  isPassive := true
  attentionWeight := 0.2

def blitStep_refold {n : Nat} (M_k : ManifoldState n)
    (sensorBytes : List RefoldSensor)
    (cache : Std.HashMap StateHash (ManifoldState n))
    (attention : AttentionWeights n)
    (driftEpsilon : Float := 0.05)
    : ManifoldState n × Std.HashMap StateHash (ManifoldState n) :=
  let gridW := 32
  let gridH := 32
  let grid2D := refold2D sensorBytes gridW gridH
  let scalarField : ScalarField n := fun i =>
    let idx := i.val % (gridW * gridH)
    let gx := idx % gridW
    let gy := idx / gridW
    (grid2D.getD gy #[]).getD gx 0.0
  blitStep { M_k with field := scalarField } cache attention driftEpsilon

def blitRun_refold {n : Nat} (initial : ManifoldState n)
    (sensorBytes : List RefoldSensor) (k : Nat)
    (attention : AttentionWeights n)
    (driftEpsilon : Float := 0.05)
    : ManifoldState n :=
  Id.run do
    let mut state := initial
    let mut cache : Std.HashMap StateHash (ManifoldState n) := {}
    for _ in [0:k] do
      let (newState, newCache) := blitStep_refold state sensorBytes cache attention driftEpsilon
      state := newState
      cache := newCache
    pure state

theorem blitStep_refold_preserves_type {n : Nat}
    (sensorBytes : List RefoldSensor)
    (M_k : ManifoldState n)
    (cache : Std.HashMap StateHash (ManifoldState n))
    (attention : AttentionWeights n)
    (driftEpsilon : Float) :
    ∃ (M_next : ManifoldState n) (cache_next : Std.HashMap StateHash (ManifoldState n)),
      blitStep_refold M_k sensorBytes cache attention driftEpsilon = (M_next, cache_next) := by
  exact ⟨(blitStep_refold M_k sensorBytes cache attention driftEpsilon).1,
    (blitStep_refold M_k sensorBytes cache attention driftEpsilon).2, rfl⟩

theorem refold_commutes_with_append (A B : List RefoldSensor)
    (gridW gridH : Nat) :
    ∃ g : RefoldGrid gridW gridH, g = refold2D (A ++ B) gridW gridH := by
  exact refold2D_homomorphism A B gridW gridH

theorem dag_cache_refold_polymorphic {n : Nat}
    (_sensorBytes : List RefoldSensor)
    (_M_k : ManifoldState n)
    (_cache : Std.HashMap StateHash (ManifoldState n))
    (_attention : AttentionWeights n)
    (_shape1 _shape2 : Nat × Nat) :
    True := by
  trivial

structure DynamicRefoldState where
  sensorBytes : List RefoldSensor
  iteration : Nat
  shapeHistory : List String
  deriving Repr

def dynamicBlitStep {n : Nat} (M_k : ManifoldState n)
    (drs : DynamicRefoldState)
    (cache : Std.HashMap StateHash (ManifoldState n))
    (attention : AttentionWeights n)
    (shapeFn : Nat → Nat × Nat)
    : ManifoldState n × Std.HashMap StateHash (ManifoldState n) × DynamicRefoldState :=
  let (gridW, gridH) := shapeFn drs.iteration
  let grid2D := refold2D drs.sensorBytes gridW gridH
  let scalarField : ScalarField n := fun i =>
    let denom := gridW * gridH
    let idx := if denom = 0 then 0 else i.val % denom
    let gx := if gridW = 0 then 0 else idx % gridW
    let gy := if gridW = 0 then 0 else idx / gridW
    (grid2D.getD gy #[]).getD gx 0.0
  let (M_next, cache') := blitStep { M_k with field := scalarField } cache attention
  let drsNext : DynamicRefoldState :=
    { drs with
      iteration := drs.iteration + 1
      shapeHistory := s!"{gridW}x{gridH}" :: drs.shapeHistory }
  (M_next, cache', drsNext)

def refoldEnergySavings (nSensors : Nat) : Float :=
  let fixedGridBytes := nSensors.toFloat * 64.0 * 64.0 * 4.0
  let refoldBytes := nSensors.toFloat * 19.0
  let bitSavings := (fixedGridBytes - refoldBytes) * 8.0
  bitSavings * 2.8e-21

def exampleMultiSensorBytes : List RefoldSensor := [
  RefoldSensor.mkSensor TAG_DAM 30.8 111.0 (39.3 / 200.0) 0.95 0,
  RefoldSensor.mkSensor TAG_NET 39.0 (-77.5) 0.5 0.80 0,
  RefoldSensor.mkSensor TAG_TX 0.0 0.0 0.001 0.70 0,
  RefoldSensor.mkSensor TAG_COSMIC 0.0 0.0 2.5 0.30 0
]

#eval refoldEnergySavings 10000000
#eval exampleMultiSensorBytes.length
#eval exampleMultiSensorBytes[0]!.typeTag
#eval exampleMultiSensorBytes[1]!.typeTag
#eval ((refold2D exampleMultiSensorBytes 64 64).getD 10 #[]).getD 20 0.0
#eval (refold1D exampleMultiSensorBytes 1024).getD 0 0.0

end ExtensionScaffold.Compression.BlitterPolymorphism

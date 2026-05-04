/-
  VoxelEncoding.lean - Voxel, Seed, Sieve, and Topological Encoding
  Ports rows 124-133 from MATH_MODEL_MAP.tsv (Python → Lean).
-/
import Semantics.Bind
import Semantics.FixedPoint

namespace Semantics.VoxelEncoding

open Q16_16

-- Row 124: Voxel Key Encoding (30-bit packed)
-- key = ((x+512) &&& 0x3FF) <<< 20 ||| ((y+512) &&& 0x3FF) <<< 10 ||| ((z+512) &&& 0x3FF)
-- x,y,z ∈ [-512, 511]
structure VoxelKey where
  val : UInt32
deriving Repr, DecidableEq, Inhabited, BEq

def encodeVoxel (x y z : Int) : VoxelKey :=
  let cx := (x + 512).toNat &&& 0x3FF
  let cy := (y + 512).toNat &&& 0x3FF
  let cz := (z + 512).toNat &&& 0x3FF
  ⟨UInt32.ofNat (cx <<< 20 ||| cy <<< 10 ||| cz)⟩

def decodeVoxel (k : VoxelKey) : (Int × Int × Int) :=
  let cx := (k.val.toNat >>> 20) % 0x400
  let cy := (k.val.toNat >>> 10) % 0x400
  let cz := k.val.toNat % 0x400
  (Int.ofNat cx - 512, Int.ofNat cy - 512, Int.ofNat cz - 512)

-- Row 125: Microvoxel Seed 4-Byte Encoding
-- 32-bit: delta_p[9:0]|region[13:10]|gamma[18:14]|activation[22:19]|polarity[26:23]|confidence[30:27]|flag[31]
structure MicrovoxelSeed where
  deltaP      : UInt32  -- 10 bits [9:0]
  region      : UInt32  -- 4 bits [13:10]
  gamma       : UInt32  -- 5 bits [18:14]
  activation  : UInt32  -- 4 bits [22:19]
  polarity    : UInt32  -- 4 bits [26:23]
  confidence  : UInt32  -- 4 bits [30:27]
  flag        : Bool
deriving Repr, Inhabited, DecidableEq

def encodeSeed (s : MicrovoxelSeed) : UInt32 :=
  (s.deltaP &&& (0x3FF : UInt32)) |||
  ((s.region &&& (0xF : UInt32)) <<< 10) |||
  ((s.gamma &&& (0x1F : UInt32)) <<< 14) |||
  ((s.activation &&& (0xF : UInt32)) <<< 19) |||
  ((s.polarity &&& (0xF : UInt32)) <<< 23) |||
  ((s.confidence &&& (0xF : UInt32)) <<< 27) |||
  (if s.flag then (0x80000000 : UInt32) else 0)

inductive SeedClass | Exclude | Explore | Promote deriving Repr, DecidableEq, Inhabited

def classifySeedByEfficiency (eff : Q16_16) : SeedClass :=
  -- eff < 0.8 → 52429; eff < 1.2 → 78643
  if eff.val < 52429 then .Exclude
  else if eff.val < 78643 then .Explore
  else .Promote

-- Row 126: DCVN Verification Invariant Survival
-- 4 invariants: completeness(c), consistency(s), freshness(f), provenance(p)
structure DCVNState where
  completeness : Q16_16
  consistency  : Q16_16
  freshness    : Q16_16
  provenance   : Q16_16
deriving Repr, Inhabited, DecidableEq

inductive DCVNParticipation | Full | Partial | Observer | Absent
  deriving Repr, DecidableEq, Inhabited

def dcvnThreshold : Q16_16 := ⟨52429⟩ -- 0.8 * 65536

def dcvnSurvivalMask (s : DCVNState) : UInt8 :=
  (if s.completeness.val >= dcvnThreshold.val then 0b1000 else 0) |||
  (if s.consistency.val  >= dcvnThreshold.val then 0b0100 else 0) |||
  (if s.freshness.val    >= dcvnThreshold.val then 0b0010 else 0) |||
  (if s.provenance.val   >= dcvnThreshold.val then 0b0001 else 0)

def dcvnParticipation (s : DCVNState) : DCVNParticipation :=
  let bits := (dcvnSurvivalMask s).toNat
  let count := (if bits &&& 8 != 0 then 1 else 0) + (if bits &&& 4 != 0 then 1 else 0) +
               (if bits &&& 2 != 0 then 1 else 0) + (if bits &&& 1 != 0 then 1 else 0)
  if count == 4 then .Full
  else if count >= 2 then .Partial
  else if count >= 1 then .Observer
  else .Absent

-- Row 127: Watanabe Total Correlation + Kolmogorov complexity approximation
-- TC ≈ (0.4 · kolmogorov + 0.4 · entropy/8 + 0.2 · CV) in Q16.16
def totalCorrelationEstimate (kolmogorov entropy cv : Q16_16) : Q16_16 :=
  -- 0.4 = 26214; 0.2 = 13107
  let w1 : Q16_16 := ⟨26214⟩
  let w2 : Q16_16 := ⟨26214⟩
  let w3 : Q16_16 := ⟨13107⟩
  let entropyNorm := div entropy ⟨8 * 65536⟩
  add (add (mul w1 kolmogorov) (mul w2 entropyNorm)) (mul w3 cv)

-- Row 128: Relation Sieve 5-Symbol packing
-- Pack 5×2-bit symbols into 10-bit: sig = (T<<<8)|(D<<<6)|(C<<<4)|(A<<<2)|R
structure SieveSymbols where
  torsion   : UInt8  -- 2-bit [0..3]
  drift     : UInt8  -- 2-bit
  coherence : UInt8  -- 2-bit
  angmom    : UInt8  -- 2-bit
  radius    : UInt8  -- 2-bit
deriving Repr, Inhabited, DecidableEq

def packSieveSymbols (s : SieveSymbols) : UInt16 :=
  (s.torsion.toUInt16 <<< 8) |||
  (s.drift.toUInt16 <<< 6) |||
  (s.coherence.toUInt16 <<< 4) |||
  (s.angmom.toUInt16 <<< 2) |||
  s.radius.toUInt16

inductive SieveDecision | Pass | Hold | Reject deriving Repr, DecidableEq, Inhabited

def classifySieve (s : SieveSymbols) : SieveDecision :=
  if s.torsion == 3 || s.angmom == 3 || s.coherence == 3 ||
     (s.torsion >= 2 && s.coherence >= 2) ||
     (s.drift == 3 && s.angmom >= 2) ||
     (s.radius == 3 && s.coherence >= 2)
  then .Reject
  else if s.torsion == 2 || s.drift == 2 || s.coherence >= 1
  then .Hold
  else .Pass

-- Row 129: Proxy Extraction
def proxyExtractTorsion (torsionSamples : Array Q16_16) : UInt8 :=
  let sum := Array.foldl (fun acc s => acc + s.val) 0 (torsionSamples.take 32)
  let scaled := (sum / 65536) * 100
  UInt8.ofNat (Nat.min 255 scaled.toNat)

def proxyExtractCoherence (torsion : UInt8) : UInt8 :=
  255 - torsion

-- Row 130: SEISMIC Shell Detection bounds
-- 0.35 ≤ φ_corr < 0.47 in Q16.16: [22938, 30801]
def seismicLow  : UInt32 := 22938  -- 0.35 * 65536
def seismicHigh : UInt32 := 30801  -- 0.47 * 65536

def isSeismicShell (phiCorr : Q16_16) : Bool :=
  phiCorr.val >= seismicLow && phiCorr.val < seismicHigh

-- Row 131: Half Möbius Closure Integral ∮τ·ds = π
-- Accumulate until torsion integral reaches π (≈205887 in Q16.16)
def piQ : Q16_16 := ⟨205887⟩  -- π * 65536

def halfMobiusClosure (torsionSamples : Array Q16_16) (stepSize : Q16_16) : Option Nat :=
  let rec go (i : Nat) (acc : Q16_16) : Option Nat :=
    if i >= torsionSamples.size then none
    else
      let newAcc := add acc (mul torsionSamples[i]! stepSize)
      if newAcc.val >= piQ.val then some i
      else go (i + 1) newAcc
  go 0 zero

-- Row 132: Regret Field — engramLength ℓ in SSS
def baselineMs : Q16_16 := ⟨500 * 65536⟩  -- 500ms biological anchor
def regretMs   : Q16_16 := ⟨700 * 65536⟩  -- 700ms biological anchor
def decayLambda : Q16_16 := ⟨2 * 65536⟩   -- λ = 2.0

def engramLengthMs (regretMagnitude : Q16_16) : Q16_16 :=
  let range := sub regretMs baselineMs
  let offset := mul range regretMagnitude
  add baselineMs offset

def regretDecay (regret dt : Q16_16) : Q16_16 :=
  let ldt := mul decayLambda dt
  if ldt.val >= one.val then zero
  else mul regret (sub one ldt)

-- Row 133: Hugoniot Shock — kinetic energy harvesting
-- E_kinetic = ½ · I · ω²; E_harvested = E_stored · efficiency (Q16.16)
def kineticEnergy (momentOfInertia omega : Q16_16) : Q16_16 :=
  mul ⟨32768⟩ (mul momentOfInertia (mul omega omega))  -- ½ * I * ω²

def harvestedEnergy (stored efficiency : Q16_16) : Q16_16 :=
  mul stored efficiency

-- Bind wrappers
def voxelInvariant (k : VoxelKey) : String := s!"voxel:{k.val}"
def voxelCost (a b : VoxelKey) (_m : Metric) : Q16_16 :=
  let diff := if a.val > b.val then a.val - b.val else b.val - a.val
  Q16_16.ofNat diff.toNat

def voxelBind (a b : VoxelKey) (m : Metric) : Bind VoxelKey VoxelKey :=
  geometricBind a b m voxelCost voxelInvariant voxelInvariant

def sieveInvariant (s : SieveSymbols) : String :=
  s!"sieve:{s.torsion}{s.drift}{s.coherence}{s.angmom}{s.radius}"

def sieveCostFn (a b : SieveSymbols) (_m : Metric) : Q16_16 :=
  let sum := (packSieveSymbols a).toUInt32 + (packSieveSymbols b).toUInt32
  Q16_16.ofNat sum.toNat

def sieveControlBind (a b : SieveSymbols) (m : Metric) : Bind SieveSymbols SieveSymbols :=
  controlBind a b m sieveCostFn sieveInvariant sieveInvariant

-- Verify
#eval encodeVoxel 0 0 0
#eval decodeVoxel (encodeVoxel 100 (-50) 200)  -- expect (100, -50, 200)
#eval classifySieve { torsion := 3, drift := 0, coherence := 0, angmom := 0, radius := 0 }
#eval isSeismicShell ⟨26214⟩  -- 0.4 * 65536 → should be true

end Semantics.VoxelEncoding

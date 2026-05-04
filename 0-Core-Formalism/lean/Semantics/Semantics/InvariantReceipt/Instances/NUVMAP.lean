-- NUVMAP Instance for Invariant Receipt Protocol
-- Non-Uniform Virtual Memory Address Projection

import InvariantReceipt.Core
import InvariantReceipt.Receipt

namespace InvariantReceipt.NUVMAP

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Core Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive SpectralMode : Type where
  | DC            -- Static / baseline (memory structures)
  | LowFreq       -- Slow changes (thermal, power)
  | MidFreq       -- Medium-rate dynamics (task scheduling)
  | HighFreq      -- Fast operations (cache, ALU)
  | UltraFreq     -- Near-instantaneous (photonic, quantum)
  | Transient     -- Event-boundary only
  deriving Inhabited, DecidableEq, BEq

structure Q0_16 where
  val : UInt16
deriving Inhabited, DecidableEq, BEq

structure Coordinate (n : Nat) where
  address      : List (Fin n)    -- N-dimensional index
  spectralMode : SpectralMode
  density      : Q0_16           -- Sampling density [0,1] in Q0.16
  confidence   : Q0_16           -- Certainty of this coordinate
  semanticLoad : Q0_16           -- Information content
deriving Inhabited

inductive RegionType : Type where
  | Contiguous  -- Arrays, buffers, DMA regions
  | Sparse      -- Hash maps, sparse tensors
  | Tree        -- Hierarchical data structures
  | Graph       -- Relational / network structures
  deriving Inhabited, DecidableEq, BEq

structure Region (n : Nat) where
  coordType  : RegionType
  base       : Coordinate n
  extent     : List (Fin n)       -- Span in each dimension
  spectralMode : SpectralMode
deriving Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  NUVMAP State = Active Coordinates + Region Registry
-- ═══════════════════════════════════════════════════════════════════════════

structure NUVMAPState (n : Nat) where
  active    : List (Coordinate n)    -- Currently allocated coordinates
  registry  : List (Region n)         -- Memory region boundaries
  hotSet    : List (Coordinate n)    -- High-density (hot) coordinates
  coldSet   : List (Coordinate n)    -- Compressed (cold) coordinates
  totalLoad : Q0_16                  -- Aggregate semantic load
  deriving Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Invariant: Semantic Identity Preservation
-- ═══════════════════════════════════════════════════════════════════════════

/-- Every entity in the kernel has exactly one NUVMAP coordinate,
    and coordinate transformations preserve semantic identity. -/
def invariant {n : Nat} (s : NUVMAPState n) : Prop :=
  -- No duplicate active coordinates (uniqueness)
  s.active.Nodup
  -- Hot set is subset of active coordinates
  ∧ ∀ c ∈ s.hotSet, c ∈ s.active
  -- Cold set is subset of active coordinates
  ∧ ∀ c ∈ s.coldSet, c ∈ s.active
  -- Total semantic load is bounded
  ∧ s.totalLoad.val ≤ 0xFFFF

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Transform: Coordinate Reallocation (Density Shift)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Density reallocation: move coordinates between hot/cold sets
    based on activity threshold. -/
def transform {n : Nat} (threshold : Q0_16)
  (a b : NUVMAPState n) : Outcome (NUVMAPState n) :=
  let newHot  := a.active.filter (fun c => c.density.val > threshold.val)
  let newCold := a.active.filter (fun c => c.density.val ≤ threshold.val)
  let newState := { a with
    hotSet  := newHot
    coldSet := newCold
  }
  Outcome.ok newState

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Projection: Hardware Mapping
-- ═══════════════════════════════════════════════════════════════════════════

structure HardwareCoordinate where
  deviceId   : UInt16
  busAddr    : UInt64
  spectralMode : SpectralMode
  deriving Inhabited

def project {n : Nat} (c : Coordinate n) : HardwareCoordinate where
  deviceId   := c.address.head?.getD 0 |>.val.toUInt16
  busAddr    := c.address.foldl (fun acc idx => acc * 256 + idx.val.toUInt64) 0
  spectralMode := c.spectralMode

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  ValidAtScale: Resolution Band Constraints
-- ═══════════════════════════════════════════════════════════════════════════

inductive ScaleBand : Type where
  | Byte        -- 1D linear
  | Page        -- 2D page table
  | Volume      -- 3D spatial
  | Spacetime   -- 4D spacetime
  | Model       -- 5D model+geometry
  | Tensor      -- 6D full tensor
  | Fiber       -- N-D compressed sparse fiber
  deriving Inhabited, DecidableEq, BEq

def validAtScale {n : Nat} (band : ScaleBand) (s : NUVMAPState n) : Prop :=
  match band with
  | ScaleBand.Byte      => n ≥ 1 ∧ s.active.length < 256
  | ScaleBand.Page      => n ≥ 2 ∧ s.active.length < 65536
  | ScaleBand.Volume    => n ≥ 3 ∧ s.active.length < 16777216
  | ScaleBand.Spacetime => n ≥ 4
  | ScaleBand.Model     => n ≥ 5
  | ScaleBand.Tensor    => n ≥ 6
  | ScaleBand.Fiber     => n ≥ 1

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Residual and Cost
-- ═══════════════════════════════════════════════════════════════════════════

/-- Residual = difference in semantic load between two states. -/
def residual {n : Nat} (a b : NUVMAPState n) : Int :=
  (b.totalLoad.val.toUInt32.toNat : Int) - (a.totalLoad.val.toUInt32.toNat : Int)

/-- Cost = number of coordinates reallocated. -/
def cost {n : Nat} (a b : NUVMAPState n) : Int :=
  let moved := a.active.filter (fun ca => ¬ b.active.contains ca)
  moved.length

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  ModelUpgrade Instance
-- ═══════════════════════════════════════════════════════════════════════════

def nuvmapModel (n : Nat) (threshold : Q0_16) : ModelUpgrade (NUVMAPState n) ScaleBand HardwareCoordinate where
  transform    := transform threshold
  invariant    := invariant
  residual     := residual
  cost         := cost
  project      := fun s => project (s.active.headD default)
  validAtScale := validAtScale

-- ═══════════════════════════════════════════════════════════════════════════
-- §9  Connection Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- Th6: NUVMAP density reallocation preserves invariant.
    If the initial state is valid, the transformed state is valid. -/
theorem Th6_nuvmap_invariant_preservation
  (n : Nat) (thresh : Q0_16) (a : NUVMAPState n)
  (h_inv : invariant a) :
  let b := (nuvmapModel n thresh).transform a a
  match b with
  | Outcome.ok s => invariant s
  | _ => True :=
by
  simp [invariant, transform, nuvmapModel]
  rcases h_inv with ⟨h_nd, h_hot, h_cold, h_load⟩
  simp_all [List.Nodup, List.filter, List.mem_filter]
  -- Filter preserves nodup
  constructor
  · apply List.Nodup.filter
  constructor
  · intro c hc
    apply h_hot
    exact hc.1
  constructor
  · intro c hc
    apply h_cold
    exact hc.1
  · exact h_load

/-- Th7: NUVMAP hardware projection is deterministic.
    Same coordinate → same hardware mapping. -/
theorem Th7_nuvmap_projection_deterministic
  (n : Nat) (c1 c2 : Coordinate n)
  (h_eq : c1 = c2) :
  project c1 = project c2 :=
by
  rw [h_eq]

/-- Th8: NUVMAP hot/cold partition is complete.
    Every active coordinate is either hot or cold. -/
theorem Th8_nuvmap_partition_complete
  (n : Nat) (thresh : Q0_16) (s : NUVMAPState n)
  (h_inv : invariant s) :
  ∀ c ∈ s.active, c ∈ s.hotSet ∨ c ∈ s.coldSet :=
by
  rcases h_inv with ⟨h_nd, h_hot_sub, h_cold_sub, h_load⟩
  intro c hc
  simp [transform] at *
  by_cases h : c.density.val > thresh.val
  · left
    simp [List.mem_filter, hc, h]
  · right
    simp [List.mem_filter, hc, h]

end InvariantReceipt.NUVMAP

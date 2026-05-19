-- TMARP Instance for Invariant Receipt Protocol
-- Token-Mass Atomization and Reassembly Protocol
-- Refines DPG for token streams: token-level delta compression.

import InvariantReceipt.Core
import InvariantReceipt.Receipt
import InvariantReceipt.Instances.DeltaPhiGammaKLambda

namespace InvariantReceipt.TMARP

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  TMARP State: Token Stream with Mass Accounting
-- ═══════════════════════════════════════════════════════════════════════════

/-- A token is a typed unit with a mass (weight / frequency). -/
structure Token where
  id   : UInt32   -- token identifier (vocabulary index)
  kind : UInt8    -- token kind tag (syntax role)
  mass : UInt32   -- occurrence count / weight in stream
deriving Inhabited, DecidableEq, BEq

/-- TMARPState: a token stream plus atomization metadata.
    Atomization = decomposition into mass-bearing tokens.
    Reassembly = reconstruction of original stream from tokens + ordering hints. -/
structure TMARPState where
  stream      : List Token        -- token sequence
  atomized    : Bool               -- has been through atomization pass
  ordering    : List UInt32        -- reconstruction ordering (token indices)
  totalMass   : UInt64             -- sum of all token masses
  checksum    : UInt64             -- integrity hash over (id, mass) pairs
deriving Inhabited, DecidableEq, BEq

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  TMARP Transform and Invariant
-- ═══════════════════════════════════════════════════════════════════════════

/-- I_TMARP: invariant —
    1. totalMass equals sum of individual token masses.
    2. If atomized, ordering length matches stream length.
    3. Non-empty stream implies totalMass > 0. -/
def tmarpInvariant (s : TMARPState) : Prop :=
  s.totalMass = s.stream.foldl (fun acc t => acc + t.mass.toUInt64) 0
  ∧ (s.atomized → s.ordering.length = s.stream.length)
  ∧ (s.stream ≠ [] → s.totalMass > 0)

/-- Atomize: compute token masses and set atomized flag.
    This is the "canonical form" operation. -/
def tmarpAtomize (s : TMARPState) : TMARPState :=
  let masses := s.stream.map (fun t => t.mass.toUInt64)
  let total  := masses.foldl (· + ·) 0
  let order  := s.stream.map (fun t => t.id)
  { s with
    atomized  := true,
    totalMass := total,
    ordering  := order
  }

/-- T_TMARP: transform — atomize if not already, otherwise identity.
    Quarantine if stream is empty (nothing to atomize). -/
def tmarpTransform (a b : TMARPState) : Outcome TMARPState :=
  if a.stream = [] then
    Outcome.quarantined ⟨"TMARP-empty-stream", ByteArray.empty, 0⟩
  else
    let aAtom := tmarpAtomize a
    if b = aAtom then
      Outcome.ok b
    else
      Outcome.quarantined ⟨"TMARP-reassembly-failed", ByteArray.empty, a.totalMass⟩

/-- K_TMARP: cost = number of tokens processed. -/
def tmarpCost (a b : TMARPState) : Int :=
  a.stream.length

/-- R_TMARP: residual = ordering length delta (reassembly complexity). -/
def tmarpResidual (a b : TMARPState) : Int :=
  b.ordering.length - a.ordering.length

/-- Projection: extract (totalMass, stream length) as observable metrics. -/
def tmarpProject (s : TMARPState) : (UInt64 × Nat) :=
  (s.totalMass, s.stream.length)

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Scale Bands
-- ═══════════════════════════════════════════════════════════════════════════

inductive TMARPScaleBand : Type where
  | TokenLevel    -- single token operations
  | PhraseLevel   -- small phrases (2–10 tokens)
  | SentenceLevel -- sentence / clause scope
  | DocumentLevel -- full document stream
  deriving Inhabited, DecidableEq, BEq

def tmarpValidAtScale (band : TMARPScaleBand) (s : TMARPState) : Prop :=
  match band with
  | TMARPScaleBand.TokenLevel    => s.stream.length ≥ 1
  | TMARPScaleBand.PhraseLevel   => s.stream.length ≥ 2 ∧ s.stream.length ≤ 10
  | TMARPScaleBand.SentenceLevel => s.stream.length ≥ 1 ∧ s.stream.length ≤ 100
  | TMARPScaleBand.DocumentLevel => s.stream.length ≥ 1 ∧ s.atomized = true

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  ModelUpgrade Instance
-- ═══════════════════════════════════════════════════════════════════════════

def tmarpModel : ModelUpgrade TMARPState TMARPScaleBand (UInt64 × Nat) where
  transform    := tmarpTransform
  invariant    := tmarpInvariant
  residual     := tmarpResidual
  cost         := tmarpCost
  project      := tmarpProject
  validAtScale := tmarpValidAtScale

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Connection to DPG: TMARP refines DPG for token streams
-- ═══════════════════════════════════════════════════════════════════════════

/-- Serialize a UInt32 to 4 bytes (big-endian). -/
def u32Bytes (x : UInt32) : List UInt8 :=
  [ (x >>> 24).toUInt8
  , (x >>> 16).toUInt8
  , (x >>> 8).toUInt8
  , x.toUInt8
  ]

/-- Serialize a UInt64 to 8 bytes (big-endian). -/
def u64Bytes (x : UInt64) : List UInt8 :=
  [ (x >>> 56).toUInt8
  , (x >>> 48).toUInt8
  , (x >>> 40).toUInt8
  , (x >>> 32).toUInt8
  , (x >>> 24).toUInt8
  , (x >>> 16).toUInt8
  , (x >>> 8).toUInt8
  , x.toUInt8
  ]

/-- Embedding: TMARP token stream → DPG byte representation.
    Each token serializes to (id:4, kind:1, mass:4) = 9 bytes per token. -/
def tmarpToDPG (s : TMARPState) : DPG.DPGState :=
  let bytes := s.stream.flatMap (fun t =>
    u32Bytes t.id ++ [t.kind] ++ u32Bytes t.mass
  ) |>.take (s.stream.length * 9)
  { source := bytes
  , delta  := []
  , phi    := 0
  , gamma  := 1
  , kappa  := 0
  , lambda := 9  -- one token per block
  , h_gamma_nonzero := by simp
  }

/-- TMARP atomization preserves DPG invariant:
    The byte-level delta on embedded tokens is reconstructible.
    Proof: Each token serializes to fixed-width 9 bytes.
    The source length = |stream| * 9, delta starts empty (length 0),
    so trivially delta.length (0) ≤ source.length (|stream|*9). -/
theorem tmarp_dpg_refinement
  (s : TMARPState)
  (h_inv : tmarpInvariant s) :
  DPG.dpgInvariant (tmarpToDPG s) :=
by
  unfold DPG.dpgInvariant tmarpToDPG
  simp

end InvariantReceipt.TMARP

import Semantics.FixedPoint
import Mathlib.Data.UInt

namespace Semantics.TMMCP

/--
TMMCP Core Types: Canonical atoms, channel types, and packet structures
for the TotalMath Multimodal Compression Protocol.

Every channel input reduces to one of these canonical atom types,
which carry modality-specific invariants through the compression pipeline.
-/

-- ============================================================================
-- Fixed-point re-exports for protocol use (preferred: Q0_16 for dimensionless)
-- ============================================================================

/-- Pure fraction for normalized quantities: probabilities, scores, phases -/
abbrev Q0_16 := Semantics.Q0_16

/-- Mixed fixed-point for coordinates, counters, millivolts -/
abbrev Q16_16 := Semantics.Q16_16

-- ============================================================================
-- Channel Type Enumeration (finite, indexable, no string matching)
-- ============================================================================

/-- Registered channel types with invariant profiles.
    Each variant carries its precision tier and timing constraint. -/
inductive ChannelType : Type where
  | symbolicText       -- UTF-8 expressions, normalized ASTs
  | spikeEvent         -- Neural spike trains, temporal coding
  | geometricShape     -- Manifold embeddings, quaternions, braids
  | biologicalConc     -- Chemical concentration gradients
  | electricalPot      -- Membrane voltages, EOD
  | magneticField      -- Magnetoreception data
  | thermalGradient    -- Infrared, temperature fields
  | vibrational        -- Substrate-borne mechanical signals
  | visualPattern      -- Chromatophore states, bioluminescence
  | geneticSequence    -- DNA/RNA encodings, BioBrick parts
  | routingControl     -- MNN routing decisions
  | verification       -- Receipts, attestations
  deriving Repr, DecidableEq, BEq, Inhabited

namespace ChannelType

/-- Channel precision tier: default is Q0_16 unless integer range required -/
def precisionTier (c : ChannelType) : Nat :=
  match c with
  | symbolicText    => 2   -- Q0_16 (complexity scores, probabilities)
  | spikeEvent      => 2   -- Q0_16 (amplitude, phase)
  | geometricShape  => 4   -- Q16_16 (coordinates need integer range)
  | biologicalConc  => 2   -- Q0_16 (normalized concentrations)
  | electricalPot   => 4   -- Q16_16 (millivolts, counters)
  | magneticField   => 4   -- Q16_16 (intensity values)
  | thermalGradient => 2   -- Q0_16 (normalized gradients)
  | vibrational     => 2   -- Q0_16 (normalized frequencies)
  | visualPattern   => 2   -- Q0_16 (normalized color intensities)
  | geneticSequence => 1   -- Q0_8 (base pair indices)
  | routingControl  => 2   -- Q0_16 (trust scores, priorities)
  | verification    => 2   -- Q0_16 (error estimates)

/-- Default compression ratio target per channel -/
def compressionTarget (c : ChannelType) : Q0_16 :=
  match c with
  | symbolicText    => ⟨0x4000⟩  -- ~0.5 (2x)
  | spikeEvent      => ⟨0x2000⟩  -- ~0.25 (4x)
  | geometricShape  => ⟨0x2000⟩  -- ~0.25 (4x)
  | biologicalConc  => ⟨0x4000⟩  -- ~0.5 (2x)
  | electricalPot   => ⟨0x2000⟩  -- ~0.25 (4x)
  | magneticField   => ⟨0x4000⟩  -- ~0.5 (2x)
  | thermalGradient => ⟨0x4000⟩  -- ~0.5 (2x)
  | vibrational     => ⟨0x2000⟩  -- ~0.25 (4x)
  | visualPattern   => ⟨0x2000⟩  -- ~0.25 (4x)
  | geneticSequence => ⟨0x1000⟩  -- ~0.125 (8x)
  | routingControl  => ⟨0x4000⟩  -- ~0.5 (2x)
  | verification    => ⟨0x4000⟩  -- ~0.5 (2x)

end ChannelType

-- ============================================================================
-- Canonical Atom IR: Universal representation for all modalities
-- ============================================================================

/-- Spike polarity enumeration -/
inductive SpikePolarity : Type where
  | positive
  | negative
  | biphasic
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Cellular/biological compartment enumeration -/
inductive Compartment : Type where
  | cytoplasm
  | nucleus
  | mitochondrion
  | er            -- endoplasmic reticulum
  | extracellular
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Routing operation goals -/
inductive OperationGoal : Type where
  | health
  | compress
  | route
  | recover
  | attest
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Routing constraints for carrier selection -/
structure RoutingConstraints where
  maxLatencyMs   : UInt32
  minTrustScore  : Q0_16
  maxEnergyCost  : Q0_16
  encryptionReq  : Bool
  recoveryMode   : Bool
  deriving Repr, DecidableEq, BEq, Inhabited

/-- The universal intermediate representation: every channel input reduces here -/
inductive CanonicalAtom : Type where
  | spikeEvent (timestamp    : UInt64)    -- nanoseconds
               (channelId    : UInt32)
               (amplitude    : Q0_16)
               (width        : Q0_16)
               (polarity     : SpikePolarity)
               (phase        : Q0_16)

  | manifoldPoint (coord   : Q16_16 × Q16_16 × Q16_16)
                  (mass    : Q0_16)
                  (torsion : Q0_16)
                  (shell   : UInt32)

  | braidCrossing (index     : UInt16)
                  (sign      : Int8)
                  (timestamp : UInt64)

  | quaternionState (q      : Q0_16 × Q0_16 × Q0_16 × Q0_16)
                    (angVel : Q0_16 × Q0_16 × Q0_16)
                    (layer  : UInt8)

  | symbolicTerm (hash         : UInt64)
                 (complexity   : Q0_16)
                 (dependencyCount : UInt16)

  | concentrationDelta (speciesId    : UInt16)
                       (delta        : Q16_16)
                       (compartment  : Compartment)
                       (diffusionCoeff : Q0_16)

  | membranePotential (voltage      : Q16_16)
                      (channelState : UInt16)
                      (timestamp    : UInt64)

  | temporalWindow (start         : UInt64)
                   (duration      : UInt64)
                   (admissibility : Q0_16)

  | routingIntent (goal        : OperationGoal)
                  (priority    : Q0_16)
                  (constraints : RoutingConstraints)
  deriving Repr, DecidableEq, BEq, Inhabited

namespace CanonicalAtom

/-- Extract channel-appropriate channel type from atom -/
def channelType (a : CanonicalAtom) : ChannelType :=
  match a with
  | spikeEvent _ _ _ _ _ _        => ChannelType.spikeEvent
  | manifoldPoint _ _ _ _         => ChannelType.geometricShape
  | braidCrossing _ _ _           => ChannelType.geometricShape
  | quaternionState _ _ _         => ChannelType.geometricShape
  | symbolicTerm _ _ _              => ChannelType.symbolicText
  | concentrationDelta _ _ _ _      => ChannelType.biologicalConc
  | membranePotential _ _ _         => ChannelType.electricalPot
  | temporalWindow _ _ _            => ChannelType.spikeEvent
  | routingIntent _ _ _             => ChannelType.routingControl

/-- Timestamp accessor (zero for atoms without explicit time) -/
def timestamp (a : CanonicalAtom) : UInt64 :=
  match a with
  | spikeEvent t _ _ _ _ _        => t
  | braidCrossing _ _ t           => t
  | membranePotential _ _ t       => t
  | temporalWindow t _ _          => t
  | _                             => 0

/-- Priority accessor (normalized importance for routing) -/
def priority (a : CanonicalAtom) : Q0_16 :=
  match a with
  | routingIntent _ p _           => p
  | temporalWindow _ _ a          => a
  | _                             => ⟨0x4000⟩  -- default mid-priority

end CanonicalAtom

-- ============================================================================
-- Delta Encoding: Differential representation for compression
-- ============================================================================

/-- Delta-encoded atom for sequential compression -/
structure DeltaAtom where
  atomType      : UInt8      -- CanonicalAtom discriminant
  deltaFlags    : UInt16     -- Bitfield: which fields are delta-encoded
  baseReference : UInt32     -- 0 = absolute (keyframe)
  -- Delta fields (presence determined by deltaFlags bits)
  timestampDelta  : Option Int64
  coordDeltaX     : Option Int32
  coordDeltaY     : Option Int32
  coordDeltaZ     : Option Int32
  amplitudeDelta  : Option Int16
  idDelta         : Option Int32
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Keyframing strategy for delta extraction -/
inductive DeltaStrategy : Type where
  | periodic (n : Nat)           -- Keyframe every n atoms
  | adaptive (threshold : Q0_16) -- Keyframe when drift exceeds threshold
  | topologyChange               -- Keyframe at topological events
  deriving Repr, DecidableEq, BEq, Inhabited

namespace DeltaAtom

/-- Create absolute delta (no base reference) from canonical atom -/
def absolute (a : CanonicalAtom) : DeltaAtom :=
  { atomType := 0,  -- discriminant stored separately
    deltaFlags := 0,
    baseReference := 0,
    timestampDelta := none,
    coordDeltaX := none,
    coordDeltaY := none,
    coordDeltaZ := none,
    amplitudeDelta := none,
    idDelta := none }

/-- Estimate size in bytes for bandwidth calculations -/
def byteSize (d : DeltaAtom) : Nat :=
  4  -- fixed header (atomType + deltaFlags + baseReference overhead)
  + if d.timestampDelta.isSome then 8 else 0
  + if d.coordDeltaX.isSome then 4 else 0
  + if d.coordDeltaY.isSome then 4 else 0
  + if d.coordDeltaZ.isSome then 4 else 0
  + if d.amplitudeDelta.isSome then 2 else 0
  + if d.idDelta.isSome then 4 else 0

end DeltaAtom

-- ============================================================================
-- Compression Pipeline Types
-- ============================================================================

/-- Compression rule classification -/
inductive DeltaRule : Type where
  | identity         -- No compression (passthrough)
  | temporalDelta    -- Time-series delta encoding
  | spatialDelta     -- Coordinate delta encoding
  | topologicalDelta  -- Manifold coordinate delta (PIST-aware)
  | symbolicDelta     -- Expression tree diff
  | hybridDelta       -- Multi-modal combined
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Compressed payload with metadata -/
structure CompressedPayload where
  atomCount       : UInt16
  keyframeCount   : UInt16
  ruleUsed        : DeltaRule
  compressionRatio : Q0_16  -- output_size / input_size
  deriving Repr, DecidableEq, BEq, Inhabited

-- ============================================================================
-- Verification Types
-- ============================================================================

/-- Invariant classification: distinguishes proven from speculative claims -/
inductive ProofStatus : Type where
  | proven       -- Formal proof completed
  | checked      -- Checked by #eval / computation
  | wip          -- Work in progress
  | axiom        -- Accepted as axiom
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Invariant claim with classification -/
inductive InvariantClaim : Type where
  | implemented   (theorem      : String)
                  (proofStatus  : ProofStatus)
  | specification (formalModule : String)
                  (leanTheorem  : String)
  | hypothesis    (paperRef     : String)
                  (conjecture   : String)
  | unverified    (reason       : String)
                  (safetyBounds : String)
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Core invariant types for compression verification -/
inductive Invariant : Type where
  | compressionRatio  (target : Q0_16)
  | reconstructionError (epsilon : Q0_16)
  | timingAdmissibility (windowNs : UInt64)
  | phaseAlignment (maxError : Q0_16)
  | channelConsistency
  | routingTermination (maxHops : UInt8)
  | fixedPointDeterminism
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Verification check result per invariant -/
structure InvariantCheck where
  invariant : Invariant
  passed    : Bool
  detail    : String  -- e.g., "ratio=0.23, target=0.50"
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Full verification result for a compressed packet -/
structure VerificationResult where
  checks      : List InvariantCheck
  allPassed   : Bool
  compressionReceipt  : Q0_16 × Q0_16  -- (ratio, error estimate)
  topologyReceipt     : UInt64          -- barcode hash
  timingReceipt       : Q0_16           -- admissibility score
  deriving Repr, DecidableEq, BEq, Inhabited

-- ============================================================================
-- Packet Format (simplified for Lean formalization)
-- ============================================================================

/-- Transport packet header -/
structure PacketHeader where
  version       : UInt8  -- = 0x01
  channelType   : ChannelType
  sequenceNum   : UInt32
  timestamp     : UInt64
  sourceNode    : UInt64
  destNode      : UInt64
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Routing metadata embedded in packet -/
structure PacketRoutingMeta where
  goal         : OperationGoal
  trustScore   : Q0_16
  memBudgetKb  : UInt16
  bandwidthKbps : UInt16
  latencyMs     : UInt16
  hopCount      : UInt8
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Complete transport packet -/
structure TMCPPacket where
  header      : PacketHeader
  routingMeta : PacketRoutingMeta
  atoms       : List CanonicalAtom
  receipt     : VerificationResult
  deriving Repr, DecidableEq, BEq, Inhabited

namespace TMCPPacket

/-- Packet size estimate for memory budget checking -/
def estimatedSize (p : TMCPPacket) : Nat :=
  32   -- header
  + 16 -- routing meta
  + p.atoms.length * 32  -- approximate atom size
  + 32 -- receipt

/-- Required trust score for processing this packet -/
def requiredTrustScore (p : TMCPPacket) : Q0_16 :=
  p.routingMeta.trustScore

/-- Memory requirement in KB (ceiling division) -/
def memoryRequirementKb (p : TMCPPacket) : Nat :=
  (p.estimatedSize + 1023) / 1024

end TMCPPacket

-- ============================================================================
-- Routing Decision Types
-- ============================================================================

/-- Carrier types for MNN routing -/
inductive CarrierType : Type where
  | local
  | atlasNetwork
  | fileStorage
  | serialInterface
  | socketInterface
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Routing cost structure -/
structure RoutingCost where
  energy      : Q0_16
  time        : UInt32  -- milliseconds
  bandwidth   : UInt32  -- bytes
  risk        : Q0_16   -- 1 - reliability
  deriving Repr, DecidableEq, BEq, Inhabited

namespace RoutingCost

/-- Weighted total cost (equal weights in default) -/
def totalCost (c : RoutingCost) : Q0_16 :=
  -- Normalize each component and sum
  let e := c.energy
  let t := ⟨c.time.toUInt16⟩  -- saturating cast
  let b := ⟨c.bandwidth.toUInt16⟩
  let r := c.risk
  Q0_16.add (Q0_16.add e t) (Q0_16.add b r)

end RoutingCost

/-- MNN routing decisions -/
inductive RoutingDecision : Type where
  | localProcess
  | globalRoute   (carrier : CarrierType)
  | reject        (reason : UInt8)
  | recover       (retryDelayMs : UInt16)
  | attest        (validationHash : UInt64)
  | defer         (queuePriority : Q0_16)
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Local node state for routing decisions -/
structure NodeState where
  memoryAvailableKb : UInt32
  trustScore        : Q0_16
  capabilities      : List OperationGoal
  deriving Repr, DecidableEq, BEq, Inhabited

/-- Carrier metrics for cost computation -/
structure CarrierMetrics where
  latencyMs       : UInt16
  bandwidthKbps   : UInt16
  reliability     : Q0_16
  energyPerByte   : Q0_16
  deriving Repr, DecidableEq, BEq, Inhabited

-- ============================================================================
-- #eval verification examples
-- ============================================================================

/-- Example: Verify Q0_16 compression target for symbolic text -/
#eval ChannelType.compressionTarget ChannelType.symbolicText

/-- Example: Verify spike event precision tier -/
#eval ChannelType.precisionTier ChannelType.spikeEvent

/-- Example: Construct a spike event atom -/
#eval CanonicalAtom.spikeEvent 1000000 42 ⟨0x7FFF⟩ ⟨0x2000⟩ SpikePolarity.positive ⟨0x0000⟩

/-- Example: Verify delta atom size calculation -/
#eval let d : DeltaAtom := { absolute (CanonicalAtom.spikeEvent 0 0 ⟨0⟩ ⟨0⟩ SpikePolarity.positive ⟨0⟩) with
                              timestampDelta := some 1000 }
      DeltaAtom.byteSize d

/-- Example: Verify channel type extraction -/
#eval CanonicalAtom.channelType (CanonicalAtom.spikeEvent 0 0 ⟨0⟩ ⟨0⟩ SpikePolarity.positive ⟨0⟩)

/-- Example: Compute routing cost total -/
#eval let c : RoutingCost := { energy := ⟨0x1000⟩, time := 50, bandwidth := 1024, risk := ⟨0x0100⟩ }
      RoutingCost.totalCost c

end Semantics.TMMCP

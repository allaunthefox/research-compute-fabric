/-
  FullMasterMassNumberReduction.lean

  Collapse the full master equation field into a single shell-addressable
  mass-number field.

  Core law:
    Do the expensive reasoning once, collapse it into A = Z + N,
    then let S3C / PIST / FAMM / BHOCS route the mass cheaply.

  Claim boundary:
  - This module is a routing/specification reducer, not a proof that the
    upstream COUCH, BHOCS, UDRS, Phi, or PIST scores are themselves valid.
  - S3C owns exact shell coordinates: k = floor(sqrt A), a, b0, bPlus.
  - Phi/PIST/BHOCS/FAMM may route or witness the mass field, but they do not
    redefine S3C shell arithmetic.
  - Q16.16 values are converted to integer mass packets by reading their
    underlying fixed-point storage as unsigned load.
-/

import Mathlib.Data.Nat.Basic
import Semantics.FixedPoint

namespace Semantics.FullMasterMassNumberReduction

open Semantics.Q16_16

/-- Components of the upstream full master score before mass reduction. -/
structure FullMasterComponents where
  phiWeighted   : Q16_16  -- Phi-S3C shell comparison cost
  pistLyapunov  : Q16_16  -- PIST witness-state Lyapunov cost
  udrsEnergy    : Q16_16  -- Unit-Distance Ripple Sieve energy
  torusDistance : Q16_16  -- 5D torus routing distance
  couchPhi      : Q16_16  -- COUCH hysteresis/scar yield
  bhocsCost     : Q16_16  -- BHOCS bounded storage/access cost
  deriving Repr, Inhabited

/-- Component weights for the full master score. -/
structure FullMasterWeights where
  phiWeight   : Q16_16
  pistWeight  : Q16_16
  udrsWeight  : Q16_16
  torusWeight : Q16_16
  couchWeight : Q16_16
  bhocsWeight : Q16_16
  deriving Repr, Inhabited

/-- Direction of Z/N imbalance. Q16_16 itself is unsigned in the hot path. -/
inductive BiasSign where
  | structuredHeavy  -- Z > N: control/witness/archive mass dominates
  | balanced         -- Z = N or within external tolerance
  | stressHeavy      -- N > Z: dynamics/residual/drain mass dominates
  deriving Repr, DecidableEq, Inhabited

/-- Operational phase after S3C shell and Z/N bias classification. -/
inductive MassPhase where
  | grounded
  | driftBalanced
  | structuredDrift
  | stressDrift
  | seismic
  deriving Repr, DecidableEq, Inhabited

/-- Downstream route selected from the collapsed mass-number field. -/
inductive MassRoute where
  | promote
  | standard
  | bhocsCommit
  | fammDrain
  | quarantine
  deriving Repr, DecidableEq, Inhabited

/-- Weighted mass packets before Z/N collapse. -/
structure ComponentMassPackets where
  phiMass   : Nat
  pistMass  : Nat
  udrsMass  : Nat
  torusMass : Nat
  couchMass : Nat
  bhocsMass : Nat
  deriving Repr, Inhabited

/-- S3C shell address for a total mass number A. -/
structure S3CShellAddress where
  totalMass : Nat  -- A = Z + N
  shellK    : Nat  -- k = floor(sqrt A)
  shellA    : Nat  -- a = A - k^2
  shellB0   : Nat  -- b0 = (k+1)^2 - 1 - A, closed shell
  shellBPlus : Nat -- b+ = (k+1)^2 - A, open shell
  mass0     : Nat  -- m0 = a * b0, closed/throat activation
  massPlus  : Nat  -- m+ = a * b+, open/next-shell tension
  deriving Repr, Inhabited

/-- The single collapsed field consumed by S3C/PIST/FAMM/BHOCS routing. -/
structure MassNumberField where
  packets    : ComponentMassPackets
  zField     : Nat       -- structured/control/witness mass
  nField     : Nat       -- stress/dynamics/residual mass
  aField     : Nat       -- total mass, A = Z + N
  biasSign   : BiasSign
  biasQ16    : Q16_16    -- |Z - N| / (A + 1), magnitude only
  shell      : S3CShellAddress
  rhoQ16     : Q16_16    -- 4*m0 / (2*k+1)^2
  phase      : MassPhase
  route      : MassRoute
  deriving Repr, Inhabited

/-- Q16.16 half threshold used for DRIFT/SEISMIC split. -/
def halfQ16 : Q16_16 := ofNat 32768

/-- Convert a Q16.16 fixed-point value into an unsigned integer mass packet. -/
def q16ToMass (x : Q16_16) : Nat :=
  x.val.toNat

/-- Absolute Nat difference. -/
def natAbsDiff (a b : Nat) : Nat :=
  if a ≥ b then a - b else b - a

/-- Bias sign from structured mass Z and stress mass N. -/
def biasSignOf (z n : Nat) : BiasSign :=
  if z > n then .structuredHeavy
  else if n > z then .stressHeavy
  else .balanced

/-- Bias magnitude |Z-N|/(A+1), represented as Q16.16. -/
def biasMagnitudeQ16 (z n a : Nat) : Q16_16 :=
  div (ofNat (natAbsDiff z n)) (ofNat (a + 1))

/-- S3C shell decomposition for a total mass A. -/
def s3cShellAddress (A : Nat) : S3CShellAddress :=
  let k := Nat.sqrt A
  let a := A - k * k
  let kp1sq := (k + 1) * (k + 1)
  let b0 := kp1sq - 1 - A
  let bPlus := kp1sq - A
  let m0 := a * b0
  let mPlus := a * bPlus
  {
    totalMass := A,
    shellK := k,
    shellA := a,
    shellB0 := b0,
    shellBPlus := bPlus,
    mass0 := m0,
    massPlus := mPlus
  }

/-- Normalized shell density/tension rho_A = 4*m0 / (2*k+1)^2. -/
def rhoA (s : S3CShellAddress) : Q16_16 :=
  let denom := (2 * s.shellK + 1) * (2 * s.shellK + 1)
  if denom = 0 then zero else div (ofNat (4 * s.mass0)) (ofNat denom)

/-- Build weighted component mass packets from full master components. -/
def componentMassPackets
  (c : FullMasterComponents)
  (w : FullMasterWeights) : ComponentMassPackets :=
  {
    phiMass := q16ToMass (w.phiWeight * c.phiWeighted),
    pistMass := q16ToMass (w.pistWeight * c.pistLyapunov),
    udrsMass := q16ToMass (w.udrsWeight * c.udrsEnergy),
    torusMass := q16ToMass (w.torusWeight * c.torusDistance),
    couchMass := q16ToMass (w.couchWeight * c.couchPhi),
    bhocsMass := q16ToMass (w.bhocsWeight * c.bhocsCost)
  }

/-- Structured/control/witness mass: Z = Phi + PIST + BHOCS. -/
def zMass (p : ComponentMassPackets) : Nat :=
  p.phiMass + p.pistMass + p.bhocsMass

/-- Stress/dynamics/residual mass: N = UDRS + T5 + COUCH. -/
def nMass (p : ComponentMassPackets) : Nat :=
  p.udrsMass + p.torusMass + p.couchMass

/-- Phase classifier over shell density and Z/N bias. -/
def classifyMassPhase
  (shell : S3CShellAddress)
  (rho biasMagnitude beta : Q16_16)
  (sign : BiasSign) : MassPhase :=
  if shell.mass0 = 0 then .grounded
  else if rho < halfQ16 then
    if biasMagnitude < beta then .driftBalanced
    else match sign with
      | .structuredHeavy => .structuredDrift
      | .stressHeavy => .stressDrift
      | .balanced => .driftBalanced
  else .seismic

/-- Route selected by phase. -/
def routeForPhase : MassPhase → MassRoute
  | .grounded => .promote
  | .driftBalanced => .standard
  | .structuredDrift => .bhocsCommit
  | .stressDrift => .fammDrain
  | .seismic => .quarantine

/-- Collapse the full master components into one shell-addressable mass field. -/
def reduceToMassNumberField
  (c : FullMasterComponents)
  (w : FullMasterWeights)
  (beta : Q16_16) : MassNumberField :=
  let packets := componentMassPackets c w
  let z := zMass packets
  let n := nMass packets
  let A := z + n
  let sign := biasSignOf z n
  let bias := biasMagnitudeQ16 z n A
  let shell := s3cShellAddress A
  let rho := rhoA shell
  let phase := classifyMassPhase shell rho bias beta sign
  let route := routeForPhase phase
  {
    packets := packets,
    zField := z,
    nField := n,
    aField := A,
    biasSign := sign,
    biasQ16 := bias,
    shell := shell,
    rhoQ16 := rho,
    phase := phase,
    route := route
  }

/-- Collapsed-field survival: routing is considered safe unless quarantined. -/
def survivesCollapsedField (m : MassNumberField) : Bool :=
  m.route ≠ .quarantine

/-- Promotion predicate for the collapsed field. -/
def promotesCollapsedField (m : MassNumberField) : Bool :=
  m.route = .promote

/-- Example using the canonical A = 458752 decomposition from the spec notes. -/
def exampleShellAddress : S3CShellAddress :=
  s3cShellAddress 458752

#eval exampleShellAddress.shellK     -- 677
#eval exampleShellAddress.shellA     -- 423
#eval exampleShellAddress.shellB0    -- 931
#eval exampleShellAddress.shellBPlus -- 932
#eval exampleShellAddress.mass0      -- 393813
#eval exampleShellAddress.massPlus   -- 394236

end Semantics.FullMasterMassNumberReduction

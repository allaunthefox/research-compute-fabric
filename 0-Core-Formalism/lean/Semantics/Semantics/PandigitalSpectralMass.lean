/-
  PandigitalSpectralMass.lean — Compact "pandigital" representations for eigenvectors
  and semantic mass.

  Core insight: Just as π = 3.8415926 - 0.7 uses each digit once,
  eigenvectors and mass triples can be encoded with minimal unique components
  and reconstructed via simple operations.

  Three compression strategies:
  1. ContinuedFractionEigenvector - Store convergents, not floats
  2. ZNCompactMass - Pack (Z, N) into single value, derive A = Z + N
  3. SpectralMassFusion - Eigenvectors with semantic mass weights

  Domain: LAYER_D_INVARIANTS (geometric_bind)
  Per AGENTS.md §1.4: Uses Q16_16 for hardware-native computation.
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Tactic
import Semantics.FixedPoint

namespace Semantics.PandigitalSpectralMass

open Semantics.Q16_16
open Semantics.FixedPoint.PandigitalPi

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Continued Fraction Eigenvector Components
-- ═══════════════════════════════════════════════════════════════════════════

structure CFConvergent where
  num : Nat
  den : Nat
  deriving Repr, DecidableEq, Inhabited

def cfConvergentToQ16 (cf : CFConvergent) : Q16_16 :=
  if cf.den = 0 then zero
  else ofRatio cf.num cf.den

def phiConvergents : List CFConvergent := [
  ⟨1, 1⟩,
  ⟨2, 1⟩,
  ⟨3, 2⟩,
  ⟨5, 3⟩,
  ⟨8, 5⟩,
  ⟨13, 8⟩,
  ⟨21, 13⟩,
  ⟨34, 21⟩,
  ⟨55, 34⟩,
  ⟨89, 55⟩
]

def piConvergents : List CFConvergent := [
  ⟨3, 1⟩,
  ⟨22, 7⟩,
  ⟨333, 106⟩,
  ⟨355, 113⟩,
  ⟨103993, 33102⟩
]

def selectConvergent (convergents : List CFConvergent) (target : Q16_16) (tolerance : Q16_16) : CFConvergent :=
  match convergents with
  | [] => ⟨0, 1⟩
  | cf :: rest =>
    let reconstructed := cfConvergentToQ16 cf
    if abs (reconstructed - target) ≤ tolerance then
      cf
    else
      selectConvergent rest target tolerance

-- Verification: 355/113 is within Q16.16 resolution of pandigital pi
#eval cfConvergentToQ16 ⟨355, 113⟩
#eval abs (cfConvergentToQ16 ⟨355, 113⟩ - PandigitalPi.piPandigital)

-- ═══════════════════════════════════════════════════════════════════════════
-- §1.5  Mass Number Type Definitions (Local to avoid otom dependency)
-- ═══════════════════════════════════════════════════════════════════════════

inductive BiasSign where
  | structuredHeavy
  | balanced
  | stressHeavy
  deriving Repr, DecidableEq, Inhabited

inductive MassPhase where
  | grounded
  | driftBalanced
  | structuredDrift
  | stressDrift
  | seismic
  deriving Repr, DecidableEq, Inhabited

inductive MassRoute where
  | promote
  | standard
  | bhocsCommit
  | fammDrain
  | quarantine
  deriving Repr, DecidableEq, Inhabited

structure S3CShellAddress where
  totalMass : Nat
  shellK    : Nat
  shellA    : Nat
  shellB0   : Nat
  shellBPlus : Nat
  mass0     : Nat
  massPlus  : Nat
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Compact Z/N Mass Encoding (Pandigital-Style)
-- ═══════════════════════════════════════════════════════════════════════════

/--
Compact encoding of (Z, N) mass pair into a single Q16_16.

Encoding stores the packed value Z*65536+N directly in `val`,
bypassing Q16.16 arithmetic scaling. This is a pure bit-pattern
storage trick, not a fixed-point value.

Constraints: Z < 65536, N < 65536 ensures Z*65536+N < 2^32.
Space: 4 bytes stores both Z and N (vs 8 bytes separate).
-/
def encodeZNCompact (Z N : Nat) : Q16_16 :=
  let packed : Nat := min Z 65535 * 65536 + min N 65535
  ⟨packed.toUInt32⟩

/--
Decode compact Z/N encoding by reading val.toNat.
Recovers Z = raw / 65536, N = raw % 65536.
-/
def decodeZNCompact (compact : Q16_16) : (Nat × Nat) :=
  let raw := compact.val.toNat
  (raw / 65536, raw % 65536)

/--
Round-trip: for Z, N < 65536, encoding then decoding recovers the original pair.

Proof uses the well-formedness of the packed value (UInt32 round-trip via <2^32)
and the standard Nat division lemma via `Nat.div_add_mod`.
-/
theorem znRoundTrip (Z N : Nat) (hZ : Z < 65536) (hN : N < 65536) :
  decodeZNCompact (encodeZNCompact Z N) = (Z, N) := by
  unfold encodeZNCompact decodeZNCompact
  have hzp : min Z 65535 = Z := Nat.min_eq_left (by omega)
  have hnp : min N 65535 = N := Nat.min_eq_left (by omega)
  rw [hzp, hnp]
  have h_packed_lt : Z * 65536 + N < 4294967296 := by
    have hZ' : Z ≤ 65535 := by omega
    have hN' : N ≤ 65535 := by omega
    nlinarith
  have hmod_2_32 : (Z * 65536 + N) % 4294967296 = Z * 65536 + N :=
    Nat.mod_eq_of_lt h_packed_lt
  have htoNat : ((Z * 65536 + N).toUInt32).toNat = Z * 65536 + N := by
    simp [UInt32.toNat_ofNat, hmod_2_32]
  rw [htoNat]
  have hdiv : (Z * 65536 + N) / 65536 = Z := by
    omega
  have hmod_65536 : (Z * 65536 + N) % 65536 = N := by
    omega
  simp [hdiv, hmod_65536]

/-- Derive total mass A from compact encoding -/
def deriveAFromCompact (compact : Q16_16) : Nat :=
  let (Z, N) := decodeZNCompact compact
  Z + N

/-- Derive bias sign from compact encoding -/
def deriveBiasFromCompact (compact : Q16_16) : BiasSign :=
  let (Z, N) := decodeZNCompact compact
  if Z > N then .structuredHeavy
  else if N > Z then .stressHeavy
  else .balanced

-- Example encodings
#eval encodeZNCompact 400 100
#eval deriveAFromCompact (encodeZNCompact 400 100)
#eval deriveBiasFromCompact (encodeZNCompact 400 100)

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Spectral-Mass Eigenvector (Pandigital Fusion)
-- ═══════════════════════════════════════════════════════════════════════════

structure SpectralMassComponent where
  cf : CFConvergent
  massWeight : Q16_16
  phase : Q16_16
  deriving Repr, Inhabited

def reconstructComponent (smc : SpectralMassComponent) : Q16_16 :=
  let rationalPart := cfConvergentToQ16 smc.cf
  rationalPart * smc.massWeight

structure SparseSpectralEigenvector (n : Nat) where
  dimension : Nat
  nonZeroCount : Nat
  components : Fin nonZeroCount → SpectralMassComponent
  indices : Fin nonZeroCount → Fin n
  deriving Repr

def reconstructEigenvectorComponent {n : Nat} (_v : SparseSpectralEigenvector n) (_i : Fin n) : Q16_16 :=
  zero

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Pandigital Mass Number Field (Compact Collapsed Field)
-- ═══════════════════════════════════════════════════════════════════════════

structure PandigitalMassField where
  znCompact : Q16_16
  shellK : Nat
  lyapunovResidual : Q16_16
  deriving Repr, Inhabited

def fromFullComponents (Z N : Nat) (lyap : Q16_16) : PandigitalMassField :=
  let compact := encodeZNCompact Z N
  let A := Z + N
  let k := Nat.sqrt A
  { znCompact := compact, shellK := k, lyapunovResidual := lyap }

def reconstructShellAddress (pmf : PandigitalMassField) : S3CShellAddress :=
  let (Z, N) := decodeZNCompact pmf.znCompact
  let A := Z + N
  let k := pmf.shellK
  let a := A - k * k
  let b0 := (k + 1) * (k + 1) - 1 - A
  let bPlus := (k + 1) * (k + 1) - A
  let m0 := a * b0
  let mPlus := a * bPlus
  { totalMass := A, shellK := k, shellA := a, shellB0 := b0, shellBPlus := bPlus, mass0 := m0, massPlus := mPlus }

def deriveMassPhase (pmf : PandigitalMassField) : MassPhase :=
  let (Z, N) := decodeZNCompact pmf.znCompact
  let A := Z + N
  if pmf.lyapunovResidual > ofNat 50000 then
    .seismic
  else if Z > N && Z > A / 3 then
    .structuredDrift
  else if N > Z && N > A / 3 then
    .stressDrift
  else
    .driftBalanced

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Verification and Examples
-- ═══════════════════════════════════════════════════════════════════════════

def exampleCompact400k : Q16_16 := encodeZNCompact 400000 100000
#eval exampleCompact400k.val.toNat

def exampleCompactSmall : Q16_16 := encodeZNCompact 400 100
#eval exampleCompactSmall.val.toNat
#eval deriveAFromCompact exampleCompactSmall
#eval deriveBiasFromCompact exampleCompactSmall

def examplePiComponent : SpectralMassComponent := {
  cf := ⟨355, 113⟩,
  massWeight := Q16_16.one,
  phase := zero
}
#eval reconstructComponent examplePiComponent

def examplePhiWeightedComponent : SpectralMassComponent := {
  cf := ⟨355, 113⟩,
  massWeight := ofNat 106039,
  phase := zero
}
#eval reconstructComponent examplePhiWeightedComponent

end Semantics.PandigitalSpectralMass

namespace Semantics
export PandigitalSpectralMass (
  CFConvergent cfConvergentToQ16
  piConvergents phiConvergents selectConvergent
  encodeZNCompact decodeZNCompact deriveAFromCompact deriveBiasFromCompact
  SpectralMassComponent reconstructComponent
  SparseSpectralEigenvector
  PandigitalMassField fromFullComponents reconstructShellAddress deriveMassPhase
)
end Semantics

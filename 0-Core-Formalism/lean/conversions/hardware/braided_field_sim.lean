/-!
Braided Field Simulation — Polaron-Polariton Topological Quantum Mechanics

Original Python: 4-Infrastructure/hardware/braided_field_sim.py
Converts the braided field simulation to Lean 4 with Q16_16 fixed-point.
-/

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Q16_16 Fixed-Point Arithmetic (32-bit: 16 integer + 16 fractional)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Q16_16: 32-bit fixed-point, value = raw / 2^16, range ≈ [-32768, 32767]. -/
structure Q16_16 where
  raw : Int
  deriving Repr, BEq

namespace Q16_16

def pi : Q16_16 := ⟨205887⟩
def twoPi : Q16_16 := ⟨411775⟩
def halfPi : Q16_16 := ⟨102944⟩
def piOver3 : Q16_16 := ⟨68629⟩
def piOver4 : Q16_16 := ⟨51472⟩
def zero : Q16_16 := ⟨0⟩
def one : Q16_16 := ⟨65536⟩
def half : Q16_16 := ⟨32768⟩
def point3 : Q16_16 := ⟨19661⟩
def point2 : Q16_16 := ⟨13107⟩

def ofRat (num den : Nat) : Q16_16 :=
  if h : den ≠ 0 then
    let n : Int := (num : Int) * 65536
    let d : Int := (den : Int)
    ⟨n / d⟩
  else zero

def add (a b : Q16_16) : Q16_16 := ⟨a.raw + b.raw⟩
def sub (a b : Q16_16) : Q16_16 := ⟨a.raw - b.raw⟩
def mul (a b : Q16_16) : Q16_16 := ⟨(a.raw * b.raw) / 65536⟩
def neg (a : Q16_16) : Q16_16 := ⟨-a.raw⟩
def isZero (a : Q16_16) : Bool := a.raw = 0

instance : Add Q16_16 := ⟨add⟩
instance : Sub Q16_16 := ⟨sub⟩
instance : Mul Q16_16 := ⟨mul⟩
instance : Neg Q16_16 := ⟨neg⟩
instance : OfNat Q16_16 0 := ⟨zero⟩
instance : OfNat Q16_16 1 := ⟨one⟩

end Q16_16


-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Complex Numbers in Q16_16
-- ═══════════════════════════════════════════════════════════════════════════

structure ComplexQ where
  re : Q16_16
  im : Q16_16
  deriving Repr

namespace ComplexQ

def zero : ComplexQ := ⟨Q16_16.zero, Q16_16.zero⟩
def one : ComplexQ := ⟨Q16_16.one, Q16_16.zero⟩

def add (a b : ComplexQ) : ComplexQ :=
  ⟨a.re + b.re, a.im + b.im⟩

def mul (a b : ComplexQ) : ComplexQ :=
  ⟨a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re⟩

def magSq (z : ComplexQ) : Q16_16 :=
  z.re * z.re + z.im * z.im

/-- Complex exponent e^{iθ} via small-angle series. -/
def expI (theta : Q16_16) : ComplexQ :=
  let thetaSq : Q16_16 := theta * theta
  let cos : Q16_16 := Q16_16.one - thetaSq * Q16_16.half
  let sin : Q16_16 := theta - (thetaSq * theta) * Q16_16.ofRat 1 6
  ⟨cos, sin⟩

instance : Add ComplexQ := ⟨add⟩
instance : Mul ComplexQ := ⟨mul⟩

end ComplexQ


-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Quasiparticle
-- ═══════════════════════════════════════════════════════════════════════════

structure Pos2D where
  x : Q16_16
  y : Q16_16
  deriving Repr

structure Quasiparticle where
  position : Pos2D
  phase : Q16_16
  particleType : Nat
  deriving Repr


-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Braiding Operation
-- ═══════════════════════════════════════════════════════════════════════════

structure Braiding where
  i : Nat
  j : Nat
  phaseShift : Q16_16
  deriving Repr


-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Hamiltonian
-- ═══════════════════════════════════════════════════════════════════════════

structure Hamiltonian where
  photonEnergyCoeff   : Q16_16
  electronEnergyCoeff : Q16_16
  phononEnergyCoeff   : Q16_16
  interactionCoeff    : Q16_16
  deriving Repr

namespace Hamiltonian

def default : Hamiltonian :=
  { photonEnergyCoeff   := Q16_16.one
    electronEnergyCoeff := Q16_16.half
    phononEnergyCoeff   := Q16_16.point3
    interactionCoeff    := Q16_16.point2
  }

def totalEnergy (h : Hamiltonian) (psiSq : Q16_16) : Q16_16 :=
  h.photonEnergyCoeff * psiSq + h.electronEnergyCoeff * psiSq +
  h.phononEnergyCoeff * psiSq + h.interactionCoeff * (psiSq * psiSq)

end Hamiltonian


-- ═══════════════════════════════════════════════════════════════════════════
-- §5  BraidedField
-- ═══════════════════════════════════════════════════════════════════════════

structure BraidedField where
  particles : List Quasiparticle
  braidingHistory : List Braiding
  hamiltonian : Hamiltonian
  magneticField : Q16_16
  deriving Repr

namespace BraidedField

def new (particles : List Quasiparticle) (h : Hamiltonian) : BraidedField :=
  { particles := particles
    braidingHistory := []
    hamiltonian := h
    magneticField := Q16_16.zero
  }

/-- Compute the total wavefunction as the sum of e^(i·phase) for each particle. -/
def totalWavefunction (bf : BraidedField) : ComplexQ :=
  List.foldl (fun (acc : ComplexQ) (p : Quasiparticle) => ComplexQ.add acc (ComplexQ.expI p.phase)) ComplexQ.zero bf.particles

/-- Compute the total energy of the field. -/
def totalEnergy (bf : BraidedField) : Q16_16 :=
  let psiSq := ComplexQ.magSq (totalWavefunction bf)
  Hamiltonian.totalEnergy bf.hamiltonian psiSq

/-- Compute the topological invariant as the sum of all phase shifts. -/
def topologicalInvariant (bf : BraidedField) : Q16_16 :=
  List.foldl (fun (acc : Q16_16) (b : Braiding) => acc + b.phaseShift) Q16_16.zero bf.braidingHistory

/-- Check if this field is a protection candidate. -/
def isProtectionCandidate (bf : BraidedField) : Bool :=
  ¬ Q16_16.isZero (topologicalInvariant bf) ∧ ¬ Q16_16.isZero bf.magneticField

end BraidedField


-- ═══════════════════════════════════════════════════════════════════════════
-- §6  PolaronPolariton
-- ═══════════════════════════════════════════════════════════════════════════

structure PolaronPolariton where
  photonComponent   : ComplexQ
  electronComponent : ComplexQ
  phononComponent   : ComplexQ
  position          : Pos2D
  statisticsParam   : Q16_16
  deriving Repr

namespace PolaronPolariton

def new (pos : Pos2D) (theta : Q16_16) : PolaronPolariton :=
  { photonComponent   := ComplexQ.one
    electronComponent := ComplexQ.one
    phononComponent   := ComplexQ.one
    position          := pos
    statisticsParam   := theta
  }

def wavefunction (pp : PolaronPolariton) : ComplexQ :=
  pp.photonComponent + pp.electronComponent + pp.phononComponent

def effectiveMass (pp : PolaronPolariton) : Q16_16 :=
  Q16_16.one + ComplexQ.magSq pp.phononComponent * Q16_16.half

def braid (pp1 pp2 : PolaronPolariton) : PolaronPolariton × PolaronPolariton :=
  let phase := ComplexQ.expI pp1.statisticsParam
  let braided1 : PolaronPolariton :=
    { pp1 with
      photonComponent   := ComplexQ.mul pp1.photonComponent phase
      electronComponent := ComplexQ.mul pp1.electronComponent phase
      phononComponent   := ComplexQ.mul pp1.phononComponent phase
    }
  let braided2 : PolaronPolariton :=
    { pp2 with
      photonComponent   := ComplexQ.mul pp2.photonComponent phase
      electronComponent := ComplexQ.mul pp2.electronComponent phase
      phononComponent   := ComplexQ.mul pp2.phononComponent phase
    }
  (braided1, braided2)

end PolaronPolariton


-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Verification with #eval
-- ═══════════════════════════════════════════════════════════════════════════

#eval Q16_16.pi
#eval Q16_16.halfPi
#eval Q16_16.one + Q16_16.half
#eval Q16_16.one * Q16_16.half
#eval ComplexQ.expI Q16_16.zero
#eval ComplexQ.expI Q16_16.halfPi
#eval ComplexQ.expI Q16_16.pi

-- Define demo field with 3 quasiparticles
def demoField : BraidedField :=
  let p0 : Quasiparticle := { position := ⟨Q16_16.zero, Q16_16.zero⟩, phase := Q16_16.zero, particleType := 0 }
  let p1 : Quasiparticle := { position := ⟨Q16_16.one, Q16_16.zero⟩, phase := Q16_16.zero, particleType := 1 }
  let p2 : Quasiparticle := { position := ⟨Q16_16.half, Q16_16.one⟩, phase := Q16_16.zero, particleType := 2 }
  BraidedField.new [p0, p1, p2] Hamiltonian.default

#eval demoField.particles.length
#eval demoField.braidingHistory.length

-- Apply braiding 0↔1 with π/2
def field1 : BraidedField :=
  { demoField with
    braidingHistory := [⟨0, 1, Q16_16.halfPi⟩]
  }

#eval BraidedField.topologicalInvariant field1

-- With magnetic field applied
def fieldWithB : BraidedField :=
  { field1 with magneticField := Q16_16.one }

#eval BraidedField.isProtectionCandidate field1
#eval BraidedField.isProtectionCandidate fieldWithB

-- Polaron-polariton demo
def pp1 : PolaronPolariton := PolaronPolariton.new (⟨Q16_16.zero, Q16_16.zero⟩) Q16_16.piOver4
def pp2 : PolaronPolariton := PolaronPolariton.new (⟨Q16_16.one, Q16_16.zero⟩) Q16_16.piOver4

#eval PolaronPolariton.effectiveMass pp1

-- ============================================================================
-- THEOREM: The topological invariant is the sum of all phase shifts
-- ============================================================================

/-- The topological invariant of a field with a single braiding equals the phase shift. -/
theorem topological_invariant_single (i j : Nat) (θ : Q16_16) :
    BraidedField.topologicalInvariant { particles := []
      , braidingHistory := [⟨i, j, θ⟩]
      , hamiltonian := Hamiltonian.default
      , magneticField := Q16_16.zero } = θ :=
  rfl

/-- The topological invariant of a field after appending a braiding.
    Proof: topologicalInvariant is defined as foldl (+) 0 over braidingHistory,
    and appending to the list means the fold includes the new element. -/
theorem topological_invariant_append (bf : BraidedField) (i j : Nat) (θ : Q16_16) :
    BraidedField.topologicalInvariant { bf with braidingHistory := bf.braidingHistory ++ [⟨i, j, θ⟩] } =
    BraidedField.topologicalInvariant bf + θ :=
  by
    simp [BraidedField.topologicalInvariant, List.foldl_append]

#eval "Braided field simulation successfully converted to Lean 4!"

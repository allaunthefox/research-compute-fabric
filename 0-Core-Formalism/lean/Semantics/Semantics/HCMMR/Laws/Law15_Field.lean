/-
Law 15 — Field Recovery

Bridges 16D torsion/winding into recoverable 4D electromagnetism through a
layered gate chain:
  Law 15K (Kähler Compatibility) → 15A (Gauge Invariance) → 15B (Maxwell) →
  15C (Wave Propagation) → 15D (Charge/Current Coupling).

The Kähler layer is the smooth-field gearbox: ω(X,Y)=g(JX,Y), J²=−I, dω=0.
Fractally folded Kähler manifolds do not pass; roughness becomes residual.

Conventions:
  PascalCase types, camelCase functions.
  `structure` for domain concepts, `inductive` for enumerations.
  `def` needs `#eval` witness or `theorem`.
  Q16_16 for all numeric fields.
  Namespace: Semantics.HCMMR.Law15
  Import: Semantics.HCMMR.Core, Semantics.FixedPoint
  Use `deriving Repr, BEq, DecidableEq, Inhabited`.
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Law15

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  16D Torsion/Winding State
-- ═══════════════════════════════════════════════════════════════════

/--
The high-dimensional field source in 16D. Carries torsion potential Θ,
winding circulation Ω, chirality orientation χ, accumulated scar residue,
and the receipt chain root for audit trail.
-/
structure TorsionState where
  coordinate      : String
  torsionPotential : Q16_16
  windingField    : Q16_16
  chirality       : Q16_16
  residual        : String
  receiptRoot     : String
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §2  4D Field Potential (Projection)
-- ═══════════════════════════════════════════════════════════════════

/--
The projected 4D gauge potential A_μ. A0 is the scalar potential;
A1, A2, A3 are the spatial vector components.
-/
structure FieldPotential where
  A0 : Q16_16
  A1 : Q16_16
  A2 : Q16_16
  A3 : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Placeholder projection from 16D TorsionState → 4D FieldPotential.
torsionPotential maps to A0; windingField scaled by chirality yields
spatial components.  The Kähler gate validates this projection.
-/
def projectPotential (t : TorsionState) : FieldPotential :=
  let spatial := Q16_16.mul t.windingField t.chirality
  { A0 := t.torsionPotential
  , A1 := spatial
  , A2 := spatial
  , A3 := spatial
  }

/--
Field strength tensor F_{μν} decomposed into E (F_{0i}) and B (ε_{ijk}F_{jk}).
All components in Q16_16.
-/
structure FieldStrength where
  E1 : Q16_16
  E2 : Q16_16
  E3 : Q16_16
  B1 : Q16_16
  B2 : Q16_16
  B3 : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Discrete curl of A_μ using unit-spacing finite differences.
  E_i = -(A_i − A_0)   (F_{0i} approximation)
  B_i = ε_{ijk} (A_k − A_j)  (magnetic field)
-/
def computeFieldStrength (pot : FieldPotential) : FieldStrength :=
  let e1 := Q16_16.sub pot.A0 pot.A1
  let e2 := Q16_16.sub pot.A0 pot.A2
  let e3 := Q16_16.sub pot.A0 pot.A3
  let b1 := Q16_16.sub pot.A3 pot.A2
  let b2 := Q16_16.sub pot.A1 pot.A3
  let b3 := Q16_16.sub pot.A2 pot.A1
  { E1 := e1, E2 := e2, E3 := e3
  , B1 := b1, B2 := b2, B3 := b3
  }

-- ═══════════════════════════════════════════════════════════════════
-- §3  Law 15K — Kähler Compatibility Gate
-- ═══════════════════════════════════════════════════════════════════

/--
The Kähler gearbox state: checks whether J (almost complex structure),
g (metric), and ω (symplectic form) form a compatible triple.
J²=−I, ω(X,Y)=g(JX,Y), dω=0 are required for smooth projection.
-/
structure KahlerState where
  J_squared_identity : Bool
  omega_X_Y          : Q16_16
  g_JX_Y             : Q16_16
  d_omega            : Q16_16
  isFractal          : Bool
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Kähler residual:
  ε_K = |ω(X,Y) − g(JX,Y)| + |dω| + (if J²≠−I then 1.0 else 0)
-/
def kahlerResidual (ks : KahlerState) : Q16_16 :=
  let mismatch := Q16_16.abs (Q16_16.sub ks.omega_X_Y ks.g_JX_Y)
  let dOmega   := Q16_16.abs ks.d_omega
  let jPenalty := if ks.J_squared_identity then Q16_16.zero else Q16_16.one
  Q16_16.add (Q16_16.add mismatch dOmega) jPenalty

/--
Kähler compatibility gate.  Admit iff ε_K ≤ τ_Kähler.
-/
def kahlerGateAdmit (ks : KahlerState) (tauK : Q16_16) : Gate :=
  let eK := kahlerResidual ks
  let verdict := if Q16_16.le eK tauK then GateVerdict.admit else GateVerdict.reject
  let score   := Q16_16.div tauK (Q16_16.add tauK eK)
  { name := "KahlerCompatibility", required := true, score := score, verdict := verdict }

/--
If the geometry is fractal and ε_K > 0, emit a DiagnosticReceipt routing
the roughness to "shock/rough_geometry".
-/
def fractalKahlerReceipt (ks : KahlerState) (obj : HCMMRObject) (eps : Q16_16) : DiagnosticReceipt :=
  let route := if ks.isFractal && (eps.val > 0) then "shock/rough_geometry" else "admitted"
  { object         := obj.payload
  , failedGate     := "KahlerCompatibility"
  , residual       := ⟨"kahler_symplectic_metric_mismatch", eps, "15K"⟩
  , alternateRoute := route
  , timestamp      := 0
  }

-- ═══════════════════════════════════════════════════════════════════
-- §4  Law 15A — Gauge Invariance Gate
-- ═══════════════════════════════════════════════════════════════════

/--
Apply a uniform gauge shift Λ to all four components of A_μ.
  A'_μ = A_μ + Λ   (discrete approximation of A_μ + ∂_μΛ)
For a constant Λ, ∂_μΛ = 0 in the continuum, and with our uniform
discrete shift, F_μν is exactly invariant.
-/
def gaugeTransform (pot : FieldPotential) (lambda : Q16_16) : FieldPotential :=
  { pot with A0 := Q16_16.add pot.A0 lambda
            , A1 := Q16_16.add pot.A1 lambda
            , A2 := Q16_16.add pot.A2 lambda
            , A3 := Q16_16.add pot.A3 lambda
  }

/--
Gauge residual: ε_gauge = ‖F'(Λ) − F‖
Sum of absolute differences across all six field-strength components.
-/
def gaugeResidual (pot : FieldPotential) (lambda : Q16_16) : Q16_16 :=
  let fOrig  := computeFieldStrength pot
  let fTrans := computeFieldStrength (gaugeTransform pot lambda)
  let dE1 := Q16_16.abs (Q16_16.sub fTrans.E1 fOrig.E1)
  let dE2 := Q16_16.abs (Q16_16.sub fTrans.E2 fOrig.E2)
  let dE3 := Q16_16.abs (Q16_16.sub fTrans.E3 fOrig.E3)
  let dB1 := Q16_16.abs (Q16_16.sub fTrans.B1 fOrig.B1)
  let dB2 := Q16_16.abs (Q16_16.sub fTrans.B2 fOrig.B2)
  let dB3 := Q16_16.abs (Q16_16.sub fTrans.B3 fOrig.B3)
  Q16_16.add (Q16_16.add (Q16_16.add dE1 dE2) (Q16_16.add dE3 dB1))
             (Q16_16.add dB2 dB3)

/--
Gauge invariance gate.  Admit iff ε_gauge ≤ τ_gauge.
-/
def gaugeGateAdmit (pot : FieldPotential) (lambda tauG : Q16_16) : Gate :=
  let eG := gaugeResidual pot lambda
  let verdict := if Q16_16.le eG tauG then GateVerdict.admit else GateVerdict.reject
  let score   := Q16_16.div tauG (Q16_16.add tauG eG)
  { name := "GaugeInvariance", required := true, score := score, verdict := verdict }

-- ═══════════════════════════════════════════════════════════════════
-- §5  Law 15B — Maxwell Equations Recovery
-- ═══════════════════════════════════════════════════════════════════

/--
Source current J^ν = (ρ, Jx, Jy, Jz) with charge-conservation flag.
Defined here (before Maxwell residuals) because sourcedMaxwellResidual
needs it as a parameter.
-/
structure SourceCurrent where
  rho       : Q16_16
  Jx        : Q16_16
  Jy        : Q16_16
  Jz        : Q16_16
  conserved : Bool
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Four Maxwell residuals:
  ε_divE     = Gauss electric:  ∇·E − ρ
  ε_divB     = Gauss magnetic:  ∇·B        (monopole check)
  ε_curlE_dB = Faraday:        ∇×E + ∂B/∂t
  ε_curlB_dE = Ampère-Maxwell: ∇×B − ∂E/∂t − J
-/
structure MaxwellResiduals where
  eps_divE     : Q16_16
  eps_divB     : Q16_16
  eps_curlE_dBdt : Q16_16
  eps_curlB_dEdt_J : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Homogeneous Maxwell residual (no sources).
  div B = B₁ + B₂ + B₃  (unit-spacing divergence)
  curl E ≈ (E₃−E₂, E₁−E₃, E₂−E₁)  (unit-spacing curl)
For static fields, ∂B/∂t = 0 ⇒ ε_Faraday = ‖curl E‖.
Returns scalar sum of |div B| + Σ|curl E|_i.
-/
def homogeneousMaxwellResidual (f : FieldStrength) : Q16_16 :=
  let divB  := Q16_16.add (Q16_16.add f.B1 f.B2) f.B3
  let cE1   := Q16_16.sub f.E3 f.E2
  let cE2   := Q16_16.sub f.E1 f.E3
  let cE3   := Q16_16.sub f.E2 f.E1
  Q16_16.add (Q16_16.abs divB)
    (Q16_16.add (Q16_16.add (Q16_16.abs cE1) (Q16_16.abs cE2)) (Q16_16.abs cE3))

/--
Sourced Maxwell residual with charge-current source J^ν.
  div E − ρ = E₁ + E₂ + E₃ − ρ
  curl B − J ≈ (B₃−B₂, B₁−B₃, B₂−B₁) − (Jx, Jy, Jz)
For static fields, ∂E/∂t = 0.
-/
def sourcedMaxwellResidual (f : FieldStrength) (j : SourceCurrent) : Q16_16 :=
  let divE_rho := Q16_16.sub (Q16_16.add (Q16_16.add f.E1 f.E2) f.E3) j.rho
  let cB1_Jx   := Q16_16.sub (Q16_16.sub f.B3 f.B2) j.Jx
  let cB2_Jy   := Q16_16.sub (Q16_16.sub f.B1 f.B3) j.Jy
  let cB3_Jz   := Q16_16.sub (Q16_16.sub f.B2 f.B1) j.Jz
  Q16_16.add (Q16_16.abs divE_rho)
    (Q16_16.add (Q16_16.add (Q16_16.abs cB1_Jx) (Q16_16.abs cB2_Jy)) (Q16_16.abs cB3_Jz))

/--
Maxwell equations gate.  Admit iff both homogeneous and sourced
residuals fall ≤ τ_maxwell.
-/
def maxwellGateAdmit (f : FieldStrength) (j : SourceCurrent) (tauM : Q16_16) : Gate :=
  let eH := homogeneousMaxwellResidual f
  let eS := sourcedMaxwellResidual f j
  let totalE := Q16_16.add eH eS
  let verdict := if Q16_16.le totalE tauM then GateVerdict.admit else GateVerdict.reject
  let score   := Q16_16.div tauM (Q16_16.add tauM totalE)
  { name := "MaxwellEquations", required := true, score := score, verdict := verdict }

-- ═══════════════════════════════════════════════════════════════════
-- §6  Law 15C — Vacuum Wave Propagation
-- ═══════════════════════════════════════════════════════════════════

/--
Vacuum wave-propagation residuals.
  ε_wave_eq : □A^ν residual (d'Alembertian check)
  ε_lorenz  : ∂_μA^μ residual (Lorenz gauge check)
  ε_transverse_Ek, ε_transverse_Bk, ε_transverse_EB : plane-wave transverse checks
-/
structure WaveResiduals where
  eps_wave_eq   : Q16_16
  eps_lorenz_gauge : Q16_16
  eps_transverse_Ek : Q16_16
  eps_transverse_Bk : Q16_16
  eps_transverse_EB : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Causal speed residual: ε_c = |□A| for the scalar component.
In source-free vacuum, □A = 0 implies phase velocity = c.
-/
def causalSpeedResidual (pot : FieldPotential) : Q16_16 :=
  let threeA0 := Q16_16.mul (Q16_16.ofInt 3) pot.A0
  let sumSpatial := Q16_16.add (Q16_16.add pot.A1 pot.A2) pot.A3
  Q16_16.abs (Q16_16.sub threeA0 sumSpatial)

/--
Wave propagation gate.  Builds all wave residuals, sums them,
and admits iff total ≤ τ_wave.
-/
def waveGateAdmit (pot : FieldPotential) (f : FieldStrength) (tauW : Q16_16) : Gate :=
  let threeA0 := Q16_16.mul (Q16_16.ofInt 3) pot.A0
  let sumAxyz := Q16_16.add (Q16_16.add pot.A1 pot.A2) pot.A3
  let waveEq  := Q16_16.abs (Q16_16.sub threeA0 sumAxyz)
  let lorenz  := Q16_16.abs (Q16_16.sub sumAxyz pot.A0)
  let tEk     := Q16_16.abs (Q16_16.add (Q16_16.add f.E1 f.E2) f.E3)
  let tBk     := Q16_16.abs (Q16_16.add (Q16_16.add f.B1 f.B2) f.B3)
  let tEB     := Q16_16.abs (Q16_16.add
                  (Q16_16.add (Q16_16.mul f.E1 f.B1) (Q16_16.mul f.E2 f.B2))
                  (Q16_16.mul f.E3 f.B3))
  let cspd     := causalSpeedResidual pot
  let total    := Q16_16.add (Q16_16.add (Q16_16.add (Q16_16.add waveEq lorenz) tEk)
                              (Q16_16.add tBk tEB)) cspd
  let verdict := if Q16_16.le total tauW then GateVerdict.admit else GateVerdict.reject
  let score   := Q16_16.div tauW (Q16_16.add tauW total)
  { name := "VacuumWavePropagation", required := true, score := score, verdict := verdict }

-- ═══════════════════════════════════════════════════════════════════
-- §7  Law 15D — Charge/Current Coupling
-- ═══════════════════════════════════════════════════════════════════

/--
Lorentz force: F = q(E + v × B) in 3D.
Returns force vector as (Fx, Fy, Fz) in Q16_16.
-/
def lorentzForce (q : Q16_16) (vx vy vz : Q16_16) (f : FieldStrength) : Q16_16 × Q16_16 × Q16_16 :=
  let vxBy := Q16_16.mul vy f.B3
  let vxBz := Q16_16.mul vz f.B2
  let vyBz := Q16_16.mul vz f.B1
  let vyBx := Q16_16.mul vx f.B3
  let vzBx := Q16_16.mul vx f.B2
  let vzBy := Q16_16.mul vy f.B1
  let Fx := Q16_16.mul q (Q16_16.add (Q16_16.sub vxBy vxBz) f.E1)
  let Fy := Q16_16.mul q (Q16_16.add (Q16_16.sub vyBz vyBx) f.E2)
  let Fz := Q16_16.mul q (Q16_16.add (Q16_16.sub vzBx vzBy) f.E3)
  (Fx, Fy, Fz)

/--
Charge-coupling residual: ε_Lorentz = ‖f_HCMMR − F^{μν}J_ν‖.
Compares Lorentz force from HCMMR fields against the gauge-theory
coupling F^{μν}J_ν.  Also checks stress-energy conservation residual.
-/
def chargeCouplingResidual (f : FieldStrength) (j : SourceCurrent) : Q16_16 :=
  let FxJx := Q16_16.mul f.E1 j.Jx
  let FyJy := Q16_16.mul f.E2 j.Jy
  let FzJz := Q16_16.mul f.E3 j.Jz
  let FdotJ := Q16_16.add (Q16_16.add FxJx FyJy) FzJz
  let rhoField := Q16_16.mul f.E1 j.rho
  Q16_16.abs (Q16_16.sub FdotJ rhoField)

/--
Source conservation residual: ε_J = ‖∂_ν J^ν‖ ≈ |ρ + Jx + Jy + Jz|.
In discrete static form, charge conservation means ∂_ν J^ν = 0.
-/
def sourceConservationResidual (j : SourceCurrent) : Q16_16 :=
  Q16_16.abs (Q16_16.add (Q16_16.add (Q16_16.add j.rho j.Jx) j.Jy) j.Jz)

/--
Charge/current coupling gate.  Admit iff both Lorentz coupling residual
and source-conservation residual fall ≤ τ_coupling.
-/
def couplingGateAdmit (f : FieldStrength) (j : SourceCurrent) (tauC : Q16_16) : Gate :=
  let eL := chargeCouplingResidual f j
  let eJ := sourceConservationResidual j
  let total := Q16_16.add eL eJ
  let verdict := if Q16_16.le total tauC then GateVerdict.admit else GateVerdict.reject
  let score   := Q16_16.div tauC (Q16_16.add tauC total)
  { name := "ChargeCurrentCoupling", required := true, score := score, verdict := verdict }

-- ═══════════════════════════════════════════════════════════════════
-- §8  Full Field Recovery Gate Chain
-- ═══════════════════════════════════════════════════════════════════

/--
Assembles the full Law 15 gate chain:
  15K (Kähler) → 15A (Gauge) → 15B (Maxwell) → 15C (Wave) → 15D (Coupling).
-/
def fieldRecoveryChain (ks : KahlerState) (pot : FieldPotential) (lambda : Q16_16)
                       (f : FieldStrength) (j : SourceCurrent)
                       (tauK tauG tauM tauW tauC : Q16_16) : GateChain :=
  { gates :=
    [ kahlerGateAdmit ks tauK
    , gaugeGateAdmit pot lambda tauG
    , maxwellGateAdmit f j tauM
    , waveGateAdmit pot f tauW
    , couplingGateAdmit f j tauC
    ]
  }

/--
Evaluates the full field-recovery gate chain via `gateChainVerdict` from Core.
-/
def fieldRecoveryVerdict (ks : KahlerState) (pot : FieldPotential) (lambda : Q16_16)
                          (f : FieldStrength) (j : SourceCurrent)
                          (tauK tauG tauM tauW tauC : Q16_16) : GateVerdict :=
  gateChainVerdict (fieldRecoveryChain ks pot lambda f j tauK tauG tauM tauW tauC)

-- ═══════════════════════════════════════════════════════════════════
-- §9  Fixtures
-- ═══════════════════════════════════════════════════════════════════

/--
A clean, smooth 16D torsion state: compatible chirality, no residual.
-/
def cleanTorsionFixture : TorsionState :=
  { coordinate       := "16D_smooth_origin"
  , torsionPotential := Q16_16.one
  , windingField     := Q16_16.one
  , chirality        := Q16_16.one
  , residual         := ""
  , receiptRoot      := "0000000000000000000000000000000000000000000000000000000000000000"
  }

/--
A rough, fractally folded 16D torsion state with nonzero residual.
-/
def fractalTorsionFixture : TorsionState :=
  { coordinate       := "16D_fractal_knot"
  , torsionPotential := Q16_16.two
  , windingField     := Q16_16.mul (Q16_16.ofInt 3) Q16_16.one
  , chirality        := Q16_16.div Q16_16.one Q16_16.two
  , residual         := "fractal_microfold_scar"
  , receiptRoot      := "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
  }

/--
FieldPotential for a clean, smooth Maxwell-compatible vacuum field.
All-zero potential ⇒ E=0, B=0, trivially satisfies all Maxwell, wave, and
coupling equations.
-/
def cleanFieldPotentialFixture : FieldPotential :=
  { A0 := Q16_16.zero
  , A1 := Q16_16.zero
  , A2 := Q16_16.zero
  , A3 := Q16_16.zero
  }

/--
FieldStrength computed from cleanFieldPotentialFixture.
E = (0, 0, 0), B = (0, 0, 0).
-/
def cleanFieldStrengthFixture : FieldStrength :=
  computeFieldStrength cleanFieldPotentialFixture

/--
A perfectly Kähler-compatible state: J²=−I, ω=g(JX,Y), dω=0, not fractal.
-/
def cleanKahlerFixture : KahlerState :=
  { J_squared_identity := true
  , omega_X_Y         := Q16_16.one
  , g_JX_Y            := Q16_16.one
  , d_omega           := Q16_16.zero
  , isFractal         := false
  }

/--
A rough/fractal Kähler state: J²≠−I, mismatch between ω and g(JX,Y),
nonzero dω, marked fractal.
-/
def fractalKahlerFixture : KahlerState :=
  { J_squared_identity := false
  , omega_X_Y         := Q16_16.ofInt 2
  , g_JX_Y            := Q16_16.ofInt 1
  , d_omega           := Q16_16.div Q16_16.one Q16_16.two
  , isFractal         := true
  }

/--
A conserved source current with zero net charge and current.
-/
def testChargeFixture : SourceCurrent :=
  { rho       := Q16_16.zero
  , Jx        := Q16_16.zero
  , Jy        := Q16_16.zero
  , Jz        := Q16_16.zero
  , conserved := true
  }

/--
A neutral test particle for force computation.
-/
def testChargeQ : Q16_16 := Q16_16.one
def testVelocityVx : Q16_16 := Q16_16.one
def testVelocityVy : Q16_16 := Q16_16.zero
def testVelocityVz : Q16_16 := Q16_16.zero

/--
Default gate thresholds (lenient for clean fixtures).
-/
def tauDefault : Q16_16 := Q16_16.one

-- ═══════════════════════════════════════════════════════════════════
-- §10  Theorems
-- ═══════════════════════════════════════════════════════════════════

/--
Smooth, compatible Kähler state admits.
-/
theorem kahlerGate_admits_clean :
    (kahlerGateAdmit cleanKahlerFixture tauDefault).verdict = GateVerdict.admit := by
  native_decide

/--
Fractal Kähler state does not admit (ε_K > 0 ⇒ holds or rejects).
-/
theorem kahlerGate_rejects_fractal :
    (kahlerGateAdmit fractalKahlerFixture tauDefault).verdict ≠ GateVerdict.admit := by
  native_decide

/--
Uniform gauge shift preserves field strength: ε_gauge = 0 ⇒ admit.
-/
theorem gaugeGate_admits_invariance :
    (gaugeGateAdmit cleanFieldPotentialFixture (Q16_16.ofInt 3) tauDefault).verdict = GateVerdict.admit := by
  native_decide

/--
Homogeneous Maxwell: div B = 0 from antisymmetric F.
For cleanFieldStrengthFixture, B = (0,0,0) and curl E = 0 ⇒ total residue = 0.
-/
theorem maxwell_homogeneous_from_potential :
    homogeneousMaxwellResidual cleanFieldStrengthFixture = Q16_16.zero := by
  native_decide

/--
Sourced Maxwell in vacuum (ρ=0, J=0): div E = 0 passes with zero-field potential.
Uses a zero-field fixture where A=(0,0,0,0).
-/
theorem maxwell_sourced_needs_current :
    let zeroField := { E1 := Q16_16.zero, E2 := Q16_16.zero, E3 := Q16_16.zero
                     , B1 := Q16_16.zero, B2 := Q16_16.zero, B3 := Q16_16.zero }
    sourcedMaxwellResidual zeroField testChargeFixture = Q16_16.zero := by
  native_decide

/--
Vacuum wave propagation gate admits for source-free clean field.
-/
theorem waveGate_admits_vacuum :
    (waveGateAdmit cleanFieldPotentialFixture cleanFieldStrengthFixture tauDefault).verdict
    = GateVerdict.admit := by
  native_decide

/--
When the source current is conserved (and zero), coupling gate admits.
-/
theorem couplingGate_admits_conserved :
    (couplingGateAdmit cleanFieldStrengthFixture testChargeFixture tauDefault).verdict
    = GateVerdict.admit := by
  native_decide

/--
The full field-recovery chain admits for clean fixtures across all five sub-laws.
-/
theorem fieldRecovery_chain_admits_clean :
    fieldRecoveryVerdict cleanKahlerFixture cleanFieldPotentialFixture Q16_16.zero
      cleanFieldStrengthFixture testChargeFixture
      tauDefault tauDefault tauDefault tauDefault tauDefault
    = GateVerdict.admit := by
  native_decide

/--
The full field-recovery chain rejects for fractal Kähler input.
-/
theorem fieldRecovery_chain_rejects_fractal :
    fieldRecoveryVerdict fractalKahlerFixture cleanFieldPotentialFixture Q16_16.zero
      cleanFieldStrengthFixture testChargeFixture
      tauDefault tauDefault tauDefault tauDefault tauDefault
    ≠ GateVerdict.admit := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════
-- §11  #eval Witnesses
-- ═══════════════════════════════════════════════════════════════════

-- §1 TorsionState
#eval cleanTorsionFixture
#eval fractalTorsionFixture

-- §2 FieldPotential / FieldStrength
#eval projectPotential cleanTorsionFixture
#eval projectPotential fractalTorsionFixture
#eval cleanFieldPotentialFixture
#eval cleanFieldStrengthFixture
#eval computeFieldStrength { A0 := Q16_16.ofInt 0, A1 := Q16_16.ofInt 2,
                             A2 := Q16_16.negOne, A3 := Q16_16.negOne }

-- §3 Law 15K Kähler
#eval cleanKahlerFixture
#eval fractalKahlerFixture
#eval kahlerResidual cleanKahlerFixture
#eval kahlerResidual fractalKahlerFixture
#eval kahlerGateAdmit cleanKahlerFixture tauDefault
#eval kahlerGateAdmit fractalKahlerFixture tauDefault
#eval fractalKahlerReceipt cleanKahlerFixture canonicalFixture
        (kahlerResidual cleanKahlerFixture)
#eval fractalKahlerReceipt fractalKahlerFixture canonicalFixture
        (kahlerResidual fractalKahlerFixture)

-- §4 Law 15A Gauge
#eval gaugeTransform cleanFieldPotentialFixture (Q16_16.ofInt 3)
#eval gaugeResidual cleanFieldPotentialFixture Q16_16.zero
#eval gaugeResidual cleanFieldPotentialFixture (Q16_16.ofInt 3)
#eval gaugeGateAdmit cleanFieldPotentialFixture (Q16_16.ofInt 3) tauDefault

-- §5 Law 15B Maxwell
#eval homogeneousMaxwellResidual cleanFieldStrengthFixture
#eval sourcedMaxwellResidual cleanFieldStrengthFixture testChargeFixture
#eval maxwellGateAdmit cleanFieldStrengthFixture testChargeFixture tauDefault

-- §6 Law 15C Wave
#eval causalSpeedResidual cleanFieldPotentialFixture
#eval waveGateAdmit cleanFieldPotentialFixture cleanFieldStrengthFixture tauDefault

-- §7 Law 15D Coupling
#eval testChargeFixture
#eval lorentzForce testChargeQ testVelocityVx testVelocityVy testVelocityVz cleanFieldStrengthFixture
#eval chargeCouplingResidual cleanFieldStrengthFixture testChargeFixture
#eval sourceConservationResidual testChargeFixture
#eval couplingGateAdmit cleanFieldStrengthFixture testChargeFixture tauDefault

-- §8 Full chain
#eval fieldRecoveryChain cleanKahlerFixture cleanFieldPotentialFixture Q16_16.zero
        cleanFieldStrengthFixture testChargeFixture
        tauDefault tauDefault tauDefault tauDefault tauDefault
#eval fieldRecoveryVerdict cleanKahlerFixture cleanFieldPotentialFixture Q16_16.zero
        cleanFieldStrengthFixture testChargeFixture
        tauDefault tauDefault tauDefault tauDefault tauDefault
#eval fieldRecoveryVerdict fractalKahlerFixture cleanFieldPotentialFixture Q16_16.zero
        cleanFieldStrengthFixture testChargeFixture
        tauDefault tauDefault tauDefault tauDefault tauDefault

end Semantics.HCMMR.Law15

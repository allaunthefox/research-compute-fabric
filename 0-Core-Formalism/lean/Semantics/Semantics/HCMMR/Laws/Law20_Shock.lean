/-
Law 20 — Shockwave / Front Gate

Formalises the HCMMR discontinuity-handling gate A_shock.

Doctrine: a discontinuity (shockwave, contact front, phase boundary) is NOT
a failure of physics.  It is a *gate event* with a typed receipt that captures:

  1. **Hyperbolicity** — the PDE system is hyperbolic, so characteristic speeds
     exist and information propagates at finite velocity.  Non-hyperbolic objects
     are rejected (Underverse entry) before any shock processing.

  2. **Rankine–Hugoniot jump relations** — across the front, mass, momentum, and
     energy flux must balance.  The residual ε_RH measures how far the candidate
     state diverges from exact balance.

  3. **Entropy (Lax) admissibility condition** — the shock is physically admissible
     only if entropy *increases* across the front (2nd-law arrow).  Entropy-
     decreasing "expansion shocks" are routed to the Underverse as inadmissible.

  4. **Causal front constraint** — the front speed s satisfies
       u_L − c_L  ≤  s  ≤  u_R + c_R   (CFL-sound-speed envelope)
     Fronts exceeding the causal envelope are rejected with a speed-excess residual.

  5. **Irreversibility receipt** — every admitted shock emits a typed receipt
     recording the jump deltas, entropy gain, characteristic speeds, and
     causal-validity flag.  These feed back into Law 16 (Entropy/Heat Leak) as
     Underverse scar contributions.

Conventions:
  PascalCase types, camelCase functions.
  `structure` for domain concepts.
  `def` needs `#eval` witness or `theorem`.
  Q16_16 for all numeric fields.
  Namespace: Semantics.HCMMR.Law20
  Imports: Semantics.HCMMR.Core, Semantics.FixedPoint
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Law20

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  Fixed-point arithmetic helpers
--     All intermediate arithmetic is done in Nat (arbitrary precision)
--     and then clamped back to UInt32 for Q16_16.val.
-- ═══════════════════════════════════════════════════════════════════

private def toN (q : Q16_16) : Nat := q.val.toNat

/--
Q16_16 subtraction clamped to zero (no wrap-around for unsigned-like use).
-/
private def q_sub (a b : Q16_16) : Q16_16 :=
  let an := toN a; let bn := toN b
  if an ≥ bn then ⟨(an - bn).toUInt32⟩ else ⟨0⟩

/--
Absolute difference of two Q16_16 values — always non-negative.
-/
private def q_absdiff (a b : Q16_16) : Q16_16 :=
  let an := toN a; let bn := toN b
  if an ≥ bn then ⟨(an - bn).toUInt32⟩ else ⟨(bn - an).toUInt32⟩

/--
Q16_16 addition, saturating at UInt32.max to avoid overflow.
-/
private def q_add (a b : Q16_16) : Q16_16 :=
  let s := toN a + toN b
  ⟨(min s 0xFFFFFFFF).toUInt32⟩

/--
Q16_16 scaled division: (a × 65536) / b in Nat, clamped to UInt32.
Returns ⟨0⟩ if b = 0.
-/
private def q_div (a b : Q16_16) : Q16_16 :=
  let bn := toN b
  if bn = 0 then ⟨0⟩ else ⟨(min ((toN a * 65536) / bn) 0xFFFFFFFF).toUInt32⟩

-- ═══════════════════════════════════════════════════════════════════
-- §2  Primitive State Vectors
-- ═══════════════════════════════════════════════════════════════════

/--
A one-dimensional conserved-variable state on one side of a discontinuity.

Fields are stored as Q16_16 scaled values:
  - `density`  : ρ    (kg m⁻³  × 65536, clipped to fit Q16_16)
  - `velocity` : u    (m s⁻¹  × 65536 / 1000  → per-km/s units)
  - `pressure` : p    (Pa     × 65536 / 10⁵   → per-bar units)
  - `energy`   : e    (J kg⁻¹ × 65536 / 10⁶   → per-MJ/kg units)
  - `soundSpd` : c_s  (m s⁻¹  × 65536 / 1000  → per-km/s units)

The internal scales are self-consistent for residual comparison; no SI
conversion is needed inside the gate.  The gate only needs ratios and differences.
-/
structure FluidState where
  density  : Q16_16
  velocity : Q16_16
  pressure : Q16_16
  energy   : Q16_16
  soundSpd : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
A discontinuity event: left state, right state, and the front propagation speed.

`frontSpeed` is signed via the convention that positive means rightward propagation.
Stored in the same per-km/s units as `velocity`.
-/
structure ShockEvent where
  stateL    : FluidState
  stateR    : FluidState
  frontSpeed : Q16_16   -- |s| in per-km/s units
  deriving Repr, BEq, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §3  Hyperbolicity Gate
-- ═══════════════════════════════════════════════════════════════════

/--
Hyperbolicity condition: a 1D system is hyperbolic when all characteristic
speeds are real and finite.  For an Euler/gas-dynamics system, the three
characteristic speeds are:

    λ₋ = u − c_s,   λ₀ = u,   λ₊ = u + c_s

Hyperbolicity holds if c_s > 0 (positive, real sound speed).  We check
soundSpd on both sides.  If either side has c_s = 0 the system is parabolic
or degenerate at that state.

Returns `true` when both states pass the hyperbolicity check.
-/
def hyperbolicityGate (ev : ShockEvent) : Bool :=
  ev.stateL.soundSpd.val > 0 && ev.stateR.soundSpd.val > 0

/--
Characteristic speeds for a given state: (λ₋, λ₀, λ₊).
Speeds are Q16_16 magnitudes; sign information is tracked externally.
-/
def characteristicSpeeds (s : FluidState) : Q16_16 × Q16_16 × Q16_16 :=
  let lMinus := q_absdiff s.velocity s.soundSpd
  let lZero  := s.velocity
  let lPlus  := q_add s.velocity s.soundSpd
  (lMinus, lZero, lPlus)

#eval characteristicSpeeds
  { density := ⟨65536⟩, velocity := ⟨65536⟩    -- u = 1 km/s
  , pressure := ⟨65536⟩, energy := ⟨65536⟩
  , soundSpd := ⟨21953⟩ }                       -- c_s ≈ 0.335 km/s (air)
-- expected: λ₋ ≈ 0.665, λ₀ ≈ 1.000, λ₊ ≈ 1.335 (all in per-km/s)

-- ═══════════════════════════════════════════════════════════════════
-- §4  Rankine–Hugoniot Residual
-- ═══════════════════════════════════════════════════════════════════

/--
Rankine–Hugoniot jump conditions for a 1D inviscid compressible flow.

The three conservation laws across a stationary frame shock at speed s are:

    [ρ(u − s)]     = 0          (mass)
    [ρu(u−s) + p]  = 0          (momentum)
    [ρe(u−s) + pu] = 0          (energy)

where [·] = (·)_R − (·)_L.

We compute unsigned residuals ε_mass, ε_mom, ε_energy as proxy distances
in Q16_16 units.  Exact enforcement would require field arithmetic (Real),
so these are *relative* residuals: (|ΔF|) / F_scale, with F_scale chosen
as the left-side flux magnitude.

A residual of 0 means exact balance.  A residual > `ε_threshold` means the
jump fails the RH gate.
-/
structure RHResidual where
  epsMass     : Q16_16
  epsMomentum : Q16_16
  epsEnergy   : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Compute the Rankine–Hugoniot residual for a shock event.

Approximation note: mass flux proxy = ρ_L × (u_L − s).
Momentum flux proxy = p_R − p_L (dominant when u ~ s is small).
Energy proxy = |e_R − e_L| relative to e_L.

These are structurally correct diagnostics, not exact SI simulations.
-/
def rankineHugoniotResidual (ev : ShockEvent) : RHResidual :=
  let rhoL := ev.stateL.density
  let rhoR := ev.stateR.density
  let uL   := ev.stateL.velocity
  let uR   := ev.stateR.velocity
  let pL   := ev.stateL.pressure
  let pR   := ev.stateR.pressure
  let eL   := ev.stateL.energy
  let eR   := ev.stateR.energy
  let s    := ev.frontSpeed
  -- mass flux residual: |ρ_R(u_R−s) − ρ_L(u_L−s)| / ρ_L
  -- All intermediate products lifted to Nat to avoid UInt32 overflow.
  let mFluxLN := toN (q_absdiff uL s)
  let mFluxRN := toN (q_absdiff uR s)
  let rhoLN   := toN rhoL
  let rhoRN   := toN rhoR
  let prodL   := (rhoLN * mFluxLN) / 65536
  let prodR   := (rhoRN * mFluxRN) / 65536
  let massDeltaN := if prodR ≥ prodL then prodR - prodL else prodL - prodR
  let epsMN := if rhoLN > 0 then (massDeltaN * 65536) / rhoLN else massDeltaN
  let epsM := ⟨(min epsMN 0xFFFFFFFF).toUInt32⟩
  -- momentum residual: |p_R − p_L| / p_L
  let epsMom := if pL.val > 0 then q_div (q_absdiff pL pR) pL else q_absdiff pL pR
  -- energy residual: |e_R − e_L| / e_L
  let epsEng := if eL.val > 0 then q_div (q_absdiff eL eR) eL else q_absdiff eL eR
  { epsMass := epsM, epsMomentum := epsMom, epsEnergy := epsEng }

#eval rankineHugoniotResidual
  { stateL := { density := ⟨65536⟩, velocity := ⟨131072⟩, pressure := ⟨65536⟩
              , energy := ⟨65536⟩, soundSpd := ⟨21953⟩ }
  , stateR := { density := ⟨104858⟩, velocity := ⟨81920⟩, pressure := ⟨104858⟩
              , energy := ⟨104858⟩, soundSpd := ⟨25000⟩ }
  , frontSpeed := ⟨65536⟩ }
-- ε_mass, ε_momentum, ε_energy all printed

-- ═══════════════════════════════════════════════════════════════════
-- §5  Entropy (Lax) Admissibility Condition
-- ═══════════════════════════════════════════════════════════════════

/--
Entropy admissibility (Lax entropy condition).

A compressive shock is admissible if the entropy *increases* across the front:
  s(state_R) ≥ s(state_L)

For a polytropic gas with γ-law equation of state, entropy is monotone in
p/ρ^γ.  We approximate this with the proxy:

  entropy_proxy(state) = pressure / density

(Valid for γ = 1 surrogate; structurally captures the admissibility sign.)

A shock is admissible (second-law) iff entropy_R ≥ entropy_L.
-/
def entropyProxy (s : FluidState) : Q16_16 :=
  if s.density.val > 0 then q_div s.pressure s.density else ⟨0⟩

/--
Returns true when the shock is entropy-admissible (ΔS ≥ 0).
-/
def entropyAdmissible (ev : ShockEvent) : Bool :=
  (entropyProxy ev.stateR).val ≥ (entropyProxy ev.stateL).val

/--
Entropy gain across the shock: S_R − S_L (in entropy-proxy units).
Zero for isentropic transitions; positive for physical shocks.
-/
def entropyGain (ev : ShockEvent) : Q16_16 :=
  q_absdiff (entropyProxy ev.stateR) (entropyProxy ev.stateL)

#eval entropyAdmissible
  { stateL := { density := ⟨65536⟩, velocity := ⟨131072⟩, pressure := ⟨65536⟩
              , energy := ⟨65536⟩, soundSpd := ⟨21953⟩ }
  , stateR := { density := ⟨104858⟩, velocity := ⟨81920⟩, pressure := ⟨131072⟩
              , energy := ⟨104858⟩, soundSpd := ⟨25000⟩ }
  , frontSpeed := ⟨65536⟩ }
-- expected: true  (pressure increased → entropy increased)

-- ═══════════════════════════════════════════════════════════════════
-- §6  Causal Front Constraint
-- ═══════════════════════════════════════════════════════════════════

/--
Causal front bound: the front speed s must remain within the sound-speed
envelope of both surrounding states.  The envelope is:

  s_min = min(u_L − c_L, u_R − c_R)   (leftward fastest wave)
  s_max = max(u_L + c_L, u_R + c_R)   (rightward fastest wave)

A front with |s| > s_max violates causality (information would need to
propagate faster than the local sound speed).

We check the simpler necessary condition:
  frontSpeed ≤ max(u_L + c_L, u_R + c_R)

and record the excess as a residual.
-/
def causalEnvelope (ev : ShockEvent) : Q16_16 :=
  let sMaxL := q_add ev.stateL.velocity ev.stateL.soundSpd
  let sMaxR := q_add ev.stateR.velocity ev.stateR.soundSpd
  if sMaxL.val ≥ sMaxR.val then sMaxL else sMaxR

def causallyValid (ev : ShockEvent) : Bool :=
  ev.frontSpeed.val ≤ (causalEnvelope ev).val

/--
Speed-excess residual: how far the front speed exceeds the causal envelope.
Zero for valid fronts.
-/
def causalExcess (ev : ShockEvent) : Q16_16 :=
  let env := causalEnvelope ev
  if ev.frontSpeed.val > env.val then ⟨ev.frontSpeed.val - env.val⟩ else ⟨0⟩

#eval causallyValid
  { stateL := { density := ⟨65536⟩, velocity := ⟨65536⟩, pressure := ⟨65536⟩
              , energy := ⟨65536⟩, soundSpd := ⟨21953⟩ }
  , stateR := { density := ⟨104858⟩, velocity := ⟨65536⟩, pressure := ⟨131072⟩
              , energy := ⟨104858⟩, soundSpd := ⟨25000⟩ }
  , frontSpeed := ⟨80000⟩ }
-- expected: true (frontSpeed < max(u+c) on both sides)

-- ═══════════════════════════════════════════════════════════════════
-- §7  Irreversibility Receipt
-- ═══════════════════════════════════════════════════════════════════

/--
Verdict enum for the shock gate.
-/
inductive ShockVerdict
  | Admitted     -- shock is hyperbolic, RH-close, entropy-admissible, causal
  | RejectedRH   -- fails Rankine–Hugoniot balance (not a real shock surface)
  | RejectedLax  -- entropy-decreasing (inadmissible expansion shock)
  | RejectedAcausal -- front speed exceeds causal envelope
  | RejectedElliptic -- hyperbolicity check failed (degenerate state)
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Full diagnostic receipt for one shock event.
-/
structure ShockReceipt where
  event          : ShockEvent
  hyperbolic     : Bool
  rhResidual     : RHResidual
  entropyGain    : Q16_16
  causalExcess   : Q16_16
  verdict        : ShockVerdict
  deriving Repr, Inhabited

/--
RH residual threshold: 5% in Q16_16 units = 0.05 × 65536 = 3277.
-/
def rhThreshold : Q16_16 := ⟨3277⟩

/--
Full shock gate evaluation: applies all four checks in order and returns a
typed `ShockReceipt`.  The gate is a logical series circuit — one failed
check terminates further evaluation.
-/
def shockGate (ev : ShockEvent) : ShockReceipt :=
  let hyp := hyperbolicityGate ev
  if !hyp then
    { event := ev, hyperbolic := false
    , rhResidual := { epsMass := ⟨0⟩, epsMomentum := ⟨0⟩, epsEnergy := ⟨0⟩ }
    , entropyGain := ⟨0⟩, causalExcess := ⟨0⟩
    , verdict := ShockVerdict.RejectedElliptic }
  else
    let rh := rankineHugoniotResidual ev
    let rhFail := rh.epsMass.val > rhThreshold.val
                || rh.epsMomentum.val > rhThreshold.val
                || rh.epsEnergy.val > rhThreshold.val
    if rhFail then
      { event := ev, hyperbolic := true, rhResidual := rh
      , entropyGain := ⟨0⟩, causalExcess := ⟨0⟩
      , verdict := ShockVerdict.RejectedRH }
    else
      let lax := entropyAdmissible ev
      if !lax then
        { event := ev, hyperbolic := true, rhResidual := rh
        , entropyGain := ⟨0⟩, causalExcess := ⟨0⟩
        , verdict := ShockVerdict.RejectedLax }
      else
        let causal := causallyValid ev
        if !causal then
          { event := ev, hyperbolic := true, rhResidual := rh
          , entropyGain := entropyGain ev, causalExcess := causalExcess ev
          , verdict := ShockVerdict.RejectedAcausal }
        else
          { event := ev, hyperbolic := true, rhResidual := rh
          , entropyGain := entropyGain ev, causalExcess := ⟨0⟩
          , verdict := ShockVerdict.Admitted }

-- ═══════════════════════════════════════════════════════════════════
-- §8  Witnesses
-- ═══════════════════════════════════════════════════════════════════

/--
Canonical physical shock: weak compression (≈ 3% jump), entropy increase, subsonic front.

The states are chosen so that the RH proxy residuals fall below the 5% threshold:
  ε_mass     ~ 3% (density × velocity-shift imbalance)
  ε_momentum ~ 3% (pressure jump / p_L)
  ε_energy   ~ 3% (energy jump / e_L)
All four gates pass: hyperbolic, RH-close, entropy-admissible, causal.
-/
def exampleShock : ShockEvent :=
  { stateL := { density := ⟨65536⟩    -- ρ_L = 1.000 (normalised)
              , velocity := ⟨131072⟩   -- u_L = 2.000 km/s
              , pressure := ⟨65536⟩    -- p_L = 1.000 bar
              , energy   := ⟨65536⟩    -- e_L = 1.000 MJ/kg
              , soundSpd := ⟨21953⟩ }  -- c_L ≈ 0.335 km/s (air-like)
  , stateR := { density := ⟨67502⟩    -- ρ_R ≈ 1.030 (3% compression)
              , velocity := ⟨127140⟩   -- u_R ≈ 1.940 km/s (slight slowdown)
              , pressure := ⟨67502⟩    -- p_R ≈ 1.030 bar (3% pressure rise)
              , energy   := ⟨67502⟩    -- e_R ≈ 1.030 MJ/kg (3% energy rise)
              , soundSpd := ⟨22283⟩ }  -- c_R ≈ 0.340 km/s (slight increase)
  , frontSpeed := ⟨65536⟩ }            -- s = 1.0 km/s  (≤ u_L + c_L = 2.335)

#eval shockGate exampleShock
-- expected: ShockVerdict.Admitted (all four gates pass)

/-- Degenerate state: zero sound speed → elliptic, rejected immediately. -/
def ellipticEvent : ShockEvent :=
  { stateL := { density := ⟨65536⟩, velocity := ⟨65536⟩, pressure := ⟨65536⟩
              , energy := ⟨65536⟩, soundSpd := ⟨0⟩ }    -- c = 0 → elliptic
  , stateR := { density := ⟨65536⟩, velocity := ⟨65536⟩, pressure := ⟨65536⟩
              , energy := ⟨65536⟩, soundSpd := ⟨21953⟩ }
  , frontSpeed := ⟨65536⟩ }

#eval (shockGate ellipticEvent).verdict
-- expected: ShockVerdict.RejectedElliptic

/--
Entropy-decreasing front: small density jump (RH-close) but p_R < p_L
so entropy_proxy(R) = p_R/ρ_R < p_L/ρ_L = entropy_proxy(L).
Passes RH gate, fails Lax admissibility → RejectedLax.
-/
def expansionShock : ShockEvent :=
  { stateL := { density := ⟨65536⟩    -- ρ_L = 1.000
              , velocity := ⟨131072⟩   -- u_L = 2.000 km/s
              , pressure := ⟨65536⟩    -- p_L = 1.000 bar
              , energy   := ⟨65536⟩    -- e_L = 1.000 MJ/kg
              , soundSpd := ⟨21953⟩ }  -- c_L ≈ 0.335 km/s
  , stateR := { density := ⟨65536⟩    -- ρ_R = 1.000 (same density — RH mass ε = 0)
              , velocity := ⟨131072⟩   -- u_R = 2.000 (same — RH mom ε ≈ 0)
              , pressure := ⟨63373⟩    -- p_R ≈ 0.967 bar  (3% pressure DROP → entropy decrease)
              , energy   := ⟨65536⟩    -- e_R = same
              , soundSpd := ⟨21953⟩ }  -- c_R same
  , frontSpeed := ⟨65536⟩ }

#eval (shockGate expansionShock).verdict
-- expected: ShockVerdict.RejectedLax  (entropy_R < entropy_L: p_R/ρ_R < p_L/ρ_L)

/--
Superluminal (acausal) front: RH-close states (small jump) but frontSpeed >>
causal envelope (u + c_s on both sides ≈ 1.335 km/s = 87,489 Q16 units).

frontSpeed = 1,000,000 >> causal envelope → RejectedAcausal.
Entropy is admissible (p_R ≥ p_L), RH residuals are small → first three
gates pass; fourth (causal) fails.
-/
def acausalShock : ShockEvent :=
  { stateL := { density := ⟨65536⟩    -- ρ_L = 1.000
              , velocity := ⟨65536⟩    -- u_L = 1.000 km/s
              , pressure := ⟨65536⟩    -- p_L = 1.000
              , energy   := ⟨65536⟩    -- e_L = 1.000
              , soundSpd := ⟨21953⟩ }  -- c_L ≈ 0.335 km/s → u+c ≈ 87,489
  , stateR := { density := ⟨65536⟩    -- same (RH ε → 0)
              , velocity := ⟨65536⟩
              , pressure := ⟨67502⟩    -- 3% pressure rise (entropy admissible)
              , energy   := ⟨65536⟩
              , soundSpd := ⟨21953⟩ }
  , frontSpeed := ⟨1000000⟩ }   -- ~15 km/s — far exceeds causal envelope

#eval (shockGate acausalShock).verdict
-- expected: ShockVerdict.RejectedAcausal

-- ═══════════════════════════════════════════════════════════════════
-- §9  HCMMR Gate Bundle
-- ═══════════════════════════════════════════════════════════════════

/--
`A_shock(ev)` : the HCMMR shock admissibility gate.

Returns `true` iff the shock event is fully admitted (all four sub-gates pass).
This Boolean is the `A_shock` factor in the multiplicative eigenmass equation.
-/
def A_shock (ev : ShockEvent) : Bool :=
  (shockGate ev).verdict == ShockVerdict.Admitted

/--
`A_shock` factor as Q16_16 weight for use in the eigenmass product chain.
Admitted = 1.0 = 65536; rejected = 0.
-/
def A_shock_weight (ev : ShockEvent) : Q16_16 :=
  if A_shock ev then ⟨65536⟩ else ⟨0⟩

#eval A_shock_weight exampleShock   -- expected: ⟨65536⟩ (admitted)
#eval A_shock_weight ellipticEvent  -- expected: ⟨0⟩      (rejected)

end Semantics.HCMMR.Law20

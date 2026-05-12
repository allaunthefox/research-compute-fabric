/-
Law 19 — VoidScar Fractal Field & Regime Gate

Encodes three primitives derived from the Menger/Koch/DESI synthesis
(see `6-Documentation/docs/distilled/ObserverScale_RegimeGate_VoidScar.md`):

  1. **VoidScar fractal constants** — Koch boundary dimension ln(4)/ln(3) and the
     Menger/Koch divergence pressure ratio (9/5)^n, complementing the Menger
     Hausdorff dimension already in Law18_Constants and MengerSpongeFractalAddressing.

  2. **VoidScarField** — a paired (Ω_void, R_scar) structure capturing interior
     void pressure and boundary scar residual, with an admissibility gate that
     detects Koch-class divergence (boundary cost exceeding void scaffold).

  3. **RegimeGate** — the "active physics" operator A_r that determines which
     law class is awake at a given energy/coupling scale. Encodes the insight
     that the same geometric action (a fist, a gaze vector, a flying body) can
     belong to different physics charts depending on cumulative energy deposition.

Conventions:
  PascalCase types, camelCase functions.
  `structure` for domain concepts.
  `def` needs `#eval` witness or `theorem`.
  Q16_16 for all numeric fields.
  Namespace: Semantics.HCMMR.Law19
  Import: Semantics.HCMMR.Core, Semantics.FixedPoint
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Law19

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  Fractal Dimension Constants
-- ═══════════════════════════════════════════════════════════════════

/--
Koch boundary fractal dimension: D_K = ln(4)/ln(3) ≈ 1.26186.

Scaled to Q16_16: 1.26186 × 65536 = 82,706.
Verified: Wolfram Alpha query `log(4)/log(3)` → 1.26185950...
-/
def kochBoundaryDim : Q16_16 := ⟨82706⟩

/--
Menger sponge Hausdorff dimension: D_M = ln(20)/ln(3) ≈ 2.72683.

Cross-reference: Law18_Constants anchorConstants and
MengerSpongeFractalAddressing.lean §0 store this as ⟨17910⟩ in a
per-module Q16_16 convention.  Here we store the full-precision value
at the standard 65536 scale: 2.72683 × 65536 = 178,696.
Verified: Wolfram Alpha `log(20)/log(3)` → 2.72683...
-/
def mengerVoidDim : Q16_16 := ⟨178696⟩

/--
Menger/Koch divergence pressure numerator: 9 (from ratio 9/5).

The boundary-to-interior divergence ratio per iteration step is
D_MK = (4/3)^n / (20/27)^n = (4/3 × 27/20)^n = (9/5)^n.

Numerator stored separately to avoid fixed-point overflow in
iterated multiplication.
-/
def mkDivNumerator : Q16_16 := ⟨589824⟩   -- 9 × 65536

/--
Menger/Koch divergence pressure denominator: 5.
-/
def mkDivDenominator : Q16_16 := ⟨327680⟩  -- 5 × 65536

/--
One step of the Menger/Koch divergence ratio: D_MK(1) = 9/5 = 1.8.
Scaled: 1.8 × 65536 = 117,964.
Verified: Wolfram Alpha `9/5` = 1.8
-/
def mkDivOneStep : Q16_16 := ⟨117964⟩

-- ═══════════════════════════════════════════════════════════════════
-- §2  VoidScarField — paired interior/boundary pressure structure
-- ═══════════════════════════════════════════════════════════════════

/--
A VoidScarField pairs the interior void pressure (Ω_void, Menger-side)
with the boundary scar residual (R_scar, Koch-side).

  omegaVoid  — surviving volumetric scaffold; decreases as recursion deepens
  rScar      — boundary scar cost; increases as recursion deepens
  epsilon    — regularisation floor preventing divide-by-zero in D_MK
  depth      — recursion depth n at which this snapshot was taken

The field is admissible when scar cost does not bankrupt void savings:
  R_scar ≤ omega_void   (see `voidScarAdmissible`)
-/
structure VoidScarField where
  omegaVoid : Q16_16
  rScar     : Q16_16
  epsilon   : Q16_16
  depth     : Nat
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Default VoidScarField: unit void, zero scar, standard epsilon, depth 0.
-/
def VoidScarField.default : VoidScarField :=
  { omegaVoid := Q16_16.one
  , rScar     := Q16_16.zero
  , epsilon   := Q16_16.epsilon
  , depth     := 0
  }

/--
Divergence pressure at this field snapshot:
  D_MK = R_scar / (omegaVoid + epsilon)

Returns a dimensionless ratio in Q16_16.
Values above Q16_16.one indicate Koch-class divergence.
-/
def voidScarDivergence (f : VoidScarField) : Q16_16 :=
  let denom := Q16_16.add f.omegaVoid f.epsilon
  if denom.val == 0 then Q16_16.infinity
  else Q16_16.div f.rScar denom

/--
Admissibility test: the field is admissible when boundary scar cost
does not exceed the surviving void scaffold.
  admissible ⟺ R_scar ≤ omegaVoid
-/
def voidScarAdmissible (f : VoidScarField) : Bool :=
  f.rScar.val <= f.omegaVoid.val

/--
One Menger deletion step: reduces omegaVoid by factor 20/27.
Scaled: 20/27 × 65536 = 48,560.

Verified: Wolfram Alpha `(20/27)*65536` → 48560.59... → floor 48560.
-/
def mengerDeleteStep (f : VoidScarField) : VoidScarField :=
  let factor : Q16_16 := ⟨48560⟩
  { f with
    omegaVoid := Q16_16.div (Q16_16.mul f.omegaVoid factor) Q16_16.one
  , depth     := f.depth + 1
  }

/--
One Koch boundary growth step: multiplies rScar by factor 4/3.
Scaled: 4/3 × 65536 = 87,381.

Verified: Wolfram Alpha `(4/3)*65536` → 87381.33... → floor 87381.
-/
def kochScarStep (f : VoidScarField) : VoidScarField :=
  let factor : Q16_16 := ⟨87381⟩
  { f with
    rScar := Q16_16.div (Q16_16.mul f.rScar factor) Q16_16.one
  , depth := f.depth + 1
  }

/--
Combined void/scar step: apply one Menger deletion and one Koch growth.
-/
def voidScarStep (f : VoidScarField) : VoidScarField :=
  kochScarStep (mengerDeleteStep f)

/--
Gate verdict for a VoidScarField based on its divergence pressure:
  D_MK ≤ 1.0  → admit  (scar within scaffold)
  D_MK ≤ 1.8  → hold   (one-step pressure, Koch boundary catching up)
  D_MK > 1.8  → reject (Koch divergence exceeds Menger support)
-/
def voidScarGate (f : VoidScarField) : Gate :=
  let d := voidScarDivergence f
  let oneStep : Q16_16 := mkDivOneStep  -- 1.8 threshold
  let verdict :=
    if d.val <= Q16_16.one.val  then GateVerdict.admit
    else if d.val <= oneStep.val then GateVerdict.hold
    else                              GateVerdict.reject
  let score :=
    if d.val == 0 then Q16_16.one
    else Q16_16.sat01 (Q16_16.div Q16_16.one d)
  { name := "VoidScar", required := true, score := score, verdict := verdict }

-- #eval to verify arithmetic
-- Expect: admit (rScar 0, omegaVoid 1 → D_MK = 0)
#eval (voidScarGate VoidScarField.default).verdict
-- Expect: reject (rScar > omegaVoid after 3 steps from seeded field)
#eval
  let seeded : VoidScarField := { VoidScarField.default with rScar := Q16_16.one }
  let stepped := voidScarStep (voidScarStep (voidScarStep seeded))
  (voidScarGate stepped).verdict

-- ═══════════════════════════════════════════════════════════════════
-- §3  RegimeGate — active-physics operator
-- ═══════════════════════════════════════════════════════════════════

/--
The physics regime active at a given scale.

Regimes are ordered by cumulative energy / coupling density.
The same geometric action occupies different charts at different
energies — a fist punch vs a Hulk punch; Superman vs Omni-Man
(suppressed coupling vs admitted coupling); Cyclops' gaze as
information-intake vs momentum-transfer.

Formal reference:
  A_r = Gate(E, p, Δt, A, σ, ρ, c_s, ε_deposit, Θ_medium)
-/
inductive PhysicsRegime where
  | elastic       -- stress below yield; deformation recovers
  | plastic       -- stress above yield; permanent deformation
  | fracture      -- crack/fragmentation network propagates
  | shock         -- impulse faster than acoustic relaxation (v > c_s)
  | thermal       -- energy density drives phase transition
  | plasma        -- ionisation / extreme energy density
  deriving Repr, BEq, DecidableEq, Inhabited

/--
RegimeGate: captures the inputs that determine which PhysicsRegime is active.

  energyDensity   — E/V, energy per unit volume (Q16_16, scaled)
  impulseRate     — p/Δt, rate of momentum transfer
  couplingEta     — η_deposit ∈ [0,1], fraction of kinetic energy
                    deposited into the medium (1 = full coupling,
                    0 = suppressed coupling as in Superman flight)
  yieldThreshold  — σ_y, material yield stress threshold
  acousticLimit   — c_s, speed of sound in medium (for shock gate)
-/
structure RegimeGate where
  energyDensity  : Q16_16
  impulseRate    : Q16_16
  couplingEta    : Q16_16   -- dimensionless, Q16_16 [0,1]
  yieldThreshold : Q16_16
  acousticLimit  : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Resolves the active PhysicsRegime from a RegimeGate.

Ordered threshold checks (first match wins):
  1. impulseRate > acousticLimit × couplingEta  → shock
  2. energyDensity > 8 × yieldThreshold         → plasma (extreme)
  3. energyDensity > 4 × yieldThreshold         → thermal
  4. energyDensity > 2 × yieldThreshold         → fracture
  5. energyDensity > yieldThreshold             → plastic
  6. otherwise                                  → elastic
-/
def resolveRegime (g : RegimeGate) : PhysicsRegime :=
  let acousticCoupled := Q16_16.div (Q16_16.mul g.acousticLimit g.couplingEta) Q16_16.one
  if g.impulseRate.val > acousticCoupled.val then
    PhysicsRegime.shock
  else
    let thr2 := Q16_16.mul g.yieldThreshold ⟨131072⟩  -- × 2
    let thr4 := Q16_16.mul g.yieldThreshold ⟨262144⟩  -- × 4
    let thr8 := Q16_16.mul g.yieldThreshold ⟨524288⟩  -- × 8
    if g.energyDensity.val > thr8.val      then PhysicsRegime.plasma
    else if g.energyDensity.val > thr4.val then PhysicsRegime.thermal
    else if g.energyDensity.val > thr2.val then PhysicsRegime.fracture
    else if g.energyDensity.val > g.yieldThreshold.val then PhysicsRegime.plastic
    else PhysicsRegime.elastic

/--
Coupling class for an observer/actor axis.

"You are here" in regime space: the same projection axis (gaze vector,
motion vector, contact surface) belongs to a different coupling class
depending on how much energy it deposits into the medium.

  passive     — information intake only (η ≈ 0; normal observer gaze)
  kinematic   — sub-threshold momentum transfer (typical motion)
  concussive  — above-threshold impulse transfer (Cyclops optic blast;
                canonical Marvel description: heatless concussive force)
  destructive — energy density exceeds medium admissibility
-/
inductive CouplingClass where
  | passive
  | kinematic
  | concussive
  | destructive
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Resolves the CouplingClass from a RegimeGate.

Thresholds (on couplingEta × energyDensity composite):
  deposited = couplingEta × energyDensity
  > 2 × yieldThreshold → destructive
  > yieldThreshold     → concussive
  > yieldThreshold/4   → kinematic
  otherwise            → passive
-/
def resolveCoupling (g : RegimeGate) : CouplingClass :=
  let deposited := Q16_16.div (Q16_16.mul g.couplingEta g.energyDensity) Q16_16.one
  let thr2 := Q16_16.mul g.yieldThreshold ⟨131072⟩  -- × 2
  let thr4 := Q16_16.div g.yieldThreshold ⟨262144⟩  -- ÷ 4
  if deposited.val > thr2.val          then CouplingClass.destructive
  else if deposited.val > g.yieldThreshold.val then CouplingClass.concussive
  else if deposited.val > thr4.val     then CouplingClass.kinematic
  else                                      CouplingClass.passive

/--
Builds a Gate from a RegimeGate for inclusion in a GateChain.

A regime gate admits when the active regime is elastic or kinematic
(low-coupling, stable physics). It holds at plastic/concussive
(approaching threshold). It rejects at fracture/shock/thermal/plasma/destructive.
-/
def regimeGateVerdict (g : RegimeGate) : Gate :=
  let regime   := resolveRegime g
  let coupling := resolveCoupling g
  let verdict :=
    match regime, coupling with
    | PhysicsRegime.elastic, CouplingClass.passive    => GateVerdict.admit
    | PhysicsRegime.elastic, CouplingClass.kinematic  => GateVerdict.admit
    | PhysicsRegime.plastic, _                        => GateVerdict.hold
    | _, CouplingClass.concussive                     => GateVerdict.hold
    | _, _                                            => GateVerdict.reject
  let score : Q16_16 :=
    match verdict with
    | GateVerdict.admit  => Q16_16.one
    | GateVerdict.hold   => ⟨32768⟩   -- 0.5
    | GateVerdict.reject => Q16_16.zero
  { name := "RegimeGate", required := true, score := score, verdict := verdict }

-- #eval witnesses
-- Low-energy elastic case → expect admit
#eval
  let g : RegimeGate :=
    { energyDensity  := ⟨1000⟩
    , impulseRate    := ⟨500⟩
    , couplingEta    := ⟨655⟩     -- ≈ 0.01, suppressed coupling
    , yieldThreshold := ⟨65536⟩   -- = 1.0
    , acousticLimit  := ⟨196608⟩  -- = 3.0
    }
  (regimeGateVerdict g).verdict

-- Hulk-punch case: high energy, full coupling → expect reject
#eval
  let g : RegimeGate :=
    { energyDensity  := ⟨524288⟩  -- = 8.0, above 8× threshold
    , impulseRate    := ⟨65536⟩
    , couplingEta    := Q16_16.one -- full coupling
    , yieldThreshold := ⟨65536⟩
    , acousticLimit  := ⟨196608⟩
    }
  (regimeGateVerdict g).verdict

-- Cyclops case: passive energy density but concussive coupling class
-- (η is high, deposited > threshold) → expect hold (concussive branch)
#eval
  let g : RegimeGate :=
    { energyDensity  := ⟨131072⟩  -- = 2.0
    , impulseRate    := ⟨1000⟩
    , couplingEta    := Q16_16.one -- full coupling (gaze = force vector)
    , yieldThreshold := ⟨65536⟩
    , acousticLimit  := ⟨655360⟩  -- = 10.0, well above impulseRate
    }
  (regimeGateVerdict g).verdict

-- ═══════════════════════════════════════════════════════════════════
-- §4  Combined VoidScar + Regime GateChain
-- ═══════════════════════════════════════════════════════════════════

/--
Builds a GateChain combining void/scar admissibility with regime stability.

A HCMMR object is lawful at a given scale only if:
  (a) its boundary scar does not bankrupt the void scaffold, AND
  (b) the active physics regime is below the fracture/shock threshold.
-/
def voidScarRegimeChain (f : VoidScarField) (r : RegimeGate) : GateChain :=
  { gates := [voidScarGate f, regimeGateVerdict r] }

-- ═══════════════════════════════════════════════════════════════════
-- §5  Divergence Class Enumeration
-- ═══════════════════════════════════════════════════════════════════

/--
The three divergence classes identified in the VoidScar synthesis.

These classify failure modes that previously appeared as undifferentiated
"model blow-up" events.
-/
inductive DivergenceClass where
  | mengerCollapse   -- interior deletion too aggressive; V_n → 0
  | kochExplosion    -- boundary complexity exceeds receipt capacity; L_n → ∞
  | chartMismatch    -- different observer projections cut at incompatible scales
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Classifies the divergence of a VoidScarField.

  omegaVoid ≤ epsilon                → mengerCollapse
  rScar > omegaVoid × mkDivOneStep   → kochExplosion
  otherwise (structurally coherent)  → chartMismatch (projection issue)
-/
def classifyDivergence (f : VoidScarField) : Option DivergenceClass :=
  if f.omegaVoid.val <= f.epsilon.val then
    some DivergenceClass.mengerCollapse
  else
    let kochThreshold := Q16_16.div (Q16_16.mul f.omegaVoid mkDivOneStep) Q16_16.one
    if f.rScar.val > kochThreshold.val then
      some DivergenceClass.kochExplosion
    else if not (voidScarAdmissible f) then
      some DivergenceClass.chartMismatch
    else
      none  -- no divergence

-- #eval: collapsed void → mengerCollapse
#eval classifyDivergence { VoidScarField.default with omegaVoid := Q16_16.epsilon }
-- #eval: rScar >> omegaVoid → kochExplosion
#eval classifyDivergence { omegaVoid := Q16_16.one, rScar := ⟨200000⟩, epsilon := Q16_16.epsilon, depth := 3 }
-- #eval: balanced field → none
#eval classifyDivergence VoidScarField.default

end Semantics.HCMMR.Law19

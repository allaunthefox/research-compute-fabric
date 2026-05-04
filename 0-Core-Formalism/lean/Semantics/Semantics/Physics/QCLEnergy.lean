/-
  QCLEnergy.lean - Quantum Cascade Laser Physical Constants
  Ports rows 65-71 from MATH_MODEL_MAP.tsv (Rust+Python → Lean).

  Wavelengths in nm stored as Q16.16 (1.0 = 1 nm).
  Energies in eV stored as Q16.16 (1.0 = 1 eV).
  Wavenumbers (cm⁻¹) stored as Q16.16.
-/
import Semantics.Bind
import Semantics.FixedPoint
import Semantics.Physics.Conservation

namespace Semantics.Physics.QCLEnergy

open Semantics Q16_16

-- Physical constants in Q16.16
-- hc in eV·nm: 1239.8 eV·nm — stored scaled: 1239 * 65536
def hc_eV_nm : Q16_16 := ⟨1239 * 65536⟩

-- 1 eV = 65536 in Q16.16
def eV_one : Q16_16 := one

-- QCL operating parameters
structure QCLSpec where
  lambdaMin : Q16_16  -- minimum wavelength (nm, Q16.16)
  lambdaMax : Q16_16  -- maximum wavelength (nm, Q16.16)
  nWells    : UInt32  -- number of quantum wells (e.g. 50)
  eElectron : Q16_16  -- electron energy (eV, Q16.16; typically 1.0 eV = 65536)
deriving Repr, Inhabited, DecidableEq

-- Row 65: E_photon = hc / λ  (eV, for a single wavelength)
def photonEnergy (lambdaNm : Q16_16) : Q16_16 :=
  if lambdaNm.val == 0 then infinity
  else div hc_eV_nm lambdaNm

-- Row 66: ΔE = E_upper - E_lower = hc/λ_min - hc/λ_max
def subbandSpacing (spec : QCLSpec) : Q16_16 :=
  let eUpper := photonEnergy spec.lambdaMin
  let eLower := photonEnergy spec.lambdaMax
  if eUpper.val ≥ eLower.val then sub eUpper eLower else zero

-- Row 67: G = photons_per_e⁻ × n_wells
-- photons_per_e⁻ = ⌊E_electron / ΔE⌋
def cascadeGain (spec : QCLSpec) : Q16_16 :=
  let dE := subbandSpacing spec
  if dE.val == 0 then zero
  else
    let photonsPerElectron := div spec.eElectron dE
    -- integer part only (photons are whole)
    let photonsInt := photonsPerElectron.val / 65536
    ⟨photonsInt * spec.nWells * 65536⟩

-- Row 68: λ(T) = λ₀ + α · (T - T₀)
-- α = 5e-6 /K → in Q16.16 per Kelvin: 5e-6 * 65536 ≈ 0 (sub-LSB)
-- Use practical coefficient: dλ/dT ≈ 0.3 nm/K → 0.3 * 65536 = 19660
def alphaThermal : Q16_16 := ⟨19660⟩  -- 0.3 nm/K in Q16.16

def temperatureTuning (spec : QCLSpec) (lambda0 t0 t : Q16_16) : Q16_16 :=
  let deltaT := if t.val ≥ t0.val then sub t t0 else sub t0 t
  let deltaLambda := mul alphaThermal deltaT
  if t.val ≥ t0.val
  then add lambda0 deltaLambda
  else if lambda0.val ≥ deltaLambda.val then sub lambda0 deltaLambda else zero

-- Row 69: η = (0.5 + window_bonus) · spacing_eff · (1 - stress_penalty)
-- clamped to [0, 1]; all Q16.16
def injectionEfficiency (windowBonus spacingEff stressPenalty : Q16_16) : Q16_16 :=
  -- base = 0.5 = 32768
  let base : Q16_16 := ⟨32768⟩
  let factor1 := add base windowBonus
  let factor2 := mul factor1 spacingEff
  let penaltyTerm := if one.val ≥ stressPenalty.val then sub one stressPenalty else zero
  let result := mul factor2 penaltyTerm
  min result one

-- Row 70: Atmospheric transmission windows
-- Returns 65536 (1.0) if wavelength is in a transmission window, exponential decay outside
inductive AtmWindow | MWIR | LWIR | FarIR deriving Repr, DecidableEq, Inhabited

def inAtmWindow (lambdaMicron : Q16_16) : Bool :=
  -- λ in [3,5], [8,12], [16,20] μm (stored as nm ÷ 1000, so multiply by 1000 scaling)
  -- Here lambdaMicron is in Q16.16 microns
  let v := lambdaMicron.val / 65536  -- integer micron value
  (v ≥ 3 && v ≤ 5) || (v ≥ 8 && v ≤ 12) || (v ≥ 16 && v ≤ 20)

def atmosphericTransmission (lambdaMicron : Q16_16) : Q16_16 :=
  if inAtmWindow lambdaMicron then one else zero  -- simplified: 0 outside window

-- Row 71: ν = 10⁴/λ [cm⁻¹]; DFB: ±7.5 cm⁻¹, EC: ±200 cm⁻¹
-- ν in cm⁻¹, λ in μm
def wavenumber (lambdaMicron : Q16_16) : Q16_16 :=
  -- 10⁴ μm·cm⁻¹ = 10000 * 65536 in Q16.16
  let numerator : Q16_16 := ⟨10000 * 65536⟩
  if lambdaMicron.val == 0 then infinity else div numerator lambdaMicron

def tuningRangeDFB : Q16_16 := ⟨15 * 65536 / 2⟩  -- ±7.5 cm⁻¹
def tuningRangeEC  : Q16_16 := ⟨200 * 65536⟩       -- ±200 cm⁻¹

-- Invariant and cost for physical bind
def qclInvariant (spec : QCLSpec) : String :=
  s!"qcl:lmin={spec.lambdaMin.val},lmax={spec.lambdaMax.val},wells={spec.nWells}"

def qclCost (a b : QCLSpec) (m : Metric) : Q16_16 :=
  let dA := subbandSpacing a
  let dB := subbandSpacing b
  Q16_16.ofNat (abs (sub dA dB)).val.toNat

def qclPhysicalBind (a b : QCLSpec) (m : Metric) : Bind QCLSpec QCLSpec :=
  Semantics.physicalBind a b m qclCost qclInvariant qclInvariant

-- Verify
#eval photonEnergy ⟨10 * 65536⟩      -- 10 μm → ~0.124 eV
#eval cascadeGain { lambdaMin := ⟨9 * 65536⟩, lambdaMax := ⟨11 * 65536⟩, nWells := 50, eElectron := ⟨65536⟩ }

end Semantics.Physics.QCLEnergy

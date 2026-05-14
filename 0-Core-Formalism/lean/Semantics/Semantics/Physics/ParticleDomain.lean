namespace Semantics.Physics

-- ============================================================================
-- Domain taxonomy for the Standard Model particle zoo
-- ============================================================================

/--
Top-level particle domains.
All observable particles collapse into one of three super-classes.
This bounds the semantic search space at the physical layer.
-/
inductive ParticleDomain : Type
  | fermion    -- spin-½ matter particles (quarks, leptons)
  | boson      -- integer-spin force carriers & scalar
  | composite  -- bound states (hadrons, nuclei)
deriving Repr, DecidableEq

/--
Color charge for the strong interaction.
Used for quarks and gluons.
-/
inductive ColorCharge : Type
  | red | green | blue | antiRed | antiGreen | antiBlue
deriving Repr, DecidableEq

/--
The six quark flavors of the Standard Model.
-/
inductive QuarkFlavor : Type
  | up | down | charm | strange | top | bottom
deriving Repr, DecidableEq

/--
The six lepton flavors of the Standard Model.
-/
inductive LeptonFlavor : Type
  | electron | muon | tau | eNeutrino | muNeutrino | tauNeutrino
deriving Repr, DecidableEq

/--
Gauge bosons (force carriers).
Gluon color is handled as a quantity, not as a distinct kind,
keeping the kind space bounded.
-/
inductive GaugeBoson : Type
  | photon | wPlus | wMinus | z | gluon
deriving Repr, DecidableEq

/--
Scalar bosons.
-/
inductive ScalarBoson : Type
  | higgs
deriving Repr, DecidableEq

/--
Common composite hadrons used as the effective composite layer.
This list is intentionally finite and closed.
-/
inductive Hadron : Type
  | proton | neutron
  | pionPlus | pionMinus | pionZero
  | kaonPlus | kaonMinus | kaonZero
  | lambda | sigmaPlus | sigmaZero | sigmaMinus
  | xiZero | xiMinus | omegaMinus
deriving Repr, DecidableEq

/--
The complete finite set of particle kinds at the effective Standard Model layer.

Cardinality:
- Quarks:  6 flavors × 6 colors × 2 (particle/anti) = 72
- Leptons: 6 flavors × 2 (particle/anti) = 12
- Gauge bosons: 5
- Scalar bosons: 1
- Hadrons: 15
- Total = 105
-/
inductive ParticleKind : Type
  | quark  (flavor : QuarkFlavor) (color : ColorCharge) (isAnti : Bool)
  | lepton (flavor : LeptonFlavor) (isAnti : Bool)
  | gauge  (boson : GaugeBoson)
  | scalar (boson : ScalarBoson)
  | hadron (h : Hadron)
deriving Repr, DecidableEq

namespace ParticleKind

def domain : ParticleKind → ParticleDomain
  | quark _ _ _ => .fermion
  | lepton _ _  => .fermion
  | gauge _     => .boson
  | scalar _    => .boson
  | hadron _    => .composite

end ParticleKind

-- ============================================================================
-- Hard limits on the model address space
-- ============================================================================

/-- Total number of distinct particle kinds (105). -/
def maxParticleKinds : Nat := 105

/--
Maximum number of quantities attached to a single particle.
Matches the current `QuantityKind` cardinality:
charge, mass, spin, energy, momentum, baryonNumber, leptonNumber.
-/
def maxQuantitiesPerParticle : Nat := 7

/--
Maximum arity (inputs + outputs) for any interaction vertex.
This bounds the branching factor of the bind graph.
-/
def maxInteractionArity : Nat := 8

/--
A model address is a finite index into the particle-kind space.
This makes the address space explicit, bounded, and hardware-friendly.
-/
structure ModelAddress where
  index : Fin maxParticleKinds
deriving Repr, DecidableEq

namespace ParticleKind

/--
Bijective encoding of every particle kind into a natural number < 105.
This is the canonical model address for neuromorphic lookup tables.
-/
def toNat : ParticleKind → Nat
  | quark q c a =>
      let f := match q with
        | .up => 0 | .down => 1 | .charm => 2 | .strange => 3 | .top => 4 | .bottom => 5
      let col := match c with
        | .red => 0 | .green => 1 | .blue => 2 | .antiRed => 3 | .antiGreen => 4 | .antiBlue => 5
      let anti := if a then 1 else 0
      f * 12 + col * 2 + anti          -- range 0 .. 71
  | lepton l a =>
      let base := 72
      let f := match l with
        | .electron => 0 | .muon => 1 | .tau => 2
        | .eNeutrino => 3 | .muNeutrino => 4 | .tauNeutrino => 5
      let anti := if a then 1 else 0
      base + f * 2 + anti              -- range 72 .. 83
  | gauge b =>
      let base := 84
      let idx := match b with
        | .photon => 0 | .wPlus => 1 | .wMinus => 2 | .z => 3 | .gluon => 4
      base + idx                         -- range 84 .. 88
  | scalar b =>
      let base := 89
      let idx := match b with | .higgs => 0
      base + idx                         -- 89
  | hadron h =>
      let base := 90
      let idx := match h with
        | .proton => 0 | .neutron => 1
        | .pionPlus => 2 | .pionMinus => 3 | .pionZero => 4
        | .kaonPlus => 5 | .kaonMinus => 6 | .kaonZero => 7
        | .lambda => 8 | .sigmaPlus => 9 | .sigmaZero => 10 | .sigmaMinus => 11
        | .xiZero => 12 | .xiMinus => 13 | .omegaMinus => 14
      base + idx                         -- range 90 .. 104

def toAddress (k : ParticleKind) : ModelAddress :=
  ⟨k.toNat, by
    cases k with
    | quark q c a =>
        cases q <;> cases c <;> cases a
        all_goals native_decide
    | lepton l a =>
        cases l <;> cases a
        all_goals native_decide
    | gauge b =>
        cases b
        all_goals native_decide
    | scalar b =>
        cases b
        all_goals native_decide
    | hadron h =>
        cases h
        all_goals native_decide
  ⟩

end ParticleKind

-- All defs in this file are data definitions exercised through theorems in dependent files.
end Semantics.Physics

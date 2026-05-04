import Semantics.Physics.Boundary

namespace Semantics.Physics

-- ---------------------------------------------------------------------------
-- Elementary examples
-- ---------------------------------------------------------------------------

/-- An electron with charge -1 and lepton number +1. -/
def exampleElectron : Particle := {
  kind := ParticleKind.lepton .electron false,
  quantities := [
    { kind := QuantityKind.charge, value := -1 },
    { kind := QuantityKind.leptonNumber, value := 1 },
    { kind := QuantityKind.mass, value := 1 }
  ]
}

/-- A photon with charge 0 and lepton number 0. -/
def examplePhoton : Particle := {
  kind := ParticleKind.gauge .photon,
  quantities := [
    { kind := QuantityKind.charge, value := 0 },
    { kind := QuantityKind.leptonNumber, value := 0 }
  ]
}

/-- A positron (electron anti-particle) with charge +1 and lepton number -1. -/
def examplePositron : Particle := {
  kind := ParticleKind.lepton .electron true,
  quantities := [
    { kind := QuantityKind.charge, value := 1 },
    { kind := QuantityKind.leptonNumber, value := -1 },
    { kind := QuantityKind.mass, value := 1 }
  ]
}

/-- A proton with charge +1 and baryon number +1. -/
def exampleProton : Particle := {
  kind := ParticleKind.hadron .proton,
  quantities := [
    { kind := QuantityKind.charge, value := 1 },
    { kind := QuantityKind.baryonNumber, value := 1 },
    { kind := QuantityKind.mass, value := 1836 }
  ]
}

/-- A neutron with charge 0 and baryon number +1. -/
def exampleNeutron : Particle := {
  kind := ParticleKind.hadron .neutron,
  quantities := [
    { kind := QuantityKind.charge, value := 0 },
    { kind := QuantityKind.baryonNumber, value := 1 },
    { kind := QuantityKind.mass, value := 1839 }
  ]
}

/-- An electron neutrino with charge 0 and lepton number +1. -/
def exampleNeutrino : Particle := {
  kind := ParticleKind.lepton .eNeutrino false,
  quantities := [
    { kind := QuantityKind.charge, value := 0 },
    { kind := QuantityKind.leptonNumber, value := 1 },
    { kind := QuantityKind.mass, value := 0 }
  ]
}

/-- An up quark (red) with charge +2/3 and baryon number +1/3.
We use integer scaling (×3) to avoid rationals: charge = 2, baryon = 1. -/
def exampleUpQuark : Particle := {
  kind := ParticleKind.quark .up .red false,
  quantities := [
    { kind := QuantityKind.charge, value := 2 },
    { kind := QuantityKind.baryonNumber, value := 1 }
  ]
}

/-- A down quark (blue) with charge -1/3 and baryon number +1/3.
Integer scaling (×3): charge = -1, baryon = 1. -/
def exampleDownQuark : Particle := {
  kind := ParticleKind.quark .down .blue false,
  quantities := [
    { kind := QuantityKind.charge, value := -1 },
    { kind := QuantityKind.baryonNumber, value := 1 }
  ]
}

end Semantics.Physics

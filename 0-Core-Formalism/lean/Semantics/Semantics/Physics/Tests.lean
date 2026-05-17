import Semantics.Physics.Interaction
import Semantics.Physics.Projection
import Semantics.Physics.Examples

namespace Semantics.Physics

-- ---------------------------------------------------------------------------
-- Conservation tests
-- ---------------------------------------------------------------------------

/-- An obviously incorrect 1→2 interaction: charge is not conserved. -/
def badInteraction : Interaction := {
  inputs := [exampleElectron],
  outputs := [examplePhoton, examplePhoton]
}

/-- The framework correctly rejects the bad interaction. -/
theorem exampleChargeNotConserved :
  ¬ conserved QuantityKind.charge badInteraction := by
  unfold conserved totalQuantity badInteraction exampleElectron examplePhoton
  native_decide

/-- A correct electron-positron annihilation into two photons. -/
def correctAnnihilation : Interaction := {
  inputs := [exampleElectron, examplePositron],
  outputs := [examplePhoton, examplePhoton]
}

/-- Charge is conserved in e⁻ + e⁺ → γ + γ. -/
theorem exampleChargeConserved :
  conserved QuantityKind.charge correctAnnihilation := by
  unfold conserved totalQuantity correctAnnihilation exampleElectron examplePositron examplePhoton
  native_decide

/-- Lepton number is conserved in e⁻ + e⁺ → γ + γ. -/
theorem exampleLeptonConserved :
  conserved QuantityKind.leptonNumber correctAnnihilation := by
  unfold conserved totalQuantity correctAnnihilation exampleElectron examplePositron examplePhoton
  native_decide

-- ---------------------------------------------------------------------------
-- Projection / measurement tests
-- ---------------------------------------------------------------------------

/-- A measurement where the hidden and observed states match. -/
def exampleMeasurement : Measurement := {
  hiddenState := exampleElectron,
  observedState := exampleElectron,
  compatible := by rfl
}

/-- The measurement is faithful because the kinds align. -/
theorem exampleMeasurementFaithful :
  faithfulMeasurement exampleMeasurement := by
  unfold faithfulMeasurement
  simp [exampleMeasurement]

-- ---------------------------------------------------------------------------
-- Physical path test
-- ---------------------------------------------------------------------------

/-- A trivial physical path containing only the correct annihilation. -/
def examplePhysicalPath : PhysicalPath := {
  steps := [correctAnnihilation],
  lawful := by
    intros step h
    cases h with
    | head _ =>
      simp [lawfulInteraction, coreConservedQuantities]
      repeat { constructor }
      all_goals
        unfold conserved totalQuantity correctAnnihilation exampleElectron examplePositron examplePhoton
        native_decide
    | tail _ h' =>
      cases h'
}

-- ---------------------------------------------------------------------------
-- Domain / address bounds tests
-- ---------------------------------------------------------------------------

/-- Electron maps to domain fermion. -/
theorem electronDomainFermion :
  (ParticleKind.lepton .electron false).domain = ParticleDomain.fermion := by
  rfl

/-- Photon maps to domain boson. -/
theorem photonDomainBoson :
  (ParticleKind.gauge .photon).domain = ParticleDomain.boson := by
  rfl

/-- Proton maps to domain composite. -/
theorem protonDomainComposite :
  (ParticleKind.hadron .proton).domain = ParticleDomain.composite := by
  rfl

/-- The electron has a valid model address (< 105). -/
theorem electronAddressBounded :
  (ParticleKind.lepton .electron false).toNat < maxParticleKinds := by
  simp [ParticleKind.toNat, maxParticleKinds]

/-- The most complex particle (anti-omega baryon) still has a valid address. -/
theorem omegaAddressBounded :
  (ParticleKind.hadron .omegaMinus).toNat < maxParticleKinds := by
  simp [ParticleKind.toNat, maxParticleKinds]

end Semantics.Physics

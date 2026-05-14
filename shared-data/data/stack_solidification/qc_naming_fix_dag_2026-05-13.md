# QC Fix DAG — Naming Convention Fixes

**Date:** 2026-05-13  
**Verdict:** PASS

## Renames

| File | Old | New | Cross-References Updated |
|------|-----|-----|-------------------------|
| Conservation.lean | LawfulInteraction | lawfulInteraction | 2 files (Interaction.lean, Tests.lean) |
| Projection.lean | FaithfulMeasurement | faithfulMeasurement | 1 file (Tests.lean) |
| Interaction.lean | LawfulInteraction | lawfulInteraction | (usage ref in `lawful` field) |
| SuperpositionalBoundaryLayers.lean | smoothstep_zero | smoothstepZero | 0 files (self-contained) |
| SuperpositionalBoundaryLayers.lean | smoothstep_one | smoothstepOne | 0 files |
| SuperpositionalBoundaryLayers.lean | smoothstep_mid | smoothstepMid | 0 files |
| SuperpositionalBoundaryLayers.lean | smoothstep_monotonic | smoothstepMonotonic | 0 files |
| QCLEnergy.lean | hc_eV_nm | hcEvNm | 0 files (internal usage updated) |
| QCLEnergy.lean | eV_one | eVOne | 0 files |
| StringStarConstants.lean | G_const | gConst | 0 files (internal usages updated) |
| StringStarConstants.lean | c_const | cConst | 0 files |
| StringStarConstants.lean | hbar_const | hbarConst | 0 files |
| StringStarConstants.lean | kB_const | kBConst | 0 files |
| DESIModelProjection.lean | q16_div | q16Div | 0 files |
| DESIModelProjection.lean | predictW0_sigma | predictW0Sigma | 0 files |
| DESIModelProjection.lean | predictWa_sigma | predictWaSigma | 0 files |
| DESIModelProjection.lean | predictOmegaM_sigma | predictOmegaMSigma | 0 files |
| DESIModelProjection.lean | predictSigma8_sigma | predictSigma8Sigma | 0 files |
| ValveTestSuite.lean | planckS8_sig | planckS8Sig | 0 files (internal usages updated) |
| ValveTestSuite.lean | desS8_sig | desS8Sig | 0 files |
| ValveTestSuite.lean | kidsS8_sig | kidsS8Sig | 0 files |
| ValveTestSuite.lean | planckAge_sig | planckAgeSig | 0 files |
| ValveTestSuite.lean | baoDM_model | baoDMModel | 0 files |
| ValveTestSuite.lean | baoDM_desi | baoDMDesi | 0 files |
| ValveTestSuite.lean | baoDM_sig | baoDMSig | 0 files |
| ValveTestSuite.lean | baoDH_model | baoDHModel | 0 files |
| ValveTestSuite.lean | baoDH_desi | baoDHDesi | 0 files |
| ValveTestSuite.lean | baoDH_sig | baoDHSig | 0 files |
| Tests.lean | example_charge_not_conserved | exampleChargeNotConserved | 0 files |
| Tests.lean | example_charge_conserved | exampleChargeConserved | 0 files |
| Tests.lean | example_lepton_conserved | exampleLeptonConserved | 0 files |
| Tests.lean | example_measurement_faithful | exampleMeasurementFaithful | 0 files |
| Tests.lean | electron_domain_fermion | electronDomainFermion | 0 files |
| Tests.lean | photon_domain_boson | photonDomainBoson | 0 files |
| Tests.lean | proton_domain_composite | protonDomainComposite | 0 files |
| Tests.lean | electron_address_bounded | electronAddressBounded | 0 files |
| Tests.lean | omega_address_bounded | omegaAddressBounded | 0 files |

## Verification
- **Command:** `lake build`
- **Result:** PASS
- **Jobs:** 3530/3530

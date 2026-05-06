/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

ConstrainedEnergyDynamics.lean — Laws of constrained energy expenditure and metabolic ceilings.

This module formalizes Herman Pontzer's laws of human and animal metabolism:
1. Constraint: The constrained Total Energy Expenditure (TEE) law and compensation.
2. Limit: The metabolic ceiling (Alimentary Limit) for long-term endurance.
3. Allocation: Dynamic energy trade-offs between activity and maintenance.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Metabolism

open Semantics
open Semantics.Q16_16

/-! ## 1. Constrained TEE (Pontzer) -/

/-- Total Energy Expenditure (TEE) with Compensation.
    TEE = BMR + (1 - C) * PAEE + TEF
    BMR: basal rate, PAEE: activity expenditure, C: compensation factor (~0.28), TEF: thermic effect.
    Formalizes the body's dynamic budget reallocation. -/
def constrainedTEE (bmr paee tef compensation_c : Q16_16) : Q16_16 :=
  let activity_contribution := Q16_16.mul (Q16_16.sub Q16_16.one compensation_c) paee
  Q16_16.add (Q16_16.add bmr activity_contribution) tef

/-- Default Energy Compensation Factor (C).
    Empirically determined to be approximately 0.28 (28%). -/
def energyCompensationConstant : Q16_16 :=
  Q16_16.mk 0x000047AE -- 0.28 in Q16.16

/-! ## 2. Metabolic Endurance Limit -/

/-- Metabolic Ceiling (TEE_max).
    TEE_max ≈ 2.5 * BMR
    The long-term physiological ceiling for sustainable energy expenditure. -/
def metabolicCeiling (bmr : Q16_16) : Q16_16 :=
  Q16_16.mul (Q16_16.div (Q16_16.ofInt 5) (Q16_16.ofInt 2)) bmr

/-- Metabolic Scope (Physical Activity Level - PAL).
    PAL = TEE / BMR. Typically caps at 2.5 for long durations. -/
def metabolicScope (tee bmr : Q16_16) : Q16_16 :=
  if bmr == Q16_16.zero then Q16_16.zero
  else Q16_16.div tee bmr

/-! ## 3. Energy Trade-off Law -/

/-- Internal Reallocation Logic.
    Models the reduction in internal budget (maintenance/immune) to fund activity. -/
def maintenanceBudget (base_maintenance activity_compensation : Q16_16) : Q16_16 :=
  Q16_16.sub base_maintenance activity_compensation

end Semantics.Biology.Metabolism

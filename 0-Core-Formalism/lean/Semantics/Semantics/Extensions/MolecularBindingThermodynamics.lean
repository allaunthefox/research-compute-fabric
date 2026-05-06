/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

MolecularBindingThermodynamics.lean — Laws of DNA-protein binding and Boltzmann weights.

This module formalizes the thermodynamic laws of gene regulation:
1. Boltzmann: The statistical weight of a molecular state.
2. Occupancy: The Langmuir/Hill equation for transcription factor binding.
3. Specificity: The ratio of specific to non-specific binding probabilities.
4. Energy: The additive energy model for position weight matrices (PWM).
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Binding

open Semantics
open Semantics.Q16_16

/-! ## 1. Boltzmann Weights -/

/-- Boltzmann Binding Weight (W).
    W = exp(-deltaG / RT)
    deltaG: Gibbs free energy change, R: gas constant, T: temperature.
    Formalizes the relative probability of a bound state. -/
def boltzmannBindingWeight (delta_g temp gas_const : Q16_16) : Q16_16 :=
  -- exp(-deltaG / RT) approximation via 1 - deltaG/RT
  let exponent := Q16_16.div delta_g (Q16_16.mul gas_const temp)
  Q16_16.sub Q16_16.one exponent

/-! ## 2. Binding Occupancy -/

/-- TF Binding Occupancy (theta).
    theta = ([TF] * W) / (1 + [TF] * W)
    Calculates the probability that a DNA site is occupied by a transcription factor. -/
def bindingOccupancy (tf_conc weight : Q16_16) : Q16_16 :=
  let num := Q16_16.mul tf_conc weight
  let den := Q16_16.add Q16_16.one num
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.div num den

/-! ## 3. Binding Specificity -/

/-- Specificity Ratio.
    Ratio = exp(-(deltaG_s - deltaG_ns) / RT)
    Measures the preference of a TF for a specific site over non-specific DNA. -/
def bindingSpecificityRatio (delta_g_s delta_g_ns temp gas_const : Q16_16) : Q16_16 :=
  let delta_delta_g := Q16_16.sub delta_g_s delta_g_ns
  boltzmannBindingWeight delta_delta_g temp gas_const

/-! ## 4. Additive Energy Model -/

/-- PWM Total Energy (E).
    E_total = Σ epsilon(i, j)
    Formalizes the independent contribution of each base to total binding affinity. -/
def totalBindingEnergy (contributions : List Q16_16) : Q16_16 :=
  contributions.foldl Q16_16.add Q16_16.zero

end Semantics.Biology.Binding

/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

NicheIonDynamics.lean — Laws of environmental niches, ion transport, and species richness.

This module formalizes the laws of ecological persistence and physical transport:
1. Ecology: Hutchinson's n-dimensional niche hypervolume.
2. Transport: Nernst-Planck equation for biological ion flux.
3. Scaling: Metabolic scaling of species richness (MTE).
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.NicheTransport

open Semantics
open Semantics.Q16_16

/-! ## 1. Hutchinsonian Niche -/

/-- Niche Hypervolume Bound.
    Checks if an environmental state is within the fundamental niche (L_i <= x_i <= U_i). -/
def isWithinNiche (state limits : List (Q16_16 × Q16_16)) : Bool :=
  -- state: List of x_i, limits: List of (L_i, U_i)
  List.zipWith (fun x range =>
    x.val.toNat >= range.1.val.toNat && x.val.toNat <= range.2.val.toNat
  ) state limits |>.all id

/-! ## 2. Bio-Ion Transport -/

/-- Nernst-Planck Flux (J).
    J = -D * (grad(c) + (ze/kT) * c * grad(phi))
    Models the combined effect of diffusion and electric fields on ion movement. -/
def nernstPlanckFlux (diffusion conc grad_c electric_field valence temp : Q16_16) : Q16_16 :=
  -- ze/kT approximation
  let zeta := Q16_16.div valence temp
  let electromigration := Q16_16.mul (Q16_16.mul zeta conc) electric_field
  let total_grad := Q16_16.add grad_c electromigration
  Q16_16.neg (Q16_16.mul diffusion total_grad)

/-! ## 3. Metabolic Scaling of Diversity -/

/-- MTE Species Richness Law (ln S).
    ln(S) = -E / (kT) + C
    Models how biodiversity scales with environmental temperature. -/
def speciesRichnessLog (activation_energy temp k_const c_offset : Q16_16) : Q16_16 :=
  if temp == Q16_16.zero then Q16_16.zero
  else Q16_16.sub c_offset (Q16_16.div activation_energy (Q16_16.mul k_const temp))

end Semantics.Biology.NicheTransport

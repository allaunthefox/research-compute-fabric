/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CellularGrowthLaws.lean — Laws of cell size scaling and DNA replication initiation.

This module formalizes the laws governing cellular growth and division timing:
1. Scaling: The Cooper-Helmstetter model for cell size vs growth rate.
2. Initiation: Donachie's rule for constant initiation mass per origin.
3. Addition: The 'Adder' principle for incremental volume addition.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.CellGrowth

open Semantics
open Semantics.Q16_16

/-! ## 1. Initiation Control (Donachie) -/

/-- Donachie's Initiation Mass Invariant.
    M_init / n_origins ≈ Constant.
    Replication initiates when the cell reaches a specific mass per origin. -/
def initiationMassRatio (mass n_origins : Q16_16) : Q16_16 :=
  if n_origins == Q16_16.zero then Q16_16.zero
  else Q16_16.div mass n_origins

/-! ## 2. Cell Size Scaling (Cooper-Helmstetter) -/

/-- Cooper-Helmstetter Size Law (S).
    S = S0 * 2^((C+D)/tau)
    S0: unit size, C: replication time, D: division lag, tau: doubling time. -/
def averageCellSize (s0 c_period d_period tau : Q16_16) : Q16_16 :=
  -- Returns size S
  -- 2^((C+D)/tau) approximation
  let exponent := Q16_16.div (Q16_16.add c_period d_period) tau
  -- 2^x approximation via 1 + x
  let factor := Q16_16.add Q16_16.one exponent
  Q16_16.mul s0 factor

/-! ## 3. The Adder Principle -/

/-- Adder Law (V_div).
    V_div = V_birth + ΔV
    Cells add a constant volume ΔV between birth and division. -/
def divisionVolume (v_birth delta_v : Q16_16) : Q16_16 :=
  Q16_16.add v_birth delta_v

end Semantics.Biology.CellGrowth

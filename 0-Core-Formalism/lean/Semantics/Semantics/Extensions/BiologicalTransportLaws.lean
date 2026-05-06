/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

BiologicalTransportLaws.lean — Laws of fluid dynamics, advection, and capillary exchange.

This module formalizes the physical laws of biological mass transport:
1. Dimensionless: Reynolds and Peclet numbers for flow and diffusion regimes.
2. Porous: Darcy's Law for interstitial fluid flow in tissues.
3. Exchange: The Starling Equation for capillary-tissue filtration.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Transport

open Semantics
open Semantics.Q16_16

/-! ## 1. Dimensionless Transport Numbers -/

/-- Reynolds Number (Re).
    Re = (density * speed * length) / viscosity
    Determines if the flow is laminar (low Re) or turbulent (high Re). -/
def reynoldsNumber (density speed length viscosity : Q16_16) : Q16_16 :=
  let num := Q16_16.mul density (Q16_16.mul speed length)
  if viscosity == Q16_16.zero then Q16_16.mk 0xFFFFFFFF
  else Q16_16.div num viscosity

/-- Peclet Number (Pe).
    Pe = (speed * length) / diffusion
    Relates advective transport to diffusive transport. -/
def pecletNumber (speed length diffusion : Q16_16) : Q16_16 :=
  let num := Q16_16.mul speed length
  if diffusion == Q16_16.zero then Q16_16.mk 0xFFFFFFFF
  else Q16_16.div num diffusion

/-! ## 2. Interstitial Flow (Darcy) -/

/-- Darcy Velocity (v).
    v = -(permeability / viscosity) * grad(P)
    Models fluid flow through the extracellular matrix (ECM). -/
def darcyVelocity (permeability viscosity pressure_grad : Q16_16) : Q16_16 :=
  let conductivity := Q16_16.div permeability viscosity
  Q16_16.neg (Q16_16.mul conductivity pressure_grad)

/-! ## 3. Capillary Exchange (Starling) -/

/-- Starling Filtration Rate (Jv).
    Jv = Lp * S * ([Pc - Pi] - sigma * [pic - pii])
    Lp: hydraulic conductivity, S: surface area, sigma: reflection coeff. -/
def starlingFiltration (lp surface_area pc pi sigma pic pii : Q16_16) : Q16_16 :=
  let hydrostatic := Q16_16.sub pc pi
  let oncotic := Q16_16.mul sigma (Q16_16.sub pic pii)
  let net_pressure := Q16_16.sub hydrostatic oncotic
  Q16_16.mul (Q16_16.mul lp surface_area) net_pressure

end Semantics.Biology.Transport

/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SpectralField.lean — Local Field Accumulation and Interaction Metrics

Per AGENTS.md §2: PascalCase for types, camelCase for functions.
Lean 4 is the source of truth.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.ShellModel
import Semantics.Spectrum

namespace Semantics

open Semantics.GeneticCode
open Semantics.ShellModel
open Semantics.Spectrum

/-- Local field aggregates mass, polarity, and spectral contributions from a neighborhood. -/
structure LocalField where
  massField : Q16_16
  polarityField : Q16_16
  spectrum : SpectralSignature
  deriving Repr, DecidableEq

/-- Zero field (neutral element for accumulation). -/
def zeroField : LocalField :=
  { massField := Q16_16.zero
  , polarityField := Q16_16.zero
  , spectrum := SpectralSignature.empty }

/-- Add two fields (piecewise summation). -/
def addField (x y : LocalField) : LocalField :=
  { massField := Q16_16.add x.massField y.massField
  , polarityField := Q16_16.add x.polarityField y.polarityField
  , spectrum := x.spectrum.piecewiseMerge y.spectrum }

/-- Compute contribution of an event at distance d to a local field. -/
def fieldContribution (w : Q16_16) (tip : TipCoord) (col : SpectralSignature) : LocalField :=
  { massField := Q16_16.mul w (Q16_16.ofInt tip.mass)
  , polarityField := Q16_16.mul w (Q16_16.ofInt tip.polarity)
  , spectrum := { bins := col.bins.map (λ b => Q16_16.mul w b) } }

/-- Build local field at position n by looking up to maxN. -/
partial def buildFieldAtLoop (n maxN : Nat) (m : Nat) (acc : LocalField) : LocalField :=
  if m > maxN then
    acc
  else
    let acc' :=
      if m > n then
        let d := m - n
        let w := tailWeight d
        match eventAt m with
        | some (_, _, tip, col) =>
            if w.val.toNat = 0 then acc else addField acc (fieldContribution w tip col)
        | none => acc
      else acc
    buildFieldAtLoop n maxN (m+1) acc'

def buildFieldAt (n maxN : Nat) : LocalField :=
  buildFieldAtLoop n maxN (n+1) zeroField

/-- Compute interaction score between a tip and a local field. -/
def interactionScore (tip : TipCoord) (field : LocalField) (col : SpectralSignature) : Q16_16 :=
  let massTerm := Q16_16.mul (Q16_16.ofInt tip.mass) field.massField
  let polTerm := Q16_16.mul (Q16_16.ofInt tip.polarity) field.polarityField
  let specTerm := SpectralSignature.spectralOverlap col field.spectrum
  Q16_16.add (Q16_16.add massTerm polTerm) specTerm

/-- Interaction score with only spectral component. -/
def spectralInteractionOnly (sig1 sig2 : SpectralSignature) : Q16_16 :=
  SpectralSignature.spectralOverlap sig1 sig2

/-- Compute field magnitude (L2 norm approximation). -/
def fieldMagnitude (field : LocalField) : Q16_16 :=
  let m2 := Q16_16.mul field.massField field.massField
  let p2 := Q16_16.mul field.polarityField field.polarityField
  let sum := Q16_16.add m2 p2
  if field.massField.val.toNat > field.polarityField.val.toNat then
    Q16_16.div sum (Q16_16.add field.massField (Q16_16.ofInt 1))
  else
    Q16_16.div sum (Q16_16.add field.polarityField (Q16_16.ofInt 1))

/-- Check if field is non-trivial. -/
def fieldIsActive (field : LocalField) : Bool :=
  field.massField.val.toNat ≠ 0 || field.polarityField.val.toNat ≠ 0 ||
  field.spectrum.bins.any (λ b => b.val.toNat ≠ 0)

-- Verification
#eval buildFieldAt 1 10
#eval spectralInteractionOnly (SpectralSignature.eventSpectrum EventType.a) (SpectralSignature.eventSpectrum EventType.a)

end Semantics

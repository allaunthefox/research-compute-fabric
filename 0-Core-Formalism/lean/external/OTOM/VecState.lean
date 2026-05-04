/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

VecState.lean — Algebraic Vector States for AVMR Tree Construction

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
open SpectralSignature

/-- Map event to bit representation (a=0, g=1, c=2, t=3). -/
def eventBits : EventType → Nat
  | EventType.a => 0
  | EventType.g => 1
  | EventType.c => 2
  | EventType.t => 3

/-- Core vector state for AVMR nodes.
    Represents the accumulated geometric and spectral properties of a manifold region. -/
structure VecState where
  mass : Int
  polarity : Int
  spectrum : SpectralSignature
  entropyApprox : Q16_16
  interactionStrength : Q16_16
  resonanceCount : Nat
  deriving Repr, DecidableEq

/-- Generate unique hash for a leaf node based on shell index and event type. -/
def leafHash (s : ShellState) (e : EventType) : UInt64 :=
  UInt64.ofNat s.n + UInt64.ofNat (eventBits e)

/-- Mix two hashes using a common combiner (Murmur/SplitMix style). -/
def mixHash (h1 h2 : UInt64) (v : VecState) : UInt64 :=
  h1 + 0x9e3779b97f4a7c15 + h2 + UInt64.ofNat v.resonanceCount

/-- Algebraic node in the AVMR vector tree.
    Combines a geometric hash with a vector state. -/
structure Node where
  hash : UInt64
  vec : VecState
  deriving Repr, DecidableEq

/-- Compute cross-boundary resonance between sibling vectors.
    Counts mass, polarity, and spectral coincidences. -/
def siblingResonance (l r : VecState) : Nat :=
  let m := if l.mass = r.mass then 1 else 0
  let p := if l.polarity = -r.polarity then 1 else 0
  let spec := l.spectrum.resonanceDegeneracy r.spectrum
  m + p + spec

/-- Vector merge law: superpose two states into a parent node.
    Sums mass and polarity, merges spectra, and accumulates resonance. -/
def mergeVec (l r : VecState) : VecState :=
  let res := siblingResonance l r
  { mass := l.mass + r.mass
  , polarity := l.polarity + r.polarity
  , spectrum := l.spectrum.piecewiseMerge r.spectrum
  , entropyApprox := Q16_16.add l.entropyApprox r.entropyApprox
  , interactionStrength := Q16_16.add l.interactionStrength r.interactionStrength
  , resonanceCount := l.resonanceCount + r.resonanceCount + res
  }

/-- Merge two AVMR nodes into a single parent node. -/
def mergeNode (l r : Node) : Node :=
  let v := mergeVec l.vec r.vec
  { hash := mixHash l.hash r.hash v
  , vec := v }

/-- Construct a leaf VecState with spectral encoding. -/
def leafVecState
    (activeIndex : Nat)
    (_maxN : Nat)
    (_s : ShellState)
    (e : EventType)
    (tip : TipCoord) : VecState :=
  let spec := SpectralSignature.eventSpectrum e
  let bin := activeIndex % 8
  -- Place spectral peak at bin position
  let positionedSpec : SpectralSignature := ⟨spec.bins.mapIdx (λ i v => if i = bin then v else Q16_16.zero)⟩
  { mass := tip.mass
  , polarity := tip.polarity
  , spectrum := positionedSpec
  , entropyApprox := Q16_16.zero
  , interactionStrength := Q16_16.zero
  , resonanceCount := 0
  }

/-- Zero vector state (neutral element for merge). -/
def zeroVecState : VecState :=
  { mass := 0
  , polarity := 0
  , spectrum := SpectralSignature.empty
  , entropyApprox := Q16_16.zero
  , interactionStrength := Q16_16.zero
  , resonanceCount := 0 }

-- Verification
#eval mergeVec zeroVecState zeroVecState
#eval siblingResonance zeroVecState zeroVecState
#eval SpectralSignature.eventSpectrum EventType.a

end Semantics

/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

ShellModel.lean — Shell State Geometry and Event Classification

This module implements the Erdős #1196 piecewise eigenvector construction
for shell-based event classification. It provides:
  • Shell state geometry (n, k, a, b parameters)
  • Integer square root for shell boundary calculation
  • Event classification at shell boundaries
  • Tip coordinates (mass, polarity) for event positioning
  • Spectral signatures for each event type

The shell model organizes events in concentric square shells, with each
shell containing events at specific geometric positions.

Per AGENTS.md §0: Lean is the source of truth.
Per AGENTS.md §1.4: Uses Q16.16 for hot-path arithmetic.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum
import Mathlib.Data.Nat.Sqrt

namespace Semantics.ShellModel

open Semantics
open Semantics.GeneticCode
open Semantics.Spectrum

-- ════════════════════════════════════════════════════════════
-- §1  Core Structures
-- ════════════════════════════════════════════════════════════

/-- Shell state parametrization.
    The Erdős shell model uses four parameters:
    • n: Global event index
    • k: Shell index (k = floor(sqrt(n)))
    • a: Distance from previous perfect square (n - k²)
    • b: Distance to next perfect square ((k+1)² - n)
    
    Invariants: n = k² + a = (k+1)² - b, with a + b = 2k + 1 -/
structure ShellState where
  n : Nat
  k : Nat
  a : Nat
  b : Nat
  deriving Repr, DecidableEq

/-- Tip coordinate representation.
    Each event has a "tip" with:
    • mass: ab (product of distances, measures event magnitude)
    • polarity: a - b (difference, measures event asymmetry) -/
structure TipCoord where
  mass : Int      -- ab
  polarity : Int  -- a - b
  deriving Repr, DecidableEq


-- ════════════════════════════════════════════════════════════
-- §2  Shell State Calculation
-- ════════════════════════════════════════════════════════════

/-- Integer square root (floor of sqrt) via Mathlib's proven `Nat.sqrt`. -/
def isqrt (n : Nat) : Nat :=
  Nat.sqrt n

/-- Construct shell state from event index.
    k = floor(sqrt(n))
    a = n - k² (distance from lower perfect square)
    b = (k+1)² - n (distance to upper perfect square) -/
def shellState (n : Nat) : ShellState :=
  let k := isqrt n
  let a := n - k*k
  let b := (k+1)*(k+1) - n
  { n := n, k := k, a := a, b := b }


-- ════════════════════════════════════════════════════════════
-- §3  Event Classification
-- ════════════════════════════════════════════════════════════

/-- Classify event type based on position within shell.
    Event positions in shell (reading clockwise from lower-right):
    • a: At k² (perfect square corner)
    • g: At k² + k (midpoint of right edge)
    • c: At k² + k + 1 (corner after midpoint)
    • t: At (k+1)² - 1 (last position before next square) -/
def classifyEvent (s : ShellState) : Option EventType :=
  let k := s.k
  let n := s.n
  if n = k*k then some .a
  else if n = k*k + k then some .g
  else if n = k*k + k + 1 then some .c
  else if n = (k+1)*(k+1) - 1 then some .t
  else none

/-- Compute tip coordinates from shell state.
    mass = a·b (product measures event "size")
    polarity = a - b (difference measures event "tilt") -/
def tipCoord (s : ShellState) : TipCoord :=
  { mass := Int.ofNat (s.a * s.b)
  , polarity := Int.ofNat s.a - Int.ofNat s.b
  }

/-- Full event information at index n.
    Returns: (ShellState, EventType, TipCoord) or none if not at special position. -/
def eventAt (n : Nat) : Option (ShellState × EventType × TipCoord × SpectralSignature) := do
  let s := shellState n
  let e ← classifyEvent s
  let t := tipCoord s
  let col := SpectralSignature.eventSpectrum e
  pure (s, e, t, col)


-- ════════════════════════════════════════════════════════════
-- §4  Spectral Encoding
-- ════════════════════════════════════════════════════════════

-- Map event to spectrum moved to Spectrum.lean

/-- Merge two spectral signatures (piecewise max). -/
def SpectralSignature.piecewiseMerge (x y : SpectralSignature) : SpectralSignature :=
  { bins := List.zipWith (λ a b => if a.val.toNat > b.val.toNat then a else b) x.bins y.bins }

/-- Compute resonance degeneracy between two spectra.
    Counts overlapping spectral peaks (both non-zero at same position). -/
def SpectralSignature.resonanceDegeneracy (x y : SpectralSignature) : Nat :=
  List.zipWith (λ a b => if a.val.toNat > 0 && b.val.toNat > 0 then 1 else 0) x.bins y.bins
  |>.foldl (· + ·) 0


-- ════════════════════════════════════════════════════════════
-- §5  Tail Weight System
-- ════════════════════════════════════════════════════════════

/-- Tail weight for backward residue as Q16_16.
    Used in field accumulation to weight backward-looking contributions.
    Weights decrease with distance: d=1 → -1, d=2 → -0.5, d=3 → -0.25 -/
def tailWeight : Nat → Q16_16
  | 1 => Q16_16.sub Q16_16.zero Q16_16.one
  | 2 => Q16_16.div (Q16_16.ofInt (-1)) (Q16_16.ofInt 2)
  | 3 => Q16_16.div (Q16_16.ofInt (-1)) (Q16_16.ofInt 4)
  | _ => Q16_16.zero

/-- Integer clamping utility.
    Restricts value to [lo, hi] range. -/
def clampInt (lo hi x : Int) : Int :=
  if x < lo then lo else if x > hi then hi else x

/-- Phase calculation from tip coordinates and interaction strength.
    Combines polarity and mass terms to produce phase index (-3 to 3). -/
def phaseFromTipAndInteraction (s : ShellState) (tip : TipCoord) (j : Q16_16) : Int :=
  let shellWidth : Int := Int.ofNat (2 * s.k + 1)
  let polTerm : Int :=
    if shellWidth = 0 then 0 else (3 * tip.polarity) / shellWidth
  let intTerm : Int :=
    if Q16_16.gt j Q16_16.zero then
      if tip.mass > 0 then 1 else -1
    else 0
  clampInt (-3) 3 (polTerm + intTerm)

/-- Boolean index from interaction sign.
    True if interaction is positive (attractive). -/
def indexBitFromInteraction (j : Q16_16) : Bool :=
  Q16_16.gt j Q16_16.zero


-- ════════════════════════════════════════════════════════════
-- §6  Verification Examples
-- ════════════════════════════════════════════════════════════

#eval shellState 1   -- k=1, a=0, b=3 (perfect square 1²)
#eval shellState 5   -- k=2, a=1, b=4 (between 2²=4 and 3²=9)
#eval classifyEvent (shellState 4)  -- Some EventType.a (4 = 2²)
#eval classifyEvent (shellState 6)  -- Some EventType.g (6 = 2² + 2)
#eval tipCoord (shellState 5)       -- mass=4, polarity=-3

end Semantics.ShellModel

namespace ExtensionScaffold.Compression.Core

/-!
# Core Compression Signatures

This namespace defines the minimal shared interface for all block-scored
compression models.

A model must:
1. carry deterministic state across blocks,
2. score a block under that state,
3. return the updated state,
4. optionally expose a coordinate path (shared/invariant structure),
5. explicitly expose residual information.

This is the formal kernel behind:

  scoreBlock(M, B_j, σ_j) = (ℓ_j, σ_{j+1})

and block-wise model selection:

  M_j* = argmin_{M ∈ Candidates(h_j)} ℓ_j
-/

/-- Q16.16 fixed-point bit-cost. -/
abbrev CostQ16 : Type := UInt64

/-- A finite token alphabet should be supplied by the embedding model. -/
class TokenLike (α : Type) where
  beq : α → α → Bool

/-- Hint classes from the offline refinement stage. -/
inductive RefTag where
  | plain
  | scaffoldLikely
  | voidLikely
  | boundary
  deriving Repr, BEq, DecidableEq

/-- A coordinate atom inside a model-specific coordinate path. -/
structure CoordAtom where
  kind  : UInt8
  value : UInt32
  deriving Repr, BEq

/-- A coordinate path is the transmitted/shared structure carried by a model. -/
structure CoordPath where
  atoms : List CoordAtom
  costQ16 : CostQ16
  deriving Repr, BEq

/-- Residual atom: explicit information that the structure/generator could not carry. -/
structure ResidualAtom where
  kind  : UInt8
  value : UInt32
  deriving Repr, BEq

/-- Residual stream emitted by a model for a block. -/
structure Residual where
  atoms   : List ResidualAtom
  costQ16 : CostQ16
  deriving Repr, BEq

/-- A block is just a finite chunk of tokens. -/
structure Block (Tok : Type) where
  symbols : List Tok
  deriving Repr

/--
Common score result returned by all models.

Fields:
- totalCostQ16 : full block cost under this model
- coordPath    : shared/invariant structure used by the model
- residual     : explicit remainder not handled by the structure
- outState     : updated model state after encoding the block
-/
structure ScoreResult (σ : Type) where
  totalCostQ16 : CostQ16
  coordPath    : CoordPath
  residual     : Residual
  outState     : σ
  deriving Repr

/--
A model family identifier.

This lets the outer controller reason about candidates without needing to know
their internal state type.
-/
inductive ModelKind where
  | baseline
  | baselineReset
  | residualLocal
  | generator
  | lutOisc
  | custom (tag : UInt16)
  deriving Repr, BEq, DecidableEq

/--
A `ModelState σ` is the carried state for a concrete model.

This is intentionally model-specific and opaque at the interface level.
Different models instantiate different state types.
-/
class ModelState (σ : Type) where
  valid : σ → Bool

/--
A `Model Tok σ` is a deterministic block-scoring machine.

The semantics of `scoreBlock` are:

  scoreBlock(M, B_j, σ_j) = (ℓ_j, σ_{j+1})

with `ℓ_j` already including:
- instruction/model cost
- coordinate-path cost
- residual cost
- any internal overhead the model needs to pay
-/
structure Model (Tok σ : Type) [TokenLike Tok] [ModelState σ] where
  kind : ModelKind
  initState : σ
  resetState : σ → σ := fun _ => initState
  scoreBlock : Block Tok → σ → ScoreResult σ
  activationCostQ16 : CostQ16 := 0
  validInit : ModelState.valid initState = true

/--
Block candidate choice result.

Stores:
- chosen model kind
- total block cost
- outgoing state
- emitted coord path
- emitted residual
-/
structure ChosenBlock (σ : Type) where
  modelKind    : ModelKind
  totalCostQ16 : CostQ16
  coordPath    : CoordPath
  residual     : Residual
  outState     : σ
  deriving Repr

/--
Helper: total explicit cost decomposition.

This is the unified equation:

  ℓ_j = L(θ_j) + L(C_j) + L(R_j)

where:
- modelOverheadQ16 = L(θ_j)
- coord.costQ16    = L(C_j)
- residual.costQ16 = L(R_j)
-/
def composeBlockCost
  (modelOverheadQ16 : CostQ16)
  (coord : CoordPath)
  (resid : Residual) : CostQ16 :=
  modelOverheadQ16 + coord.costQ16 + resid.costQ16

/--
A candidate family for a refinement tag.

This is the outer policy layer.
It narrows which models should be tested for a block.
-/
def Candidates (h : RefTag) : List ModelKind :=
  match h with
  | .plain          => [.baseline]
  | .scaffoldLikely => [.baseline, .generator, .lutOisc]
  | .voidLikely     => [.baseline, .residualLocal]
  | .boundary       => [.baselineReset, .residualLocal]

instance : Inhabited CoordPath where
  default := { atoms := [], costQ16 := 0 }

instance : Inhabited Residual where
  default := { atoms := [], costQ16 := 0 }

instance [Inhabited σ] : Inhabited (ChosenBlock σ) where
  default := {
    modelKind := .baseline
    totalCostQ16 := 0
    coordPath := default
    residual := default
    outState := default
  }

/--
Abstract comparison helper for model-selection loops.

Given a list of candidate score results already computed for one block,
pick the cheapest.
-/
def chooseMinCost [Inhabited σ] (xs : List (ChosenBlock σ)) : ChosenBlock σ :=
  xs.foldl
    (fun best x =>
      if x.totalCostQ16 < best.totalCostQ16 then x else best)
    default

/--
Optional outer total:

  L_total(X) = L(H_used) + Σ_j ℓ_j*

This structure is returned by a block-wise controller.
-/
structure CompressionTrace (σ : Type) where
  hintCostQ16  : CostQ16
  blocks       : List (ChosenBlock σ)
  totalCostQ16 : CostQ16
  deriving Repr

/-- Convenience sum over chosen block costs. -/
def sumBlockCosts (xs : List (ChosenBlock σ)) : CostQ16 :=
  xs.foldl (fun acc b => acc + b.totalCostQ16) 0

/--
Convenience theorem shape for future proofs:
the total cost is the hint cost plus the sum of chosen block costs.
-/
theorem totalTraceForm
  (hint : CostQ16) (xs : List (ChosenBlock σ)) :
  (CompressionTrace.mk hint xs (hint + sumBlockCosts xs)).totalCostQ16
    = hint + sumBlockCosts xs := by
  rfl

end ExtensionScaffold.Compression.Core

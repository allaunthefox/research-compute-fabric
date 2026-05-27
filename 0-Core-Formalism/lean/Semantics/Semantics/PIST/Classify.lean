-- Semantics.PIST.Classify — RRC shape classifier over braid adjacency matrices
--
-- Maps an 8×8 braid adjacency matrix (Int counts) to an optional shape-name
-- string.  The output plugs directly into FixtureRow.pistProxyLabel /
-- pistExactLabel (both Option String).  The alignment gate in RRC.Emit
-- compares these strings against shapeStr(row.shape).
--
-- Pipeline:
--   pist_matrix_builder.py  →  rrc_pist_predictions_278_v1.json  (matrix-only)
--   build_pist_matrices_278.py  →  Semantics/PIST/Matrices278.lean
--   build_corpus278.py  →  Semantics/RRC/Corpus278.lean  (labels via classify*)
--   Semantics.RRC.Emit.determineAlignment  →  alignment_status
--
-- The alignment gate reads pistProxyLabel/pistExactLabel from FixtureRow.
-- When both classify functions return none (v2 stub), every row gets
-- missing_prediction.  When they return some "shapeName", labels flow
-- through automatically — no emit logic changes needed.

namespace Semantics.PIST.Classify

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  Matrix type
-- ─────────────────────────────────────────────────────────────────────────────

/-- 8×8 braid adjacency matrix (integer crossing counts).
    Same representation as Semantics.PIST.Spectral uses. -/
abbrev Matrix8 : Type := Array (Array Int)

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  Classifier stubs (v2 — return none until classifier surface is defined)
-- ─────────────────────────────────────────────────────────────────────────────

/-- Advisory shape proxy (high recall, may be heuristic).
    Returns none until a classifier surface is defined in this module.
    Output is a shape-name string matching RRC/Emit.lean's shapeStr
    (e.g. "cognitiveLoadField", "signalShapedRouteCompiler", etc.).

    Contract:
      - Deterministic: same matrix always returns the same result.
      - Side-effect-free: pure function of the matrix alone.
      - Never drives promotion alone — only exact_pred can advance promotion. -/
def classifyProxy (m : Matrix8) : Option String :=
  none

/-- Attested shape exact match (high precision, affects promotion).
    Returns none until a classifier surface is defined in this module.
    Output is a shape-name string matching RRC/Emit.lean's shapeStr.

    Contract:
      - Deterministic: same matrix always returns the same result.
      - Side-effect-free: pure function of the matrix alone.
      - Can drive alignedExact and advance promotion when populated. -/
def classifyExact (m : Matrix8) : Option String :=
  none

end Semantics.PIST.Classify

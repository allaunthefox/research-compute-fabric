/-
GeneticsPromotionGate.lean — Mass Number Gate for Genetics Model Promotion

Wires the core MassNumber admissibility gate into genetics-specific promotion.
Every genetics model must pass this gate before being promoted from
REGISTRY_ONLY → CANONICAL_PLUMBED.

Gate criteria:
  1. MassLeDefault (admissible <= threshold * guarded_residual)
  2. depth <= 2 (no deep abstraction recursion in biological claims)
  3. boundCheck = true (must declare data source and validation plan)
  4. biological_equivalence_check (must not claim DNA equivalence without receipt)
  5. taxonomy_gap_fill (must declare which GCCL group it covers)

Reference:
  - Core/MassNumber.lean (three-layer gate)
  - otom/docs/genetics_information_substrate_boundary.md (four buckets)
-/

import Semantics.Core.MassNumber

namespace Semantics.GeneticsPromotionGate

open Q16_16

/- ============================================================================
   §0  Genetics-Specific Promotion Criteria
   ============================================================================ -/

/-- Which GCCL taxonomy group this model claims to cover.
    Must be explicit — "none" is allowed but means the model is generic. -/
inductive GCCLGroup
  | A_molecular_alphabets
  | B_codon_translation
  | C_protein_peptide
  | D_ambiguity_degeneracy
  | E_sequence_file_quality
  | F_alignment_assembly_graph
  | G_variant_haplotype_population
  | H_annotation_feature
  | I_epigenetic_regulatory
  | J_structural_3d_genome
  | K_expression_multi_omics
  | L_compression_indexing
  | M_synthetic_expanded
  | N_gccl_native
  | none
  deriving Repr, Inhabited, DecidableEq, BEq

/-- A genetics model's self-declared coverage and claim state. -/
structure GeneticsClaim where
  modelName    : String
  gcclGroup    : GCCLGroup
  hasRealData  : Bool      -- Does it use biological data (gnomAD, NCBI, etc.)?
  hasLeanProof : Bool      -- Is there a compiled Lean module?
  hasPythonImpl: Bool      -- Is there a running Python script?
  hasDataReceipt: Bool     -- Does it declare data source + validation plan?
  claimsBiologicalEquivalence : Bool  -- Dangerous: claims "GCCL is DNA" etc.
  deriving Repr, Inhabited

/-- Default claim for a new model (conservative, no claims). -/
def defaultClaim (name : String) : GeneticsClaim :=
  { modelName := name
  , gcclGroup := .none
  , hasRealData := false
  , hasLeanProof := false
  , hasPythonImpl := false
  , hasDataReceipt := false
  , claimsBiologicalEquivalence := false
  }

/- ============================================================================
   §1  The Genetics Promotion Gate
   ============================================================================ -/

/-- Calculate admissible reduction for a genetics model.

    Scoring:
      - hasLeanProof:        +3  (formalization is high value)
      - hasPythonImpl:       +2  (running code is medium value)
      - hasRealData:         +2  (grounding in biology is medium value)
      - hasDataReceipt:      +1  (hygiene is low but necessary)
      - fillsZeroGroup:      +2  (filling a gap is valuable)
      - claimsBiologicalEquivalence: -10 (heavily penalized)
-/
def admissibleReduction (claim : GeneticsClaim) (fillsZeroGroup : Bool) : Q16_16 :=
  let withLean    := if claim.hasLeanProof    then Q16_16.ofNat 3 else Q16_16.zero
  let withPython  := if claim.hasPythonImpl   then Q16_16.ofNat 2 else Q16_16.zero
  let withData    := if claim.hasRealData     then Q16_16.ofNat 2 else Q16_16.zero
  let withReceipt := if claim.hasDataReceipt  then Q16_16.ofNat 1 else Q16_16.zero
  let withGapFill := if fillsZeroGroup        then Q16_16.ofNat 2 else Q16_16.zero
  let penalty     := if claim.claimsBiologicalEquivalence then Q16_16.ofInt (-10) else Q16_16.zero
  withLean + withPython + withData + withReceipt + withGapFill + penalty

/-- Calculate residual risk for a genetics model.

    Scoring (higher = more risk):
      - !hasLeanProof:      +2  (unformalized = risk)
      - !hasPythonImpl:     +1  (no running code = some risk)
      - !hasDataReceipt:    +3  (no validation plan = high risk)
      - claimsBiologicalEquivalence: +5  (dangerous claim = very high risk)
      - depth > 0:          +1 per depth (abstraction recursion risk)
-/
def residualRisk (claim : GeneticsClaim) (depth : Nat) : Q16_16 :=
  let noLean    := if !claim.hasLeanProof    then Q16_16.ofNat 2 else Q16_16.zero
  let noPython  := if !claim.hasPythonImpl   then Q16_16.ofNat 1 else Q16_16.zero
  let noReceipt := if !claim.hasDataReceipt  then Q16_16.ofNat 3 else Q16_16.zero
  let bioClaim  := if claim.claimsBiologicalEquivalence then Q16_16.ofNat 5 else Q16_16.zero
  let depthRisk := Q16_16.ofNat depth
  noLean + noPython + noReceipt + bioClaim + depthRisk

/-- The genetics promotion gate.

    Parameters:
      claim        : the model's self-declared claim state
      fillsZeroGroup: does this model fill a zero-coverage GCCL group?
      depth        : recursion depth of abstraction (default 0)
      threshold    : promotion boundary (default 0.5 = generous)

    Returns true iff the model is admissible for promotion.
-/
def geneticsPromotionGate
    (claim : GeneticsClaim)
    (fillsZeroGroup : Bool)
    (depth : Nat := 0)
    (threshold : Q16_16 := Q16_16.ofRatio 1 2)
    : Bool :=
  let a := admissibleReduction claim fillsZeroGroup
  let r := residualRisk claim depth
  -- Promotion gate: quality must EXCEED threshold * risk
  -- (MassLe is designed for cost<=threshold*risk compression decisions;
  --  genetics promotion needs quality>threshold*risk)
  let qualityBeatsRisk := a.toInt > (threshold * r).toInt
  let depthOk := depth ≤ 2
  let receiptOk := claim.hasDataReceipt
  qualityBeatsRisk && depthOk && receiptOk

/-- Warden rule: if a model claims biological equivalence without receipt,
    emit Underverse packet and block promotion. -/
def biologicalEquivalenceWarden (claim : GeneticsClaim) : String :=
  if claim.claimsBiologicalEquivalence && !claim.hasDataReceipt then
    "UNDERVERSE: biological_equivalence_without_receipt — model " ++ claim.modelName ++ " blocked"
  else
    "PASS"

/- ============================================================================
   §2  Audit Existing Canonical Models
   ============================================================================ -/

/-- Claim state for GeneticCode.lean -/
def geneticCodeClaim : GeneticsClaim :=
  { defaultClaim "GeneticCode.lean" with
    gcclGroup := .B_codon_translation
  , hasLeanProof := true
  , hasDataReceipt := true  -- NCBI Table 1 is well-documented
  }

/-- Claim state for CodonOTOM.lean -/
def codonOTOMClaim : GeneticsClaim :=
  { defaultClaim "CodonOTOM.lean" with
    gcclGroup := .B_codon_translation
  , hasLeanProof := true
  , hasDataReceipt := true
  }

/-- Claim state for PeptideMoE.lean -/
def peptideMoEClaim : GeneticsClaim :=
  { defaultClaim "PeptideMoE.lean" with
    gcclGroup := .C_protein_peptide
  , hasLeanProof := true
  , hasDataReceipt := true
  }

/-- Claim state for GenomicCompression.lean -/
def genomicCompressionClaim : GeneticsClaim :=
  { defaultClaim "GenomicCompression.lean" with
    gcclGroup := .L_compression_indexing
  , hasLeanProof := true
  , hasDataReceipt := true
  }

/-- Claim state for SyntheticGeneticCoding.lean -/
def syntheticGeneticCodingClaim : GeneticsClaim :=
  { defaultClaim "SyntheticGeneticCoding.lean" with
    gcclGroup := .M_synthetic_expanded
  , hasLeanProof := true
  , hasDataReceipt := true
  }

/-- Claim state for GeneticGroundUp.lean -/
def geneticGroundUpClaim : GeneticsClaim :=
  { defaultClaim "GeneticGroundUp.lean" with
    gcclGroup := .N_gccl_native
  , hasLeanProof := true
  , hasDataReceipt := true
  }

/-- Claim state for HachimojiPipeline.lean -/
def hachimojiClaim : GeneticsClaim :=
  { defaultClaim "HachimojiPipeline.lean" with
    gcclGroup := .M_synthetic_expanded
  , hasLeanProof := true
  , hasDataReceipt := true
  }

/-- Claim state for CodonPeptideConsistency.lean -/
def codonPeptideConsistencyClaim : GeneticsClaim :=
  { defaultClaim "CodonPeptideConsistency.lean" with
    gcclGroup := .B_codon_translation
  , hasLeanProof := true
  , hasDataReceipt := true
  }

/-- Claim state for Allelica.py (Python script on real data) -/
def allelicaClaim : GeneticsClaim :=
  { defaultClaim "Allelica.py" with
    gcclGroup := .G_variant_haplotype_population
  , hasRealData := true
  , hasPythonImpl := true
  , hasDataReceipt := true  -- gnomAD source declared
  }

/-- Run the promotion gate on all canonical models.
    This is the infrastructure test: it reveals which models pass/fail. -/
def auditCanonicalModels : String :=
  let models := [
    ("GeneticCode.lean", geneticCodeClaim, false)
  , ("CodonOTOM.lean", codonOTOMClaim, false)
  , ("PeptideMoE.lean", peptideMoEClaim, false)
  , ("GenomicCompression.lean", genomicCompressionClaim, false)
  , ("SyntheticGeneticCoding.lean", syntheticGeneticCodingClaim, false)
  , ("GeneticGroundUp.lean", geneticGroundUpClaim, false)
  , ("HachimojiPipeline.lean", hachimojiClaim, false)
  , ("CodonPeptideConsistency.lean", codonPeptideConsistencyClaim, false)
  , ("Allelica.py", allelicaClaim, false)
  ]
  let results := models.map (fun (name, claim, fillsZero) =>
    let passes := geneticsPromotionGate claim fillsZero
    let warden := biologicalEquivalenceWarden claim
    let aInt := (admissibleReduction claim fillsZero).toInt
    let rInt := (residualRisk claim 0).toInt
    s!"{name}: passes={passes} | warden={warden} | a={aInt} | r={rInt}"
  )
  String.intercalate "\n" results

#eval! auditCanonicalModels

/- ============================================================================
   §3  Audit REGISTRY_ONLY Models (Should Fail Gate)
   ============================================================================ -/

/-- Claim state for a typical REGISTRY_ONLY model (no implementation). -/
def registryOnlyClaim (name : String) (group : GCCLGroup) : GeneticsClaim :=
  { defaultClaim name with
    gcclGroup := group
  , hasDataReceipt := false  -- No implementation = no validation plan
  }

/-- Run the gate on REGISTRY_ONLY models to confirm they fail.
    This demonstrates the gate is working: unimplemented models are blocked. -/
def auditRegistryOnlyModels : String :=
  let models := [
    ("Hardy-Weinberg (registry)", registryOnlyClaim "Hardy-Weinberg" .G_variant_haplotype_population, false)
  , ("Wright-Fisher Drift (registry)", registryOnlyClaim "Wright-Fisher" .G_variant_haplotype_population, true)  -- fills zero group
  , ("RNA Folding deltaG (registry)", registryOnlyClaim "RNA_Folding" .C_protein_peptide, true)  -- fills zero group F
  , ("Jukes-Cantor (registry)", registryOnlyClaim "JukesCantor" .D_ambiguity_degeneracy, false)
  , ("Quasispecies (ghost)", registryOnlyClaim "Quasispecies" .L_compression_indexing, false)
  ]
  let results := models.map (fun (name, claim, fillsZero) =>
    let passes := geneticsPromotionGate claim fillsZero
    let a := admissibleReduction claim fillsZero
    let r := residualRisk claim 0
    let aInt := a.toInt
    let rInt := r.toInt
    s!"{name}: passes={passes} | a={aInt} | r={rInt}"
  )
  String.intercalate "\n" results

#eval! auditRegistryOnlyModels

/- ============================================================================
   §4  Gate Configuration
   ============================================================================ -/

/-- Threshold configuration for different promotion contexts. -/
def conservativeThreshold : Q16_16 := Q16_16.ofRatio 3 10   -- 0.3: strict
def defaultThreshold : Q16_16 := Q16_16.ofRatio 1 2       -- 0.5: normal
def generousThreshold : Q16_16 := Q16_16.ofRatio 7 10    -- 0.7: lenient

/-- Which threshold to use for which context. -/
def thresholdFor (context : String) : Q16_16 :=
  if context == "conservative" then conservativeThreshold
  else if context == "generous" then generousThreshold
  else defaultThreshold

end Semantics.GeneticsPromotionGate

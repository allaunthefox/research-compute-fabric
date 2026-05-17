/-!
# GCCL Formal Core

This module formalizes the broad GCCL space described in
`docs/research/GCCL_THEORY_INTRO.md` and
`docs/research/GCCL_GENETIC_INFORMATION_MIXTURE_PRIMITIVES.md`.

GCCL is treated here as Geometric, Cognitive, and Compression Law: a
receipt-bounded discipline for transitions that declare state, projection,
invariants, residual, cost, quarantine, scale, and receipt evidence.
-/

namespace Semantics.GCCL

/-! ## Law stack axes -/

/-- The three named GCCL law axes plus the audit axes that bound promotion. -/
inductive LawAxis where
  | geometric
  | cognitive
  | compression
  | residual
  | cost
  | scale
  | receipt
  deriving DecidableEq, Repr

/-- The naming stack separates the law from executable and transport layers. -/
inductive StackLayer where
  | gcclLaw
  | gcLangExecutable
  | gcclRepCarrier
  | umupLambdaWrapper
  | invariantReceiptProtocol
  deriving DecidableEq, Repr

/-- Promotion states for a candidate GCCL object. -/
inductive PromotionRung where
  | rawIdea
  | sanitizedMetaphor
  | toyModel
  | typedModel
  | residualTested
  | costAccounted
  | proofCandidate
  | coreModule
  deriving DecidableEq, Repr

/-- Receipt decision states. -/
inductive Decision where
  | accept
  | reject
  | hold
  | quarantine
  deriving DecidableEq, Repr

/-- Projection families that occur across GCCL surfaces. -/
inductive ProjectionKind where
  | address
  | vectorState
  | commitHistory
  | orthogonalBasis
  | goxelScalarField
  | logogramGlyphPayload
  | modelGenome
  | workflowDag
  | externalArtifact
  deriving DecidableEq, Repr

/-- Broad scale-band declarations. -/
inductive ScaleBand where
  | toy
  | local
  | benchmark
  | production
  | crossDomain
  deriving DecidableEq, Repr

/-- Minimal receipt for a transition. Strings carry external hashes/refs. -/
structure Receipt where
  modelId : String
  sourceId : String
  baselineHash : String
  targetHash : String
  proofRef : String
  benchmarkRef : String
  decision : Decision
  deriving Repr

/-- UMUP-lambda / IRP wrapper core: M = (S,T,I,R,K,P,Q,Lambda). -/
structure Wrapper where
  stateSpaceDeclared : Bool
  transformDeclared : Bool
  invariantsDeclared : Bool
  residualDeclared : Bool
  costDeclared : Bool
  projectionDeclared : Bool
  quarantineDeclared : Bool
  scaleDeclared : Bool
  deriving Repr

/-- A transition attempt with explicit gates and receipt evidence. -/
structure Transition where
  wrapper : Wrapper
  validSyntax : Bool
  roundTripOrLossPolicy : Bool
  invariantPreserved : Bool
  residualWithinBound : Bool
  costWithinBound : Bool
  receipt : Receipt
  scaleBand : ScaleBand
  deriving Repr

/-- The universal wrapper is complete when every field is declared. -/
def wrapperComplete (w : Wrapper) : Bool :=
  w.stateSpaceDeclared &&
  w.transformDeclared &&
  w.invariantsDeclared &&
  w.residualDeclared &&
  w.costDeclared &&
  w.projectionDeclared &&
  w.quarantineDeclared &&
  w.scaleDeclared

/-- GCCL acceptability is receipt-bounded; elegance or compression alone is insufficient. -/
def transitionAccepted (t : Transition) : Bool :=
  t.receipt.decision == Decision.accept

/-- The bounded lawful surface admission predicate from the GCCL docs. -/
def lawfulSurfaceAdmissible (t : Transition) : Bool :=
  wrapperComplete t.wrapper &&
  t.validSyntax &&
  t.roundTripOrLossPolicy &&
  t.invariantPreserved &&
  t.residualWithinBound &&
  t.costWithinBound &&
  transitionAccepted t

/-- Quarantine routing is legal only when the wrapper declared a quarantine path. -/
def quarantineRoutable (t : Transition) : Bool :=
  t.wrapper.quarantineDeclared &&
  t.receipt.decision == Decision.quarantine

/-! ## GCCL-Rep transport -/

/-- A compact representative is a carrier, not the truth of the transition. -/
structure GcclRepEvent where
  baselineDeclared : Bool
  representativeDeclared : Bool
  replayAvailable : Bool
  residualChecked : Bool
  kotAccounted : Bool
  receiptAttached : Bool
  committed : Bool
  deriving Repr

/-- Minimal GCCL-Rep verification equation as executable gate. -/
def repVerified (e : GcclRepEvent) : Bool :=
  e.baselineDeclared &&
  e.representativeDeclared &&
  e.replayAvailable &&
  e.residualChecked &&
  e.kotAccounted &&
  e.receiptAttached &&
  e.committed

/-- A representative may be compact while still failing verification. -/
def repPromotable (e : GcclRepEvent) (t : Transition) : Bool :=
  repVerified e && lawfulSurfaceAdmissible t

/-! ## Genetic-information mixture primitives inside GCCL -/

/-- The registry groups from the genetic-information mixture primitive document. -/
inductive PrimitiveGroup where
  | molecularAlphabet
  | codonTranslation
  | proteinPeptide
  | ambiguityDegeneracy
  | sequenceQualityFile
  | alignmentAssemblyGraph
  | variantHaplotypePopulation
  | annotationFeature
  | epigeneticRegulatory
  | structural3DGenome
  | expressionMultiOmics
  | compressionIndexing
  | syntheticExpandedAlphabet
  | gcclNativeModelGenome
  deriving DecidableEq, Repr

/-- Direction or shape of a primitive carrier. -/
inductive PrimitiveDirection where
  | linear
  | graph
  | bidirectional
  | hierarchical
  | spatial
  | temporal
  | frameDependent
  deriving DecidableEq, Repr

/-- Claim boundary for a primitive. -/
inductive PrimitiveDomain where
  | biologicalReference
  | gcclNative
  | synthetic
  | externalCodec
  | mixedByReceipt
  deriving DecidableEq, Repr

/-- Ambiguity policy for active alphabets and mixed symbols. -/
inductive AmbiguityPolicy where
  | rejectUnknown
  | expandIupac
  | boundedMixture
  | probabilisticProfile
  | quarantineUnknown
  deriving DecidableEq, Repr

/-- Lean-facing mixture primitive schema. -/
structure MixturePrimitive where
  primitiveId : String
  group : PrimitiveGroup
  alphabetName : String
  arity : Nat
  direction : PrimitiveDirection
  domain : PrimitiveDomain
  decoderName : String
  ambiguityPolicy : AmbiguityPolicy
  residualPolicyDeclared : Bool
  costPolicyDeclared : Bool
  projectionDeclared : Bool
  receiptRequired : Bool
  claimBoundaryDeclared : Bool
  deriving Repr

/-- A primitive may be decoded only when its active alphabet and decoder are declared. -/
def activeAlphabetDeclared (p : MixturePrimitive) : Bool :=
  p.alphabetName != "" && p.decoderName != ""

/-- Mixture primitive admission from the docs. -/
def mixturePrimitiveAdmissible (p : MixturePrimitive) : Bool :=
  activeAlphabetDeclared p &&
  p.arity > 0 &&
  p.residualPolicyDeclared &&
  p.costPolicyDeclared &&
  p.projectionDeclared &&
  p.receiptRequired &&
  p.claimBoundaryDeclared

/-- Biological and GCCL-native meanings must not be merged without receipt mapping. -/
def domainMixAllowed (left right : PrimitiveDomain) : Bool :=
  if left == right then
    true
  else
    left == PrimitiveDomain.mixedByReceipt || right == PrimitiveDomain.mixedByReceipt

/-- Two primitives can mix only when both are admissible and their domains are bridged. -/
def primitivesCanMix (left right : MixturePrimitive) : Bool :=
  mixturePrimitiveAdmissible left &&
  mixturePrimitiveAdmissible right &&
  domainMixAllowed left.domain right.domain

/-! ## Canonical examples and executable witnesses -/

def completeWrapper : Wrapper :=
  { stateSpaceDeclared := true
    transformDeclared := true
    invariantsDeclared := true
    residualDeclared := true
    costDeclared := true
    projectionDeclared := true
    quarantineDeclared := true
    scaleDeclared := true }

def acceptedReceipt : Receipt :=
  { modelId := "gccl.example.model"
    sourceId := "gccl.example.source"
    baselineHash := "baseline"
    targetHash := "target"
    proofRef := "lean:GCCL"
    benchmarkRef := "example"
    decision := Decision.accept }

def lawfulExample : Transition :=
  { wrapper := completeWrapper
    validSyntax := true
    roundTripOrLossPolicy := true
    invariantPreserved := true
    residualWithinBound := true
    costWithinBound := true
    receipt := acceptedReceipt
    scaleBand := ScaleBand.local }

def compressionOnlyExample : Transition :=
  { lawfulExample with
    invariantPreserved := false }

def verifiedRep : GcclRepEvent :=
  { baselineDeclared := true
    representativeDeclared := true
    replayAvailable := true
    residualChecked := true
    kotAccounted := true
    receiptAttached := true
    committed := true }

def dnaIupacPrimitive : MixturePrimitive :=
  { primitiveId := "gccl.mix.dna.iupac.v1"
    group := PrimitiveGroup.molecularAlphabet
    alphabetName := "DNA-IUPAC"
    arity := 1
    direction := PrimitiveDirection.linear
    domain := PrimitiveDomain.biologicalReference
    decoderName := "iupac_dna_decoder"
    ambiguityPolicy := AmbiguityPolicy.expandIupac
    residualPolicyDeclared := true
    costPolicyDeclared := true
    projectionDeclared := true
    receiptRequired := true
    claimBoundaryDeclared := true }

def modelCodonPrimitive : MixturePrimitive :=
  { primitiveId := "gccl.mix.model.codon.v1"
    group := PrimitiveGroup.gcclNativeModelGenome
    alphabetName := "GCCL-model-codon"
    arity := 3
    direction := PrimitiveDirection.frameDependent
    domain := PrimitiveDomain.gcclNative
    decoderName := "gccl_model_codon_decoder"
    ambiguityPolicy := AmbiguityPolicy.quarantineUnknown
    residualPolicyDeclared := true
    costPolicyDeclared := true
    projectionDeclared := true
    receiptRequired := true
    claimBoundaryDeclared := true }

def mappedBridgePrimitive : MixturePrimitive :=
  { modelCodonPrimitive with
    primitiveId := "gccl.mix.bridge.biological-to-model.v1"
    domain := PrimitiveDomain.mixedByReceipt
    decoderName := "receipt_bound_bio_model_bridge" }

theorem complete_wrapper_true :
    wrapperComplete completeWrapper = true := by
  native_decide

theorem lawful_example_admissible :
    lawfulSurfaceAdmissible lawfulExample = true := by
  native_decide

theorem compression_gain_without_invariant_is_not_lawful :
    lawfulSurfaceAdmissible compressionOnlyExample = false := by
  native_decide

theorem verified_rep_and_lawful_transition_promotes :
    repPromotable verifiedRep lawfulExample = true := by
  native_decide

theorem verified_rep_does_not_promote_unlawful_transition :
    repPromotable verifiedRep compressionOnlyExample = false := by
  native_decide

theorem dna_primitive_admissible :
    mixturePrimitiveAdmissible dnaIupacPrimitive = true := by
  native_decide

theorem model_codon_primitive_admissible :
    mixturePrimitiveAdmissible modelCodonPrimitive = true := by
  native_decide

theorem biological_and_model_domains_do_not_mix_without_receipt :
    primitivesCanMix dnaIupacPrimitive modelCodonPrimitive = false := by
  native_decide

theorem biological_and_model_domains_mix_with_receipt_bridge :
    primitivesCanMix dnaIupacPrimitive mappedBridgePrimitive = true := by
  native_decide

/-- Any object admitted to the bounded lawful surface has a complete wrapper. -/
theorem lawful_surface_implies_complete_wrapper (t : Transition) :
    lawfulSurfaceAdmissible t = true -> wrapperComplete t.wrapper = true := by
  unfold lawfulSurfaceAdmissible
  intro h
  cases hWrap : wrapperComplete t.wrapper
  · simp [hWrap] at h
  · simp

/-- Any promotable representative has a verified carrier. -/
theorem rep_promotion_implies_verified (e : GcclRepEvent) (t : Transition) :
    repPromotable e t = true -> repVerified e = true := by
  unfold repPromotable
  intro h
  cases hRep : repVerified e
  · simp [hRep] at h
  · simp

/-- A decodable primitive necessarily declared an active alphabet. -/
theorem admissible_primitive_has_active_alphabet (p : MixturePrimitive) :
    mixturePrimitiveAdmissible p = true -> activeAlphabetDeclared p = true := by
  unfold mixturePrimitiveAdmissible
  intro h
  cases hAlphabet : activeAlphabetDeclared p
  · simp [hAlphabet] at h
  · simp

#eval lawfulSurfaceAdmissible lawfulExample
#eval lawfulSurfaceAdmissible compressionOnlyExample
#eval repPromotable verifiedRep lawfulExample
#eval primitivesCanMix dnaIupacPrimitive modelCodonPrimitive
#eval primitivesCanMix dnaIupacPrimitive mappedBridgePrimitive

end Semantics.GCCL

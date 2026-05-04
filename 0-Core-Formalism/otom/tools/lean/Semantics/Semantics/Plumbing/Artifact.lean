/-
Project: GraphPlumbing
Domain: axis-04-formalization
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: graph-plumbing/axis-04-formalization/leanmodule/artifact/v0
-/

namespace Semantics.Plumbing

inductive ArtifactKind where
  | leanModule | graphml | mermaid | markdown | json | jsonld
  | zipBundle | chatHistory | researchReport | marketPrototype
  | equation | connectorRecord | visualProjection | unknown
  deriving Repr, DecidableEq

inductive AuthorityLevel where
  | canonicalProof
  | canonicalRegistry
  | operationalMirror
  | evidenceContext
  | projectionOnly
  | draftHypothesis
  | quarantined
  deriving Repr, DecidableEq

inductive SettlementState where
  | seed | forming | stable | crystallized | compressed
  deriving Repr, DecidableEq

structure ArtifactRecord where
  artifactId      : String
  artifactKind    : ArtifactKind
  project         : String
  domain          : String
  artifactType    : String
  settlement      : SettlementState
  title           : String
  contentHash     : String
  semanticHash    : String
  authorityLevel  : AuthorityLevel
  quarantine      : Bool
  tags            : List String
  summary         : String
  deriving Repr

def mayUpdateCanonical (a : ArtifactRecord) : Bool :=
  match a.authorityLevel with
  | .canonicalProof    => !a.quarantine
  | .canonicalRegistry => !a.quarantine
  | _                  => false

def mayUpdateFAMM (a : ArtifactRecord) : Bool :=
  match a.authorityLevel with
  | .canonicalProof    => !a.quarantine
  | .canonicalRegistry => !a.quarantine
  | .evidenceContext   => !a.quarantine
  | .draftHypothesis   => !a.quarantine
  | _                  => false

end Semantics.Plumbing

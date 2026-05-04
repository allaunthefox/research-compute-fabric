/-
Project: GraphPlumbing
Domain: axis-04-formalization
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: graph-plumbing/axis-04-formalization/leanmodule/route/v0
-/

import Semantics.Plumbing.Artifact

namespace Semantics.Plumbing

inductive RouteTarget where
  | leanRegistry
  | graphDiffQueue
  | fammObservationQueue
  | notionMirror
  | linearTaskQueue
  | githubCodeReview
  | consensusEvidence
  | marketPrototypeQueue
  | aceProjection
  | quarantineArchive
  deriving Repr, DecidableEq

inductive CheckKind where
  | syntaxCheck
  | lakeBuild
  | proofCheck
  | duplicateCheck
  | provenanceCheck
  | sourceAudit
  | graphDiff
  | torsionScore
  | quarantineBoundary
  | marketNoAdviceBoundary
  | connectorAuthorityCheck
  deriving Repr, DecidableEq

inductive MutationKind where
  | updateLean
  | updateGraph
  | updateFAMM
  | updateMemory
  | createTask
  | createDoc
  | createProjection
  | createEvidenceLink
  | none
  deriving Repr, DecidableEq

structure RouteDecision where
  artifactId       : String
  routeTarget      : RouteTarget
  routeReason      : String
  requiredChecks   : List CheckKind
  allowedMutations : List MutationKind
  deniedMutations  : List MutationKind
  deriving Repr

inductive OutcomeStatus where
  | accepted
  | acceptedAsDraft
  | mirroredOnly
  | projectionOnly
  | needsReview
  | rejected
  | quarantined
  deriving Repr, DecidableEq

structure OutcomeRecord where
  artifactId     : String
  routeTarget    : RouteTarget
  status         : OutcomeStatus
  checksPassed   : List CheckKind
  checksFailed   : List CheckKind
  emittedRecords : List String
  notes          : String
  deriving Repr

end Semantics.Plumbing

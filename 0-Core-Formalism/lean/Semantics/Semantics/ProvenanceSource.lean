import Semantics.Bind

namespace Semantics.ProvenanceSource

/-!
ProvenanceSource is the open-future event surface for artifact lifecycle
reports. A source event is a report, not a theorem: observation changes the
receipt surface, not the underlying law.

The backend and reference kinds deliberately carry strings instead of closed
enums. The stack should accept future source classes without recompiling the
formal core: a future VCS, ledger, object store, toolbelt, stream, or manual
fixture drop is a configuration entry plus an adapter, not a new ontology law.
-/

inductive Backend where
  | vcs (kind : String) (host : String)
  | objectStore (kind : String)
  | ledger (kind : String)
  | registry (kind : String)
  | stream (kind : String)
  | filesystem (kind : String)
  | toolbelt (kind : String)
  | manual
  | other (name : String)
  deriving Repr, Inhabited

structure Identity where
  scheme : String
  name : String
  deriving Repr, Inhabited

structure Reference where
  scheme : String
  value : String
  deriving Repr, Inhabited

inductive Visibility where
  | publicRecord
  | privateRecord
  | internalRecord
  | unspecifiedRecord
  deriving Repr, Inhabited

structure SourceEvent where
  backend : Backend
  source : String
  action : String
  actor : Identity
  ref : Reference
  visibility : Visibility
  isValid : Bool
  deriving Repr, Inhabited

open Semantics.Q16_16

structure CostPolicy where
  trustedActors : List String
  trustedCost : Semantics.Q16_16
  untrustedCost : Semantics.Q16_16
  publicCost : Semantics.Q16_16
  deriving Repr, Inhabited

def CostPolicy.neutral : CostPolicy := {
  trustedActors := []
  trustedCost := ofNat 1
  untrustedCost := ofNat 1
  publicCost := ofNat 1
}

def CostPolicy.internalReview : CostPolicy := {
  trustedActors := []
  trustedCost := ofFloat 0.5
  untrustedCost := ofNat 2
  publicCost := ofNat 5
}

def actorKey (actor : Identity) : String :=
  s!"{actor.scheme}:{actor.name}"

def isTrusted (policy : CostPolicy) (actor : Identity) : Bool :=
  policy.trustedActors.any (fun key => key == actor.name || key == actorKey actor)

def visibilityToken : Visibility → String
  | .publicRecord => "public"
  | .privateRecord => "private"
  | .internalRecord => "internal"
  | .unspecifiedRecord => "unspecified"

def backendToken : Backend → String
  | .vcs kind host => s!"vcs:{kind}:{host}"
  | .objectStore kind => s!"object-store:{kind}"
  | .ledger kind => s!"ledger:{kind}"
  | .registry kind => s!"registry:{kind}"
  | .stream kind => s!"stream:{kind}"
  | .filesystem kind => s!"filesystem:{kind}"
  | .toolbelt kind => s!"toolbelt:{kind}"
  | .manual => "manual"
  | .other name => s!"other:{name}"

def invariant (event : SourceEvent) : String :=
  if event.isValid then
    s!"lawful_source:{backendToken event.backend}:{event.source}:{event.action}:{event.ref.scheme}:{event.ref.value}"
  else
    "unlawful_source"

def legacyInvariant (validPrefix invalidToken : String) (event : SourceEvent) : String :=
  if event.isValid then s!"{validPrefix}:{event.source}:{event.action}" else invalidToken

def targetInvariant (event : SourceEvent) (_target : String) : String :=
  invariant event

def legacyTargetInvariant (validPrefix : String) (event : SourceEvent) (_target : String) : String :=
  s!"{validPrefix}:{event.source}:{event.action}"

def cost (policy : CostPolicy) (event : SourceEvent) (_target : String) (_g : Metric) : Semantics.Q16_16 :=
  if isTrusted policy event.actor then
    policy.trustedCost
  else
    match event.visibility with
    | .publicRecord => policy.publicCost
    | _ => policy.untrustedCost

def bind (policy : CostPolicy) (event : SourceEvent) (target : String) (g : Metric) : Bind SourceEvent String :=
  controlBind event target g (cost policy) invariant (targetInvariant event)

def legacyBind
    (policy : CostPolicy)
    (validPrefix invalidToken : String)
    (event : SourceEvent)
    (target : String)
    (g : Metric) : Bind SourceEvent String :=
  controlBind event target g
    (cost policy)
    (legacyInvariant validPrefix invalidToken)
    (legacyTargetInvariant validPrefix event)

#eval invariant {
  backend := .toolbelt "science-toolbelt",
  source := "shared-data/artifacts/science_toolbelt/probe.json",
  action := "probed",
  actor := { scheme := "tool", name := "probe_science_toolbelt.py" },
  ref := { scheme := "sha256", value := "example" },
  visibility := .internalRecord,
  isValid := true
}

end Semantics.ProvenanceSource

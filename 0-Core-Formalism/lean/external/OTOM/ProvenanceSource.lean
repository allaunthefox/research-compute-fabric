import Semantics.Bind

namespace Semantics.ProvenanceSource

/-!
Open provenance-source surface for legacy OTOM staging modules.

This mirrors the active Q16.16 module with raw UInt32 scalars so historical
external modules can delegate to the same source-event shape without importing
the active fixed-point stack.
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

structure Identity where
  scheme : String
  name : String

structure Reference where
  scheme : String
  value : String

inductive Visibility where
  | publicRecord
  | privateRecord
  | internalRecord
  | unspecifiedRecord

structure SourceEvent where
  backend : Backend
  source : String
  action : String
  actor : Identity
  ref : Reference
  visibility : Visibility
  isValid : Bool

structure CostPolicy where
  trustedActors : List String
  trustedCost : UInt32
  untrustedCost : UInt32
  publicCost : UInt32

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

def cost (policy : CostPolicy) (event : SourceEvent) (_target : String) (_g : Metric) : UInt32 :=
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

end Semantics.ProvenanceSource

import Semantics.Bind
import Lean.Data.Json

namespace Semantics.JsonLSurfaceConnector

open Lean

/-!
# JSON-L Surface Connector

Lean-owned connector manifest for this instance. External MCP/surface shims may
serialize these records, but source/op categories, genome routing, bind class,
and connector lawfulness live here.
-/

abbrev TimestampMillis := Nat
abbrev GenomeBin := Fin 8
abbrev Q16_16 := UInt32

inductive EventSource where
  | notion
  | linear
  | ene
  | rgflow
  | swarm
  deriving Repr, DecidableEq, BEq

inductive EventOperation where
  | upsert
  | delete
  | snapshot
  | correct
  | attest
  deriving Repr, DecidableEq, BEq

inductive BindClass where
  | informational
  | geometric
  | thermodynamic
  | physical
  | control
  deriving Repr, DecidableEq, BEq

inductive SwarmEventType where
  | topologyChange
  | taskComplete
  | nodeFailure
  | syncManifest
  deriving Repr, DecidableEq, BEq

inductive SurfaceTarget where
  | enePackages
  | swarmManifest
  | swarmNodes
  | swarmWorkQueue
  | multicastBucket
  deriving Repr, DecidableEq, BEq

inductive McpTool where
  | appendJsonL
  | attestJsonL
  | surfaceSync
  | connectorHealth
  deriving Repr, DecidableEq, BEq

structure Genome where
  mu : GenomeBin
  rho : GenomeBin
  c : GenomeBin
  m : GenomeBin
  ne : GenomeBin
  sig : GenomeBin
  deriving Repr, DecidableEq

structure JsonLBindWitness where
  lawful : Bool
  cost : Q16_16
  invariant : String
  bindClass : BindClass
  deriving Repr, DecidableEq

structure Provenance where
  node : String
  lakeSeed : String
  tailscaleIp : String
  attestationHash : String
  prevId : Option String
  deriving Repr, DecidableEq

structure JsonLEvent where
  tMillis : TimestampMillis
  src : EventSource
  id : String
  op : EventOperation
  dataTag : String
  genome : Genome
  bind : JsonLBindWitness
  provenance : Provenance
  deriving Repr, DecidableEq

structure SurfaceConnector where
  instanceId : String
  acceptedSources : List EventSource
  acceptedOps : List EventOperation
  tools : List McpTool
  surfaceTargets : List SurfaceTarget
  deriving Repr, DecidableEq

def EventSource.toTag : EventSource → String
  | .notion => "notion"
  | .linear => "linear"
  | .ene => "ene"
  | .rgflow => "rgflow"
  | .swarm => "swarm"

def EventOperation.toTag : EventOperation → String
  | .upsert => "upsert"
  | .delete => "delete"
  | .snapshot => "snapshot"
  | .correct => "correct"
  | .attest => "attest"

def BindClass.toTag : BindClass → String
  | .informational => "informational_bind"
  | .geometric => "geometric_bind"
  | .thermodynamic => "thermodynamic_bind"
  | .physical => "physical_bind"
  | .control => "control_bind"

def McpTool.toName : McpTool → String
  | .appendJsonL => "append_jsonl"
  | .attestJsonL => "attest_jsonl"
  | .surfaceSync => "surface_sync"
  | .connectorHealth => "connector_health"

def SurfaceTarget.toTag : SurfaceTarget → String
  | .enePackages => "packages"
  | .swarmManifest => "swarm_manifest"
  | .swarmNodes => "swarm_nodes"
  | .swarmWorkQueue => "swarm_work_queue"
  | .multicastBucket => "multicast_bucket"

def bin (n : Nat) : GenomeBin :=
  ⟨n % 8, Nat.mod_lt n (by decide)⟩

def genomeAddress (g : Genome) : Nat :=
  (g.mu.val <<< 15) ||| (g.rho.val <<< 12) ||| (g.c.val <<< 9) |||
    (g.m.val <<< 6) ||| (g.ne.val <<< 3) ||| g.sig.val

def genomeBucket (g : Genome) : Nat :=
  genomeAddress g >>> 15

def sourceTarget (e : JsonLEvent) : SurfaceTarget :=
  match e.src with
  | .notion | .linear | .ene => .enePackages
  | .rgflow => .swarmManifest
  | .swarm =>
      if e.bind.lawful then .swarmNodes else .swarmWorkQueue

def connectorInvariant (e : JsonLEvent) : String :=
  s!"jsonl:{e.src.toTag}:{e.op.toTag}:{e.id}:bucket={genomeBucket e.genome}"

def connectorCost (_connector : SurfaceConnector) (event : JsonLEvent) (_metric : Metric) : Semantics.Q16_16 :=
  ⟨event.bind.cost + UInt32.ofNat (genomeBucket event.genome)⟩

def bindConnectorEvent (connector : SurfaceConnector) (event : JsonLEvent) : Bind SurfaceConnector JsonLEvent :=
  let metric := { Metric.euclidean with reference := "jsonl_surface_connector", history_len := connector.tools.length }
  informationalBind
    connector
    event
    metric
    connectorCost
    (fun _ => connectorInvariant event)
    connectorInvariant

def toJsonGenome (g : Genome) : Json :=
  Json.mkObj [
    ("mu", Json.num g.mu.val),
    ("rho", Json.num g.rho.val),
    ("c", Json.num g.c.val),
    ("m", Json.num g.m.val),
    ("ne", Json.num g.ne.val),
    ("sig", Json.num g.sig.val)
  ]

def toJsonBindWitness (b : JsonLBindWitness) : Json :=
  Json.mkObj [
    ("lawful", Json.bool b.lawful),
    ("cost", Json.num b.cost.toNat),
    ("invariant", Json.str b.invariant),
    ("class", Json.str b.bindClass.toTag)
  ]

def toJsonProvenance (p : Provenance) : Json :=
  Json.mkObj [
    ("node", Json.str p.node),
    ("lake_seed", Json.str p.lakeSeed),
    ("tailscale_ip", Json.str p.tailscaleIp),
    ("attestation_hash", Json.str p.attestationHash),
    ("prev_id", match p.prevId with | some id => Json.str id | none => Json.null)
  ]

def toJsonEvent (e : JsonLEvent) : Json :=
  Json.mkObj [
    ("t", Json.num e.tMillis),
    ("src", Json.str e.src.toTag),
    ("id", Json.str e.id),
    ("op", Json.str e.op.toTag),
    ("data", Json.mkObj [("tag", Json.str e.dataTag)]),
    ("genome", toJsonGenome e.genome),
    ("bind", toJsonBindWitness e.bind),
    ("provenance", toJsonProvenance e.provenance)
  ]

def toJsonConnector (c : SurfaceConnector) : Json :=
  Json.mkObj [
    ("instance_id", Json.str c.instanceId),
    ("accepted_sources", Json.arr ((c.acceptedSources.map (fun s => Json.str s.toTag)).toArray)),
    ("accepted_ops", Json.arr ((c.acceptedOps.map (fun op => Json.str op.toTag)).toArray)),
    ("mcp_tools", Json.arr ((c.tools.map (fun tool => Json.str tool.toName)).toArray)),
    ("surface_targets", Json.arr ((c.surfaceTargets.map (fun target => Json.str target.toTag)).toArray))
  ]

def instanceConnector : SurfaceConnector :=
  { instanceId := "research-stack-jsonl-surface"
    acceptedSources := [.notion, .linear, .ene, .rgflow, .swarm]
    acceptedOps := [.upsert, .delete, .snapshot, .correct, .attest]
    tools := [.appendJsonL, .attestJsonL, .surfaceSync, .connectorHealth]
    surfaceTargets := [.enePackages, .swarmManifest, .swarmNodes, .swarmWorkQueue, .multicastBucket] }

def exampleGenome : Genome :=
  { mu := bin 2, rho := bin 4, c := bin 0, m := bin 4, ne := bin 7, sig := bin 0 }

def exampleBindWitness : JsonLBindWitness :=
  { lawful := true, cost := 0x00010000, invariant := "jsonlSchemaFiniteSourceOp", bindClass := .informational }

def exampleProvenance : Provenance :=
  { node := "qfox", lakeSeed := "nnyyP7DoHS11CNTRL", tailscaleIp := "100.105.111.120",
    attestationHash := "sha256:lean-owned-jsonl-surface", prevId := none }

def exampleEvent : JsonLEvent :=
  { tMillis := 1777042802000, src := .ene, id := "ene:jsonl-surface:example",
    op := .upsert, dataTag := "lean_connector_manifest", genome := exampleGenome,
    bind := exampleBindWitness, provenance := exampleProvenance }

theorem bindConnectorEventLawful :
    (bindConnectorEvent instanceConnector exampleEvent).lawful = true := by
  rfl

theorem sourceTargetSwarmUnlawful (e : JsonLEvent) :
    e.src = .swarm → e.bind.lawful = false → sourceTarget e = .swarmWorkQueue := by
  intro hSrc hLawful
  unfold sourceTarget
  simp [hSrc, hLawful]

#eval genomeAddress exampleGenome -- expected: 82232
#eval genomeBucket exampleGenome -- expected: 2
#eval connectorInvariant exampleEvent -- expected: jsonl:ene:upsert:ene:jsonl-surface:example:bucket=2
#eval (bindConnectorEvent instanceConnector exampleEvent).lawful -- expected: true

end Semantics.JsonLSurfaceConnector

import Semantics.Testing.ErdosHarness

namespace Semantics.Testing.ErdosSurface

open Semantics.Testing.ErdosHarness

/-!
ErdosSurface.lean

Pure Lean surface plan for the DAG/FAMM split.  Lean owns the finite packet
status model and emits a compact receipt for the Rust surface manager.

The surface lanes are deliberately treated as acceleration and transport
lanes.  They do not promote theorem claims.
-/

inductive SurfaceLane where
  | leanTrust
  | shmControl
  | vulkanShader
  | h264Transport
  | h265Transport
  | audioDsp
  deriving Repr, DecidableEq

structure LanePlan where
  lane : SurfaceLane
  role : String
  trustBoundary : String
  deriving Repr

structure FammCount where
  domain : String
  status : String
  count : Nat
  deriving Repr, DecidableEq

def laneName : SurfaceLane -> String
  | .leanTrust => "lean_trust"
  | .shmControl => "shm_control"
  | .vulkanShader => "vulkan_shader"
  | .h264Transport => "h264_transport"
  | .h265Transport => "h265_transport"
  | .audioDsp => "audio_dsp"

def surfacePlan : List LanePlan :=
  [ { lane := .leanTrust
      role := "packet status model and promotion gate"
      trustBoundary := "authoritative finite receipt classifier" }
  , { lane := .shmControl
      role := "RAM resident payload exchange"
      trustBoundary := "transport only; hash and length checked by host" }
  , { lane := .vulkanShader
      role := "numeric reductions over compact packet counts"
      trustBoundary := "acceleration only; results rechecked by Lean/CPU" }
  , { lane := .h264Transport
      role := "dense packet-frame telemetry transport"
      trustBoundary := "lossy unless decoded and hash-verified" }
  , { lane := .h265Transport
      role := "denser packet-frame telemetry transport"
      trustBoundary := "lossy unless decoded and hash-verified" }
  , { lane := .audioDsp
      role := "streaming DSP metrics over packet waveforms"
      trustBoundary := "signal lane only; not proof-bearing" } ]

def currentFammCounts : List FammCount :=
  [ { domain := "erdos_gyarfas", status := "verified_has_power_two_cycle", count := 5 }
  , { domain := "erdos_mollin_walsh", status := "finite_smoke_pass", count := 3 }
  , { domain := "erdos_selfridge", status := "finite_smoke_pass", count := 2 }
  , { domain := "erdos_selfridge", status := "invalid_packet", count := 2 } ]

def totalCount (xs : List FammCount) : Nat :=
  xs.foldl (fun acc x => acc + x.count) 0

def allSurfaceClaimsFinite (xs : List FammCount) : Bool :=
  xs.all (fun x =>
    x.status == "verified_has_power_two_cycle" ||
    x.status == "finite_smoke_pass" ||
    x.status == "invalid_packet" ||
    x.status == "detector_anomaly")

theorem current_surface_claims_are_finite :
    allSurfaceClaimsFinite currentFammCounts = true := by
  native_decide

theorem current_surface_total_count :
    totalCount currentFammCounts = 12 := by
  native_decide

def escapeJson (s : String) : String :=
  s.foldl
    (fun acc c =>
      if c == '"' then acc ++ "\\\""
      else if c == '\\' then acc ++ "\\\\"
      else if c == '\n' then acc ++ "\\n"
      else acc.push c)
    ""

def q (s : String) : String :=
  "\"" ++ escapeJson s ++ "\""

def joinWith (sep : String) : List String -> String
  | [] => ""
  | x :: xs => xs.foldl (fun acc y => acc ++ sep ++ y) x

def boolJson (b : Bool) : String :=
  if b then "true" else "false"

def lanePlanJson (p : LanePlan) : String :=
  "{" ++
    q "lane" ++ ":" ++ q (laneName p.lane) ++ "," ++
    q "role" ++ ":" ++ q p.role ++ "," ++
    q "trust_boundary" ++ ":" ++ q p.trustBoundary ++
  "}"

def countJson (c : FammCount) : String :=
  "{" ++
    q "domain" ++ ":" ++ q c.domain ++ "," ++
    q "status" ++ ":" ++ q c.status ++ "," ++
    q "count" ++ ":" ++ toString c.count ++
  "}"

def countsArrayJson (xs : List FammCount) : String :=
  "[" ++ joinWith "," (xs.map countJson) ++ "]"

def countValuesJson (xs : List FammCount) : String :=
  "[" ++ joinWith "," (xs.map (fun x => toString x.count)) ++ "]"

def lanesJson : String :=
  "[" ++ joinWith "," (surfacePlan.map lanePlanJson) ++ "]"

def surfaceReceiptJson : String :=
  "{" ++
    q "schema" ++ ":" ++ q "erdos_surface_v1" ++ "," ++
    q "claim_boundary" ++ ":" ++ q "surface lanes accelerate or transport; Lean owns promotion gates" ++ "," ++
    q "finite_statuses_only" ++ ":" ++ boolJson (allSurfaceClaimsFinite currentFammCounts) ++ "," ++
    q "total_count" ++ ":" ++ toString (totalCount currentFammCounts) ++ "," ++
    q "counts" ++ ":" ++ countsArrayJson currentFammCounts ++ "," ++
    q "count_values" ++ ":" ++ countValuesJson currentFammCounts ++ "," ++
    q "lanes" ++ ":" ++ lanesJson ++
  "}"

def main : IO Unit := do
  IO.println surfaceReceiptJson

end Semantics.Testing.ErdosSurface

def main : IO Unit :=
  Semantics.Testing.ErdosSurface.main

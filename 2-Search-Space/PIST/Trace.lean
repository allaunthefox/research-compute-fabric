import Lean

open Lean Elab Tactic Meta

/-!
# PIST Trace — goal-state snapshotter for Tier 2 flexure recording.

Provides a tactic `trace_state_json "tag"` that emits structured goal-state
snapshots to `logInfo` with a `@@PIST_TRACE_JSON@@` sentinel that the Python
trace bridge can parse from stdout.

Usage:
```lean
import PIST.Trace

theorem t (n : Nat) : n + 0 = n := by
  trace_state_json "step_0_before"
  simp
  trace_state_json "step_0_after"
```
-/

namespace PIST.Trace

private def natToJson (n : Nat) : Json :=
  Json.num { mantissa := (n : Int), exponent := 0 }

private def goalToJson (g : MVarId) : MetaM Json := do
  let decl ← g.getDecl
  let target ← instantiateMVars decl.type
  let targetFmt ← ppExpr target

  let mut hyps : Array Json := #[]
  for localDecl in decl.lctx do
    if !localDecl.isImplementationDetail then
      let ty ← instantiateMVars localDecl.type
      let tyFmt ← ppExpr ty
      hyps := hyps.push <| Json.mkObj [
        ("name", Json.str localDecl.userName.toString),
        ("type", Json.str tyFmt.pretty)
      ]

  return Json.mkObj [
    ("target",           Json.str targetFmt.pretty),
    ("goal_id",          Json.str g.name.toString),
    ("hypotheses",       Json.arr hyps),
    ("hypothesis_count", natToJson hyps.size)
  ]

/-- Emit a structured goal-state snapshot tagged with `tag`.

The output is prefixed with `@@PIST_TRACE_JSON@@` so the Python bridge
can scrape it from Lean's stdout.
-/
elab "trace_state_json" tag:str : tactic => do
  let goals ← getGoals
  let goalJsons ← goals.mapM (fun g => liftMetaM (goalToJson g))

  let payload : Json := Json.mkObj [
    ("event",      Json.str "pist_trace_state"),
    ("tag",        Json.str tag.getString),
    ("goal_count", natToJson goals.length),
    ("goals",      Json.arr goalJsons.toArray)
  ]

  logInfo m!"@@PIST_TRACE_JSON@@{payload.compress}"

end PIST.Trace

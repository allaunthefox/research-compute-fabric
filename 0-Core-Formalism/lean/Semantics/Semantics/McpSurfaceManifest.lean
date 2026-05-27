import Semantics.JsonLSurfaceConnector
import Lean.Data.Json

namespace Semantics.McpSurfaceManifest

open Lean
open Semantics.JsonLSurfaceConnector

/-!
Lean-first MCP surface manifest.

This file defines the *published* tool list and per-tool input schemas for the
JsonL surface connector. Shims may expose these tools over MCP, but MUST NOT
invent tool names or schemas.
-/

structure JsonSchema where
  schema : Json
  deriving Repr, DecidableEq

structure ToolSpec where
  name : String
  description : String
  inputSchema : JsonSchema
  deriving Repr, DecidableEq

/-- Minimal JSON schema for a single JsonL line payload. -/
def jsonlLineSchema : JsonSchema :=
  { schema := Json.mkObj [
      ("type", Json.str "object"),
      ("properties", Json.mkObj [
        ("line", Json.mkObj [("type", Json.str "string")])
      ]),
      ("required", Json.arr #[Json.str "line"]),
      ("additionalProperties", Json.bool false)
    ] }

/-- Minimal JSON schema for a connector-health request. -/
def connectorHealthSchema : JsonSchema :=
  { schema := Json.mkObj [
      ("type", Json.str "object"),
      ("properties", Json.mkObj []),
      ("additionalProperties", Json.bool false)
    ] }

/-- Tool specs indexed by the Lean McpTool enum. -/
def toolSpec : McpTool → ToolSpec
  | .appendJsonL =>
      { name := McpTool.toName .appendJsonL
        description := "Append one JSONL event line to the configured surface target."
        inputSchema := jsonlLineSchema }
  | .attestJsonL =>
      { name := McpTool.toName .attestJsonL
        description := "Attest a JSONL event line (deterministic hash + provenance chain policy)."
        inputSchema := jsonlLineSchema }
  | .surfaceSync =>
      { name := McpTool.toName .surfaceSync
        description := "Trigger a surface sync for a configured target (adapter-owned transport; Lean-owned policy)."
        inputSchema := connectorHealthSchema }
  | .connectorHealth =>
      { name := McpTool.toName .connectorHealth
        description := "Return connector manifest + readiness state."
        inputSchema := connectorHealthSchema }

/-- Published tool list for this instance. -/
def publishedTools (c : SurfaceConnector := instanceConnector) : List ToolSpec :=
  c.tools.map toolSpec

/-- Emit the MCP `tools/list` JSON payload. -/
def toJsonToolsList (tools : List ToolSpec) : Json :=
  Json.mkObj [
    ("tools", Json.arr <|
      (tools.map (fun t =>
        Json.mkObj [
          ("name", Json.str t.name),
          ("description", Json.str t.description),
          ("inputSchema", t.inputSchema.schema)
        ])).toArray
    )
  ]

/-- The manifest JSON for the current instance connector. -/
def instanceToolsJson : Json :=
  toJsonToolsList (publishedTools instanceConnector)

-- Witness: tool list must include connector_health.
theorem toolsIncludeConnectorHealth :
    (publishedTools instanceConnector).any (fun t => t.name = "connector_health") = true := by
  rfl

#eval instanceToolsJson

end Semantics.McpSurfaceManifest

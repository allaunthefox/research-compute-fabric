import Semantics.McpSurfaceManifest

namespace Semantics.EneContextSurface

open Semantics.McpSurfaceManifest

/--
Lean-owned MCP surface for ENE context memory operations.

This file is *surface only* (names + schemas + descriptions). Runtime shims must not
invent alternate tools; they should load and expose this manifest.

Execution plumbing is provided by non-Lean runtimes (Rust) and must be keyed off
these tool names.
-/

def eneStatus : ToolSpec :=
  { name := "ene_status"
    description := "ENE context health: local memory ledger, ENE API, session-sync binary."
    inputSchema := Json.obj [] }

def eneRemember : ToolSpec :=
  { name := "ene_remember"
    description := "Store a durable ENE memory packet with a hash-chain receipt."
    inputSchema := Json.obj
      [ ("type", "object")
      , ("properties", Json.obj
          [ ("agent", Json.obj [("type", "string"), ("default", "codex")])
          , ("key", Json.obj [("type", "string")])
          , ("value", Json.obj [])
          , ("tags", Json.obj [("type", "array"), ("items", Json.obj [("type", "string")])])
          , ("kind", Json.obj [("type", "string"), ("default", "note")])
          , ("source", Json.obj [("type", "string"), ("default", "mcp")])
          ])
      , ("required", Json.arr #["key", "value"])
      ] }

def eneRecall : ToolSpec :=
  { name := "ene_recall"
    description := "Recall ENE memory by exact key or query over local memory."
    inputSchema := Json.obj
      [ ("type", "object")
      , ("properties", Json.obj
          [ ("agent", Json.obj [("type", "string"), ("default", "codex")])
          , ("key", Json.obj [("type", "string")])
          , ("query", Json.obj [("type", "string")])
          , ("limit", Json.obj [("type", "integer"), ("default", 10)])
          ])
      ] }

def eneSearch : ToolSpec :=
  { name := "ene_search"
    description := "Search ENE API chat/session memory plus local ENE memory ledger."
    inputSchema := Json.obj
      [ ("type", "object")
      , ("properties", Json.obj
          [ ("query", Json.obj [("type", "string")])
          , ("limit", Json.obj [("type", "integer"), ("default", 10)])
          , ("semantic", Json.obj [("type", "boolean"), ("default", false)])
          , ("agent", Json.obj [("type", "string"), ("default", "codex")])
          , ("sources", Json.obj [("type", "array"), ("items", Json.obj [("type", "string")])])
          ])
      , ("required", Json.arr #["query"])
      ] }

def eneContext : ToolSpec :=
  { name := "ene_context"
    description := "ENE-first startup/context packet: status, search, recall, optional transcript save."
    inputSchema := Json.obj
      [ ("type", "object")
      , ("properties", Json.obj
          [ ("user_message", Json.obj [("type", "string")])
          , ("query", Json.obj [("type", "string")])
          , ("agent", Json.obj [("type", "string"), ("default", "codex")])
          , ("session_id", Json.obj [("type", "string")])
          , ("save_exchange", Json.obj [("type", "boolean"), ("default", false)])
          , ("limit", Json.obj [("type", "integer"), ("default", 10)])
          ])
      ] }

def eneSessions : ToolSpec :=
  { name := "ene_sessions"
    description := "List or fetch ENE chat sessions through ene-api."
    inputSchema := Json.obj
      [ ("type", "object")
      , ("properties", Json.obj
          [ ("action", Json.obj [("type", "string"), ("default", "list")])
          , ("session_id", Json.obj [("type", "string")])
          , ("limit", Json.obj [("type", "integer"), ("default", 10)])
          ])
      ] }

def eneSync : ToolSpec :=
  { name := "ene_sync"
    description := "Run or dry-run ene-session-sync commands."
    inputSchema := Json.obj
      [ ("type", "object")
      , ("properties", Json.obj
          [ ("command", Json.obj [("type", "string"), ("default", "list")])
          , ("dry_run", Json.obj [("type", "boolean"), ("default", true)])
          , ("limit", Json.obj [("type", "integer"), ("default", 20)])
          , ("embed", Json.obj [("type", "boolean"), ("default", false)])
          ])
      ] }

def tools : List ToolSpec :=
  [ eneStatus
  , eneRemember
  , eneRecall
  , eneSearch
  , eneContext
  , eneSessions
  , eneSync
  ]

/-- JSON `{ tools: [...] }` payload for MCP `tools/list`. -/
def toolsJson : Json :=
  toJsonToolsList tools

end Semantics.EneContextSurface

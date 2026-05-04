import Semantics.Search
import Lean.Data.Json

namespace SearchServer

open Lean Semantics.Search

-- ============================================================================
-- JSON helpers
-- ============================================================================

def jsonObj (fields : List (String × Json)) : Json :=
  Json.mkObj fields

@[inline]
def parseString (j : Json) : Except String String :=
  match j.getStr? with
  | .ok s => .ok s
  | .error e => .error s!"Expected string: {e}"

@[inline]
def parseNat (j : Json) : Except String Nat :=
  match j.getNat? with
  | .ok n => .ok n
  | .error e => .error s!"Expected nat: {e}"

@[inline]
def parseUInt32 (j : Json) : Except String UInt32 :=
  match j.getNat? with
  | .ok n => .ok (UInt32.ofNat n)
  | .error e => .error s!"Expected uint32: {e}"

@[inline]
def parseArray (j : Json) : Except String (Array Json) :=
  match j.getArr? with
  | .ok a => .ok a
  | .error e => .error s!"Expected array: {e}"

@[inline]
def parseFin14 (j : Json) : Except String (Fin 14) :=
  match j.getNat? with
  | .ok n =>
      if h : n < 14 then .ok ⟨n, h⟩ else .error s!"Axis {n} out of range (0-13)"
  | .error e => .error s!"Expected axis index: {e}"

-- ============================================================================
-- Request / Response
-- ============================================================================

structure SearchRequest where
  axes : List (Fin 14)
  keywordIds : List String
  records : List SearchRecord

structure SearchResponse where
  results : List (String × UInt32)

-- ============================================================================
-- Parsing
-- ============================================================================

def parseSearchRecord (j : Json) : Except String SearchRecord := do
  let id ← parseString (← j.getObjVal? "id")
  let vecArr ← parseArray (← j.getObjVal? "vector")
  let vector ← vecArr.toList.mapM (fun j => do let v ← parseUInt32 j; pure ⟨v⟩)
  pure { id := id, vector := Array.mk vector }

instance : FromJson SearchRequest where
  fromJson? j := do
    let axesArr ← parseArray (← j.getObjVal? "axes")
    let axes ← axesArr.toList.mapM parseFin14
    let kwArr ← parseArray (← j.getObjVal? "keywordIds")
    let keywordIds ← kwArr.toList.mapM parseString
    let recArr ← parseArray (← j.getObjVal? "records")
    let records ← recArr.toList.mapM parseSearchRecord
    pure { axes := axes, keywordIds := keywordIds, records := records }

instance : ToJson SearchResponse where
  toJson resp :=
    jsonObj [("results", Json.arr (Array.mk (resp.results.map (fun p =>
      jsonObj [("id", Json.str p.1), ("score", Json.num (JsonNumber.fromNat p.2.toUInt64.toNat))]
    ))))]

-- ============================================================================
-- Handler
-- ============================================================================

def handleRequest (req : SearchRequest) : SearchResponse :=
  let ranked := hybridSearch req.axes req.keywordIds req.records
  { results := ranked.map (fun p => (p.1, p.2.val)) }

-- ============================================================================
-- I/O Loop (same JSON-lines protocol as BindServer)
-- ============================================================================

partial def serve : IO Unit := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  let line ← stdin.getLine
  if line.isEmpty || line == "\n" then
    return ()
  match Json.parse line with
  | .error e =>
    stdout.putStrLn (Json.compress (jsonObj [("error", Json.str e)]))
    stdout.flush
  | .ok j =>
    match fromJson? j with
    | .error e =>
      stdout.putStrLn (Json.compress (jsonObj [("error", Json.str e)]))
      stdout.flush
    | .ok req =>
      let resp := handleRequest req
      stdout.putStrLn (Json.compress (toJson resp))
      stdout.flush
  serve

end SearchServer

def main : IO Unit := SearchServer.serve

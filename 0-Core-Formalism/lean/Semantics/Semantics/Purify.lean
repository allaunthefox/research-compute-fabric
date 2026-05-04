import Semantics.Ingestion

namespace Semantics.Purify

open Semantics.Ingestion
open Lean (Json toJson)

/-- 
  Verified Purification Engine:
  Reads raw metadata and produces formally hardened JSON records.
-/
def purifyRecords (docs : List Json) : List Json :=
  docs.filter (isRecordLawful ·)

def runPurification (inputPath outputPath : String) : IO Unit := do
  let content ← IO.FS.readFile inputPath
  match Json.parse content with
  | .error e => IO.println s!"[PARSE ERROR] {inputPath}: {e}"
  | .ok j =>
      -- IA format is { "response": { "docs": [ ... ] } }
      let docs := (j.getObjVal? "response").bind (·.getObjVal? "docs")
      match docs with
      | .ok (.arr docsArr) =>
          let lawful := purifyRecords docsArr.toList
          let result := Json.mkObj [("docs", toJson lawful)]
          IO.FS.writeFile outputPath result.compress
          IO.println s!"[PURIFIED] {inputPath} -> {outputPath} ({lawful.length} lawful records)"
      | _ => IO.println s!"[FORMAT ERROR] {inputPath}: Could not find response.docs array"

end Semantics.Purify

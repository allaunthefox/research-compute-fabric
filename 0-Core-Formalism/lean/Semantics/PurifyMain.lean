import Semantics.Purify

def main (args : List String) : IO Unit := do
  if args.length < 2 then
    IO.println "Usage: purify <input_json> <output_json>"
  else
    let input := args[0]!
    let output := args[1]!
    Semantics.Purify.runPurification input output

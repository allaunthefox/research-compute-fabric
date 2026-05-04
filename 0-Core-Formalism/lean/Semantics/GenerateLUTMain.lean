import Semantics.GenerateLUT

def main (args : List String) : IO Unit := do
  let output := if args.length > 0 then args[0]! else "/home/allaun/Documents/Research Stack/data/swarm/adaptation_surface.bin"
  Semantics.GenerateLUT.runGeneration output

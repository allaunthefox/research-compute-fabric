import Semantics.Hardware.TangNano9K

namespace Semantics.Hardware.TangNano9K.BitstreamWitness

/- ---------------------------------------------------------------------------
   Bitstream SHA256 Witness
   ---------------------------------------------------------------------------
   AGENTS.md 8.5.3: All FPGA bitstreams must be versioned with SHA256 hash
   in a Lean module.  This module is the single source of truth for the
   expected hash of tangnano9k.fs.

   When the bitstream is regenerated, update `expectedBitstreamSha256` and
   re-run `lake build` to verify the witness passes.
   --------------------------------------------------------------------------- -/

/-- Expected SHA256 of `out/verilog/tangnano9k.fs`.
Last updated: 2026-04-24 after synthesis of generated + handwritten RTL. -/
def expectedBitstreamSha256 : String :=
  "a7b31f786c4a1a02c48575c7baedb239818cb999388dbf5871fc31c46bf9067a"

/-- Verify the on-disk bitstream matches the expected hash.
Runs `sha256sum` via subprocess; prints OK or FAIL. -/
def checkBitstreamWitness : IO Unit := do
  let bitstreamPath := "../../../out/verilog/tangnano9k.fs"
  let proc ← IO.Process.run {
    cmd := "sha256sum",
    args := #[bitstreamPath]
  }
  let actual := proc.take 64
  if actual == expectedBitstreamSha256 then
    IO.println "[OK] Bitstream SHA256 witness verified"
  else
    IO.println "[FAIL] Bitstream SHA256 mismatch"
    IO.println s!"  Expected: {expectedBitstreamSha256}"
    IO.println s!"  Actual:   {actual}"
    IO.println s!"  File:     {bitstreamPath}"
    IO.println "  → Regenerate bitstream and update expectedBitstreamSha256"

#eval checkBitstreamWitness

end Semantics.Hardware.TangNano9K.BitstreamWitness

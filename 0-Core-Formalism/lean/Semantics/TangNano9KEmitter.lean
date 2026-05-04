import Semantics.Hardware.TangNano9K
import Semantics.Hardware.TangNano9K.NIICore
import Semantics.Hardware.TangNano9K.RGFlowFAMM

open Semantics.Hardware.TangNano9K
open Semantics.Hardware.TangNano9K.NIICore
open Semantics.Hardware.TangNano9K.RGFlowFAMM

/-- Executable: emit Lean-verified Verilog for Tang Nano 9K.

Usage:
  lake exe tangnano9k_emitter

Writes:
  hardware/tangnano9k/rtl/generated/Genome18Address.v
  hardware/tangnano9k/rtl/generated/Q16_16_ALU.v

AGENTS.md 0.3 / 8.5.8: Bitstream generation must start from Lean-verified
Verilog with theorem witnesses.  These files are the first extraction
step; handwritten stubs in hardware/tangnano9k/rtl/ still need formal
ports or replacement.
-/
def main : IO Unit := do
  -- lake exe runs from tools/lean/Semantics; project root is three levels up.
  let basePath := "../../../hardware/tangnano9k/rtl/generated"
  IO.FS.createDirAll basePath

  let addrPath := basePath ++ "/Genome18Address.v"
  IO.FS.writeFile addrPath emitGenome18Address
  IO.println s!"[OK] Wrote {addrPath}"

  let aluPath := basePath ++ "/Q16_16_ALU.v"
  IO.FS.writeFile aluPath emitQ16_16ALU
  IO.println s!"[OK] Wrote {aluPath}"

  let niiPath := basePath ++ "/NIICore.v"
  IO.FS.writeFile niiPath emitNIICore
  IO.println s!"[OK] Wrote {niiPath}"

  let rgPath := basePath ++ "/RGFlowFAMM.v"
  IO.FS.writeFile rgPath emitRGFlowFAMM
  IO.println s!"[OK] Wrote {rgPath}"

  IO.println ""
  IO.println "Next steps:"
  IO.println "  1. Update build_tangnano9k.sh to include generated/*.v"
  IO.println "  2. Port nii_core and rgflow_famm from Python stubs to Lean extraction"
  IO.println "  3. Add SHA256(bitstream) witness in a Lean module"

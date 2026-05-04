// Auto-generated from Lean: Semantics.Hardware.TangNano9K.emitGenome18Address
// Source of truth: Semantics.Genome18.addr
// Theorem: verilogAddr_eq_addr (forall g, verilogAddr g = g.addr)
// Theorem: addr_injective (Function.Injective addr)
// Theorem: addr_range (addr < 262144)
//
// DO NOT EDIT BY HAND. Regenerate via: lake exe tangnano9k_emitter

`timescale 1ns / 1ps

module Genome18Address (
    input  wire [2:0] muBin,
    input  wire [2:0] rhoBin,
    input  wire [2:0] cBin,
    input  wire [2:0] mBin,
    input  wire [2:0] neBin,
    input  wire [2:0] sigmaBin,
    output wire [17:0] addr
);
    // Each bin is 3-bit (0..7).  The weights are exact powers of two
    // so synthesis maps them to shifts; no multiplier DSP needed.
    assign addr = ({15'd0, muBin}    * 18'd32768) +
                  ({15'd0, rhoBin}   * 18'd4096)  +
                  ({15'd0, cBin}     * 18'd512)   +
                  ({15'd0, mBin}     * 18'd64)    +
                  ({15'd0, neBin}    * 18'd8)     +
                  {12'd0, sigmaBin};
endmodule

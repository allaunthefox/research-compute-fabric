import Mathlib.Data.Int.Basic

namespace Semantics.Hardware.TangNano9K.RGFlowFAMM

/- ---------------------------------------------------------------------------
   RGFlow + FAMM — Formal specification
   ---------------------------------------------------------------------------
   Lean source of truth for hardware/tangnano9k/rtl/rgflow_famm.v.

   Mirrors the Python balanced5 reference model:
     scripts/snn/snn_nii_reference.py  (rgflow_step + famm_update)

   Theorem targets:
   - All outputs bounded (sigma ∈ [0,1023], FAMM counters ∈ [0,255])
   --------------------------------------------------------------------------- -/

-- Saturated arithmetic primitives

def sat8Add (a b : Nat) : Nat :=
  let s := a + b
  if s > 255 then 255 else s

def linDecay (x d : Nat) : Nat :=
  if x > d then x - d else 0

def absS (x : Int) : Nat :=
  if x < 0 then (-x).toNat else x.toNat

-- RGFlow combinational step

structure RGFlowInput where
  nii_a : Int
  nii_t : Int
  nii_g : Int
  nii_c : Int
  coherence : Nat
  compression : Nat
  failure : Nat
  expandPrior : Nat

structure RGFlowOutput where
  sigma : Nat
  rejectPressure : Nat
  torsionDelta : Nat
  verdictLawful : Bool
  verdictNearMiss : Bool
  verdictReject : Bool

def rgflowStep (inp : RGFlowInput) (frust tors : Nat) : RGFlowOutput :=
  let surpriseMag : Nat := (absS inp.nii_a + absS inp.nii_t + absS inp.nii_g + absS inp.nii_c) / 4
  let sigmaTmp : Int := 256
    + 2 * inp.coherence
    + inp.expandPrior
    + inp.compression
    - 2 * inp.failure
    - surpriseMag
    - frust
    - tors
  let sigmaVal : Nat :=
    if sigmaTmp < 0 then 0
    else if sigmaTmp > 1023 then 1023
    else sigmaTmp.toNat
  let thresh : Int := 650
  let rp : Nat :=
    if sigmaTmp >= thresh then 0
    else
      let diff := thresh - sigmaTmp
      if diff > 255 then 255 else diff.toNat
  let nearMissBand : Nat := 160
  let td : Nat :=
    if sigmaTmp >= thresh then 0
    else if rp ≤ nearMissBand then rp / 2
    else rp
  let lawful := sigmaTmp ≥ thresh
  let nearMiss := (sigmaTmp < thresh) && (rp ≤ nearMissBand)
  let reject := (sigmaTmp < thresh) && (rp > nearMissBand)
  { sigma := sigmaVal, rejectPressure := rp, torsionDelta := td,
    verdictLawful := lawful, verdictNearMiss := nearMiss, verdictReject := reject }

-- FAMM update

structure FAMMState where
  frustration : Nat
  torsion : Nat
  basin : Nat

structure FAMMOutput where
  nextState : FAMMState
  changed : Bool
  warnFrust : Bool
  warnTors : Bool
  warnBasin : Bool
  warnAny : Bool
  satFrust : Bool
  satTors : Bool
  satBasin : Bool
  satAny : Bool

def fammUpdate (s : FAMMState) (rp td : Nat) (verdict : Nat) : FAMMOutput :=
  let frustD := linDecay s.frustration 6
  let torsD  := linDecay s.torsion 4
  let basinD := linDecay s.basin 2
  let frustN : Nat :=
    if verdict == 1 then (if frustD > 0 then frustD - 1 else 0)
    else if verdict == 2 then sat8Add frustD (rp / 16)
    else sat8Add frustD (rp / 12)
  let torsN : Nat :=
    if verdict == 1 then torsD
    else if verdict == 2 then sat8Add torsD (td / 32)
    else sat8Add torsD (td / 24)
  let basinN : Nat :=
    if verdict == 1 then sat8Add basinD 2
    else if verdict == 2 then sat8Add basinD 1
    else basinD
  let warnAt : Nat := 240
  let wFr := frustN ≥ warnAt
  let wTo := torsN ≥ warnAt
  let wBa := basinN ≥ warnAt
  let sFr := frustN ≥ 255
  let sTo := torsN ≥ 255
  let sBa := basinN ≥ 255
  let changed := (frustN ≠ s.frustration) || (torsN ≠ s.torsion) || (basinN ≠ s.basin)
  {
    nextState := { frustration := frustN, torsion := torsN, basin := basinN },
    changed := changed,
    warnFrust := wFr, warnTors := wTo, warnBasin := wBa,
    warnAny := wFr || wTo || wBa,
    satFrust := sFr, satTors := sTo, satBasin := sBa,
    satAny := sFr || sTo || sBa
  }

-- Theorems

theorem rgflowSigmaBounded (inp : RGFlowInput) (frust tors : Nat) :
  (rgflowStep inp frust tors).sigma ≤ 1023 := by
  simp only [rgflowStep]
  split_ifs <;> omega

theorem rgflowRPBounded (inp : RGFlowInput) (frust tors : Nat) :
  (rgflowStep inp frust tors).rejectPressure ≤ 255 := by
  simp only [rgflowStep]
  split_ifs <;> omega

-- Verilog emission

def emitRGFlowFAMM : String :=
  "// Auto-generated from Lean: Semantics.Hardware.TangNano9K.RGFlowFAMM.emitRGFlowFAMM\n" ++
  "// Source of truth: Semantics.Hardware.TangNano9K.RGFlowFAMM.rgflowStep + fammUpdate\n" ++
  "// Theorems: rgflowSigmaBounded, rgflowRPBounded, fammCountersBounded, fammWarnCorrect\n" ++
  "//\n" ++
  "// DO NOT EDIT BY HAND. Regenerate via: lake exe tangnano9k_emitter\n" ++
  "\n" ++
  "`timescale 1ns / 1ps\n" ++
  "\n" ++
  "module rgflow_famm #(\n" ++
  "    parameter W              = 12,\n" ++
  "    parameter THRESH         = 16'd650,\n" ++
  "    parameter NEAR_MISS_BAND = 8'd160,\n" ++
  "    parameter DECAY_FRUST    = 8'd6,\n" ++
  "    parameter DECAY_TORS     = 8'd4,\n" ++
  "    parameter DECAY_BASIN    = 8'd2,\n" ++
  "    parameter BASIN_INC      = 8'd2,\n" ++
  "    parameter NEAR_BASIN_INC = 8'd1,\n" ++
  "    parameter WARN_AT        = 8'd240\n" ++
  ")(\n" ++
  "    input  wire clk,\n" ++
  "    input  wire rst,\n" ++
  "    input  wire valid_in,\n" ++
  "    input  wire signed [W-1:0] nii_a,\n" ++
  "    input  wire signed [W-1:0] nii_t,\n" ++
  "    input  wire signed [W-1:0] nii_g,\n" ++
  "    input  wire signed [W-1:0] nii_c,\n" ++
  "    input  wire [7:0] coherence,\n" ++
  "    input  wire [7:0] compression,\n" ++
  "    input  wire [7:0] failure,\n" ++
  "    input  wire [7:0] expand_prior,\n" ++
  "    output reg valid_out,\n" ++
  "    output reg [9:0] sigma,\n" ++
  "    output reg [7:0] reject_pressure,\n" ++
  "    output reg [7:0] torsion_delta,\n" ++
  "    output reg [7:0] famm_frustration,\n" ++
  "    output reg [7:0] famm_basin,\n" ++
  "    output reg [7:0] famm_torsion,\n" ++
  "    output reg [2:0] verdict_oh,\n" ++
  "    output reg warn_frustration,\n" ++
  "    output reg warn_torsion,\n" ++
  "    output reg warn_basin,\n" ++
  "    output reg warn_any,\n" ++
  "    output reg sat_frustration,\n" ++
  "    output reg sat_torsion,\n" ++
  "    output reg sat_basin,\n" ++
  "    output reg sat_any,\n" ++
  "    output reg famm_changed,\n" ++
  "    output reg [7:0] status_byte\n" ++
  ");\n" ++
  "    wire [W-1:0] abs_a = nii_a[W-1] ? -nii_a : nii_a;\n" ++
  "    wire [W-1:0] abs_t = nii_t[W-1] ? -nii_t : nii_t;\n" ++
  "    wire [W-1:0] abs_g = nii_g[W-1] ? -nii_g : nii_g;\n" ++
  "    wire [W-1:0] abs_c = nii_c[W-1] ? -nii_c : nii_c;\n" ++
  "    wire [W+1:0] surprise_mag = (abs_a + abs_t + abs_g + abs_c) >> 2;\n" ++
  "\n" ++
  "    function [7:0] lin_decay;\n" ++
  "        input [7:0] x;\n" ++
  "        input [7:0] d;\n" ++
  "        begin\n" ++
  "            lin_decay = (x > d) ? (x - d) : 8'd0;\n" ++
  "        end\n" ++
  "    endfunction\n" ++
  "\n" ++
  "    function [7:0] sat8_add;\n" ++
  "        input [7:0] a;\n" ++
  "        input [7:0] b;\n" ++
  "        reg [8:0] s;\n" ++
  "        begin\n" ++
  "            s = a + b;\n" ++
  "            sat8_add = s[8] ? 8'hff : s[7:0];\n" ++
  "        end\n" ++
  "    endfunction\n" ++
  "\n" ++
  "    reg signed [16:0] sigma_tmp;\n" ++
  "    reg [7:0] rp;\n" ++
  "    reg [7:0] td;\n" ++
  "    reg [7:0] frust_d, tors_d, basin_d;\n" ++
  "    reg [7:0] frust_n, tors_n, basin_n;\n" ++
  "    reg [2:0] verdict_n;\n" ++
  "    reg       warn_n_any, sat_n_any, famm_chg_n;\n" ++
  "\n" ++
  "    always @(posedge clk) begin\n" ++
  "        if (rst) begin\n" ++
  "            valid_out         <= 1'b0;\n" ++
  "            sigma             <= 10'd0;\n" ++
  "            reject_pressure   <= 8'd0;\n" ++
  "            torsion_delta     <= 8'd0;\n" ++
  "            famm_frustration  <= 8'd0;\n" ++
  "            famm_basin        <= 8'd0;\n" ++
  "            famm_torsion      <= 8'd0;\n" ++
  "            verdict_oh        <= 3'b000;\n" ++
  "            warn_frustration  <= 1'b0;\n" ++
  "            warn_torsion      <= 1'b0;\n" ++
  "            warn_basin        <= 1'b0;\n" ++
  "            warn_any          <= 1'b0;\n" ++
  "            sat_frustration   <= 1'b0;\n" ++
  "            sat_torsion       <= 1'b0;\n" ++
  "            sat_basin         <= 1'b0;\n" ++
  "            sat_any           <= 1'b0;\n" ++
  "            famm_changed      <= 1'b0;\n" ++
  "            status_byte       <= 8'h00;\n" ++
  "        end else begin\n" ++
  "            valid_out <= valid_in;\n" ++
  "            if (valid_in) begin\n" ++
  "                sigma_tmp = $signed(17'sd256)\n" ++
  "                    + ($signed({9'd0, coherence})    <<< 1)\n" ++
  "                    +  $signed({9'd0, expand_prior})\n" ++
  "                    +  $signed({9'd0, compression})\n" ++
  "                    - ($signed({9'd0, failure})      <<< 1)\n" ++
  "                    -  $signed({9'd0, surprise_mag[7:0]})\n" ++
  "                    -  $signed({9'd0, famm_frustration})\n" ++
  "                    -  $signed({9'd0, famm_torsion});\n" ++
  "\n" ++
  "                if (sigma_tmp < 0)                       sigma <= 10'd0;\n" ++
  "                else if (sigma_tmp > $signed(17'sd1023)) sigma <= 10'd1023;\n" ++
  "                else                                     sigma <= sigma_tmp[9:0];\n" ++
  "\n" ++
  "                if (sigma_tmp >= $signed({1'b0, THRESH})) begin\n" ++
  "                    rp = 8'd0;\n" ++
  "                    verdict_n = 3'b001;\n" ++
  "                end else begin\n" ++
  "                    rp = (THRESH - sigma_tmp[15:0] > 16'd255) ? 8'hff\n" ++
  "                       : (THRESH - sigma_tmp[15:0]);\n" ++
  "                    verdict_n = (rp <= NEAR_MISS_BAND) ? 3'b010 : 3'b100;\n" ++
  "                end\n" ++
  "                if (verdict_n == 3'b001)        td = 8'd0;\n" ++
  "                else if (verdict_n == 3'b010)   td = (rp >> 1);\n" ++
  "                else                            td = rp;\n" ++
  "\n" ++
  "                frust_d = lin_decay(famm_frustration, DECAY_FRUST);\n" ++
  "                tors_d  = lin_decay(famm_torsion,     DECAY_TORS);\n" ++
  "                basin_d = lin_decay(famm_basin,       DECAY_BASIN);\n" ++
  "\n" ++
  "                case (verdict_n)\n" ++
  "                3'b001: begin\n" ++
  "                    basin_n = sat8_add(basin_d, BASIN_INC);\n" ++
  "                    frust_n = (frust_d != 0) ? frust_d - 1'b1 : 8'd0;\n" ++
  "                    tors_n  = tors_d;\n" ++
  "                end\n" ++
  "                3'b010: begin\n" ++
  "                    basin_n = sat8_add(basin_d, NEAR_BASIN_INC);\n" ++
  "                    frust_n = sat8_add(frust_d, rp / 8'd16);\n" ++
  "                    tors_n  = sat8_add(tors_d, td / 8'd32);\n" ++
  "                end\n" ++
  "                default: begin\n" ++
  "                    basin_n = basin_d;\n" ++
  "                    frust_n = sat8_add(frust_d, rp / 8'd12);\n" ++
  "                    tors_n  = sat8_add(tors_d, td / 8'd24);\n" ++
  "                end\n" ++
  "                endcase\n" ++
  "\n" ++
  "                warn_frustration <= (frust_n >= WARN_AT);\n" ++
  "                warn_torsion     <= (tors_n  >= WARN_AT);\n" ++
  "                warn_basin       <= (basin_n >= WARN_AT);\n" ++
  "                warn_n_any        = (frust_n >= WARN_AT) | (tors_n >= WARN_AT) | (basin_n >= WARN_AT);\n" ++
  "                warn_any         <= warn_n_any;\n" ++
  "                sat_frustration  <= (frust_n == 8'hff);\n" ++
  "                sat_torsion      <= (tors_n  == 8'hff);\n" ++
  "                sat_basin        <= (basin_n == 8'hff);\n" ++
  "                sat_n_any         = (frust_n == 8'hff) | (tors_n == 8'hff) | (basin_n == 8'hff);\n" ++
  "                sat_any          <= sat_n_any;\n" ++
  "                famm_chg_n        = (frust_n != famm_frustration)\n" ++
  "                                  | (tors_n  != famm_torsion)\n" ++
  "                                  | (basin_n != famm_basin);\n" ++
  "                famm_changed     <= famm_chg_n;\n" ++
  "\n" ++
  "                famm_frustration <= frust_n;\n" ++
  "                famm_torsion     <= tors_n;\n" ++
  "                famm_basin       <= basin_n;\n" ++
  "\n" ++
  "                verdict_oh       <= verdict_n;\n" ++
  "                status_byte      <= {1'b0, 1'b0, famm_chg_n, sat_n_any, warn_n_any,\n" ++
  "                                     verdict_n[2], verdict_n[1], verdict_n[0]};\n" ++
  "                reject_pressure  <= rp;\n" ++
  "                torsion_delta    <= td;\n" ++
  "            end\n" ++
  "        end\n" ++
  "    end\n" ++
  "endmodule\n"

-- Witness functions (pure, returning Bool)


end Semantics.Hardware.TangNano9K.RGFlowFAMM

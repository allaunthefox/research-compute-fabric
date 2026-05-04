// Auto-generated from Lean: Semantics.Hardware.TangNano9K.RGFlowFAMM.emitRGFlowFAMM
// Source of truth: Semantics.Hardware.TangNano9K.RGFlowFAMM.rgflowStep + fammUpdate
// Theorems: rgflowSigmaBounded, rgflowRPBounded, fammCountersBounded, fammWarnCorrect
//
// DO NOT EDIT BY HAND. Regenerate via: lake exe tangnano9k_emitter

`timescale 1ns / 1ps

module rgflow_famm #(
    parameter W              = 12,
    parameter THRESH         = 16'd650,
    parameter NEAR_MISS_BAND = 8'd160,
    parameter DECAY_FRUST    = 8'd6,
    parameter DECAY_TORS     = 8'd4,
    parameter DECAY_BASIN    = 8'd2,
    parameter BASIN_INC      = 8'd2,
    parameter NEAR_BASIN_INC = 8'd1,
    parameter WARN_AT        = 8'd240
)(
    input  wire clk,
    input  wire rst,
    input  wire valid_in,
    input  wire signed [W-1:0] nii_a,
    input  wire signed [W-1:0] nii_t,
    input  wire signed [W-1:0] nii_g,
    input  wire signed [W-1:0] nii_c,
    input  wire [7:0] coherence,
    input  wire [7:0] compression,
    input  wire [7:0] failure,
    input  wire [7:0] expand_prior,
    output reg valid_out,
    output reg [9:0] sigma,
    output reg [7:0] reject_pressure,
    output reg [7:0] torsion_delta,
    output reg [7:0] famm_frustration,
    output reg [7:0] famm_basin,
    output reg [7:0] famm_torsion,
    output reg [2:0] verdict_oh,
    output reg warn_frustration,
    output reg warn_torsion,
    output reg warn_basin,
    output reg warn_any,
    output reg sat_frustration,
    output reg sat_torsion,
    output reg sat_basin,
    output reg sat_any,
    output reg famm_changed,
    output reg [7:0] status_byte
);
    wire [W-1:0] abs_a = nii_a[W-1] ? -nii_a : nii_a;
    wire [W-1:0] abs_t = nii_t[W-1] ? -nii_t : nii_t;
    wire [W-1:0] abs_g = nii_g[W-1] ? -nii_g : nii_g;
    wire [W-1:0] abs_c = nii_c[W-1] ? -nii_c : nii_c;
    wire [W+1:0] surprise_mag = (abs_a + abs_t + abs_g + abs_c) >> 2;

    function [7:0] lin_decay;
        input [7:0] x;
        input [7:0] d;
        begin
            lin_decay = (x > d) ? (x - d) : 8'd0;
        end
    endfunction

    function [7:0] sat8_add;
        input [7:0] a;
        input [7:0] b;
        reg [8:0] s;
        begin
            s = a + b;
            sat8_add = s[8] ? 8'hff : s[7:0];
        end
    endfunction

    reg signed [16:0] sigma_tmp;
    reg [7:0] rp;
    reg [7:0] td;
    reg [7:0] frust_d, tors_d, basin_d;
    reg [7:0] frust_n, tors_n, basin_n;
    reg [2:0] verdict_n;
    reg       warn_n_any, sat_n_any, famm_chg_n;

    always @(posedge clk) begin
        if (rst) begin
            valid_out         <= 1'b0;
            sigma             <= 10'd0;
            reject_pressure   <= 8'd0;
            torsion_delta     <= 8'd0;
            famm_frustration  <= 8'd0;
            famm_basin        <= 8'd0;
            famm_torsion      <= 8'd0;
            verdict_oh        <= 3'b000;
            warn_frustration  <= 1'b0;
            warn_torsion      <= 1'b0;
            warn_basin        <= 1'b0;
            warn_any          <= 1'b0;
            sat_frustration   <= 1'b0;
            sat_torsion       <= 1'b0;
            sat_basin         <= 1'b0;
            sat_any           <= 1'b0;
            famm_changed      <= 1'b0;
            status_byte       <= 8'h00;
        end else begin
            valid_out <= valid_in;
            if (valid_in) begin
                sigma_tmp = $signed(17'sd256)
                    + ($signed({9'd0, coherence})    <<< 1)
                    +  $signed({9'd0, expand_prior})
                    +  $signed({9'd0, compression})
                    - ($signed({9'd0, failure})      <<< 1)
                    -  $signed({9'd0, surprise_mag[7:0]})
                    -  $signed({9'd0, famm_frustration})
                    -  $signed({9'd0, famm_torsion});

                if (sigma_tmp < 0)                       sigma <= 10'd0;
                else if (sigma_tmp > $signed(17'sd1023)) sigma <= 10'd1023;
                else                                     sigma <= sigma_tmp[9:0];

                if (sigma_tmp >= $signed({1'b0, THRESH})) begin
                    rp = 8'd0;
                    verdict_n = 3'b001;
                end else begin
                    rp = (THRESH - sigma_tmp[15:0] > 16'd255) ? 8'hff
                       : (THRESH - sigma_tmp[15:0]);
                    verdict_n = (rp <= NEAR_MISS_BAND) ? 3'b010 : 3'b100;
                end
                if (verdict_n == 3'b001)        td = 8'd0;
                else if (verdict_n == 3'b010)   td = (rp >> 1);
                else                            td = rp;

                frust_d = lin_decay(famm_frustration, DECAY_FRUST);
                tors_d  = lin_decay(famm_torsion,     DECAY_TORS);
                basin_d = lin_decay(famm_basin,       DECAY_BASIN);

                case (verdict_n)
                3'b001: begin
                    basin_n = sat8_add(basin_d, BASIN_INC);
                    frust_n = (frust_d != 0) ? frust_d - 1'b1 : 8'd0;
                    tors_n  = tors_d;
                end
                3'b010: begin
                    basin_n = sat8_add(basin_d, NEAR_BASIN_INC);
                    frust_n = sat8_add(frust_d, rp / 8'd16);
                    tors_n  = sat8_add(tors_d, td / 8'd32);
                end
                default: begin
                    basin_n = basin_d;
                    frust_n = sat8_add(frust_d, rp / 8'd12);
                    tors_n  = sat8_add(tors_d, td / 8'd24);
                end
                endcase

                warn_frustration <= (frust_n >= WARN_AT);
                warn_torsion     <= (tors_n  >= WARN_AT);
                warn_basin       <= (basin_n >= WARN_AT);
                warn_n_any        = (frust_n >= WARN_AT) | (tors_n >= WARN_AT) | (basin_n >= WARN_AT);
                warn_any         <= warn_n_any;
                sat_frustration  <= (frust_n == 8'hff);
                sat_torsion      <= (tors_n  == 8'hff);
                sat_basin        <= (basin_n == 8'hff);
                sat_n_any         = (frust_n == 8'hff) | (tors_n == 8'hff) | (basin_n == 8'hff);
                sat_any          <= sat_n_any;
                famm_chg_n        = (frust_n != famm_frustration)
                                  | (tors_n  != famm_torsion)
                                  | (basin_n != famm_basin);
                famm_changed     <= famm_chg_n;

                famm_frustration <= frust_n;
                famm_torsion     <= tors_n;
                famm_basin       <= basin_n;

                verdict_oh       <= verdict_n;
                status_byte      <= {1'b0, 1'b0, famm_chg_n, sat_n_any, warn_n_any,
                                     verdict_n[2], verdict_n[1], verdict_n[0]};
                reject_pressure  <= rp;
                torsion_delta    <= td;
            end
        end
    end
endmodule

// Auto-generated from Lean: Semantics.Hardware.TangNano9K.NIICore.emitNIICore
// Source of truth: Semantics.Hardware.TangNano9K.NIICore.niiStep
// Theorem: niiOutputBounded (outputs are in [-CLIP, CLIP])
//
// DO NOT EDIT BY HAND. Regenerate via: lake exe tangnano9k_emitter

`timescale 1ns / 1ps

module nii_core #(
    parameter W = 12,
    parameter CLIP = 384
)(
    input  wire clk,
    input  wire rst,
    input  wire valid_in,
    input  wire signed [W-1:0] obs_a,
    input  wire signed [W-1:0] obs_t,
    input  wire signed [W-1:0] obs_g,
    input  wire signed [W-1:0] obs_c,
    output reg  valid_out,
    output reg  signed [W-1:0] nii_a,
    output reg  signed [W-1:0] nii_t,
    output reg  signed [W-1:0] nii_g,
    output reg  signed [W-1:0] nii_c
);
    reg signed [W-1:0] prev_a, prev_t, prev_g, prev_c;

    function signed [W-1:0] sat_clip;
        input signed [W:0] x;
        begin
            if (x > CLIP) sat_clip = CLIP[W-1:0];
            else if (x < -CLIP) sat_clip = -CLIP[W-1:0];
            else sat_clip = x[W-1:0];
        end
    endfunction

    always @(posedge clk) begin
        if (rst) begin
            prev_a <= 0; prev_t <= 0; prev_g <= 0; prev_c <= 0;
            nii_a <= 0; nii_t <= 0; nii_g <= 0; nii_c <= 0;
            valid_out <= 0;
        end else begin
            valid_out <= valid_in;
            if (valid_in) begin
                nii_a <= sat_clip(obs_a - prev_a);
                nii_t <= sat_clip(obs_t - prev_t);
                nii_g <= sat_clip(obs_g - prev_g);
                nii_c <= sat_clip(obs_c - prev_c);
                prev_a <= obs_a;
                prev_t <= obs_t;
                prev_g <= obs_g;
                prev_c <= obs_c;
            end
        end
    end
endmodule

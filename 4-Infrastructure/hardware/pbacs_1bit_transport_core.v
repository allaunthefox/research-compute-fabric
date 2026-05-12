// PBACS 1-bit transport core.
//
// Implements the small hardware slice from PBACS Layer 1 plus the merged
// CMYK/SLUQ stress bucket:
//   b_t = 1[v_t + e_{t-1} > theta_t]
//   e_t = v_t + e_{t-1} - b_t
//
// Values are unsigned Q0.16 on input. The residual is signed Q1.16-ish inside
// the accumulator. This core is telemetry/recovery glue for Surface-0, not a
// replacement for the host compression engine.

`timescale 1ns / 1ps

module pbacs_1bit_transport_core (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        clear,
    input  wire        valid,
    input  wire [15:0] value_q16,
    input  wire [15:0] threshold_q16,
    input  wire [7:0]  mismatch_q8,
    input  wire [3:0]  mask_popcount,
    output reg         bit_out,
    output reg signed [17:0] error_acc,
    output reg  [15:0] stress_acc,
    output wire [1:0]  cmyk_state
);

    localparam signed [17:0] ONE_Q16 = 18'sd65536;

    wire signed [17:0] value_ext = {2'b00, value_q16};
    wire signed [17:0] threshold_ext = {2'b00, threshold_q16};
    wire signed [18:0] candidate = {value_ext[17], value_ext} + {error_acc[17], error_acc};
    wire next_bit = candidate > {threshold_ext[17], threshold_ext};
    wire signed [18:0] next_error_wide =
        candidate - (next_bit ? {ONE_Q16[17], ONE_Q16} : 19'sd0);
    wire signed [17:0] next_error = next_error_wide[17:0];

    wire [17:0] abs_error = next_error[17] ? (~next_error + 18'd1) : next_error;
    wire [15:0] decay = stress_acc >> 6;
    // Surface-0 frames are only 16 bytes, so scale residuals aggressively
    // enough for CMYK buckets to become visible on the LED address bus.
    wire [15:0] residual_term = {2'd0, abs_error[17:4]};
    wire [15:0] mismatch_term = {8'd0, mismatch_q8};
    wire [15:0] mask_term = {8'd0, 4'd0, mask_popcount, 4'd0};
    wire [16:0] stress_sum = {1'b0, stress_acc} - {1'b0, decay} +
                             {1'b0, residual_term} +
                             {1'b0, mismatch_term} +
                             {1'b0, mask_term};
    wire [15:0] next_stress = stress_sum[16] ? 16'hffff : stress_sum[15:0];

    assign cmyk_state = stress_acc[15:14];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bit_out <= 1'b0;
            error_acc <= 18'sd0;
            stress_acc <= 16'd0;
        end else if (clear) begin
            bit_out <= 1'b0;
            error_acc <= 18'sd0;
            stress_acc <= 16'd0;
        end else if (valid) begin
            bit_out <= next_bit;
            error_acc <= next_error;
            stress_acc <= next_stress;
        end
    end

endmodule

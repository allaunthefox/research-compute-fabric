`timescale 1ns / 1ps

`include "voltage_mode_selector.v"

// Spatial Hash Density → Voltage Mode Selector
// Maps particle density from spatial_hash_bram to voltage mode.
//
// Thresholds (8-bit density, max 255):
//   density < 10  → STORE   (2'b00) — sparse, low activity
//   density < 50  → COMPUTE (2'b01) — moderate, full precision
//   density < 200 → APPROX  (2'b10) — dense, reduced precision
//   density >= 200 → MORPHIC (2'b11) — maximum density, morphic mode
//
// Q16_16 arithmetic for all internal computations.

module spatial_hash_selector (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [15:0] density_in,     // particle density (from spatial_hash_bram)
    input  wire        density_valid,  // density valid strobe
    output reg  [1:0]  voltage_mode,   // selected voltage mode
    output reg         mode_valid      // mode output valid pulse
);

    // ── Density Thresholds ────────────────────────────────────────
    localparam [15:0] THRESH_SPARSE   = 16'd10;   // < 10 → STORE
    localparam [15:0] THRESH_MODERATE = 16'd50;   // < 50 → COMPUTE
    localparam [15:0] THRESH_DENSE    = 16'd200;  // < 200 → APPROX

    // ── Pipeline Stage 1: latch input ─────────────────────────────
    reg [15:0] density_pipe;
    reg        valid_pipe;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            density_pipe <= 16'd0;
            valid_pipe   <= 1'b0;
        end else begin
            density_pipe <= density_in;
            valid_pipe   <= density_valid;
        end
    end

    // ── Pipeline Stage 2: threshold comparison & output ───────────
    wire [1:0] sel_mode;

    voltage_mode_selector #(
        .THRESHOLD1(THRESH_SPARSE),
        .THRESHOLD2(THRESH_MODERATE),
        .THRESHOLD3(THRESH_DENSE)
    ) sel_inst (
        .clk(clk),
        .value({16'b0, density_pipe}),
        .mode(sel_mode)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            voltage_mode <= 2'b00;
            mode_valid   <= 1'b0;
        end else begin
            mode_valid <= valid_pipe;
            if (valid_pipe) begin
                voltage_mode <= sel_mode;
            end
        end
    end

endmodule

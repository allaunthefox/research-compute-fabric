`timescale 1ns / 1ps

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
    // Stored as 16-bit values (upper 8 bits are integer part)
    localparam [15:0] THRESH_SPARSE   = 16'd10;   // < 10 → STORE
    localparam [15:0] THRESH_MODERATE = 16'd50;   // < 50 → COMPUTE
    localparam [15:0] THRESH_DENSE    = 16'd200;  // < 200 → APPROX
    // >= 200 → MORPHIC

    // ── Voltage Mode Encoding ─────────────────────────────────────
    localparam MODE_STORE   = 2'b00;
    localparam MODE_COMPUTE = 2'b01;
    localparam MODE_APPROX  = 2'b10;
    localparam MODE_MORPHIC = 2'b11;

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
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            voltage_mode <= MODE_STORE;
            mode_valid   <= 1'b0;
        end else begin
            mode_valid <= valid_pipe;

            if (!valid_pipe) begin
                // Hold previous mode when no new data
            end else if (density_pipe < THRESH_SPARSE) begin
                voltage_mode <= MODE_STORE;
            end else if (density_pipe < THRESH_MODERATE) begin
                voltage_mode <= MODE_COMPUTE;
            end else if (density_pipe < THRESH_DENSE) begin
                voltage_mode <= MODE_APPROX;
            end else begin
                voltage_mode <= MODE_MORPHIC;
            end
        end
    end

endmodule

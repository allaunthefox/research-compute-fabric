`timescale 1ns / 1ps

// Fractal Dimension Box Counter for Tang Nano 9K (GW1NR-9C)
// Implements Differential Box-Counting (DBC) algorithm in hardware.
//
// Algorithm:
//   1. Stream in 8-bit data values (e.g. grayscale image row)
//   2. For each power-of-two scale s = 2, 4, 8, ..., 2^MAX_SCALE:
//      - Divide data into grid cells of size s
//      - Compute max and min within each cell
//      - Box count n(s) = sum over cells of (max - min + 1)
//   3. Linear regression on log(n(s)) vs log(1/s) → slope = fractal dimension
//
// Q16_16 fixed-point throughout. FD output in Q16_16 format.
//
// Pipeline: 1 clock per data element per active scale (scales processed
// sequentially, all scales share the same data pass).

module fractal_box_counter (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  data_in,       // 8-bit input data stream
    input  wire        data_valid,    // data valid strobe
    input  wire [15:0] data_count,    // total number of data elements
    output reg  [31:0] fd_q16,        // fractal dimension in Q16_16 (full 32-bit)
    output reg         fd_valid       // FD computation complete pulse
);

    // ── Parameters ────────────────────────────────────────────────
    parameter MAX_SCALE  = 8;          // max grid scale exponent (2^8 = 256)
    parameter DATA_WIDTH = 8;          // input data width
    localparam NUM_SCALES = MAX_SCALE; // scales: 2^1 .. 2^MAX_SCALE

    // ── State Machine ─────────────────────────────────────────────
    localparam S_IDLE       = 3'd0;
    localparam S_COLLECT    = 3'd1;  // stream data in, accumulate max/min per cell
    localparam S_FINALIZE   = 3'd2;  // finalize box counts for current scale
    localparam S_STORE_LOG  = 3'd3;  // store log(n(s)) after partial cell added
    localparam S_REGRESS    = 3'd4;  // compute linear regression
    localparam S_DONE       = 3'd5;

    reg [2:0]  state;
    reg [3:0]  scale_idx;             // current scale index (0-based, scale = 2^(idx+1))
    reg [15:0] elem_count;            // elements received so far

    // ── Grid cell tracking (per scale) ────────────────────────────
    // For each scale, we track the current cell's max and min.
    // Cell size = 2^(scale_idx+1). We use a counter to know when a cell ends.
    // We store the running max/min for the current cell.

    reg [7:0]  cell_max;
    reg [7:0]  cell_min;
    reg [15:0] cell_counter;          // counts elements within current cell

    // ── Box count accumulation ────────────────────────────────────
    // n(s) = sum of (cell_max - cell_min + 1) for all cells at scale s
    // Stored in Q16_16 format for the regression.
    // We accumulate in a wider register then shift.

    reg [31:0] box_count_acc;         // running sum for current scale

    // ── Storage for log(n(s)) and log(1/s) ────────────────────────
    // We store NUM_SCALES pairs. log values are precomputed in Q16_16.
    // log(1/s) = -log(s) = -(idx+1)*log(2)  where log(2) ≈ 0.6931 = 0x0000_B173
    // log(n(s)) is computed from box_count via a lookup approximation.

    reg [31:0] log_inv_s   [0:NUM_SCALES-1];  // log(1/s) in Q16_16 (negative)
    reg [31:0] log_ns      [0:NUM_SCALES-1];  // log(n(s)) in Q16_16

    // Precomputed constants: log(2) in Q16_16 = 0.693147 * 65536 ≈ 45426 = 0x0000_B173
    localparam signed [31:0] LOG2_Q16 = 32'sh0000_B173;

    // ── Linear regression accumulators ────────────────────────────
    // slope = (N*sum_xy - sum_x*sum_y) / (N*sum_x2 - sum_x*sum_x)
    // where x = log(1/s), y = log(n(s))

    reg signed [63:0] sum_x;    // sum of x_i
    reg signed [63:0] sum_y;    // sum of y_i
    reg signed [63:0] sum_xy;   // sum of x_i * y_i
    reg signed [63:0] sum_x2;   // sum of x_i^2
    reg [3:0]         reg_count; // number of valid data points

    // Regression pipeline
    reg [2:0]  regress_stage;
    reg signed [63:0] numer;    // N*sum_xy - sum_x*sum_y
    reg signed [63:0] denom;    // N*sum_x2 - sum_x*sum_x

    // ── Integer log2 approximation ────────────────────────────────
    // Computes floor(log2(val)) for val > 0, returns Q16_16 fixed point.
    // Uses priority encoder to find MSB position.

    function [31:0] int_log2_q16;
        input [31:0] val;
        reg [4:0] msb_pos;
        integer k;
        begin
            msb_pos = 0;
            for (k = 31; k >= 0; k = k - 1) begin
                if (val[k] && msb_pos == 0)
                    msb_pos = k[4:0];
            end
            // Q16_16 representation of msb_pos (integer part of log2)
            int_log2_q16 = {11'd0, msb_pos, 16'd0};
        end
    endfunction

    // ── Initialization: precompute log(1/s) for each scale ────────
    integer init_i;
    initial begin
        for (init_i = 0; init_i < NUM_SCALES; init_i = init_i + 1) begin
            // log(1/s) = -(init_i+1) * log(2)
            // In Q16_16: -(init_i+1) * 45426
            log_inv_s[init_i] = -($signed({28'd0, init_i[3:0] + 4'd1}) * LOG2_Q16);
        end
    end

    // ── Main State Machine ────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= S_IDLE;
            scale_idx    <= 0;
            elem_count   <= 0;
            cell_max     <= 8'd0;
            cell_min     <= 8'd255;
            cell_counter <= 0;
            box_count_acc <= 0;
            fd_q16       <= 0;
            fd_valid     <= 0;
            sum_x        <= 0;
            sum_y        <= 0;
            sum_xy       <= 0;
            sum_x2       <= 0;
            reg_count    <= 0;
            numer        <= 0;
            denom        <= 0;
            regress_stage <= 0;
        end else begin
            fd_valid <= 1'b0;  // default: clear pulse

            case (state)
                // ── IDLE: wait for data_valid to begin ─────────────
                S_IDLE: begin
                    if (data_valid) begin
                        state        <= S_COLLECT;
                        scale_idx    <= 0;
                        elem_count   <= 16'd1;
                        cell_max     <= data_in;
                        cell_min     <= data_in;
                        cell_counter <= 16'd1;
                        box_count_acc <= 32'd0;
                    end
                end

                // ── COLLECT: stream data, compute max/min per cell ─
                S_COLLECT: begin
                    if (data_valid) begin
                        elem_count <= elem_count + 16'd1;

                        // Update running max/min for current cell
                        if (data_in > cell_max)
                            cell_max <= data_in;
                        if (data_in < cell_min)
                            cell_min <= data_in;

                        cell_counter <= cell_counter + 16'd1;

                        // Check if we've completed a cell
                        // Cell size = 2^(scale_idx+1)
                        if (cell_counter == (16'd1 << (scale_idx + 1))) begin
                            // Finalize this cell: add (max - min + 1) to accumulator
                            box_count_acc <= box_count_acc +
                                             {24'd0, cell_max} - {24'd0, cell_min} + 32'd1;
                            // Reset for next cell
                            cell_max     <= data_in;
                            cell_min     <= data_in;
                            cell_counter <= 16'd1;
                        end
                    end else begin
                        // data_valid deasserted → data stream ended
                        state <= S_FINALIZE;
                    end
                end

                // ── FINALIZE: add partial cell's contribution ─────
                S_FINALIZE: begin
                    // Handle last (possibly partial) cell
                    if (cell_counter > 0) begin
                        box_count_acc <= box_count_acc +
                                         {24'd0, cell_max} - {24'd0, cell_min} + 32'd1;
                    end
                    // Wait one cycle for box_count_acc to update, then store log
                    state <= S_STORE_LOG;
                end

                // ── STORE_LOG: log(n(s)) now uses updated box_count_acc ──
                S_STORE_LOG: begin
                    // Compute log(n(s)) from box_count_acc (now includes partial cell)
                    log_ns[scale_idx] <= int_log2_q16(box_count_acc);

                    // Advance to next scale
                    if (scale_idx < NUM_SCALES - 1) begin
                        scale_idx     <= scale_idx + 1;
                        elem_count    <= 16'd1;
                        cell_max      <= 8'd0;
                        cell_min      <= 8'd255;
                        cell_counter  <= 16'd0;
                        box_count_acc <= 32'd0;
                        state         <= S_COLLECT;
                    end else begin
                        // All scales done → compute regression
                        state <= S_REGRESS;
                    end
                end

                // ── REGRESS: linear regression on log(n(s)) vs log(1/s)
                S_REGRESS: begin
                    case (regress_stage)
                        3'd0: begin
                            // Initialize accumulators
                            sum_x     <= 64'sd0;
                            sum_y     <= 64'sd0;
                            sum_xy    <= 64'sd0;
                            sum_x2    <= 64'sd0;
                            reg_count <= 0;
                            regress_stage <= 3'd1;
                        end
                        3'd1: begin
                            // Accumulate over all scales
                            // We process one scale per clock
                            if (reg_count < NUM_SCALES) begin
                                sum_x  <= sum_x  + $signed(log_inv_s[reg_count]);
                                sum_y  <= sum_y  + $signed(log_ns[reg_count]);
                                sum_xy <= sum_xy + $signed(log_inv_s[reg_count]) *
                                                   $signed(log_ns[reg_count]);
                                sum_x2 <= sum_x2 + $signed(log_inv_s[reg_count]) *
                                                   $signed(log_inv_s[reg_count]);
                                reg_count <= reg_count + 1;
                            end else begin
                                regress_stage <= 3'd2;
                            end
                        end
                        3'd2: begin
                            // Compute numerator and denominator
                            // N = NUM_SCALES
                            // numer = N * sum_xy - sum_x * sum_y
                            // denom = N * sum_x2 - sum_x * sum_x
                            numer <= $signed({60'd0, NUM_SCALES[3:0]}) * sum_xy -
                                     sum_x * sum_y;
                            denom <= $signed({60'd0, NUM_SCALES[3:0]}) * sum_x2 -
                                     sum_x * sum_x;
                            regress_stage <= 3'd3;
                        end
                        3'd3: begin
                            // Compute slope = numer / denom
                            // Result is in Q16_16: shift left 16 before dividing
                            if (denom != 64'sd0) begin
                                // slope = (numer << 16) / denom → full Q16_16
                                fd_q16 <= ((numer <<< 16) / denom)[31:0];
                            end else begin
                                // Degenerate case: flat data, FD ≈ 2.0
                                fd_q16 <= 32'h0002_0000;  // 2.0 in Q16_16
                            end
                            regress_stage <= 3'd4;
                        end
                        3'd4: begin
                            // Fractal dimension is always positive
                            if (fd_q16[31]) begin
                                // Negative slope → take absolute value
                                fd_q16 <= (~fd_q16) + 32'd1;
                            end
                            // Clamp to [1.0, 3.0] in Q16_16
                            if (fd_q16 < 32'h0001_0000)   // < 1.0
                                fd_q16 <= 32'h0001_0000;
                            if (fd_q16 > 32'h0003_0000)   // > 3.0
                                fd_q16 <= 32'h0003_0000;

                            fd_valid      <= 1'b1;
                            regress_stage <= 3'd0;
                            state         <= S_DONE;
                        end
                    endcase
                end

                // ── DONE: hold result, wait for new data ──────────
                S_DONE: begin
                    if (data_valid) begin
                        // New data stream → restart
                        state        <= S_COLLECT;
                        scale_idx    <= 0;
                        elem_count   <= 16'd1;
                        cell_max     <= data_in;
                        cell_min     <= data_in;
                        cell_counter <= 16'd1;
                        box_count_acc <= 32'd0;
                    end
                end
            endcase
        end
    end

endmodule

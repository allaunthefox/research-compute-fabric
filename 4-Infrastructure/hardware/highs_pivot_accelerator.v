`timescale 1ns / 1ps

// HiGHS Pivot Accelerator for Tang Nano 9K (GW1NR-9C)
// Simplex pivot: column[j] = column[j] / pivot_element
// 3-stage pipeline: load / divide / writeback
// Q16_16 division inline: result = (column_val << 16) / pivot_element
// 64-element column support

module highs_pivot_accelerator (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [31:0] pivot_element,
    input  wire [31:0] column_in,
    input  wire [5:0]  column_idx,
    output reg  [31:0] result,
    output reg         done,
    output reg         write_en,
    output reg  [5:0]  write_idx,
    output reg  [31:0] write_data
);

    // State machine
    localparam IDLE     = 2'b00;
    localparam LOAD     = 2'b01;
    localparam DIVIDE   = 2'b10;
    localparam WRITEBACK = 2'b11;

    reg [1:0]  state;
    reg [5:0]  elem_count;     // tracks which element we're processing (0..63)
    reg [5:0]  elem_count_d1;  // delayed count for pipeline

    // Pipeline registers
    reg [31:0] column_val_reg;  // stage 1 output
    reg [63:0] dividend;        // stage 2: column_val << 16 for Q16_16 division
    reg [31:0] pivot_reg;       // latched pivot element

    // Division result
    reg [31:0] div_result;

    always @(posedge clk) begin
        if (!rst_n) begin
            state        <= IDLE;
            result       <= 32'd0;
            done         <= 1'b0;
            write_en     <= 1'b0;
            write_idx    <= 6'd0;
            write_data   <= 32'd0;
            elem_count   <= 6'd0;
            elem_count_d1 <= 6'd0;
            column_val_reg <= 32'd0;
            dividend     <= 64'd0;
            pivot_reg    <= 32'd0;
            div_result   <= 32'd0;
        end else begin
            // Default: deassert single-cycle pulses
            write_en <= 1'b0;
            done     <= 1'b0;

            case (state)
                IDLE: begin
                    if (start) begin
                        pivot_reg  <= pivot_element;
                        elem_count <= 6'd0;
                        state      <= LOAD;
                    end
                end

                LOAD: begin
                    // Stage 1: Latch column input
                    column_val_reg <= column_in;
                    elem_count_d1  <= elem_count;
                    dividend       <= {32'd0, column_in} << 16;  // Q16_16 shift
                    state          <= DIVIDE;
                end

                DIVIDE: begin
                    // Stage 2: Perform division
                    // result = (column_val << 16) / pivot_element
                    if (pivot_reg != 32'd0) begin
                        div_result <= dividend[63:0] / {32'd0, pivot_reg};
                    end else begin
                        div_result <= 32'h7FFFFFFF;  // saturate on divide-by-zero
                    end
                    state <= WRITEBACK;
                end

                WRITEBACK: begin
                    // Stage 3: Write result back
                    write_en   <= 1'b1;
                    write_idx  <= elem_count_d1;
                    write_data <= div_result;
                    result     <= div_result;

                    if (elem_count_d1 == 6'd63) begin
                        // All 64 elements processed
                        done  <= 1'b1;
                        state <= IDLE;
                    end else begin
                        elem_count <= elem_count_d1 + 6'd1;
                        state      <= LOAD;
                    end
                end
            endcase
        end
    end

endmodule

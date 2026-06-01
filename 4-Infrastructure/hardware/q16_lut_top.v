// Wrapper for q16_lut_core with separate valid output pin
// FIX: Valid bit no longer overwrites MSB of result; widened output bus
module q16_lut_top (
    input  wire        clk,
    input  wire        rst,
    input  wire [2:0]  op_select,
    input  wire [15:0] a,
    input  wire [15:0] b,
    output wire [31:0] result,
    output wire        valid
);

    wire [31:0] core_result;
    wire        core_valid;

    q16_lut_core u_core (
        .clk       (clk),
        .rst       (rst),
        .op_select (op_select),
        .a         (a),
        .b         (b),
        .result    (core_result),
        .valid     (core_valid)
    );

    // FIX: Full 32-bit result preserved; valid exposed as separate pin
    assign result = core_result;
    assign valid  = core_valid;

endmodule

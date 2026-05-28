// Wrapper for q16_lut_core that maps valid to result[31]
// This reduces the pin count to fit the Tang Nano 9K
module q16_lut_top (
    input  wire        clk,
    input  wire        rst,
    input  wire [2:0]  op_select,
    input  wire [15:0] a,
    input  wire [15:0] b,
    output wire [31:0] result
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

    // Map valid into result[31] bit for external observation
    assign result = {core_valid, core_result[30:0]};

endmodule

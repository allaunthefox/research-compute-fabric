// voltage_mode_selector.v — Parameterized threshold-to-voltage-mode mapper
`ifndef VOLTAGE_MODE_SELECTOR_V
`define VOLTAGE_MODE_SELECTOR_V

module voltage_mode_selector #(
    parameter THRESHOLD1 = 16,
    parameter THRESHOLD2 = 32,
    parameter THRESHOLD3 = 64
) (
    input wire clk,
    input wire [31:0] value,
    output reg [1:0] mode
);
    localparam MODE_STORE   = 2'b00;
    localparam MODE_COMPUTE = 2'b01;
    localparam MODE_APPROX  = 2'b10;
    localparam MODE_MORPHIC = 2'b11;

    reg [1:0] mode_next;

    always @(*) begin
        if (value < THRESHOLD1)      mode_next = MODE_STORE;
        else if (value < THRESHOLD2) mode_next = MODE_COMPUTE;
        else if (value < THRESHOLD3) mode_next = MODE_APPROX;
        else                         mode_next = MODE_MORPHIC;
    end

    always @(posedge clk) begin
        mode <= mode_next;
    end
endmodule

`endif

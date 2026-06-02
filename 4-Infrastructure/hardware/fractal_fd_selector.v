`timescale 1ns / 1ps

`include "voltage_mode_selector.v"

// Fractal Dimension → Voltage Mode Selector
// Maps computed fractal dimension (Q16_16) to a 2-bit voltage mode for the
// voltage_mode_controller.
//
//   FD < 2.3  →  voltage_mode = 0 (STORE)
//   FD < 2.6  →  voltage_mode = 1 (COMPUTE)
//   FD < 2.9  →  voltage_mode = 2 (APPROX)
//   FD >= 2.9 →  voltage_mode = 3 (MORPHIC)
//
// Thresholds in Q16_16:
//   2.3 = 2 + 0.3 = 0x0002_4CCD  (131072 + 19661 = 150733)
//   2.6 = 2 + 0.6 = 0x0002_999A  (131072 + 39322 = 170394)
//   2.9 = 2 + 0.9 = 0x0002_E666  (131072 + 58982 = 190054)

module fractal_fd_selector (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] fd_q16,       // fractal dimension in Q16_16
    input  wire        fd_valid,     // fd_q16 is valid
    output reg  [1:0]  voltage_mode, // 0=STORE, 1=COMPUTE, 2=APPROX, 3=MORPHIC
    output reg         mode_valid    // mode output is valid
);

    localparam [31:0] THRESH_2_3 = 32'h0002_4CCD;  // 2.3
    localparam [31:0] THRESH_2_6 = 32'h0002_999A;  // 2.6
    localparam [31:0] THRESH_2_9 = 32'h0002_E666;  // 2.9

    wire [1:0] sel_mode;

    voltage_mode_selector #(
        .THRESHOLD1(THRESH_2_3),
        .THRESHOLD2(THRESH_2_6),
        .THRESHOLD3(THRESH_2_9)
    ) sel_inst (
        .clk(clk),
        .value(fd_q16),
        .mode(sel_mode)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            voltage_mode <= 2'b00;
            mode_valid   <= 1'b0;
        end else begin
            mode_valid <= 1'b0;
            if (fd_valid) begin
                voltage_mode <= sel_mode;
                mode_valid   <= 1'b1;
            end
        end
    end

endmodule

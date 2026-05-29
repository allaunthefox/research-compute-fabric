// Minimal UART test: sends 'R' (0x52) continuously at 115200 baud
// Verifies FT2232 channel B ↔ FPGA pin 18 connection

module uart_test (
    input  wire clk,
    output wire uart_tx,
    output wire [5:0] led
);

    // 27MHz / 234 = 115384 baud
    localparam BAUD_DIV = 16'd233;
    localparam TEST_BYTE = 8'h52;  // 'R' for Research Stack

    assign led = 6'b101010;  // Pattern to confirm FPGA is alive

    reg [15:0] baud_cnt = 0;
    reg [3:0] bit_cnt = 0;
    reg [9:0] shift_reg = 10'b1111111111;
    reg tx_out = 1'b1;
    assign uart_tx = tx_out;

    always @(posedge clk) begin
        if (baud_cnt >= BAUD_DIV) begin
            baud_cnt <= 0;
            if (bit_cnt == 0) begin
                // Load start bit + data + stop bit
                shift_reg <= {1'b1, TEST_BYTE, 1'b0};
                bit_cnt <= 10;
                tx_out <= 1'b0;  // Start bit
            end else begin
                tx_out <= shift_reg[0];
                shift_reg <= {1'b1, shift_reg[9:1]};
                bit_cnt <= bit_cnt - 1;
            end
        end else begin
            baud_cnt <= baud_cnt + 1;
        end
    end

endmodule

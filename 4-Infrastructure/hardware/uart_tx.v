// UART Transmitter for Tang Nano 9K
// 115200 baud, 8N1 configuration
// Clock: 27 MHz
// Baud divider: 27MHz / 115200 = 234.375 ≈ 234

`timescale 1ns / 1ps

module uart_tx (
    input         clk,
    input         rst_n,
    input         tx_start,
    input  [7:0]  tx_data,
    output        uart_tx,
    output        tx_busy
);

    localparam BAUD_DIV = 16'd234;  // 27MHz / 115200
    localparam IDLE = 2'd0;
    localparam START = 2'd1;
    localparam DATA = 2'd2;
    localparam STOP = 2'd3;

    reg [15:0] baud_counter;
    reg [2:0]  bit_counter;
    reg [1:0]  state;
    reg [7:0]  tx_shift;
    reg        tx_busy_r;
    reg        uart_tx_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            baud_counter <= 16'd0;
            bit_counter <= 3'd0;
            tx_shift <= 8'd0;
            tx_busy_r <= 1'b0;
            uart_tx_r <= 1'b1;
        end else begin
            case (state)
                IDLE: begin
                    if (tx_start) begin
                        state <= START;
                        tx_shift <= tx_data;
                        tx_busy_r <= 1'b1;
                        baud_counter <= 16'd0;
                        uart_tx_r <= 1'b0;  // Start bit
                    end else begin
                        tx_busy_r <= 1'b0;
                        uart_tx_r <= 1'b1;
                    end
                end
                START: begin
                    if (baud_counter == BAUD_DIV) begin
                        state <= DATA;
                        baud_counter <= 16'd0;
                        bit_counter <= 3'd0;
                        uart_tx_r <= tx_shift[0];  // LSB first
                    end else begin
                        baud_counter <= baud_counter + 1'b1;
                    end
                end
                DATA: begin
                    if (baud_counter == BAUD_DIV) begin
                        if (bit_counter == 3'd7) begin
                            state <= STOP;
                            uart_tx_r <= 1'b1;  // Stop bit
                        end else begin
                            bit_counter <= bit_counter + 1'b1;
                            tx_shift <= tx_shift >> 1;
                            uart_tx_r <= tx_shift[0];
                        end
                        baud_counter <= 16'd0;
                    end else begin
                        baud_counter <= baud_counter + 1'b1;
                    end
                end
                STOP: begin
                    if (baud_counter == BAUD_DIV) begin
                        state <= IDLE;
                        tx_busy_r <= 1'b0;
                    end else begin
                        baud_counter <= baud_counter + 1'b1;
                    end
                end
            endcase
        end
    end

    assign uart_tx = uart_tx_r;
    assign tx_busy = tx_busy_r;

endmodule

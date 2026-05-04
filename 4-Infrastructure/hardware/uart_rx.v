// UART Receiver for Tang Nano 9K
// 115200 baud, 8N1 configuration
// Clock: 27 MHz
// Baud divider: 27MHz / 115200 ≈ 234

`timescale 1ns / 1ps

module uart_rx (
    input         clk,
    input         rst_n,
    input         rx_pin,
    output [7:0]  rx_data,
    output        rx_done
);
    localparam BAUD_DIV = 16'd234;
    localparam IDLE = 2'd0;
    localparam START = 2'd1;
    localparam DATA = 2'd2;
    localparam STOP = 2'd3;

    reg [15:0] baud_counter;
    reg [2:0]  bit_counter;
    reg [1:0]  state;
    reg [7:0]  rx_shift;
    reg        rx_done_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            baud_counter <= 16'd0;
            bit_counter <= 3'd0;
            rx_shift <= 8'd0;
            rx_done_r <= 1'b0;
        end else begin
            rx_done_r <= 1'b0;
            case (state)
                IDLE: begin
                    if (rx_pin == 1'b0) begin // Start bit detected
                        state <= START;
                        baud_counter <= 16'd0;
                    end
                end
                START: begin
                    if (baud_counter == BAUD_DIV / 2) begin // Sample in the middle
                        if (rx_pin == 1'b0) begin
                            state <= DATA;
                            baud_counter <= 16'd0;
                            bit_counter <= 3'd0;
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        baud_counter <= baud_counter + 1'b1;
                    end
                end
                DATA: begin
                    if (baud_counter == BAUD_DIV) begin
                        rx_shift <= {rx_pin, rx_shift[7:1]};
                        if (bit_counter == 3'd7) begin
                            state <= STOP;
                        end else begin
                            bit_counter <= bit_counter + 1'b1;
                        end
                        baud_counter <= 16'd0;
                    end else begin
                        baud_counter <= baud_counter + 1'b1;
                    end
                end
                STOP: begin
                    if (baud_counter == BAUD_DIV) begin
                        state <= IDLE;
                        rx_done_r <= 1'b1;
                    end else begin
                        baud_counter <= baud_counter + 1'b1;
                    end
                end
            endcase
        end
    end

    assign rx_data = rx_shift;
    assign rx_done = rx_done_r;

endmodule

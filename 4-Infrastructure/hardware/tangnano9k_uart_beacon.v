// Tang Nano 9K UART TX beacon.
//
// This isolates the fabric TX pin from RX framing and host protocol logic. It
// emits a repeating receipt-like byte pattern at 115200 baud:
//   A6 42 51 31 36 0A
// which reads as a board-level "Q16" beacon after the magic/version bytes.

`timescale 1ns / 1ps

module tangnano9k_uart_beacon (
    input        clk,
    input        rst_n,
    input        uart_rx_pin,
    output       uart_tx_pin,
    output [5:0] led
);
    localparam GAP_CYCLES = 24'd2700000; // about 100 ms at 27 MHz

    wire tx_busy;
    reg tx_start;
    reg [7:0] tx_data;
    reg [23:0] gap_counter;
    reg [2:0] byte_index;
    reg [5:0] sent_count;

    wire rst_n_internal = 1'b1; // Bypass physical reset button

    uart_tx tx_inst (
        .clk(clk),
        .rst_n(rst_n_internal),
        .tx_start(tx_start),
        .tx_data(tx_data),
        .uart_tx(uart_tx_pin),
        .tx_busy(tx_busy)
    );

    function [7:0] beacon_byte;
        input [2:0] idx;
        begin
            case (idx)
                3'd0: beacon_byte = 8'hA6;
                3'd1: beacon_byte = 8'h42;
                3'd2: beacon_byte = 8'h51;
                3'd3: beacon_byte = 8'h31;
                3'd4: beacon_byte = 8'h36;
                default: beacon_byte = 8'h0A;
            endcase
        end
    endfunction

    always @(posedge clk or negedge rst_n_internal) begin
        if (!rst_n_internal) begin
            tx_start <= 1'b0;
            tx_data <= 8'h00;
            gap_counter <= 24'd0;
            byte_index <= 3'd0;
            sent_count <= 6'd0;
        end else begin
            tx_start <= 1'b0;
            if (gap_counter < GAP_CYCLES) begin
                gap_counter <= gap_counter + 24'd1;
            end else if (!tx_busy) begin
                tx_data <= beacon_byte(byte_index);
                tx_start <= 1'b1;
                sent_count <= sent_count + 6'd1;
                if (byte_index == 3'd5) begin
                    byte_index <= 3'd0;
                    gap_counter <= 24'd0;
                end else begin
                    byte_index <= byte_index + 3'd1;
                end
            end
        end
    end

    assign led = ~sent_count;

    wire unused_rx = uart_rx_pin;
    wire unused_rst = rst_n;

endmodule

// Tang Nano 9K UART Loopback & FAMM Logic Test
// Host sends a byte, FPGA adds 1 and echoes back.
// Lower 6 bits of RX data are displayed on LEDs.

`timescale 1ns / 1ps

module tangnano9k_uart_loopback (
    input        clk,         // 27 MHz
    input        rst_n,       // Reset button (active low)
    input        uart_rx_pin, // UART RX
    output       uart_tx_pin, // UART TX
    output [5:0] led          // Onboard LEDs (active low)
);

    wire [7:0] rx_data;
    wire       rx_done;
    
    reg [7:0]  tx_data;
    reg        tx_start;
    wire       tx_busy;
    
    // Record of last received byte for LED display
    reg [7:0]  last_rx;
    
    // UART Receiver Instance
    uart_rx rx_inst (
        .clk(clk),
        .rst_n(rst_n),
        .rx_pin(uart_rx_pin),
        .rx_data(rx_data),
        .rx_done(rx_done)
    );
    
    // UART Transmitter Instance
    uart_tx tx_inst (
        .clk(clk),
        .rst_n(rst_n),
        .tx_start(tx_start),
        .tx_data(tx_data),
        .uart_tx(uart_tx_pin),
        .tx_busy(tx_busy)
    );
    
    // Control Logic: Echo RX+1 to TX
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_start <= 1'b0;
            tx_data  <= 8'h00;
            last_rx  <= 8'h00;
        end else begin
            if (rx_done) begin
                last_rx <= rx_data;
                // Prepare echo
                tx_data <= rx_data + 8'h01; // The "FAMM Transform" placeholder
                tx_start <= 1'b1;
            end else if (tx_start && !tx_busy) begin
                // Wait for TX to start before dropping start signal
                tx_start <= 1'b0;
            end else if (!tx_busy) begin
                tx_start <= 1'b0;
            end
        end
    end
    
    // Display last received byte on LEDs (active low)
    assign led = ~last_rx[5:0];

endmodule

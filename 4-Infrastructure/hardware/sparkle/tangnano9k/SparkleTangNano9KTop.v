// Sparkle Tang Nano 9K board wrapper
// Target: Sipeed Tang Nano 9K, Gowin GW1NR-LV9QN88PC6/I5, QN88 package
//
// This wrapper exposes only real board-level pins. The payload is generated
// from Sparkle IR by tools/lean/Semantics/GenerateSparklePhiS3C.lean.

`timescale 1ns / 1ps

module SparkleTangNano9KTop (
    input  wire       clk,       // Pin 52, 27 MHz oscillator
    input  wire       rst_n,     // Pin 4, active-low reset button
    input  wire       user_btn,  // Pin 3, active-low user button on board
    output wire [5:0] led,       // Pins 10,11,13,14,15,16
    output wire       uart_tx,   // Pin 17, USB-UART TX from FPGA
    /* verilator lint_off UNUSEDSIGNAL */
    input  wire       uart_rx,   // Pin 18, USB-UART RX to FPGA (unused by payload)
    /* verilator lint_on UNUSEDSIGNAL */

    // External I2S microphone/header pins. SPH0645-style mics are I2S, not PDM.
    // The FPGA generates master clocks (SCLK + WS); the mic drives SD.
    output wire       i2s_sclk,
    output wire       i2s_ws,
    input  wire       i2s_sd
);
    // Tang Nano 9K buttons are active-low. Internal payloads use active-high
    // edge detection for user button, so invert it here.
    wire user_btn_pressed = ~user_btn;
    wire rst = ~rst_n;

    /* verilator lint_off UNUSEDSIGNAL */
    wire [15:0] handleK;  // driven by payload for UART frame, not routed to pins
    /* verilator lint_on UNUSEDSIGNAL */

    sparkle_phi_s3c_payload payload (
        .clk(clk),
        .rst(rst),
        .user_btn(user_btn_pressed),
        .i2s_sd(i2s_sd),
        .led(led),
        .uart_tx(uart_tx),
        .i2s_sclk(i2s_sclk),
        .i2s_ws(i2s_ws),
        .handleK(handleK)
    );

endmodule

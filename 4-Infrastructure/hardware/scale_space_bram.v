`timescale 1ns / 1ps

// Scale Space BRAM for Tang Nano 9K (GW1NR-9C)
// 4 BRAM banks with Gaussian kernels at sigma=0.25/0.50/0.75/1.00
// 256 entries each, Q16_16 fixed-point
// Precomputed Gaussian G(x) = exp(-x^2 / (2*sigma^2)) scaled to Q16_16

module scale_space_bram (
    input  wire        clk,
    input  wire        we,
    input  wire [1:0]  bank_select,
    input  wire [7:0]  addr,
    input  wire [31:0] din,
    output reg  [31:0] dout,
    output reg  [31:0] kernel_sum
);

    // ---------------------------------------------------------------
    // Gaussian kernel ROMs (precomputed, Q16_16 fixed-point)
    // G(x) = exp(-x^2 / (2*sigma^2)) * 65536
    // x ranges from -128 to 127 mapped to addr[7:0]
    // ---------------------------------------------------------------

    // Bank 0: sigma = 0.25
    // sigma^2 = 0.0625, 2*sigma^2 = 0.125
    // G(x) = exp(-x^2 / 0.125) = exp(-8*x^2)
    // At center (x=0): G=1.0 => 65536 in Q16_16
    // At x=1: exp(-8) = 0.000335 => 22 in Q16_16
    // Kernel is very narrow, most energy at center

    reg [31:0] bank0 [0:255];  // sigma=0.25
    reg [31:0] bank1 [0:255];  // sigma=0.50
    reg [31:0] bank2 [0:255];  // sigma=0.75
    reg [31:0] bank3 [0:255];  // sigma=1.00

    // Precomputed kernel initialization
    integer i;
    reg signed [8:0] x;  // signed offset from center

    initial begin
        // Bank 0: sigma = 0.25
        // G(x) = exp(-x^2 / (2 * 0.0625)) = exp(-8*x^2)
        // Precomputed values for x = -128..127
        for (i = 0; i < 256; i = i + 1) begin
            x = i - 128;  // signed offset
            // Approximate: exp(-8*x^2) * 65536
            // For |x| >= 2, value is essentially 0
            if (x == 0)
                bank0[i] = 32'd65536;        // 1.0 in Q16_16
            else if (x == -1 || x == 1)
                bank0[i] = 32'd22;           // exp(-8) * 65536 ≈ 22
            else if (x == -2 || x == 2)
                bank0[i] = 32'd0;            // exp(-32) ≈ 0
            else
                bank0[i] = 32'd0;
        end

        // Bank 1: sigma = 0.50
        // G(x) = exp(-x^2 / (2 * 0.25)) = exp(-2*x^2)
        for (i = 0; i < 256; i = i + 1) begin
            x = i - 128;
            if (x == 0)
                bank1[i] = 32'd65536;        // 1.0
            else if (x == -1 || x == 1)
                bank1[i] = 32'd8855;         // exp(-2) * 65536 ≈ 8855
            else if (x == -2 || x == 2)
                bank1[i] = 32'd218;          // exp(-8) * 65536 ≈ 218
            else if (x == -3 || x == 3)
                bank1[i] = 32'd1;            // exp(-18) * 65536 ≈ 1
            else
                bank1[i] = 32'd0;
        end

        // Bank 2: sigma = 0.75
        // G(x) = exp(-x^2 / (2 * 0.5625)) = exp(-x^2 / 1.125)
        for (i = 0; i < 256; i = i + 1) begin
            x = i - 128;
            if (x == 0)
                bank2[i] = 32'd65536;        // 1.0
            else if (x == -1 || x == 1)
                bank2[i] = 32'd24180;        // exp(-0.889) * 65536 ≈ 24180
            else if (x == -2 || x == 2)
                bank2[i] = 32'd2052;         // exp(-3.556) * 65536 ≈ 2052
            else if (x == -3 || x == 3)
                bank2[i] = 32'd47;           // exp(-8) * 65536 ≈ 47
            else if (x == -4 || x == 4)
                bank2[i] = 32'd0;            // exp(-14.22) ≈ 0
            else
                bank2[i] = 32'd0;
        end

        // Bank 3: sigma = 1.00
        // G(x) = exp(-x^2 / 2)
        for (i = 0; i < 256; i = i + 1) begin
            x = i - 128;
            if (x == 0)
                bank3[i] = 32'd65536;        // 1.0
            else if (x == -1 || x == 1)
                bank3[i] = 32'd39557;        // exp(-0.5) * 65536 ≈ 39557
            else if (x == -2 || x == 2)
                bank3[i] = 32'd8855;         // exp(-2) * 65536 ≈ 8855
            else if (x == -3 || x == 3)
                bank3[i] = 32'd729;          // exp(-4.5) * 65536 ≈ 729
            else if (x == -4 || x == 4)
                bank3[i] = 32'd22;           // exp(-8) * 65536 ≈ 22
            else if (x == -5 || x == 5)
                bank3[i] = 32'd0;            // exp(-12.5) ≈ 0
            else
                bank3[i] = 32'd0;
        end
    end

    // Kernel sums (precomputed for normalization)
    // bank0 sum: 65536 + 2*22 = 65580
    // bank1 sum: 65536 + 2*8855 + 2*218 + 2*1 = 83684
    // bank2 sum: 65536 + 2*24180 + 2*2052 + 2*47 = 118094
    // bank3 sum: 65536 + 2*39557 + 2*8855 + 2*729 + 2*22 = 163942

    // Bank write and read logic
    always @(posedge clk) begin
        if (we) begin
            case (bank_select)
                2'b00: bank0[addr] <= din;
                2'b01: bank1[addr] <= din;
                2'b10: bank2[addr] <= din;
                2'b11: bank3[addr] <= din;
            endcase
        end

        case (bank_select)
            2'b00: dout <= bank0[addr];
            2'b01: dout <= bank1[addr];
            2'b10: dout <= bank2[addr];
            2'b11: dout <= bank3[addr];
        endcase
    end

    // Kernel sum output
    always @(posedge clk) begin
        case (bank_select)
            2'b00: kernel_sum <= 32'd65580;    // sigma=0.25
            2'b01: kernel_sum <= 32'd83684;    // sigma=0.50
            2'b10: kernel_sum <= 32'd118094;   // sigma=0.75
            2'b11: kernel_sum <= 32'd163942;   // sigma=1.00
        endcase
    end

endmodule

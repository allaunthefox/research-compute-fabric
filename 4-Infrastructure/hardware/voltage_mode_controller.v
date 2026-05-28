`timescale 1ns / 1ps

// Voltage Mode Controller for Tang Nano 9K (GW1NR-9C)
// 4 BRAM instances (one per mode: STORE/COMPUTE/APPROX/MORPHIC)
// Mode mux selects output. APPROX truncates Q16_16 to 12-bit.
// MORPHIC: bram_dout = stored + (morphic_amp >>> 8)

module voltage_mode_controller (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [1:0]  mode,
    input  wire [9:0]  bram_addr,
    input  wire [31:0] bram_din,
    input  wire        bram_we,
    input  wire [31:0] morphic_amp,
    output reg  [31:0] bram_dout,
    output reg  [1:0]  voltage_level,
    output reg  [4:0]  precision_bits,
    output reg         active
);

    // Mode definitions
    localparam MODE_STORE   = 2'b00;
    localparam MODE_COMPUTE = 2'b01;
    localparam MODE_APPROX  = 2'b10;
    localparam MODE_MORPHIC = 2'b11;

    // BRAM arrays (1024 x 32-bit each)
    reg [31:0] bram_store   [0:1023];
    reg [31:0] bram_compute [0:1023];
    reg [31:0] bram_approx  [0:1023];
    reg [31:0] bram_morphic [0:1023];

    // Per-bank write enables
    wire we_store   = bram_we && (mode == MODE_STORE);
    wire we_compute = bram_we && (mode == MODE_COMPUTE);
    wire we_approx  = bram_we && (mode == MODE_APPROX);
    wire we_morphic = bram_we && (mode == MODE_MORPHIC);

    // Read outputs from each bank
    reg [31:0] dout_store;
    reg [31:0] dout_compute;
    reg [31:0] dout_approx_raw;
    reg [31:0] dout_morphic_raw;

    // BRAM STORE
    always @(posedge clk) begin
        if (we_store)
            bram_store[bram_addr] <= bram_din;
        dout_store <= bram_store[bram_addr];
    end

    // BRAM COMPUTE
    always @(posedge clk) begin
        if (we_compute)
            bram_compute[bram_addr] <= bram_din;
        dout_compute <= bram_compute[bram_addr];
    end

    // BRAM APPROX
    always @(posedge clk) begin
        if (we_approx)
            bram_approx[bram_addr] <= bram_din;
        dout_approx_raw <= bram_approx[bram_addr];
    end

    // BRAM MORPHIC
    always @(posedge clk) begin
        if (we_morphic)
            bram_morphic[bram_addr] <= bram_din;
        dout_morphic_raw <= bram_morphic[bram_addr];
    end

    // APPROX: truncate Q16_16 to 12-bit (zero lower 4 bits of fractional part)
    // Q16_16 format: [31:16] integer, [15:0] fractional
    // Truncate: keep upper 12 bits of fractional (bits [15:4]), zero bits [3:0]
    wire [31:0] dout_approx_trunc;
    assign dout_approx_trunc = {dout_approx_raw[31:16], dout_approx_raw[15:4], 4'b0000};

    // MORPHIC: bram_dout = stored + (morphic_amp >>> 8)
    wire [31:0] morphic_shifted;
    assign morphic_shifted = {{8{morphic_amp[31]}}, morphic_amp[31:8]};  // arithmetic right shift

    wire [31:0] dout_morphic_result;
    assign dout_morphic_result = dout_morphic_raw + morphic_shifted;

    // Mode mux
    always @(posedge clk) begin
        if (!rst_n) begin
            bram_dout     <= 32'd0;
            voltage_level <= 2'd0;
            precision_bits <= 5'd0;
            active        <= 1'b0;
        end else begin
            active <= 1'b1;
            case (mode)
                MODE_STORE: begin
                    bram_dout     <= dout_store;
                    voltage_level <= 2'b00;
                    precision_bits <= 5'd16;
                end
                MODE_COMPUTE: begin
                    bram_dout     <= dout_compute;
                    voltage_level <= 2'b01;
                    precision_bits <= 5'd16;
                end
                MODE_APPROX: begin
                    bram_dout     <= dout_approx_trunc;
                    voltage_level <= 2'b10;
                    precision_bits <= 5'd12;
                end
                MODE_MORPHIC: begin
                    bram_dout     <= dout_morphic_result;
                    voltage_level <= 2'b11;
                    precision_bits <= 5'd16;
                end
            endcase
        end
    end

endmodule

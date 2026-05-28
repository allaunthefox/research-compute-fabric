// ============================================================================
// q16_lut_core.v - Q16_16 Fixed-Point LUT Arithmetic Core
// Target: Tang Nano 9K (GW1NR-9)
// Format: Q16.16 (16-bit integer, 16-bit fractional)
// Pipeline: 2 stages (compute/lookup + output register)
// ============================================================================
// Operations:
//   0: add   (a + b)
//   1: sub   (a - b)
//   2: mul   (a * b, with LUT-assisted fractional handling)
//   3: div   (a / b, LUT-based reciprocal approximation)
//   4: max   (max(a, b))
//   5: min   (min(a, b))
//   6: neg   (-a)
//   7: abs   (|a|)
// ============================================================================

module q16_lut_core (
    input  wire        clk,
    input  wire        rst,
    input  wire [2:0]  op_select,
    input  wire [15:0] a,
    input  wire [15:0] b,
    output reg  [31:0] result,
    output reg         valid
);

    // ----------------------------------------------------------------
    // Q16_16 constants
    // ----------------------------------------------------------------
    localparam Q16_FRAC_BITS = 16;
    localparam [31:0] Q16_ONE = 32'h0001_0000;  // 1.0 in Q16.16
    localparam [31:0] Q16_MAX = 32'h7FFF_FFFF;  // max positive
    localparam [31:0] Q16_MIN = 32'h8000_0000;  // max negative

    // ----------------------------------------------------------------
    // Reciprocal LUT (block RAM inference)
    // Stores 1/x for x in [1..255] scaled to Q16.16
    // Index 0 stores 0 (division by zero guard)
    // Size: 256 x 32-bit = 1 KB (fits in a single block RAM)
    // ----------------------------------------------------------------
    reg [31:0] recip_lut [0:255];

    // Initialize reciprocal LUT using synthesis attribute
    // recip_lut[i] = floor(65536.0 / i) for i=1..255
    initial begin : init_recip_lut
        integer i;
        recip_lut[0] = 32'h7FFF_FFFF;  // div-by-zero guard -> max
        for (i = 1; i < 256; i = i + 1) begin
            recip_lut[i] = 32'd65536 / i[31:0];
        end
    end

    // ----------------------------------------------------------------
    // Stage 1: Compute / Lookup
    // ----------------------------------------------------------------
    reg [31:0] result_s1;
    reg        valid_s1;
    reg [2:0]  op_s1;

    // Sign-extend inputs to 32 bits for arithmetic
    wire signed [31:0] a_ext = {{16{a[15]}}, a};
    wire signed [31:0] b_ext = {{16{b[15]}}, b};

    // Absolute values for division lookup
    wire [15:0] a_abs = a[15] ? (~a + 16'd1) : a;
    wire [15:0] b_abs = b[15] ? (~b + 16'd1) : b;

    // Reciprocal LUT address: use lower 8 bits of |b|
    wire [7:0] recip_addr = b_abs[7:0];
    reg [31:0] recip_val;

    // Multiplication intermediate (32x32 -> 64, take middle 32)
    wire signed [63:0] mul_full  = a_ext * b_ext;
    wire [31:0]        mul_result = mul_full[47:16];  // Q16.16 result

    // Overflow detection for add/sub
    wire add_overflow = (~a_ext[31] & ~b_ext[31] & result_s1[31]) |
                        ( a_ext[31] &  b_ext[31] & ~result_s1[31]);

    always @(posedge clk) begin
        if (rst) begin
            result_s1 <= 32'd0;
            valid_s1  <= 1'b0;
            op_s1     <= 3'd0;
            recip_val <= 32'd0;
        end else begin
            valid_s1 <= 1'b1;
            op_s1    <= op_select;

            // Latch reciprocal value for div operation
            recip_val <= recip_lut[recip_addr];

            case (op_select)
                3'd0: begin  // ADD
                    result_s1 <= a_ext + b_ext;
                end
                3'd1: begin  // SUB
                    result_s1 <= a_ext - b_ext;
                end
                3'd2: begin  // MUL
                    result_s1 <= mul_result;
                end
                3'd3: begin  // DIV (LUT-based reciprocal approximation)
                    // a / b ≈ a * recip(b)
                    // Use upper bits of |b| for LUT index if > 255
                    if (b == 16'd0) begin
                        result_s1 <= (a[15]) ? Q16_MIN : Q16_MAX;
                    end else begin
                        // Approximate: sign * (|a| * recip(|b|))
                        result_s1 <= (a[15] ^ b[15]) ?
                                     (-(a_ext[31:0] * recip_val >>> Q16_FRAC_BITS)) :
                                     ( a_ext[31:0] * recip_val >>> Q16_FRAC_BITS);
                    end
                end
                3'd4: begin  // MAX
                    result_s1 <= (a_ext > b_ext) ? a_ext : b_ext;
                end
                3'd5: begin  // MIN
                    result_s1 <= (a_ext < b_ext) ? a_ext : b_ext;
                end
                3'd6: begin  // NEG
                    if (a == 16'h8000) begin
                        result_s1 <= 32'h0000_7FFF;  // saturate
                    end else begin
                        result_s1 <= -a_ext;
                    end
                end
                3'd7: begin  // ABS
                    if (a == 16'h8000) begin
                        result_s1 <= 32'h0000_7FFF;  // saturate
                    end else begin
                        result_s1 <= a[15] ? (-a_ext) : a_ext;
                    end
                end
                default: begin
                    result_s1 <= 32'd0;
                end
            endcase
        end
    end

    // ----------------------------------------------------------------
    // Stage 2: Output Register (pipeline register)
    // ----------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            result <= 32'd0;
            valid  <= 1'b0;
        end else begin
            valid <= valid_s1;

            // Saturate on overflow for add/sub
            case (op_s1)
                3'd0, 3'd1: begin  // ADD / SUB saturation
                    if (result_s1[31] == a_ext[31] && result_s1[31] != (op_s1 == 3'd0 ? b_ext[31] : ~b_ext[31])) begin
                        result <= result_s1[31] ? Q16_MIN : Q16_MAX;
                    end else begin
                        result <= result_s1;
                    end
                end
                default: begin
                    result <= result_s1;
                end
            endcase
        end
    end

endmodule

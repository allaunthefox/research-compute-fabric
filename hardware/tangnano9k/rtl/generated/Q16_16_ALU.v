// Auto-generated from Lean: Semantics.Hardware.TangNano9K.emitQ16_16ALU
// Source of truth: Semantics.Q16_16
// NOTE: All arithmetic is SIGNED and SATURATING.
//
// DO NOT EDIT BY HAND. Regenerate via: lake exe tangnano9k_emitter

`timescale 1ns / 1ps

module Q16_16_ALU (
    input  wire [31:0] a,
    input  wire [31:0] b,
    input  wire [2:0]  op,        // 0=add, 1=sub, 2=mul, 3=div, 4=max, 5=min, 6=abs
    output reg  [31:0] result,
    output reg         overflow
);
    localparam OP_ADD = 3'd0;
    localparam OP_SUB = 3'd1;
    localparam OP_MUL = 3'd2;
    localparam OP_DIV = 3'd3;
    localparam OP_MAX = 3'd4;
    localparam OP_MIN = 3'd5;
    localparam OP_ABS = 3'd6;

    localparam MAX_POS = 32'h7FFFFFFF;
    localparam MAX_NEG = 32'h80000000;

    // Signed Addition with Saturation
    wire [32:0] add_full = {a[31], a} + {b[31], b};
    wire [31:0] add_sat  = (add_full[32] != add_full[31]) ? 
                           (add_full[32] ? MAX_NEG : MAX_POS) : add_full[31:0];

    // Signed Subtraction with Saturation
    wire [32:0] sub_full = {a[31], a} - {b[31], b};
    wire [31:0] sub_sat  = (sub_full[32] != sub_full[31]) ? 
                           (sub_full[32] ? MAX_NEG : MAX_POS) : sub_full[31:0];

    // Signed Multiplication with Saturation: (a * b) >>> 16
    wire [63:0] mul_full = $signed(a) * $signed(b);
    wire [63:0] mul_shifted = mul_full >>> 16;
    wire [31:0] mul_sat = ($signed(mul_shifted) > $signed({32'd0, MAX_POS})) ? MAX_POS :
                          ($signed(mul_shifted) < $signed({32'hFFFFFFFF, MAX_NEG})) ? MAX_NEG :
                          mul_shifted[31:0];

    // Signed Division: (a << 16) / b
    wire [63:0] div_num = {{16{a[31]}}, a, 16'd0};
    wire [31:0] div_res = (b == 0) ? (a[31] ? MAX_NEG : MAX_POS) : (div_num / $signed(b));

    always @(*) begin
        overflow = 1'b0;
        case (op)
            OP_ADD: result = add_sat;
            OP_SUB: result = sub_sat;
            OP_MUL: result = mul_sat;
            OP_DIV: result = div_res;
            OP_MAX: result = ($signed(a) > $signed(b)) ? a : b;
            OP_MIN: result = ($signed(a) < $signed(b)) ? a : b;
            OP_ABS: result = (a[31]) ? sub_sat : a; // abs(a) = 0 - a (saturating)
            default: result = 32'd0;
        endcase
    end
endmodule

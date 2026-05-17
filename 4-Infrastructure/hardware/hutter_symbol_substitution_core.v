// Hutter/metaprobe symbol substitution core for Tang Nano 9K surface tests.
//
// This is intentionally small: one input byte becomes a 4-bit dictionary code
// plus a hit flag. The host owns full codec/search logic; FPGA owns the
// deterministic substitution witness path.

`timescale 1ns / 1ps

module hutter_symbol_substitution_core (
    input  wire [7:0] symbol,
    output reg  [3:0] code,
    output reg        hit
);

    always @* begin
        hit  = 1'b1;
        code = 4'h0;
        case (symbol)
            8'h20: code = 4'h0; // space
            "e", "E": code = 4'h1;
            "t", "T": code = 4'h2;
            "a", "A": code = 4'h3;
            "o", "O": code = 4'h4;
            "i", "I": code = 4'h5;
            "n", "N": code = 4'h6;
            "s", "S": code = 4'h7;
            "r", "R": code = 4'h8;
            "h", "H": code = 4'h9;
            "l", "L": code = 4'hA;
            "d":      code = 4'hB;
            "c", "C": code = 4'hC;
            "u", "U": code = 4'hD;
            "F":      code = 4'hE; // full metaprobe token marker
            "D":      code = 4'hF; // delta metaprobe token marker
            default: begin
                hit  = 1'b0;
                code = symbol[3:0];
            end
        endcase
    end

endmodule

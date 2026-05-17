`timescale 1ns / 1ps

module tb_hutter_symbol_substitution_core;
    reg [7:0] symbol;
    wire [3:0] code;
    wire hit;

    hutter_symbol_substitution_core dut (
        .symbol(symbol),
        .code(code),
        .hit(hit)
    );

    task expect_symbol;
        input [7:0] s;
        input [3:0] expected_code;
        input expected_hit;
        begin
            symbol = s;
            #1;
            if (code !== expected_code || hit !== expected_hit) begin
                $display("FAIL symbol=%h code=%h hit=%b expected_code=%h expected_hit=%b",
                         s, code, hit, expected_code, expected_hit);
                $finish;
            end
        end
    endtask

    initial begin
        expect_symbol(" ", 4'h0, 1'b1);
        expect_symbol("e", 4'h1, 1'b1);
        expect_symbol("T", 4'h2, 1'b1);
        expect_symbol("F", 4'hE, 1'b1);
        expect_symbol("D", 4'hF, 1'b1);
        expect_symbol("x", 4'h8, 1'b0);
        expect_symbol("0", 4'h0, 1'b0);
        $display("PASS hutter_symbol_substitution_core");
        $finish;
    end
endmodule

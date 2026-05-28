// ============================================================================
// q16_lut_core_tb.v - Testbench for Q16_16 LUT Core
// Tests all 8 operations with known values and edge cases
// ============================================================================
`timescale 1ns / 1ps

module q16_lut_core_tb;

    // ----------------------------------------------------------------
    // Signals
    // ----------------------------------------------------------------
    reg         clk;
    reg         rst;
    reg  [2:0]  op_select;
    reg  [15:0] a;
    reg  [15:0] b;
    wire [31:0] result;
    wire        valid;

    // Test counters
    integer test_count;
    integer pass_count;
    integer fail_count;

    // Expected value for comparison
    reg [31:0] expected;

    // Q16_16 constants
    localparam [15:0] Q16_ZERO    = 16'h0000;
    localparam [15:0] Q16_ONE     = 16'h0001;
    localparam [15:0] Q16_TWO     = 16'h0002;
    localparam [15:0] Q16_HALF    = 16'h0000;  // 0.5 needs 32-bit, using 0 here
    localparam [15:0] Q16_NEG_ONE = 16'hFFFF;  // -1 in 16-bit signed
    localparam [15:0] Q16_MAX_POS = 16'h7FFF;
    localparam [15:0] Q16_MAX_NEG = 16'h8000;
    localparam [15:0] Q16_FOUR    = 16'h0004;
    localparam [15:0] Q16_THREE   = 16'h0003;

    // ----------------------------------------------------------------
    // DUT instantiation
    // ----------------------------------------------------------------
    q16_lut_core dut (
        .clk(clk),
        .rst(rst),
        .op_select(op_select),
        .a(a),
        .b(b),
        .result(result),
        .valid(valid)
    );

    // ----------------------------------------------------------------
    // Clock generation: 27 MHz (Tang Nano 9K default)
    // ----------------------------------------------------------------
    initial clk = 0;
    always #18.5 clk = ~clk;  // ~27 MHz

    // ----------------------------------------------------------------
    // Task: run one test and check result
    // ----------------------------------------------------------------
    task run_test;
        input [2:0]  op;
        input [15:0] in_a;
        input [15:0] in_b;
        input [31:0] exp;
        input [255:0] name;  // test name (ASCII)
        begin
            @(posedge clk);
            op_select <= op;
            a <= in_a;
            b <= in_b;
            expected <= exp;

            // Wait for pipeline (2 cycles) + 1 for safety
            @(posedge clk);
            @(posedge clk);
            @(posedge clk);

            test_count = test_count + 1;

            // Allow +-1 tolerance for LUT-based approximate operations
            if (result == exp ||
                (op == 3'd3 && (result >= exp - 32'd2 && result <= exp + 32'd2))) begin
                pass_count = pass_count + 1;
                $display("PASS [%0s] op=%0d a=%h b=%h result=%h expected=%h",
                         name, op, in_a, in_b, result, exp);
            end else begin
                fail_count = fail_count + 1;
                $display("FAIL [%0s] op=%0d a=%h b=%h result=%h expected=%h",
                         name, op, in_a, in_b, result, exp);
            end
        end
    endtask

    // ----------------------------------------------------------------
    // Task: run test with approximate tolerance
    // ----------------------------------------------------------------
    task run_test_approx;
        input [2:0]  op;
        input [15:0] in_a;
        input [15:0] in_b;
        input [31:0] exp;
        input [31:0] tolerance;
        input [255:0] name;
        begin
            @(posedge clk);
            op_select <= op;
            a <= in_a;
            b <= in_b;
            expected <= exp;

            @(posedge clk);
            @(posedge clk);
            @(posedge clk);

            test_count = test_count + 1;

            if ((result >= exp - tolerance) && (result <= exp + tolerance)) begin
                pass_count = pass_count + 1;
                $display("PASS [%0s] op=%0d a=%h b=%h result=%h expected=%h (tol=%0d)",
                         name, op, in_a, in_b, result, exp, tolerance);
            end else begin
                fail_count = fail_count + 1;
                $display("FAIL [%0s] op=%0d a=%h b=%h result=%h expected=%h (tol=%0d)",
                         name, op, in_a, in_b, result, exp, tolerance);
            end
        end
    endtask

    // ----------------------------------------------------------------
    // Main test sequence
    // ----------------------------------------------------------------
    initial begin
        $display("=== Q16_16 LUT Core Testbench ===");
        $display("Target: Tang Nano 9K (GW1NR-9)");
        $display("");

        test_count = 0;
        pass_count = 0;
        fail_count = 0;

        // Reset
        rst = 1;
        op_select = 0;
        a = 0;
        b = 0;
        repeat (5) @(posedge clk);
        rst = 0;
        repeat (2) @(posedge clk);

        // ============================================================
        // ADD tests (op=0)
        // ============================================================
        $display("--- ADD Tests ---");
        run_test(3'd0, 16'd5, 16'd3, 32'd8, "add_basic");
        run_test(3'd0, 16'd0, 16'd0, 32'd0, "add_zero_zero");
        run_test(3'd0, 16'd100, 16'd200, 32'd300, "add_pos_pos");
        run_test(3'd0, 16'hFFFF, 16'd1, 32'd0, "add_neg1_plus_1");  // -1 + 1 = 0

        // ============================================================
        // SUB tests (op=1)
        // ============================================================
        $display("");
        $display("--- SUB Tests ---");
        run_test(3'd1, 16'd10, 16'd3, 32'd7, "sub_basic");
        run_test(3'd1, 16'd3, 16'd10, 32'hFFFFFFF9, "sub_negative_result");  // 3-10 = -7
        run_test(3'd1, 16'd5, 16'd5, 32'd0, "sub_same");

        // ============================================================
        // MUL tests (op=2)
        // ============================================================
        $display("");
        $display("--- MUL Tests ---");
        run_test(3'd2, 16'd2, 16'd3, 32'd6, "mul_basic");
        run_test(3'd2, 16'd0, 16'd100, 32'd0, "mul_by_zero");
        run_test(3'd2, 16'd1, 16'd1, 32'd1, "mul_one_one");

        // ============================================================
        // DIV tests (op=3) - LUT-based, approximate
        // ============================================================
        $display("");
        $display("--- DIV Tests (approximate) ---");
        run_test_approx(3'd3, 16'd6, 16'd2, 32'd3, 32'd2, "div_6_2");
        run_test_approx(3'd3, 16'd10, 16'd5, 32'd2, 32'd2, "div_10_5");
        run_test_approx(3'd3, 16'd7, 16'd2, 32'd3, 32'd2, "div_7_2");

        // Division by zero: should saturate
        @(posedge clk);
        op_select <= 3'd3;
        a <= 16'd5;
        b <= 16'd0;
        @(posedge clk);
        @(posedge clk);
        @(posedge clk);
        test_count = test_count + 1;
        if (result == 32'h7FFF_FFFF) begin
            pass_count = pass_count + 1;
            $display("PASS [div_by_zero] result=%h (saturated to max)", result);
        end else begin
            fail_count = fail_count + 1;
            $display("FAIL [div_by_zero] result=%h expected=7FFFFFFF", result);
        end

        // ============================================================
        // MAX tests (op=4)
        // ============================================================
        $display("");
        $display("--- MAX Tests ---");
        run_test(3'd4, 16'd5, 16'd3, 32'd5, "max_5_3");
        run_test(3'd4, 16'd3, 16'd5, 32'd5, "max_3_5");
        run_test(3'd4, 16'd7, 16'd7, 32'd7, "max_equal");

        // ============================================================
        // MIN tests (op=5)
        // ============================================================
        $display("");
        $display("--- MIN Tests ---");
        run_test(3'd5, 16'd5, 16'd3, 32'd3, "min_5_3");
        run_test(3'd5, 16'd3, 16'd5, 32'd3, "min_3_5");
        run_test(3'd5, 16'd7, 16'd7, 32'd7, "min_equal");

        // ============================================================
        // NEG tests (op=6)
        // ============================================================
        $display("");
        $display("--- NEG Tests ---");
        run_test(3'd6, 16'd5, 16'd0, 32'hFFFFFFFB, "neg_positive");
        run_test(3'd6, 16'd0, 16'd0, 32'd0, "neg_zero");

        // NEG of 0x8000 should saturate to 0x7FFF
        @(posedge clk);
        op_select <= 3'd6;
        a <= 16'h8000;
        b <= 16'd0;
        @(posedge clk);
        @(posedge clk);
        @(posedge clk);
        test_count = test_count + 1;
        if (result == 32'h0000_7FFF) begin
            pass_count = pass_count + 1;
            $display("PASS [neg_saturate] result=%h (saturated)", result);
        end else begin
            fail_count = fail_count + 1;
            $display("FAIL [neg_saturate] result=%h expected=00007FFF", result);
        end

        // ============================================================
        // ABS tests (op=7)
        // ============================================================
        $display("");
        $display("--- ABS Tests ---");
        run_test(3'd7, 16'd5, 16'd0, 32'd5, "abs_positive");
        run_test(3'd7, 16'hFFFB, 16'd0, 32'd5, "abs_negative");  // -5 -> 5
        run_test(3'd7, 16'd0, 16'd0, 32'd0, "abs_zero");

        // ABS of 0x8000 should saturate to 0x7FFF
        @(posedge clk);
        op_select <= 3'd7;
        a <= 16'h8000;
        b <= 16'd0;
        @(posedge clk);
        @(posedge clk);
        @(posedge clk);
        test_count = test_count + 1;
        if (result == 32'h0000_7FFF) begin
            pass_count = pass_count + 1;
            $display("PASS [abs_saturate] result=%h (saturated)", result);
        end else begin
            fail_count = fail_count + 1;
            $display("FAIL [abs_saturate] result=%h expected=00007FFF", result);
        end

        // ============================================================
        // Summary
        // ============================================================
        $display("");
        $display("========================================");
        $display("Test Summary: %0d/%0d passed, %0d failed",
                 pass_count, test_count, fail_count);
        $display("========================================");

        if (fail_count == 0) begin
            $display("ALL TESTS PASSED");
        end else begin
            $display("*** FAILURES DETECTED ***");
        end

        $finish;
    end

    // ----------------------------------------------------------------
    // Optional: VCD dump for waveform viewing
    // ----------------------------------------------------------------
    initial begin
        $dumpfile("q16_lut_core_tb.vcd");
        $dumpvars(0, q16_lut_core_tb);
    end

endmodule

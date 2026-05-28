// ============================================================================
// braid_crossing_core_tb.v - Testbench for Braid Crossing Core
// Tests crossing residual computation with known strand inputs
// ============================================================================
`timescale 1ns / 1ps

module braid_crossing_core_tb;

    // ----------------------------------------------------------------
    // Signals
    // ----------------------------------------------------------------
    reg         clk;
    reg         rst;
    reg         start;
    reg  [127:0] strand_a;
    reg  [127:0] strand_b;
    wire [127:0] result;
    wire         done;

    // Test counters
    integer test_count;
    integer pass_count;
    integer fail_count;

    // Q16_16 helper: convert integer to Q16.16 (lower 16 bits used by core)
    function [15:0] q16;
        input [15:0] val;
        begin
            q16 = val;
        end
    endfunction

    // Pack 4 x 16-bit values into 128-bit strand
    function [127:0] make_strand;
        input [15:0] x0, y0, x1, y1;
        begin
            make_strand = {x0, y0, x1, y1};
        end
    endfunction

    // ----------------------------------------------------------------
    // DUT instantiation
    // ----------------------------------------------------------------
    braid_crossing_core dut (
        .clk(clk),
        .rst(rst),
        .start(start),
        .strand_a(strand_a),
        .strand_b(strand_b),
        .result(result),
        .done(done)
    );

    // ----------------------------------------------------------------
    // Clock generation: 27 MHz (Tang Nano 9K)
    // ----------------------------------------------------------------
    initial clk = 0;
    always #18.5 clk = ~clk;

    // ----------------------------------------------------------------
    // Task: run one crossing test
    // ----------------------------------------------------------------
    task run_crossing_test;
        input [127:0] sa;
        input [127:0] sb;
        input [31:0]  exp_residual;
        input [31:0]  tolerance;
        input [255:0] name;
        begin
            @(posedge clk);
            strand_a <= sa;
            strand_b <= sb;
            start <= 1'b1;

            @(posedge clk);
            start <= 1'b0;

            // Wait for done (pipeline is 4 stages, wait up to 10 cycles)
            repeat (10) begin
                @(posedge clk);
                if (done) begin
                    test_count = test_count + 1;

                    // Check crossing residual (upper 32 bits of result)
                    if ((result[127:96] >= exp_residual - tolerance) &&
                        (result[127:96] <= exp_residual + tolerance)) begin
                        pass_count = pass_count + 1;
                        $display("PASS [%0s] residual=%h expected=%h",
                                 name, result[127:96], exp_residual);
                    end else begin
                        fail_count = fail_count + 1;
                        $display("FAIL [%0s] residual=%h expected=%h (tol=%0d)",
                                 name, result[127:96], exp_residual, tolerance);
                    end
                    // Exit inner loop
                    repeat (2) @(posedge clk);
                end
            end
        end
    endtask

    // ----------------------------------------------------------------
    // Task: check done signal
    // ----------------------------------------------------------------
    task check_done;
        input [255:0] name;
        begin
            @(posedge clk);
            test_count = test_count + 1;
            if (done) begin
                pass_count = pass_count + 1;
                $display("PASS [%0s] done asserted", name);
            end else begin
                fail_count = fail_count + 1;
                $display("FAIL [%0s] done not asserted", name);
            end
        end
    endtask

    // ----------------------------------------------------------------
    // Main test sequence
    // ----------------------------------------------------------------
    initial begin
        $display("=== Braid Crossing Core Testbench ===");
        $display("Target: Tang Nano 9K (GW1NR-9)");
        $display("Pipeline: 4 stages");
        $display("");

        test_count = 0;
        pass_count = 0;
        fail_count = 0;

        // Reset
        rst = 1;
        start = 0;
        strand_a = 0;
        strand_b = 0;
        repeat (5) @(posedge clk);
        rst = 0;
        repeat (2) @(posedge clk);

        // ============================================================
        // Test 1: Perpendicular crossing
        // Strand A: horizontal (0,0) -> (4,0)
        // Strand B: vertical   (2,-2) -> (2,2)
        // Direction A: dx=4, dy=0
        // Direction B: dx=0, dy=4
        // Cross product: 4*4 - 0*0 = 16
        // ============================================================
        $display("--- Test 1: Perpendicular Crossing ---");
        run_crossing_test(
            make_strand(q16(16'd0), q16(16'd0), q16(16'd4), q16(16'd0)),
            make_strand(q16(16'd2), q16(16'hFFFE), q16(16'd2), q16(16'd2)),  // -2 in 16-bit
            32'd16, 32'd4, "perpendicular"
        );

        // ============================================================
        // Test 2: Parallel strands (no crossing)
        // Strand A: (0,0) -> (2,2)
        // Strand B: (1,0) -> (3,2)
        // Direction A: dx=2, dy=2
        // Direction B: dx=2, dy=2
        // Cross product: 2*2 - 2*2 = 0
        // ============================================================
        $display("");
        $display("--- Test 2: Parallel Strands ---");
        run_crossing_test(
            make_strand(q16(16'd0), q16(16'd0), q16(16'd2), q16(16'd2)),
            make_strand(q16(16'd1), q16(16'd0), q16(16'd3), q16(16'd2)),
            32'd0, 32'd4, "parallel"
        );

        // ============================================================
        // Test 3: Anti-parallel crossing (negative residual)
        // Strand A: (0,0) -> (4,0)  dx=4, dy=0
        // Strand B: (2,2) -> (2,-2) dx=0, dy=-4
        // Cross product: 4*(-4) - 0*0 = -16
        // ============================================================
        $display("");
        $display("--- Test 3: Anti-Parallel Crossing ---");
        run_crossing_test(
            make_strand(q16(16'd0), q16(16'd0), q16(16'd4), q16(16'd0)),
            make_strand(q16(16'd2), q16(16'd2), q16(16'd2), q16(16'hFFFC)),  // -4
            32'hFFFFFFF0, 32'd4, "anti_parallel"  // -16 in 32-bit
        );

        // ============================================================
        // Test 4: 45-degree crossing
        // Strand A: (0,0) -> (2,2)  dx=2, dy=2
        // Strand B: (0,2) -> (2,0)  dx=2, dy=-2
        // Cross product: 2*(-2) - 2*2 = -4 - 4 = -8
        // ============================================================
        $display("");
        $display("--- Test 4: 45-Degree Crossing ---");
        run_crossing_test(
            make_strand(q16(16'd0), q16(16'd0), q16(16'd2), q16(16'd2)),
            make_strand(q16(16'd0), q16(16'd2), q16(16'd2), q16(16'd0)),
            32'hFFFFFFF8, 32'd4, "45_degree"  // -8 in 32-bit
        );

        // ============================================================
        // Test 5: Zero-length strand (degenerate case)
        // Strand A: (1,1) -> (1,1)  dx=0, dy=0
        // Strand B: (0,0) -> (2,2)  dx=2, dy=2
        // Cross product: 0*2 - 0*2 = 0
        // ============================================================
        $display("");
        $display("--- Test 5: Zero-Length Strand ---");
        run_crossing_test(
            make_strand(q16(16'd1), q16(16'd1), q16(16'd1), q16(16'd1)),
            make_strand(q16(16'd0), q16(16'd0), q16(16'd2), q16(16'd2)),
            32'd0, 32'd4, "zero_length"
        );

        // ============================================================
        // Test 6: Large values
        // Strand A: (100,200) -> (300,400)  dx=200, dy=200
        // Strand B: (150,100) -> (250,500)  dx=100, dy=400
        // Cross product: 200*400 - 200*100 = 80000 - 20000 = 60000
        // ============================================================
        $display("");
        $display("--- Test 6: Large Values ---");
        run_crossing_test(
            make_strand(q16(16'd100), q16(16'd200), q16(16'd300), q16(16'd400)),
            make_strand(q16(16'd150), q16(16'd100), q16(16'd250), q16(16'd500)),
            32'd60000, 32'd100, "large_values"
        );

        // ============================================================
        // Test 7: Back-to-back operations (pipeline flush)
        // ============================================================
        $display("");
        $display("--- Test 7: Pipeline Flush ---");
        @(posedge clk);
        strand_a <= make_strand(q16(16'd0), q16(16'd0), q16(16'd1), q16(16'd0));
        strand_b <= make_strand(q16(16'd0), q16(16'd0), q16(16'd0), q16(16'd1));
        start <= 1'b1;
        @(posedge clk);
        start <= 1'b0;

        // Wait for first result
        repeat (6) @(posedge clk);
        test_count = test_count + 1;
        if (done) begin
            pass_count = pass_count + 1;
            $display("PASS [pipeline_flush_1] done asserted, residual=%h", result[127:96]);
        end else begin
            fail_count = fail_count + 1;
            $display("FAIL [pipeline_flush_1] done not asserted");
        end

        // Immediately start second operation
        @(posedge clk);
        strand_a <= make_strand(q16(16'd0), q16(16'd0), q16(16'd2), q16(16'd0));
        strand_b <= make_strand(q16(16'd0), q16(16'd0), q16(16'd0), q16(16'd3));
        start <= 1'b1;
        @(posedge clk);
        start <= 1'b0;

        repeat (6) @(posedge clk);
        test_count = test_count + 1;
        if (done) begin
            pass_count = pass_count + 1;
            $display("PASS [pipeline_flush_2] done asserted, residual=%h", result[127:96]);
        end else begin
            fail_count = fail_count + 1;
            $display("FAIL [pipeline_flush_2] done not asserted");
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
    // VCD dump
    // ----------------------------------------------------------------
    initial begin
        $dumpfile("braid_crossing_core_tb.vcd");
        $dumpvars(0, braid_crossing_core_tb);
    end

    // ----------------------------------------------------------------
    // Timeout watchdog
    // ----------------------------------------------------------------
    initial begin
        #1000000;  // 1ms timeout
        $display("TIMEOUT: Testbench did not complete");
        $finish;
    end

endmodule

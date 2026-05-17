`timescale 1ns / 1ps

module tb_pbacs_1bit_transport_core;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg clear = 1'b0;
    reg valid = 1'b0;
    reg [15:0] value_q16 = 16'd0;
    reg [15:0] threshold_q16 = 16'h8000;
    reg [7:0] mismatch_q8 = 8'd0;
    reg [3:0] mask_popcount = 4'd0;

    wire bit_out;
    wire signed [17:0] error_acc;
    wire [15:0] stress_acc;
    wire [1:0] cmyk_state;

    pbacs_1bit_transport_core dut (
        .clk(clk),
        .rst_n(rst_n),
        .clear(clear),
        .valid(valid),
        .value_q16(value_q16),
        .threshold_q16(threshold_q16),
        .mismatch_q8(mismatch_q8),
        .mask_popcount(mask_popcount),
        .bit_out(bit_out),
        .error_acc(error_acc),
        .stress_acc(stress_acc),
        .cmyk_state(cmyk_state)
    );

    always #5 clk = ~clk;

    task tick_valid;
        input [15:0] value;
        input [7:0] mismatch;
        input [3:0] popcount;
        begin
            value_q16 = value;
            mismatch_q8 = mismatch;
            mask_popcount = popcount;
            valid = 1'b1;
            @(posedge clk);
            #1;
            valid = 1'b0;
        end
    endtask

    initial begin
        repeat (2) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);

        tick_valid(16'h4000, 8'd0, 4'd0);
        if (bit_out !== 1'b0) begin
            $display("FAIL expected first low sample to emit 0");
            $finish;
        end

        tick_valid(16'hc000, 8'd0, 4'd0);
        if (bit_out !== 1'b1) begin
            $display("FAIL expected accumulated high sample to emit 1");
            $finish;
        end

        tick_valid(16'hffff, 8'hff, 4'hf);
        tick_valid(16'hffff, 8'hff, 4'hf);
        if (stress_acc == 16'd0) begin
            $display("FAIL expected stress to accumulate");
            $finish;
        end

        clear = 1'b1;
        @(posedge clk);
        #1;
        clear = 1'b0;
        if (error_acc !== 18'sd0 || stress_acc !== 16'd0 || cmyk_state !== 2'b00) begin
            $display("FAIL expected clear to reset PBACS state");
            $finish;
        end

        $display("PASS pbacs_1bit_transport_core");
        $finish;
    end
endmodule

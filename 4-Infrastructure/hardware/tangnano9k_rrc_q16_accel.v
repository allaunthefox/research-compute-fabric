// Tang Nano 9K Rainbow Raccoon Q16.16 accelerator surface.
//
// UART frame in:
//   A5 02 seq opcode len payload[len] crc8
//
// UART frame out:
//   A6 02 seq status len payload[len] crc8
//
// Opcodes:
//   0x20 = Q16.16 arithmetic shift/divide by 65536 witness
//          payload: int32 x
//          output:  opcode, int32 (x >>> 16), pass
//   0x21 = Q16.16 weighted-term bounded witness
//          payload: int32 E, int32 alpha
//          output:  opcode, int32 ((E * alpha) >>> 16), pass
//   0x22 = Q16.16 shift monotonicity witness
//          payload: int32 a, int32 b
//          output:  opcode, int32 (a >>> 16), int32 (b >>> 16), pass
//
// This is a receipt surface for Lean-proved fixed-point lowering lemmas. The
// host owns route selection and proof admission; the FPGA only accelerates the
// deterministic arithmetic witness lane.

`timescale 1ns / 1ps

module tangnano9k_rrc_q16_accel (
    input        clk,
    input        rst_n,
    input        uart_rx_pin,
    output       uart_tx_pin,
    output [5:0] led
);

    localparam MAGIC_IN  = 8'hA5;
    localparam MAGIC_OUT = 8'hA6;
    localparam VERSION   = 8'h02;

    localparam OP_SHIFT_DIV = 8'h20;
    localparam OP_WEIGHTED  = 8'h21;
    localparam OP_MONOTONE  = 8'h22;

    localparam RX_WAIT_MAGIC = 4'd0;
    localparam RX_VERSION    = 4'd1;
    localparam RX_SEQ        = 4'd2;
    localparam RX_OPCODE     = 4'd3;
    localparam RX_LEN        = 4'd4;
    localparam RX_PAYLOAD    = 4'd5;
    localparam RX_CRC        = 4'd6;
    localparam RX_PROCESS    = 4'd7;
    localparam TX_WAIT       = 4'd8;

    localparam RX_TIMEOUT_CYCLES = 19'd270000; // about 10 ms at 27 MHz

    wire [7:0] rx_data;
    wire       rx_done;
    reg  [7:0] tx_data;
    reg        tx_start;
    wire       tx_busy;

    reg [3:0] state;
    reg [7:0] seq;
    reg [7:0] opcode;
    reg [4:0] payload_len;
    reg [4:0] payload_index;
    reg [7:0] payload [0:15];
    reg [7:0] calc_crc;
    reg [7:0] frame_crc;
    reg [7:0] status;
    reg [7:0] resp_len;
    reg [7:0] resp_crc;
    reg [4:0] tx_index;
    reg [18:0] rx_idle_cycles;

    reg signed [31:0] result0;
    reg signed [31:0] result1;
    reg pass_bit;

    wire signed [31:0] payload_i32_0;
    wire signed [31:0] payload_i32_1;
    wire signed [63:0] weighted_product;
    wire signed [31:0] shifted0;
    wire signed [31:0] shifted1;
    wire signed [31:0] weighted_shifted;

    assign payload_i32_0 = {payload[0], payload[1], payload[2], payload[3]};
    assign payload_i32_1 = {payload[4], payload[5], payload[6], payload[7]};
    assign weighted_product = $signed(payload_i32_0) * $signed(payload_i32_1);
    assign shifted0 = payload_i32_0 >>> 16;
    assign shifted1 = payload_i32_1 >>> 16;
    assign weighted_shifted = weighted_product >>> 16;

    uart_rx rx_inst (
        .clk(clk),
        .rst_n(rst_n),
        .rx_pin(uart_rx_pin),
        .rx_data(rx_data),
        .rx_done(rx_done)
    );

    uart_tx tx_inst (
        .clk(clk),
        .rst_n(rst_n),
        .tx_start(tx_start),
        .tx_data(tx_data),
        .uart_tx(uart_tx_pin),
        .tx_busy(tx_busy)
    );

    function [7:0] crc8_next;
        input [7:0] crc;
        input [7:0] data;
        begin
            crc8_next = crc ^ data;
        end
    endfunction

    function [7:0] result0_byte;
        input [1:0] idx;
        begin
            case (idx)
                2'd0: result0_byte = result0[31:24];
                2'd1: result0_byte = result0[23:16];
                2'd2: result0_byte = result0[15:8];
                default: result0_byte = result0[7:0];
            endcase
        end
    endfunction

    function [7:0] result1_byte;
        input [1:0] idx;
        begin
            case (idx)
                2'd0: result1_byte = result1[31:24];
                2'd1: result1_byte = result1[23:16];
                2'd2: result1_byte = result1[15:8];
                default: result1_byte = result1[7:0];
            endcase
        end
    endfunction

    function [7:0] tx_byte_at;
        input [4:0] idx;
        begin
            case (idx)
                5'd0: tx_byte_at = MAGIC_OUT;
                5'd1: tx_byte_at = VERSION;
                5'd2: tx_byte_at = seq;
                5'd3: tx_byte_at = status;
                5'd4: tx_byte_at = resp_len;
                5'd5: tx_byte_at = opcode;
                5'd6: tx_byte_at = result0_byte(2'd0);
                5'd7: tx_byte_at = result0_byte(2'd1);
                5'd8: tx_byte_at = result0_byte(2'd2);
                5'd9: tx_byte_at = result0_byte(2'd3);
                5'd10: tx_byte_at = (resp_len == 8'd10) ? result1_byte(2'd0) : {7'd0, pass_bit};
                5'd11: tx_byte_at = (resp_len == 8'd10) ? result1_byte(2'd1) : resp_crc;
                5'd12: tx_byte_at = result1_byte(2'd2);
                5'd13: tx_byte_at = result1_byte(2'd3);
                5'd14: tx_byte_at = {7'd0, pass_bit};
                5'd15: tx_byte_at = resp_crc;
                default: tx_byte_at = 8'h00;
            endcase
        end
    endfunction

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= RX_WAIT_MAGIC;
            seq <= 8'h00;
            opcode <= 8'h00;
            payload_len <= 5'd0;
            payload_index <= 5'd0;
            calc_crc <= 8'h00;
            frame_crc <= 8'h00;
            status <= 8'h00;
            resp_len <= 8'd0;
            resp_crc <= 8'h00;
            tx_index <= 5'd0;
            tx_data <= 8'h00;
            tx_start <= 1'b0;
            rx_idle_cycles <= 19'd0;
            result0 <= 32'sd0;
            result1 <= 32'sd0;
            pass_bit <= 1'b0;
            for (i = 0; i < 16; i = i + 1) begin
                payload[i] <= 8'h00;
            end
        end else begin
            tx_start <= 1'b0;

            if (rx_done || state == RX_WAIT_MAGIC || state == RX_PROCESS || state == TX_WAIT) begin
                rx_idle_cycles <= 19'd0;
            end else if (rx_idle_cycles >= RX_TIMEOUT_CYCLES) begin
                state <= RX_WAIT_MAGIC;
                calc_crc <= 8'h00;
                payload_index <= 5'd0;
                rx_idle_cycles <= 19'd0;
            end else begin
                rx_idle_cycles <= rx_idle_cycles + 19'd1;
            end

            if (rx_done && rx_data == MAGIC_IN && state != TX_WAIT) begin
                calc_crc <= rx_data;
                payload_index <= 5'd0;
                state <= RX_VERSION;
            end else case (state)
                RX_WAIT_MAGIC: begin
                    if (rx_done && rx_data == MAGIC_IN) begin
                        calc_crc <= rx_data;
                        state <= RX_VERSION;
                    end
                end

                RX_VERSION: begin
                    if (rx_done) begin
                        calc_crc <= crc8_next(calc_crc, rx_data);
                        state <= (rx_data == VERSION) ? RX_SEQ : RX_WAIT_MAGIC;
                    end
                end

                RX_SEQ: begin
                    if (rx_done) begin
                        seq <= rx_data;
                        calc_crc <= crc8_next(calc_crc, rx_data);
                        state <= RX_OPCODE;
                    end
                end

                RX_OPCODE: begin
                    if (rx_done) begin
                        opcode <= rx_data;
                        calc_crc <= crc8_next(calc_crc, rx_data);
                        state <= RX_LEN;
                    end
                end

                RX_LEN: begin
                    if (rx_done) begin
                        payload_len <= (rx_data[4:0] > 5'd16) ? 5'd16 : rx_data[4:0];
                        payload_index <= 5'd0;
                        calc_crc <= crc8_next(calc_crc, rx_data);
                        state <= (rx_data == 8'd0) ? RX_CRC : RX_PAYLOAD;
                    end
                end

                RX_PAYLOAD: begin
                    if (rx_done) begin
                        payload[payload_index] <= rx_data;
                        calc_crc <= crc8_next(calc_crc, rx_data);
                        if (payload_index + 5'd1 >= payload_len) begin
                            state <= RX_CRC;
                        end
                        payload_index <= payload_index + 5'd1;
                    end
                end

                RX_CRC: begin
                    if (rx_done) begin
                        frame_crc <= rx_data;
                        if (rx_data != calc_crc) begin
                            status <= 8'hE1;
                        end else begin
                            status <= 8'h00;
                        end
                        state <= RX_PROCESS;
                    end
                end

                RX_PROCESS: begin
                    result0 <= 32'sd0;
                    result1 <= 32'sd0;
                    pass_bit <= 1'b0;
                    resp_len <= 8'd1;

                    if (status == 8'hE1) begin
                        resp_len <= 8'd1;
                        resp_crc <= MAGIC_OUT ^ VERSION ^ seq ^ status ^ 8'd1 ^ opcode;
                    end else if (opcode == OP_SHIFT_DIV && payload_len == 5'd4) begin
                        result0 <= shifted0;
                        pass_bit <= 1'b1;
                        resp_len <= 8'd6;
                        resp_crc <= MAGIC_OUT ^ VERSION ^ seq ^ 8'h00 ^ 8'd6 ^ opcode ^
                                    shifted0[31:24] ^ shifted0[23:16] ^
                                    shifted0[15:8] ^ shifted0[7:0] ^ 8'h01;
                    end else if (opcode == OP_WEIGHTED && payload_len == 5'd8) begin
                        result0 <= weighted_shifted;
                        pass_bit <= (payload_i32_0 >= 32'sd0) &&
                                    (payload_i32_1 >= 32'sd0) &&
                                    (payload_i32_1 <= 32'sd65536) &&
                                    (weighted_shifted <= payload_i32_0);
                        resp_len <= 8'd6;
                        resp_crc <= MAGIC_OUT ^ VERSION ^ seq ^ 8'h00 ^ 8'd6 ^ opcode ^
                                    weighted_shifted[31:24] ^ weighted_shifted[23:16] ^
                                    weighted_shifted[15:8] ^ weighted_shifted[7:0] ^
                                    {7'd0, ((payload_i32_0 >= 32'sd0) &&
                                           (payload_i32_1 >= 32'sd0) &&
                                           (payload_i32_1 <= 32'sd65536) &&
                                           (weighted_shifted <= payload_i32_0))};
                    end else if (opcode == OP_MONOTONE && payload_len == 5'd8) begin
                        result0 <= shifted0;
                        result1 <= shifted1;
                        pass_bit <= (payload_i32_0 <= payload_i32_1) && (shifted0 <= shifted1);
                        resp_len <= 8'd10;
                        resp_crc <= MAGIC_OUT ^ VERSION ^ seq ^ 8'h00 ^ 8'd10 ^ opcode ^
                                    shifted0[31:24] ^ shifted0[23:16] ^
                                    shifted0[15:8] ^ shifted0[7:0] ^
                                    shifted1[31:24] ^ shifted1[23:16] ^
                                    shifted1[15:8] ^ shifted1[7:0] ^
                                    {7'd0, ((payload_i32_0 <= payload_i32_1) && (shifted0 <= shifted1))};
                    end else begin
                        status <= 8'hE2;
                        resp_len <= 8'd1;
                        resp_crc <= MAGIC_OUT ^ VERSION ^ seq ^ 8'hE2 ^ 8'd1 ^ opcode;
                    end

                    tx_index <= 5'd0;
                    state <= TX_WAIT;
                end

                TX_WAIT: begin
                    if (!tx_busy && !tx_start) begin
                        tx_data <= tx_byte_at(tx_index);
                        tx_start <= 1'b1;
                        if ((resp_len == 8'd10 && tx_index == 5'd15) ||
                            (resp_len == 8'd6 && tx_index == 5'd11) ||
                            (resp_len == 8'd1 && tx_index == 5'd6)) begin
                            state <= RX_WAIT_MAGIC;
                        end else begin
                            tx_index <= tx_index + 5'd1;
                        end
                    end
                end

                default: state <= RX_WAIT_MAGIC;
            endcase
        end
    end

    wire [5:0] led_state;
    assign led_state = {status[1:0], opcode[3:0]};
    assign led = ~led_state;

endmodule

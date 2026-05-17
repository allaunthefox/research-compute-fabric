// Tang Nano 9K Hutter/metaprobe symbol surface.
//
// UART frame in:
//   A5 01 seq opcode len payload[len] crc8
//
// Current opcode:
//   0x10 = substitute metaprobe/Hutter text token bytes through a tiny LUT.
//
// UART frame out:
//   A6 01 seq status 06 opcode hash_hi hash_lo mapped literal crc8
//
// LED reservoir address surface:
//   logical LED address = {PBACS/CMYK route state, mapped_count[3:0]}
//   physical LEDs are active low, so pins drive ~logical_address.
//   This gives the loaded FPGA a tiny visible reservoir/state address bus:
//     bits [5:4] = PBACS/CMYK route state
//     bits [3:0] = mapped-symbol bucket
//
// The response is a receipt, not a compressed artifact. The host keeps the full
// codec and verifies this hardware witness against software substitution.

`timescale 1ns / 1ps

module tangnano9k_hutter_symbol_surface (
    input        clk,         // 27 MHz
    input        rst_n,       // Reset button, active low
    input        uart_rx_pin,
    output       uart_tx_pin,
    output [5:0] led          // active low
);

    localparam MAGIC_IN  = 8'hA5;
    localparam MAGIC_OUT = 8'hA6;
    localparam VERSION   = 8'h01;
    localparam OP_SUBST  = 8'h10;

    localparam RX_WAIT_MAGIC = 4'd0;
    localparam RX_VERSION    = 4'd1;
    localparam RX_SEQ        = 4'd2;
    localparam RX_OPCODE     = 4'd3;
    localparam RX_LEN        = 4'd4;
    localparam RX_PAYLOAD    = 4'd5;
    localparam RX_CRC        = 4'd6;
    localparam RX_PROCESS    = 4'd7;
    localparam TX_LOAD       = 4'd8;
    localparam TX_WAIT       = 4'd9;

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
    reg [7:0] frame_crc;
    reg [7:0] calc_crc;

    reg [15:0] rolling_hash;
    reg [7:0] mapped_count;
    reg [7:0] literal_count;
    reg [7:0] status;
    reg [3:0] tx_index;
    reg [7:0] tx_crc;
    reg [7:0] last_token;
    reg [18:0] rx_idle_cycles;

    localparam RX_TIMEOUT_CYCLES = 19'd270000; // ~10 ms at 27 MHz

    wire [3:0] subst_code;
    wire       subst_hit;
    wire       pbacs_valid;
    wire [15:0] pbacs_value_q16;
    wire [1:0] pbacs_cmyk_state;
    wire pbacs_bit_out;
    wire signed [17:0] pbacs_error_acc;
    wire [15:0] pbacs_stress_acc;

    assign pbacs_valid = (state == RX_PROCESS) && (payload_index < payload_len);
    assign pbacs_value_q16 = {subst_hit, subst_code, 11'd0};

    hutter_symbol_substitution_core subst (
        .symbol(payload[payload_index]),
        .code(subst_code),
        .hit(subst_hit)
    );

    pbacs_1bit_transport_core pbacs (
        .clk(clk),
        .rst_n(rst_n),
        .clear(state == RX_CRC && rx_done),
        .valid(pbacs_valid),
        .value_q16(pbacs_value_q16),
        .threshold_q16(16'h8000),
        .mismatch_q8({literal_count[3:0], mapped_count[3:0]}),
        .mask_popcount({3'd0, subst_hit}),
        .bit_out(pbacs_bit_out),
        .error_acc(pbacs_error_acc),
        .stress_acc(pbacs_stress_acc),
        .cmyk_state(pbacs_cmyk_state)
    );

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
            // Cheap XOR checksum for Surface-0. Replace with polynomial CRC
            // when the frame contract stabilizes.
            crc8_next = crc ^ data;
        end
    endfunction

    function [7:0] tx_byte_at;
        input [3:0] idx;
        begin
            case (idx)
                4'd0: tx_byte_at = MAGIC_OUT;
                4'd1: tx_byte_at = VERSION;
                4'd2: tx_byte_at = seq;
                4'd3: tx_byte_at = status;
                4'd4: tx_byte_at = 8'd6;
                4'd5: tx_byte_at = opcode;
                4'd6: tx_byte_at = rolling_hash[15:8];
                4'd7: tx_byte_at = rolling_hash[7:0];
                4'd8: tx_byte_at = mapped_count;
                4'd9: tx_byte_at = literal_count;
                4'd10: tx_byte_at = tx_crc;
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
            frame_crc <= 8'h00;
            calc_crc <= 8'h00;
            rolling_hash <= 16'hACE1;
            mapped_count <= 8'd0;
            literal_count <= 8'd0;
            status <= 8'h00;
            tx_index <= 4'd0;
            tx_crc <= 8'h00;
            tx_data <= 8'h00;
            tx_start <= 1'b0;
            last_token <= 8'h00;
            rx_idle_cycles <= 19'd0;
            for (i = 0; i < 16; i = i + 1) begin
                payload[i] <= 8'h00;
            end
        end else begin
            tx_start <= 1'b0;

            if (rx_done || state == RX_WAIT_MAGIC || state == RX_PROCESS ||
                state == TX_LOAD || state == TX_WAIT) begin
                rx_idle_cycles <= 19'd0;
            end else if (rx_idle_cycles >= RX_TIMEOUT_CYCLES) begin
                state <= RX_WAIT_MAGIC;
                calc_crc <= 8'h00;
                payload_index <= 5'd0;
                rx_idle_cycles <= 19'd0;
            end else begin
                rx_idle_cycles <= rx_idle_cycles + 19'd1;
            end

            // A fresh magic byte can resynchronize the framed stream from any
            // receive state. Surface-0 payloads do not use 0xA5.
            if (rx_done && rx_data == MAGIC_IN && state != TX_LOAD && state != TX_WAIT) begin
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
                        last_token <= rx_data;
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
                        payload_index <= 5'd0;
                        rolling_hash <= 16'hACE1;
                        mapped_count <= 8'd0;
                        literal_count <= 8'd0;
                        if (rx_data != calc_crc) begin
                            status <= 8'hE1;
                            state <= TX_LOAD;
                        end else if (opcode != OP_SUBST) begin
                            status <= 8'hE2;
                            state <= TX_LOAD;
                        end else begin
                            status <= 8'h00;
                            state <= RX_PROCESS;
                        end
                    end
                end

                RX_PROCESS: begin
                    if (payload_index < payload_len) begin
                        rolling_hash <= {rolling_hash[14:0], rolling_hash[15]} ^
                                        {11'd0, subst_hit, subst_code};
                        if (subst_hit) begin
                            mapped_count <= mapped_count + 8'd1;
                        end else begin
                            literal_count <= literal_count + 8'd1;
                        end
                        payload_index <= payload_index + 5'd1;
                    end else begin
                        state <= TX_LOAD;
                    end
                end

                TX_LOAD: begin
                    tx_index <= 4'd0;
                    tx_crc <= MAGIC_OUT ^ VERSION ^ seq ^ status ^ 8'd6 ^ opcode ^
                              rolling_hash[15:8] ^ rolling_hash[7:0] ^
                              mapped_count ^ literal_count;
                    state <= TX_WAIT;
                end

                TX_WAIT: begin
                    if (!tx_busy && !tx_start) begin
                        tx_data <= tx_byte_at(tx_index);
                        tx_start <= 1'b1;
                        if (tx_index == 4'd10) begin
                            state <= RX_WAIT_MAGIC;
                        end else begin
                            tx_index <= tx_index + 4'd1;
                        end
                    end
                end

                default: state <= RX_WAIT_MAGIC;
            endcase
        end
    end

    wire [5:0] led_reservoir_address;
    assign led_reservoir_address = {pbacs_cmyk_state, mapped_count[3:0]};
    assign led = ~led_reservoir_address;

endmodule

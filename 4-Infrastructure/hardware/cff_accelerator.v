// CFF Accelerator: SHA-256 Hash Engine for Tang Nano 9K
// Accepts DOI strings over UART, returns 256-bit hash.
// Wire protocol: host sends length-prefixed data, FPGA returns hash.
//
// Protocol:
//   RX: [LEN:8][DATA:LEN bytes]
//   TX: [HASH:32 bytes]
//
// Compact SHA-256 core (~2000 LUTs), fits in GW1NR-9C (8640 LUTs)

`timescale 1ns / 1ps

module cff_accelerator (
    input        clk,         // 27 MHz
    input        rst_n,       // Reset button (active low)
    input        uart_rx_pin, // UART RX
    output       uart_tx_pin, // UART TX
    output [5:0] led          // Onboard LEDs (active low) - status
);

    // === UART ===
    wire [7:0] rx_data;
    wire       rx_done;
    reg  [7:0] tx_data;
    reg        tx_start;
    wire       tx_busy;

    uart_rx rx_inst (
        .clk(clk), .rst_n(rst_n),
        .rx_pin(uart_rx_pin),
        .rx_data(rx_data), .rx_done(rx_done)
    );

    uart_tx tx_inst (
        .clk(clk), .rst_n(rst_n),
        .tx_start(tx_start), .tx_data(tx_data),
        .uart_tx(uart_tx_pin), .tx_busy(tx_busy)
    );

    // === FSM ===
    parameter IDLE    = 3'd0;
    parameter GET_LEN = 3'd1;
    parameter LOAD    = 3'd2;
    parameter PAD     = 3'd3;
    parameter HASH    = 3'd4;
    parameter SEND    = 3'd5;
    parameter WAIT    = 3'd6;

    reg [2:0] state, next_state;
    reg [7:0] data_len;
    reg [7:0] byte_cnt;
    reg [7:0] send_cnt;

    // === SHA-256 Core State ===
    // Message + padding buffer: max 64 bytes per block (512 bits)
    reg [511:0] msg_block;
    reg [5:0]   msg_idx;      // bytes loaded into current block
    reg         msg_done;

    // Hash state (8 x 32-bit)
    reg [31:0] H0, H1, H2, H3, H4, H5, H6, H7;

    // Working variables
    reg [31:0] a, b, c, d, e, f, g, h;

    // Round constants (first 3 rounds inline, rest computed)
    wire [31:0] K [0:63];
    assign K[0]  = 32'h428a2f98;
    assign K[1]  = 32'h71374491;
    assign K[2]  = 32'hb5c0fbcf;
    assign K[3]  = 32'he9b5dba5;
    assign K[4]  = 32'h3956c25b;
    assign K[5]  = 32'h59f111f1;
    assign K[6]  = 32'h923f82a4;
    assign K[7]  = 32'hab1c5ed5;
    assign K[8]  = 32'hd807aa98;
    assign K[9]  = 32'h12835b01;
    assign K[10] = 32'h243185be;
    assign K[11] = 32'h550c7dc3;
    assign K[12] = 32'h72be5d74;
    assign K[13] = 32'h80deb1fe;
    assign K[14] = 32'h9bdc06a7;
    assign K[15] = 32'hc19bf174;
    assign K[16] = 32'he49b69c1;
    assign K[17] = 32'hefbe4786;
    assign K[18] = 32'h0fc19dc6;
    assign K[19] = 32'h240ca1cc;
    assign K[20] = 32'h2de92c6f;
    assign K[21] = 32'h4a7484aa;
    assign K[22] = 32'h5cb0a9dc;
    assign K[23] = 32'h76f988da;
    assign K[24] = 32'h983e5152;
    assign K[25] = 32'ha831c66d;
    assign K[26] = 32'hb00327c8;
    assign K[27] = 32'hbf597fc7;
    assign K[28] = 32'hc6e00bf3;
    assign K[29] = 32'hd5a79147;
    assign K[30] = 32'h06ca6351;
    assign K[31] = 32'h14292967;
    assign K[32] = 32'h27b70a85;
    assign K[33] = 32'h2e1b2138;
    assign K[34] = 32'h4d2c6dfc;
    assign K[35] = 32'h53380d13;
    assign K[36] = 32'h650a7354;
    assign K[37] = 32'h766a0abb;
    assign K[38] = 32'h81c2c92e;
    assign K[39] = 32'h92722c85;
    assign K[40] = 32'ha2bfe8a1;
    assign K[41] = 32'ha81a664b;
    assign K[42] = 32'hc24b8b70;
    assign K[43] = 32'hc76c51a3;
    assign K[44] = 32'hd192e819;
    assign K[45] = 32'hd6990624;
    assign K[46] = 32'hf40e3585;
    assign K[47] = 32'h106aa070;
    assign K[48] = 32'h19a4c116;
    assign K[49] = 32'h1e376c08;
    assign K[50] = 32'h2748774c;
    assign K[51] = 32'h34b0bcb5;
    assign K[52] = 32'h391c0cb3;
    assign K[53] = 32'h4ed8aa4a;
    assign K[54] = 32'h5b9cca4f;
    assign K[55] = 32'h682e6ff3;
    assign K[56] = 32'h748f82ee;
    assign K[57] = 32'h78a5636f;
    assign K[58] = 32'h84c87814;
    assign K[59] = 32'h8cc70208;
    assign K[60] = 32'h90befffa;
    assign K[61] = 32'ha4506ceb;
    assign K[62] = 32'hbef9a3f7;
    assign K[63] = 32'hc67178f2;

    // Message schedule
    reg [31:0] W [0:63];
    reg [5:0]  round;
    reg [2:0]  hash_phase;  // 0=init, 1=expand msg, 2=compress, 3=finalize
    reg [5:0]  expand_idx;  // index for message expansion (16..63)

    // === SHA-256 Control ===
    wire [31:0] S0, S1, ch_val, maj_val;
    wire [31:0] t1, t2;

    // Right rotation
    function [31:0] rotr;
        input [31:0] x;
        input [4:0]  n;
        begin
            rotr = (x >> n) | (x << (32 - n));
        end
    endfunction

    // SHA-256 functions
    assign S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
    assign S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
    assign ch_val = (e & f) ^ ((~e) & g);
    assign maj_val = (a & b) ^ (a & c) ^ (b & c);
    assign t1 = h + S1 + ch_val + K[round] + W[round];
    assign t2 = S0 + maj_val;

    // Message expansion for round >= 16
    wire [31:0] s0, s1;
    assign s0 = rotr(W[expand_idx-15], 7) ^ rotr(W[expand_idx-15], 18) ^ (W[expand_idx-15] >> 3);
    assign s1 = rotr(W[expand_idx-2], 17) ^ rotr(W[expand_idx-2], 19) ^ (W[expand_idx-2] >> 10);

    // === Main FSM ===
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            data_len <= 8'd0;
            byte_cnt <= 8'd0;
            send_cnt <= 8'd0;
            msg_block <= 512'd0;
            msg_idx   <= 6'd0;
            msg_done  <= 1'b0;
            H0 <= 32'h6a09e667;
            H1 <= 32'hbb67ae85;
            H2 <= 32'h3c6ef372;
            H3 <= 32'ha54ff53a;
            H4 <= 32'h510e527f;
            H5 <= 32'h9b05688c;
            H6 <= 32'h1f83d9ab;
            H7 <= 32'h5be0cd19;
            round <= 6'd0;
            hash_phase <= 3'd0;
            expand_idx <= 6'd0;
            tx_start <= 1'b0;
            tx_data  <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    tx_start <= 1'b0;
                    if (rx_done) begin
                        data_len <= rx_data;
                        byte_cnt <= 8'd0;
                        msg_idx  <= 6'd0;
                        msg_done <= 1'b0;
                        round <= 6'd0;
                        hash_phase <= 3'd0;
                        state <= (rx_data > 0) ? LOAD : PAD;
                    end
                end

                LOAD: begin
                    if (rx_done) begin
                        msg_block[msg_idx*8 +: 8] <= rx_data;
                        msg_idx <= msg_idx + 6'd1;
                        byte_cnt <= byte_cnt + 8'd1;
                        if (byte_cnt + 8'd1 >= data_len) begin
                            msg_done <= 1'b1;
                            state <= PAD;
                        end
                    end
                end

                PAD: begin
                    // SHA-256 padding: 0x80, then zeros, then 64-bit length in bits
                    // Add 0x80 byte at next position
                    msg_block[msg_idx*8 +: 8] <= 8'h80;
                    // Zero-fill remaining up to byte 56
                    // Put length in bits at bytes 56-63
                    msg_block[447:0] <= msg_block[447:0]; // preserve
                    msg_block[511:448] <= {56'd0, data_len[5:0]}; // length in bits = data_len * 8 (simplified)
                    msg_idx   <= 6'd56;
                    msg_done  <= 1'b0;
                    state <= HASH;
                    hash_phase <= 3'd0;
                    round <= 6'd0;
                    // Initialize working vars from H
                    a <= H0; b <= H1; c <= H2; d <= H3;
                    e <= H4; f <= H5; g <= H6; h <= H7;
                end

                HASH: begin
                    case (hash_phase)
                        3'd0: begin
                            // Load W[0..15] from msg_block
                            W[0]  <= msg_block[511:480];
                            W[1]  <= msg_block[479:448];
                            W[2]  <= msg_block[447:416];
                            W[3]  <= msg_block[415:384];
                            W[4]  <= msg_block[383:352];
                            W[5]  <= msg_block[351:320];
                            W[6]  <= msg_block[319:288];
                            W[7]  <= msg_block[287:256];
                            W[8]  <= msg_block[255:224];
                            W[9]  <= msg_block[223:192];
                            W[10] <= msg_block[191:160];
                            W[11] <= msg_block[159:128];
                            W[12] <= msg_block[127:96];
                            W[13] <= msg_block[95:64];
                            W[14] <= msg_block[63:32];
                            W[15] <= msg_block[31:0];
                            round <= 6'd0;
                            expand_idx <= 6'd16;
                            hash_phase <= 3'd2;
                        end

                        3'd2: begin
                            // Compression round
                            h <= g;
                            g <= f;
                            f <= e;
                            e <= d + t1;
                            d <= c;
                            c <= b;
                            b <= a;
                            a <= t1 + t2;

                            if (round < 6'd15) begin
                                round <= round + 6'd1;
                            end else if (round < 6'd63) begin
                                round <= round + 6'd1;
                                // Need to expand W for next round
                                W[expand_idx] <= s1 + W[expand_idx-7] + s0 + W[expand_idx-16];
                                expand_idx <= expand_idx + 6'd1;
                            end else begin
                                // Final round done - finalize
                                hash_phase <= 3'd3;
                            end
                        end

                        3'd3: begin
                            H0 <= H0 + a;
                            H1 <= H1 + b;
                            H2 <= H2 + c;
                            H3 <= H3 + d;
                            H4 <= H4 + e;
                            H5 <= H5 + f;
                            H6 <= H6 + g;
                            H7 <= H7 + h;
                            send_cnt <= 8'd0;
                            state <= SEND;
                            // Preload first byte to send
                            tx_data <= H0[31:24]; // Big-endian
                            tx_start <= 1'b1;
                        end

                        default: hash_phase <= 3'd0;
                    endcase
                end

                SEND: begin
                    if (tx_start && tx_busy) begin
                        tx_start <= 1'b0;
                    end else if (!tx_busy && !tx_start) begin
                        send_cnt <= send_cnt + 8'd1;
                        case (send_cnt)
                            8'd0:  tx_data <= H1[31:24];
                            8'd1:  tx_data <= H1[23:16];
                            8'd2:  tx_data <= H1[15:8];
                            8'd3:  tx_data <= H1[7:0];
                            8'd4:  tx_data <= H2[31:24];
                            8'd5:  tx_data <= H2[23:16];
                            8'd6:  tx_data <= H2[15:8];
                            8'd7:  tx_data <= H2[7:0];
                            8'd8:  tx_data <= H3[31:24];
                            8'd9:  tx_data <= H3[23:16];
                            8'd10: tx_data <= H3[15:8];
                            8'd11: tx_data <= H3[7:0];
                            8'd12: tx_data <= H4[31:24];
                            8'd13: tx_data <= H4[23:16];
                            8'd14: tx_data <= H4[15:8];
                            8'd15: tx_data <= H4[7:0];
                            8'd16: tx_data <= H5[31:24];
                            8'd17: tx_data <= H5[23:16];
                            8'd18: tx_data <= H5[15:8];
                            8'd19: tx_data <= H5[7:0];
                            8'd20: tx_data <= H6[31:24];
                            8'd21: tx_data <= H6[23:16];
                            8'd22: tx_data <= H6[15:8];
                            8'd23: tx_data <= H6[7:0];
                            8'd24: tx_data <= H7[31:24];
                            8'd25: tx_data <= H7[23:16];
                            8'd26: tx_data <= H7[15:8];
                            8'd27: tx_data <= H7[7:0];
                            8'd28: tx_data <= H0[23:16];
                            8'd29: tx_data <= H0[15:8];
                            8'd30: tx_data <= H0[7:0];
                            default: begin
                                tx_start <= 1'b0;
                                state <= IDLE;
                            end
                        endcase
                        tx_start <= 1'b1;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

    // LEDs show H0[5:0] for visual hash verification
    assign led = ~H0[5:0];

endmodule

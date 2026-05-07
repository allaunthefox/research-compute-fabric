// CFF Invariant Scanner for Tang Nano 9K
// Compact (~500 LUT) real-time constraint verifier over UART.
//
// Protocol:
//   Host sends:  [CMD:8][EQ_ID:16]
//   CMD = 0x01: Verify equation
//   CMD = 0x02: Get chiral state
//   CMD = 0x03: List admissible neighbors
//
//   FPGA responds: [STATUS:8][DATA:N bytes]
//
// Stores a small constraint routing table in BRAM.
// Used as real-time validation co-processor alongside GPU.

`timescale 1ns / 1ps

module cff_invariant_scanner (
    input        clk,          // 27 MHz
    input        rst_n,        // Reset button (active low)
    input        uart_rx_pin,  // UART RX
    output       uart_tx_pin,  // UART TX
    output [5:0] led           // Onboard LEDs (active low)
);

    // === UART ===
    wire [7:0] rx_data;
    wire       rx_done;
    reg  [7:0] tx_data;
    reg        tx_start;
    wire       tx_busy;

    uart_rx rx (
        .clk(clk), .rst_n(rst_n),
        .rx_pin(uart_rx_pin),
        .rx_data(rx_data), .rx_done(rx_done)
    );

    uart_tx tx (
        .clk(clk), .rst_n(rst_n),
        .tx_start(tx_start), .tx_data(tx_data),
        .uart_tx(uart_tx_pin), .tx_busy(tx_busy)
    );

    // === FSM ===
    localparam IDLE    = 3'd0;
    localparam GET_CMD = 3'd1;
    localparam GET_IDH = 3'd2;
    localparam GET_IDL = 3'd3;
    localparam LOOKUP  = 3'd4;
    localparam SEND    = 3'd5;

    reg [2:0] state;
    reg [7:0] cmd;
    reg [15:0] eq_id;
    reg [7:0] resp_data[0:4];   // up to 5 response bytes
    reg [3:0] resp_len;
    reg [3:0] resp_idx;
    reg [6:0] send_pause;       // delay between sends

    // === Simple Routing Table (BRAM-inferred) ===
    // 256 entries x 16-bit = 4 Kbit
    // Entry: [chiral_state:2][admissible:1][layer:2][strength:11]
    reg [15:0] routing_table[0:255];
    reg [7:0]   table_addr;
    wire [15:0] entry = routing_table[table_addr];

    // Pre-load a small constraint table on startup
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 256; i = i + 1)
                routing_table[i] <= 16'd0;
            // Load known extremophile/DNA bounds
            routing_table[0]   <= 16'h8001;  // Eq #1: layer1, admissible, achiral
            routing_table[1]   <= 16'h8002;  // Eq #2: layer1, admissible, achiral
            routing_table[38]  <= 16'h8002;  // Eq #38: Maxwell (verified)
            routing_table[68]  <= 16'hC003;  // Eq #68: chiral_scarred
            routing_table[232] <= 16'hB002;  // Eq #232: layer3 with mass bias
    end
    end

    // === FSM Logic ===
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            cmd <= 8'd0;
            eq_id <= 16'd0;
            tx_data <= 8'd0;
            tx_start <= 1'b0;
            resp_idx <= 4'd0;
            resp_len <= 4'd0;
            send_pause <= 7'd0;
        end else begin
            case (state)
                IDLE: begin
                    tx_start <= 1'b0;
                    if (rx_done) begin
                        cmd <= rx_data;
                        state <= GET_IDH;
                    end
                end

                GET_IDH: begin
                    if (rx_done) begin
                        eq_id[15:8] <= rx_data;
                        state <= GET_IDL;
                    end
                end

                GET_IDL: begin
                    if (rx_done) begin
                        eq_id[7:0] <= rx_data;
                        state <= LOOKUP;
                        table_addr <= rx_data; // Use low byte as addr (wrap)
                    end
                end

                LOOKUP: begin
                    // Build response based on cmd and entry
                    if (cmd == 8'h01) begin
                        resp_data[0] <= entry[15];
                        resp_data[1] <= entry[7:0];
                        resp_len <= 4'd2;
                    end else if (cmd == 8'h02) begin
                        resp_data[0] <= entry[15:14];  // chiral state
                        resp_data[1] <= entry[13];     // admissible
                        resp_len <= 4'd2;
                    end else if (cmd == 8'h03) begin
                        resp_data[0] <= eq_id[15:8];
                        resp_data[1] <= eq_id[7:0];
                        resp_data[2] <= entry[15:12];  // layer info
                        resp_data[3] <= entry[11:0] >> 4;
                        resp_len <= 4'd4;
                    end else begin
                        resp_data[0] <= 8'hFF;  // error
                        resp_data[1] <= cmd;
                        resp_len <= 4'd2;
                    end
                    resp_idx <= 4'd0;
                    state <= SEND;
                    tx_data <= resp_data[0];
                    tx_start <= 1'b1;
                end

                SEND: begin
                    if (tx_start && tx_busy) begin
                        tx_start <= 1'b0;
                        send_pause <= 7'd50;
                    end else if (!tx_start && !tx_busy) begin
                        if (send_pause > 0) begin
                            send_pause <= send_pause - 1'b1;
                        end else begin
                            resp_idx <= resp_idx + 4'd1;
                            if (resp_idx + 4'd1 < resp_len) begin
                                tx_data <= resp_data[resp_idx + 4'd1];
                                tx_start <= 1'b1;
                            end else begin
                                state <= IDLE;
                            end
                        end
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

    // LED status: shows last cmd and admissible bit
    assign led = ~{cmd[3:0], entry[13], 1'b0};

endmodule

//------------------------------------------------------------------------------
// 6502 OISC Blitter — 0D Scalar Proof Engine
// Target: Sipeed Tang Nano 9K (GW1NR-LV9QN88PC6/I5)
//
// One-Instruction-Set Computer with 6502 memory map.
// Single instruction: SUBLEQ (Subtract and Branch if Less-or-Equal).
//
// SUBLEQ src dst next:
//   MEM[dst] <= MEM[dst] - MEM[src]
//   if MEM[dst] <= 0 then PC <= next else PC <= PC + 6
//
// The "blitter" is built from SUBLEQ loops — block memory operations
// that iterate over memory, one cell at a time (0D scalar).
//
// Memory map:
//   $0000-$00FF  : Zero page (registers, blitter params)
//   $0100-$01FF  : Stack
//   $0200-$02FF  : S3C sqrt LUT (256 entries)
//   $0300-$03FF  : Blitter program segment
//   $0400-$7FFF  : General memory
//   $8000-$FFFF  : I/O mapped (LEDs, UART, I2S)
//------------------------------------------------------------------------------

module Blitter6502OISC (
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    output reg  busy,
    output reg  [5:0] led,
    output reg  uart_tx,
    // Memory interface (for external loading)
    input  wire mem_we,
    input  wire [15:0] mem_addr,
    input  wire [7:0]  mem_wdata,
    output wire [7:0]  mem_rdata
);

    //==========================================================================
    // Parameters
    //==========================================================================
    localparam MEM_SIZE = 65536;
    localparam MAX_CYCLES = 24'd1000000;  // ~37ms at 27MHz

    //==========================================================================
    // Memory (64K x 8-bit)
    // Implemented as block RAM (BSRAM) on GW1NR
    //==========================================================================
    reg [7:0] mem [0:MEM_SIZE-1];
    reg [15:0] mem_raddr;

    // Dual-port memory interface
    // Port A: CPU access (synchronous read, synchronous write)
    // Port B: External loader access
    always @(posedge clk) begin
        if (mem_we)
            mem[mem_addr] <= mem_wdata;
        mem_raddr <= mem_addr;
    end
    assign mem_rdata = mem[mem_raddr];

    //==========================================================================
    // CPU State
    //==========================================================================
    reg [15:0] pc;
    reg [7:0]  a_reg;     // Accumulator (mirrors $0000)
    reg [7:0]  x_reg;     // X register (mirrors $0001)
    reg [7:0]  y_reg;     // Y register (mirrors $0002)
    reg [23:0] cycle_cnt;
    reg        halted;

    // Instruction decode registers
    reg [15:0] src_addr;
    reg [15:0] dst_addr;
    reg [15:0] next_addr;
    reg [7:0]  src_val;
    reg [7:0]  dst_val;
    reg [7:0]  result;

    // State machine
    localparam ST_IDLE     = 4'd0;
    localparam ST_FETCH_S0 = 4'd1;
    localparam ST_FETCH_S1 = 4'd2;
    localparam ST_FETCH_D0 = 4'd3;
    localparam ST_FETCH_D1 = 4'd4;
    localparam ST_FETCH_N0 = 4'd5;
    localparam ST_FETCH_N1 = 4'd6;
    localparam ST_READ_SRC = 4'd7;
    localparam ST_READ_DST = 4'd8;
    localparam ST_EXECUTE  = 4'd9;
    localparam ST_WRITE    = 4'd10;
    localparam ST_BRANCH   = 4'd11;
    localparam ST_HALT     = 4'd12;

    reg [3:0] state;

    //==========================================================================
    // S3C sqrt LUT (preloaded at $0200-$02FF)
    // 256 entries: sqrtLUT8[n] = floor(sqrt(n))
    //==========================================================================
    initial begin
        // First 32 entries (rest loaded via external interface or defaults)
        mem[16'h0200] = 8'd0;  mem[16'h0201] = 8'd1;  mem[16'h0202] = 8'd1;  mem[16'h0203] = 8'd1;
        mem[16'h0204] = 8'd2;  mem[16'h0205] = 8'd2;  mem[16'h0206] = 8'd2;  mem[16'h0207] = 8'd2;
        mem[16'h0208] = 8'd2;  mem[16'h0209] = 8'd3;  mem[16'h020A] = 8'd3;  mem[16'h020B] = 8'd3;
        mem[16'h020C] = 8'd3;  mem[16'h020D] = 8'd3;  mem[16'h020E] = 8'd3;  mem[16'h020F] = 8'd3;
        mem[16'h0210] = 8'd4;  mem[16'h0211] = 8'd4;  mem[16'h0212] = 8'd4;  mem[16'h0213] = 8'd4;
        mem[16'h0214] = 8'd4;  mem[16'h0215] = 8'd4;  mem[16'h0216] = 8'd4;  mem[16'h0217] = 8'd4;
        mem[16'h0218] = 8'd4;  mem[16'h0219] = 8'd5;  mem[16'h021A] = 8'd5;  mem[16'h021B] = 8'd5;
        mem[16'h021C] = 8'd5;  mem[16'h021D] = 8'd5;  mem[16'h021E] = 8'd5;  mem[16'h021F] = 8'd5;
    end

    //==========================================================================
    // State Machine
    //==========================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc <= 16'h0300;  // Program starts at $0300
            a_reg <= 8'd0;
            x_reg <= 8'd0;
            y_reg <= 8'd0;
            cycle_cnt <= 24'd0;
            halted <= 1'b0;
            busy <= 1'b0;
            led <= 6'b000000;
            state <= ST_IDLE;
        end else begin
            case (state)
                ST_IDLE: begin
                    if (start) begin
                        busy <= 1'b1;
                        pc <= 16'h0300;
                        cycle_cnt <= 24'd0;
                        halted <= 1'b0;
                        state <= ST_FETCH_S0;
                    end
                end

                // Fetch src address (2 bytes, little-endian)
                ST_FETCH_S0: begin
                    src_addr[7:0] <= mem[pc];
                    state <= ST_FETCH_S1;
                end
                ST_FETCH_S1: begin
                    src_addr[15:8] <= mem[pc + 16'd1];
                    state <= ST_FETCH_D0;
                end

                // Fetch dst address
                ST_FETCH_D0: begin
                    dst_addr[7:0] <= mem[pc + 16'd2];
                    state <= ST_FETCH_D1;
                end
                ST_FETCH_D1: begin
                    dst_addr[15:8] <= mem[pc + 16'd3];
                    state <= ST_FETCH_N0;
                end

                // Fetch next address
                ST_FETCH_N0: begin
                    next_addr[7:0] <= mem[pc + 16'd4];
                    state <= ST_FETCH_N1;
                end
                ST_FETCH_N1: begin
                    next_addr[15:8] <= mem[pc + 16'd5];
                    state <= ST_READ_SRC;
                end

                // Read src and dst values
                ST_READ_SRC: begin
                    src_val <= mem[src_addr];
                    state <= ST_READ_DST;
                end
                ST_READ_DST: begin
                    dst_val <= mem[dst_addr];
                    state <= ST_EXECUTE;
                end

                // Execute: dst = dst - src (unsigned wrap, check signed <= 0)
                ST_EXECUTE: begin
                    result <= dst_val - src_val;
                    cycle_cnt <= cycle_cnt + 24'd1;
                    state <= ST_WRITE;
                end

                // Write result back
                ST_WRITE: begin
                    mem[dst_addr] <= result;
                    state <= ST_BRANCH;
                end

                // Branch if result <= 0 (signed interpretation)
                // In 8-bit signed: negative if MSB is 1, zero if all bits 0
                ST_BRANCH: begin
                    if (result[7] == 1'b1 || result == 8'd0) begin
                        // Result <= 0: branch to next_addr
                        pc <= next_addr;
                    end else begin
                        // Result > 0: fall through
                        pc <= pc + 16'd6;
                    end

                    // Check halt conditions
                    if (cycle_cnt >= MAX_CYCLES) begin
                        halted <= 1'b1;
                        busy <= 1'b0;
                        led <= 6'b111111;  // Error: cycle exhausted
                        state <= ST_HALT;
                    end else if (next_addr == 16'hFFFF) begin
                        // Halt opcode: next_addr = $FFFF
                        halted <= 1'b1;
                        busy <= 1'b0;
                        led <= {a_reg[1:0], x_reg[1:0], y_reg[1:0]};  // Success pattern
                        state <= ST_HALT;
                    end else begin
                        state <= ST_FETCH_S0;
                    end
                end

                ST_HALT: begin
                    // Remain halted until reset
                    halted <= 1'b1;
                    busy <= 1'b0;
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

    // UART telemetry: when halted, send a_reg as status byte
    reg [3:0] uart_bit_cnt;
    reg [15:0] uart_div;
    reg [9:0] uart_shift;
    reg uart_active;

    localparam UART_DIV = 16'd234;  // ~115200 baud at 27MHz

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            uart_tx <= 1'b1;
            uart_bit_cnt <= 4'd0;
            uart_div <= 16'd0;
            uart_shift <= 10'b0;
            uart_active <= 1'b0;
        end else begin
            if (halted && !uart_active) begin
                // Start UART transmission with a_reg as payload
                uart_shift <= {1'b1, a_reg, 1'b0};  // stop, data, start
                uart_active <= 1'b1;
                uart_bit_cnt <= 4'd0;
                uart_div <= 16'd0;
            end

            if (uart_active) begin
                if (uart_div >= UART_DIV) begin
                    uart_div <= 16'd0;
                    uart_tx <= uart_shift[0];
                    uart_shift <= {1'b1, uart_shift[9:1]};
                    uart_bit_cnt <= uart_bit_cnt + 4'd1;
                    if (uart_bit_cnt >= 4'd9) begin
                        uart_active <= 1'b0;
                        uart_tx <= 1'b1;
                    end
                end else begin
                    uart_div <= uart_div + 16'd1;
                end
            end
        end
    end

endmodule

//------------------------------------------------------------------------------
// Blitter Top-Level Wrapper with Clock/Reset
//------------------------------------------------------------------------------
module Blitter6502OISCTop (
    input  wire clk,      // 27 MHz oscillator
    input  wire rst_n,    // Active-low reset
    input  wire user_btn, // Button to start blitter
    output wire [5:0] led,
    output wire uart_tx
);

    wire btn_pressed = ~user_btn;
    reg btn_sync1, btn_sync2, btn_rise;
    reg [19:0] debounce_cnt;

    // Button debounce (same as SparkleTangNano9KTop)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            btn_sync1 <= 1'b0;
            btn_sync2 <= 1'b0;
            btn_rise <= 1'b0;
            debounce_cnt <= 20'd0;
        end else begin
            btn_sync1 <= btn_pressed;
            btn_sync2 <= btn_sync1;
            if (btn_sync2) begin
                if (debounce_cnt < 20'd500000)
                    debounce_cnt <= debounce_cnt + 20'd1;
            end else begin
                debounce_cnt <= 20'd0;
            end
            btn_rise <= (debounce_cnt >= 20'd500000) && !btn_sync2;
        end
    end

    // Blitter instance
    Blitter6502OISC blitter (
        .clk(clk),
        .rst_n(rst_n),
        .start(btn_rise),
        .busy(),
        .led(led),
        .uart_tx(uart_tx),
        .mem_we(1'b0),
        .mem_addr(16'd0),
        .mem_wdata(8'd0),
        .mem_rdata()
    );

endmodule

// Research Stack Top-Level Module
// Unified FPGA design for Tang Nano 9K (GW1NR-9C)
// Combines: Blitter6502OISC + Q16 LUT + Memory Map + Voltage Controller
//           + Scale Space BRAM + HiGHS Pivot Accelerator

`timescale 1ns / 1ps

module research_stack_top (
    input  wire       clk,       // 27 MHz oscillator (pin 52)
    input  wire       rst_n,     // Active-low reset (pin 4)
    input  wire       user_btn,  // Active-low user button (pin 3)
    output wire [5:0] led,       // Status LEDs (pins 10,11,13,14,15,16)
    output wire       uart_tx,   // UART TX (pin 17)
    input  wire       uart_rx    // UART RX (pin 18, unused)
);

    // ── Reset & Button ─────────────────────────────────────────────
    wire rst = ~rst_n;
    wire btn_pressed = ~user_btn;

    // Button debounce
    reg btn_d1, btn_d2;
    reg [19:0] debounce_cnt;
    reg btn_stable, btn_stable_prev;
    wire btn_rise;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            btn_d1 <= 0; btn_d2 <= 0;
            debounce_cnt <= 0;
            btn_stable <= 0; btn_stable_prev <= 0;
        end else begin
            btn_d1 <= btn_pressed;
            btn_d2 <= btn_d1;
            if (btn_d2) begin
                if (debounce_cnt < 20'd500000)
                    debounce_cnt <= debounce_cnt + 1;
            end else begin
                debounce_cnt <= 0;
            end
            btn_stable <= (debounce_cnt >= 20'd500000);
            btn_stable_prev <= btn_stable;
        end
    end
    assign btn_rise = btn_stable & ~btn_stable_prev;

    // ── Blitter CPU Signals ────────────────────────────────────────
    wire        cpu_busy;
    wire [5:0]  cpu_led;
    wire        cpu_uart_tx;
    wire [7:0]  cpu_rdata;
    wire [11:0] cpu_mem_addr;
    wire [7:0]  cpu_mem_wdata;
    wire        cpu_mem_we;

    // ── Memory Map Signals ─────────────────────────────────────────
    wire [7:0]  map_rdata;
    wire [31:0] map_q16_a;
    wire [31:0] map_q16_b;
    wire [2:0]  map_q16_op;
    wire        map_q16_trigger;
    wire [1:0]  map_voltage_mode;
    wire [1:0]  map_scale_select;
    wire [31:0] map_highs_pivot;
    wire        map_highs_trigger;

    // ── Q16 LUT Core Signals ───────────────────────────────────────
    wire [31:0] q16_result;
    wire        q16_valid;

    // ── Voltage Controller Signals ─────────────────────────────────
    wire [31:0] vctrl_dout;
    wire [1:0]  vctrl_voltage;
    wire [4:0]  vctrl_precision;
    wire        vctrl_active;

    // ── Scale Space BRAM Signals ───────────────────────────────────
    wire [31:0] ss_dout;
    wire [31:0] ss_kernel_sum;

    // ── HiGHS Pivot Signals ────────────────────────────────────────
    wire [31:0] highs_result;
    wire        highs_done;
    wire        highs_write_en;
    wire [5:0]  highs_write_idx;
    wire [31:0] highs_write_data;

    // ── Q16 LUT: use lower 16 bits of operands ────────────────────
    wire [15:0] q16_a_16 = map_q16_a[15:0];
    wire [15:0] q16_b_16 = map_q16_b[15:0];

    // ── Result mux: select result source based on address ──────────
    reg [31:0] result_latched;
    reg        q16_done_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result_latched <= 0;
            q16_done_reg <= 0;
        end else begin
            if (map_q16_trigger && !q16_busy) begin
                q16_done_reg <= 0;
            end
            if (q16_valid && !q16_done_reg) begin
                result_latched <= q16_result;
                q16_done_reg <= 1;
            end
        end
    end

    reg q16_busy;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) q16_busy <= 0;
        else if (map_q16_trigger) q16_busy <= 1;
        else if (q16_valid) q16_busy <= 0;
    end

    // ── Instantiations ─────────────────────────────────────────────

    // Blitter6502OISC CPU
    Blitter6502OISC cpu (
        .clk(clk),
        .rst_n(rst_n),
        .start(btn_rise),
        .busy(cpu_busy),
        .led(cpu_led),
        .uart_tx(cpu_uart_tx),
        .mem_we(1'b0),
        .mem_addr(16'd0),
        .mem_wdata(8'd0),
        .mem_rdata()
    );

    // Blitter Memory Map (8-bit CPU ↔ 32-bit peripherals)
    blitter_memory_map mem_map (
        .clk(clk),
        .rst_n(rst_n),
        .addr({4'b0, cpu_mem_addr}),  // pad 12-bit to 16-bit
        .wdata(cpu_mem_wdata),
        .we(cpu_mem_we),
        .rdata(map_rdata),
        .q16_a(map_q16_a),
        .q16_b(map_q16_b),
        .q16_op(map_q16_op),
        .q16_trigger(map_q16_trigger),
        .voltage_mode(map_voltage_mode),
        .scale_select(map_scale_select),
        .highs_pivot_element(map_highs_pivot),
        .highs_trigger(map_highs_trigger)
    );

    // Q16 LUT Core (8 operations, 2-stage pipeline)
    q16_lut_core q16 (
        .clk(clk),
        .rst(rst),
        .op_select(map_q16_op),
        .a(q16_a_16),
        .b(q16_b_16),
        .result(q16_result),
        .valid(q16_valid)
    );

    // Voltage Mode Controller (4 BRAM modes)
    voltage_mode_controller vctrl (
        .clk(clk),
        .rst_n(rst_n),
        .mode(map_voltage_mode),
        .bram_addr(q16_a_16[9:0]),
        .bram_din(map_q16_b),
        .bram_we(map_q16_trigger),
        .morphic_amp(map_highs_pivot),
        .bram_dout(vctrl_dout),
        .voltage_level(vctrl_voltage),
        .precision_bits(vctrl_precision),
        .active(vctrl_active)
    );

    // Scale Space BRAM (4 Gaussian kernel banks)
    scale_space_bram ss_bram (
        .clk(clk),
        .we(1'b0),
        .bank_select(map_scale_select),
        .addr(q16_a_16[7:0]),
        .din(32'd0),
        .dout(ss_dout),
        .kernel_sum(ss_kernel_sum)
    );

    // HiGHS Pivot Accelerator
    highs_pivot_accelerator highs (
        .clk(clk),
        .rst_n(rst_n),
        .start(map_highs_trigger),
        .pivot_element(map_highs_pivot),
        .column_in(map_q16_a),
        .column_idx(map_q16_b[5:0]),
        .result(highs_result),
        .done(highs_done),
        .write_en(highs_write_en),
        .write_idx(highs_write_idx),
        .write_data(highs_write_data)
    );

    // ── LED Output ─────────────────────────────────────────────────
    // led[5] = CPU busy
    // led[4] = Q16 done
    // led[3:2] = voltage mode
    // led[1:0] = scale select
    assign led = {cpu_busy, q16_done_reg, map_voltage_mode, map_scale_select};

    // ── UART ───────────────────────────────────────────────────────
    assign uart_tx = cpu_uart_tx;

endmodule

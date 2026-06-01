// Research Stack Top-Level Module
// Unified FPGA design for Tang Nano 9K (GW1NR-9C)
// Combines: Blitter6502OISC + Q16 LUT + Memory Map + Voltage Controller
//           + Scale Space BRAM + HiGHS Pivot Accelerator
//           + Fractal Box Counter + FD Selector
//           + Spatial Hash BRAM + Density Selector

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

    // Auto-start: trigger CPU 100ms after reset (no button needed)
    reg [31:0] auto_start_cnt;
    reg auto_start;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            auto_start_cnt <= 0;
            auto_start <= 0;
        end else if (!auto_start) begin
            if (auto_start_cnt >= 2700000) begin  // 100ms at 27MHz
                auto_start <= 1;
            end else begin
                auto_start_cnt <= auto_start_cnt + 1;
            end
        end
    end

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

    // ── Fractal Box Counter Signals ────────────────────────────────
    wire [31:0] frac_fd_q16;
    wire        frac_fd_valid;
    wire [1:0]  frac_voltage_mode;
    wire        frac_mode_valid;

    // ── Spatial Hash BRAM Signals ─────────────────────────────────
    wire [15:0] sh_cell_density;
    wire [15:0] sh_neighbor_density;
    wire        sh_query_done;

    // ── Spatial Hash Selector Signals ─────────────────────────────
    wire [1:0]  sh_voltage_mode;
    wire        sh_mode_valid;

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
        .start(auto_start),
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

    // FIX: Address-decoded trigger enables to prevent aliasing
    // Each module only fires when its specific address range is selected
    wire highs_addr_match = (cpu_mem_addr[11:8] == 4'h4);  // $04xx range
    wire frac_addr_match  = (cpu_mem_addr[11:8] == 4'h5);  // $05xx range
    wire spatial_addr_match = (cpu_mem_addr[11:8] == 4'h6); // $06xx range

    wire highs_trigger_gated  = map_highs_trigger & highs_addr_match;
    wire frac_trigger_gated   = map_highs_trigger & frac_addr_match;
    wire spatial_trigger_gated = map_highs_trigger & spatial_addr_match;

    // HiGHS Pivot Accelerator
    highs_pivot_accelerator highs (
        .clk(clk),
        .rst_n(rst_n),
        .start(highs_trigger_gated),
        .pivot_element(map_highs_pivot),
        .column_in(map_q16_a),
        .column_idx(map_q16_b[5:0]),
        .result(highs_result),
        .done(highs_done),
        .write_en(highs_write_en),
        .write_idx(highs_write_idx),
        .write_data(highs_write_data)
    );

    // Fractal Box Counter (DBC algorithm, 8-bit input, Q16_16 FD output)
    fractal_box_counter #(
        .MAX_SCALE(8),
        .DATA_WIDTH(8)
    ) frac_bc (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(map_q16_a[7:0]),
        .data_valid(frac_trigger_gated),
        .data_count(map_q16_b[15:0]),
        .fd_q16(frac_fd_q16),
        .fd_valid(frac_fd_valid)
    );

    // Fractal FD → Voltage Mode Selector
    // Maps fractal dimension to voltage mode:
    //   FD < 2.3 → STORE (0), FD < 2.6 → COMPUTE (1),
    //   FD < 2.9 → APPROX (2), FD >= 2.9 → MORPHIC (3)
    fractal_fd_selector frac_sel (
        .clk(clk),
        .rst_n(rst_n),
        .fd_q16(frac_fd_q16),
        .fd_valid(frac_fd_valid),
        .voltage_mode(frac_voltage_mode),
        .mode_valid(frac_mode_valid)
    );

    // Spatial Hash BRAM (16×16×16 grid, 8 particles/cell, dual-port)
    // Insert: particle position from map_q16_a[3:0], trigger from map_highs_trigger
    // Query:  query position from map_q16_b[3:0], trigger from map_q16_trigger
    spatial_hash_bram spatial_hash (
        .clk(clk),
        .rst_n(rst_n),
        .particle_x(map_q16_a[3:0]),
        .particle_y(map_q16_a[7:4]),
        .particle_z(map_q16_a[11:8]),
        .particle_valid(spatial_trigger_gated),
        .query_x(map_q16_b[3:0]),
        .query_y(map_q16_b[7:4]),
        .query_z(map_q16_b[11:8]),
        .query_valid(map_q16_trigger),
        .cell_density(sh_cell_density),
        .neighbor_density(sh_neighbor_density),
        .query_done(sh_query_done)
    );

    // Spatial Hash Density → Voltage Mode Selector
    // Maps particle density to voltage mode:
    //   density < 10 → STORE, < 50 → COMPUTE, < 200 → APPROX, >= 200 → MORPHIC
    spatial_hash_selector sh_sel (
        .clk(clk),
        .rst_n(rst_n),
        .density_in(sh_cell_density),
        .density_valid(sh_query_done),
        .voltage_mode(sh_voltage_mode),
        .mode_valid(sh_mode_valid)
    );

    // ── LED Output ─────────────────────────────────────────────────
    // When CPU is busy: show running pattern (blinking)
    // When CPU is halted: show cpu_led (register values from Blitter)
    // Otherwise: show status
    reg [24:0] heartbeat;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) heartbeat <= 0;
        else heartbeat <= heartbeat + 1;
    end
    assign led = cpu_busy ? {1'b1, heartbeat[23], 1'b0, heartbeat[21], 1'b0, heartbeat[19]}
                 : cpu_led;  // Blitter's register output after halt

    // ── UART ───────────────────────────────────────────────────────
    assign uart_tx = cpu_uart_tx;

endmodule

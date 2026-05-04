// Morphic Scalar FPGA Implementation - OPTIMIZED
// Derived from Lean: Semantics/MorphicScalar.lean
// Target: Gowin GW1NR-9 (Tang Nano 9K)
// Q16.16 fixed-point arithmetic with aggressive optimizations
// Implements quantum-inspired computational stem cell

`timescale 1ns / 1ps

// ═══════════════════════════════════════════════════════════════════════════
// Scalar State Encoding (4-bit state ID - minimal encoding)
// ═══════════════════════════════════════════════════════════════════════════
localparam STATE_SUPERPOSED           = 4'd0;
localparam STATE_SCOUTING             = 4'd1;
localparam STATE_MEASURE_LOCAL_NEED   = 4'd2;
localparam STATE_COLLAPSED_PROFILE     = 4'd3;
localparam STATE_EXECUTE              = 4'd4;
localparam STATE_RECEIPT              = 4'd5;
localparam STATE_AMPLITUDE_UPDATE     = 4'd6;
localparam STATE_QUERY_COLLECTIVE     = 4'd7;
localparam STATE_COLLECTIVE_RESPONSE  = 4'd8;
localparam STATE_QUERY_LLM            = 4'd9;
localparam STATE_DIRECTED             = 4'd10;
localparam STATE_HOLD                 = 4'd11;
localparam STATE_OPERATOR_ALERT       = 4'd12;
localparam STATE_LOW_POWER_PASSIVE    = 4'd13;
localparam STATE_QUARANTINE           = 4'd14;
localparam STATE_MIGRATE              = 4'd15;

// ═══════════════════════════════════════════════════════════════════════════
// OPTIMIZED Q16.16 Fixed-Point Arithmetic
// ═══════════════════════════════════════════════════════════════════════════

// OPTIMIZATION: Use carry chain for addition (Lattice-specific)
module q16_16_add_opt (
    input  signed [31:0] a,
    input  signed [31:0] b,
    output signed [31:0] sum,
    output               overflow
);
    wire signed [32:0] ext = $signed({a[31], a}) + $signed({b[31], b});
    assign overflow = (a[31] == b[31]) && (ext[32] != a[31]);
    // OPTIMIZATION: Use ternary for mux, synthesis tool infers carry chain
    assign sum = overflow ? (a[31] ? 32'sh80000000 : 32'sh7FFFFFFF) : ext[31:0];
endmodule

// OPTIMIZATION: Use DSP slices if available, otherwise optimized logic
module q16_16_mul_opt (
    input  signed [31:0] a,
    input  signed [31:0] b,
    output signed [31:0] product
);
    // OPTIMIZATION: Direct assignment, synthesis infers DSP or optimized multiplier
    wire signed [63:0] full = $signed(a) * $signed(b);
    assign product = full[47:16];  // Q16.16 multiply: keep middle 32 bits
endmodule

// OPTIMIZATION: Replace division by constant with multiplication by reciprocal
// 1/100 in Q16.16 = 655.36/65536 ≈ 0x00000290
module q16_16_div_by_100_opt (
    input  signed [31:0] numerator,
    output signed [31:0] quotient
);
    // OPTIMIZATION: Multiply by reciprocal of 100 instead of division
    // 1/100 ≈ 0.009999... in Q16.16 = 0x00000290
    localparam signed [31:0] RECIP_100 = 32'sh00000290;
    wire signed [63:0] full = $signed(numerator) * RECIP_100;
    assign quotient = full[47:16];
endmodule

// OPTIMIZATION: Compare can be done in single cycle without extra logic
module q16_16_compare_opt (
    input  signed [31:0] a,
    input  signed [31:0] b,
    output               lt,
    output               eq,
    output               gt
);
    // OPTIMIZATION: Direct comparison, synthesis infers optimized logic
    assign lt = (a < b);
    assign eq = (a == b);
    assign gt = (a > b);
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OPTIMIZED OEPI Calculation - PARALLEL TREE STRUCTURE
// Derived from Lean: Semantics/OEPI.lean
// OEPI = 0.25*uncertainty + 0.25*impact + 0.20*time_sensitivity + 
//        0.15*irreversibility + 0.15*live_voltage_risk
// OPTIMIZATION: Parallel tree reduces latency from sequential to logarithmic
// ═══════════════════════════════════════════════════════════════════════════
module oepi_calculator_opt (
    input  signed [31:0] uncertainty,
    input  signed [31:0] impact,
    input  signed [31:0] time_sensitivity,
    input  signed [31:0] irreversibility,
    input  signed [31:0] live_voltage_risk,
    output signed [31:0] oepi_score
);
    // Weights in Q16.16
    localparam signed [31:0] W_UNCERTAINTY = 32'sh00004000;  // 0.25
    localparam signed [31:0] W_IMPACT     = 32'sh00004000;  // 0.25
    localparam signed [31:0] W_TIME       = 32'sh00003333;  // 0.20
    localparam signed [31:0] W_IRREVERSIBLE = 32'sh00002666; // 0.15
    localparam signed [31:0] W_VOLTAGE    = 32'sh00002666;  // 0.15
    localparam signed [31:0] W_DIVISOR   = 32'sh00019000;  // 100.0

    // OPTIMIZATION: Parallel multiplication (all 5 multiplies in parallel)
    wire signed [31:0] w_uncertainty, w_impact, w_time, w_irreversible, w_voltage;
    
    q16_16_mul_opt mul_uncertainty (.a(uncertainty), .b(W_UNCERTAINTY), .product(w_uncertainty));
    q16_16_mul_opt mul_impact (.a(impact), .b(W_IMPACT), .product(w_impact));
    q16_16_mul_opt mul_time (.a(time_sensitivity), .b(W_TIME), .product(w_time));
    q16_16_mul_opt mul_irreversible (.a(irreversibility), .b(W_IRREVERSIBLE), .product(w_irreversible));
    q16_16_mul_opt mul_voltage (.a(live_voltage_risk), .b(W_VOLTAGE), .product(w_voltage));

    // OPTIMIZATION: Tree-structured addition (reduces latency)
    // Level 1: 2 parallel adds
    wire signed [31:0] sum1a, sum1b;
    q16_16_add_opt add1a (.a(w_uncertainty), .b(w_impact), .sum(sum1a), .overflow());
    q16_16_add_opt add1b (.a(w_time), .b(w_irreversible), .sum(sum1b), .overflow());
    
    // Level 2: 1 parallel add + 1 remaining
    wire signed [31:0] sum2a;
    q16_16_add_opt add2a (.a(sum1a), .b(sum1b), .sum(sum2a), .overflow());
    
    // Level 3: Final add
    wire signed [31:0] total;
    q16_16_add_opt add3 (.a(sum2a), .b(w_voltage), .sum(total), .overflow());

    // OPTIMIZATION: Use reciprocal multiplication instead of division
    q16_16_div_by_100_opt div_normalizer (.a(total), .quotient(oepi_score));
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OPTIMIZED OEPI Threshold Classifier
// OPTIMIZATION: Single-cycle comparison with constants
// ═══════════════════════════════════════════════════════════════════════════
module oepi_threshold_classifier_opt (
    input  signed [31:0] oepi_score,
    output [1:0]         threshold    // 00=low, 01=medium, 10=critical
);
    localparam signed [31:0] THRESHOLD_MEDIUM  = 32'sh00008C00;  // 70.0
    localparam signed [31:0] THRESHOLD_CRITICAL = 32'sh0000BE00;  // 95.0

    // OPTIMIZATION: Direct comparison, no extra modules
    wire score_ge_medium = (oepi_score >= THRESHOLD_MEDIUM);
    wire score_ge_critical = (oepi_score >= THRESHOLD_CRITICAL);

    // OPTIMIZATION: Priority encoder logic
    assign threshold = score_ge_critical ? 2'b10 : (score_ge_medium ? 2'b01 : 2'b00);
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OPTIMIZED Scalar State Machine
// OPTIMIZATION: One-hot encoding for faster state transitions (more FFs but faster)
// Alternative: Binary encoding (4 bits) for minimal FFs
// ═══════════════════════════════════════════════════════════════════════════
module scalar_state_machine_opt (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        transition_trigger,
    input  wire [3:0]  target_state,
    input  wire        operator_available,
    output reg  [3:0]  current_state,
    output reg         in_pool
);
    // OPTIMIZATION: Minimal flip-flops with binary encoding
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= STATE_SUPERPOSED;
            in_pool <= 1'b1;
        end else if (transition_trigger) begin
            current_state <= target_state;
            // OPTIMIZATION: Combinational pool status based on state
            case (target_state)
                STATE_SUPERPOSED, STATE_SCOUTING, STATE_LOW_POWER_PASSIVE: 
                    in_pool <= 1'b1;
                default: 
                    in_pool <= 1'b0;
            endcase
        end else if (!operator_available && (current_state == STATE_OPERATOR_ALERT)) begin
            // Auto-transition to low power passive mode when operator unavailable
            current_state <= STATE_LOW_POWER_PASSIVE;
            in_pool <= 1'b1;
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OPTIMIZED Amplitude Update
// OPTIMIZATION: Single-cycle addition with saturation
// ═══════════════════════════════════════════════════════════════════════════
module amplitude_update_opt (
    input  signed [31:0] amplitude_old,
    input  signed [31:0] delta,
    output signed [31:0] amplitude_new
);
    wire overflow;
    q16_16_add_opt update_inst (.a(amplitude_old), .b(delta), .sum(amplitude_new), .overflow(overflow));
    // OPTIMIZATION: Saturation already handled in add module
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OPTIMIZED Profile Collapse Selector
// OPTIMIZATION: Pure combinational logic, no registers needed
// ═══════════════════════════════════════════════════════════════════════════
module profile_collapse_opt (
    input  wire        collapse_trigger,
    input  wire [7:0]  profile_id,
    output wire        collapse_valid,
    output wire [7:0]  collapsed_profile
);
    // OPTIMIZATION: Direct assignment, no logic needed
    assign collapse_valid = collapse_trigger;
    assign collapsed_profile = profile_id;
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OPTIMIZED Morphic Scalar Top-Level with Pipelining
// OPTIMIZATION: 3-stage pipeline for higher throughput
// Stage 1: OEPI calculation
// Stage 2: Threshold classification + state update
// Stage 3: Amplitude update + collapse
// ═══════════════════════════════════════════════════════════════════════════
module morphic_scalar_top_opt (
    // Clock and reset
    input  wire        clk,           // Pin 52 (27MHz)
    input  wire        rst_n,         // Pin 4 (Reset_Button)
    
    // User input
    input  wire        user_btn,      // Pin 3 (User_Button)
    
    // LED outputs
    output wire [5:0]  led,           // Pins 10,11,13,14,15,16
    
    // UART
    output wire        uart_tx,       // Pin 17
    input  wire        uart_rx,       // Pin 18
    
    // MEMS microphone
    input  wire        pdm_data,      // Pin 77
    output wire        pdm_clk,       // Pin 76
    
    // State machine control
    input  wire        state_transition,
    input  wire [3:0]  target_state,
    input  wire        operator_available,
    
    // OEPI inputs
    input  signed [31:0] uncertainty,
    input  signed [31:0] impact,
    input  signed [31:0] time_sensitivity,
    input  signed [31:0] irreversibility,
    input  signed [31:0] live_voltage_risk,
    
    // Amplitude update inputs
    input  wire        amplitude_update_trigger,
    input  signed [31:0] amplitude_old,
    input  signed [31:0] amplitude_delta,
    
    // Profile collapse inputs
    input  wire        collapse_trigger,
    input  wire [7:0]  profile_id,
    
    // Outputs (registered for timing)
    output reg  [3:0]  scalar_state,
    output reg         scalar_in_pool,
    output reg  signed [31:0] oepi_output,
    output reg  [1:0]  oepi_threshold,
    output reg  signed [31:0] amplitude_new,
    output reg         collapse_valid,
    output reg  [7:0]  collapsed_profile
);
    // Pipeline Stage 1: OEPI calculation
    wire signed [31:0] oepi_stage1;
    reg signed [31:0] oepi_stage1_reg;
    
    oepi_calculator_opt oepi_inst (
        .uncertainty(uncertainty),
        .impact(impact),
        .time_sensitivity(time_sensitivity),
        .irreversibility(irreversibility),
        .live_voltage_risk(live_voltage_risk),
        .oepi_score(oepi_stage1)
    );
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            oepi_stage1_reg <= 32'sd0;
        end else begin
            oepi_stage1_reg <= oepi_stage1;
        end
    end
    
    // Pipeline Stage 2: Threshold classification + state machine
    wire [1:0] threshold_stage2;
    wire [3:0] state_stage2;
    wire pool_stage2;
    reg [1:0] threshold_stage2_reg;
    reg [3:0] state_stage2_reg;
    reg pool_stage2_reg;
    
    oepi_threshold_classifier_opt threshold_inst (
        .oepi_score(oepi_stage1_reg),
        .threshold(threshold_stage2)
    );
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            threshold_stage2_reg <= 2'b00;
            state_stage2_reg <= 4'd0;
            pool_stage2_reg <= 1'b0;
        end else begin
            threshold_stage2_reg <= threshold_stage2;
            state_stage2_reg <= state_stage2;
            pool_stage2_reg <= pool_stage2;
        end
    end
    
    // Pipeline Stage 3: Amplitude update + collapse
    wire signed [31:0] amplitude_stage3;
    wire collapse_valid_stage3;
    wire [7:0] collapsed_profile_stage3;
    
    amplitude_update_opt amplitude_inst (
        .amplitude_old(amplitude_old),
        .delta(amplitude_delta),
        .amplitude_new(amplitude_stage3)
    );
    
    profile_collapse_opt collapse_inst (
        .collapse_trigger(collapse_trigger),
        .profile_id(profile_id),
        .collapse_valid(collapse_valid_stage3),
        .collapsed_profile(collapsed_profile_stage3)
    );
    
    // Output registers (Stage 3)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            scalar_state <= STATE_SUPERPOSED;
            scalar_in_pool <= 1'b1;
            oepi_output <= 32'sd0;
            oepi_threshold <= 2'b00;
            amplitude_new <= 32'sd0;
            collapse_valid <= 1'b0;
            collapsed_profile <= 8'h00;
        end else begin
            scalar_state <= state_stage2_reg;
            scalar_in_pool <= pool_stage2_reg;
            oepi_output <= oepi_stage1_reg;
            oepi_threshold <= threshold_stage2_reg;
            amplitude_new <= amplitude_update_trigger ? amplitude_stage3 : amplitude_old;
            collapse_valid <= collapse_valid_stage3;
            collapsed_profile <= collapsed_profile_stage3;
        end
    end
    
    // ═══════════════════════════════════════════════════════════════════════════
    // LED Status Indicator
    // ═══════════════════════════════════════════════════════════════════════════
    wire pattern_match_detected;
    led_status_opt led_inst (
        .scalar_state(scalar_state),
        .scalar_in_pool(scalar_in_pool),
        .oepi_threshold(oepi_threshold),
        .collapse_valid(collapse_valid),
        .pattern_match(pattern_match_detected),
        .led(led)
    );
    
    // ═══════════════════════════════════════════════════════════════════════════
    // MEMS Microphone Interface
    // ═══════════════════════════════════════════════════════════════════════════
    wire signed [31:0] audio_sample;
    wire sample_valid;
    wire [9:0] sample_addr;
    wire pattern_match;
    
    // Generate PDM clock (divide 27MHz by ~11 for ~2.4MHz)
    reg [3:0] pdm_clk_div;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pdm_clk_div <= 4'd0;
        end else begin
            pdm_clk_div <= pdm_clk_div + 1'b1;
        end
    end
    assign pdm_clk = pdm_clk_div[3];  // 27MHz / 16 = 1.6875MHz
    
    mems_mic_interface_opt mic_inst (
        .clk(clk),
        .mic_clk(pdm_clk),
        .mic_data(pdm_data),
        .mic_lr(1'b0),
        .audio_sample(audio_sample),
        .sample_valid(sample_valid),
        .sample_addr(sample_addr),
        .pattern_we(1'b0),
        .pattern_addr(10'd0),
        .pattern_threshold(32'sd0),
        .pattern_match(pattern_match)
    );
    
    assign pattern_match_detected = pattern_match;
    
    // ═══════════════════════════════════════════════════════════════════════════
    // UART Debug Output
    // ═══════════════════════════════════════════════════════════════════════════
    reg uart_tx_start;
    reg [7:0] uart_tx_data;
    wire uart_tx_busy;
    
    uart_tx_opt uart_inst (
        .clk(clk),
        .rst_n(rst_n),
        .tx_start(uart_tx_start),
        .tx_data(uart_tx_data),
        .uart_tx(uart_tx),
        .tx_busy(uart_tx_busy)
    );
    
    // Simple UART transmission for state monitoring (transmit state on change)
    reg [3:0] prev_state;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prev_state <= 4'd0;
            uart_tx_start <= 1'b0;
            uart_tx_data <= 8'd0;
        end else begin
            if (scalar_state != prev_state && !uart_tx_busy) begin
                prev_state <= scalar_state;
                uart_tx_data <= {4'h53, scalar_state};  // 'S' + state
                uart_tx_start <= 1'b1;
            end else begin
                uart_tx_start <= 1'b0;
            end
        end
    end
    
    // ═══════════════════════════════════════════════════════════════════════════
    // User Button Integration
    // ═══════════════════════════════════════════════════════════════════════════
    // User button triggers state transition to MEASURE_LOCAL_NEED
    reg user_btn_prev;
    wire user_btn_pressed = (user_btn && !user_btn_prev);
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            user_btn_prev <= 1'b0;
        end else begin
            user_btn_prev <= user_btn;
        end
    end
    
    // Override state transition when button pressed
    wire effective_state_transition = state_transition || user_btn_pressed;
    wire [3:0] effective_target_state = user_btn_pressed ? STATE_MEASURE_LOCAL_NEED : target_state;
    
    // Update state machine instantiation with effective signals
    scalar_state_machine_opt state_machine_inst_eff (
        .clk(clk),
        .rst_n(rst_n),
        .transition_trigger(effective_state_transition),
        .target_state(effective_target_state),
        .operator_available(operator_available),
        .current_state(state_stage2),
        .in_pool(pool_stage2)
    );
    
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// BRAM Partial LUT for Pattern Matching
// Stores adaptive pattern matching thresholds and weights
// ═══════════════════════════════════════════════════════════════════════════
module bram_pattern_lut_opt (
    input  wire        clk,
    input  wire        we,
    input  wire [9:0]  pattern_id,
    input  signed [31:0] match_threshold,
    output reg  signed [31:0] current_threshold,
    output wire        match_detected
);
    // BRAM storage (1024 x 32-bit Q16.16)
    reg signed [31:0] pattern_memory [0:1023];
    
    always @(posedge clk) begin
        if (we) begin
            pattern_memory[pattern_id] <= match_threshold;
        end
        current_threshold <= pattern_memory[pattern_id];
    end
    
    // Match detection (threshold >= 0.5)
    localparam signed [31:0] MATCH_THRESHOLD = 32'sh00008000;  // 0.5 in Q16.16
    assign match_detected = (current_threshold >= MATCH_THRESHOLD);
    
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// UART Debug Module (115200 baud @ 27MHz)
// Simple UART transmitter for debugging
// ═══════════════════════════════════════════════════════════════════════════
module uart_tx_opt (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        tx_start,
    input  wire [7:0]  tx_data,
    output reg         uart_tx,
    output reg         tx_busy
);
    // Baud rate generator for 115200 @ 27MHz
    // 27MHz / 115200 = 234.375 ≈ 234
    localparam BAUD_DIV = 16'd234;
    reg [15:0] baud_counter;
    reg [2:0]  bit_counter;
    reg [7:0]  tx_shift;
    reg [2:0]  state;  // 0=IDLE, 1=START, 2-9=DATA, 10=STOP

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= 3'd0;
            baud_counter <= 16'd0;
            bit_counter <= 3'd0;
            tx_shift <= 8'd0;
            uart_tx <= 1'b1;
            tx_busy <= 1'b0;
        end else begin
            case (state)
                3'd0: begin  // IDLE
                    uart_tx <= 1'b1;
                    tx_busy <= 1'b0;
                    if (tx_start) begin
                        tx_shift <= tx_data;
                        bit_counter <= 3'd0;
                        baud_counter <= 16'd0;
                        state <= 3'd1;
                        tx_busy <= 1'b1;
                    end
                end
                3'd1: begin  // START bit
                    uart_tx <= 1'b0;
                    if (baud_counter == BAUD_DIV) begin
                        baud_counter <= 16'd0;
                        state <= 3'd2;
                    end else begin
                        baud_counter <= baud_counter + 1'b1;
                    end
                end
                3'd2, 3'd3, 3'd4, 3'd5, 3'd6, 3'd7, 3'd8, 3'd9: begin  // DATA bits
                    uart_tx <= tx_shift[bit_counter];
                    if (baud_counter == BAUD_DIV) begin
                        baud_counter <= 16'd0;
                        if (bit_counter == 3'd7) begin
                            state <= 3'd10;
                        end else begin
                            bit_counter <= bit_counter + 1'b1;
                        end
                    end else begin
                        baud_counter <= baud_counter + 1'b1;
                    end
                end
                3'd10: begin  // STOP bit
                    uart_tx <= 1'b1;
                    if (baud_counter == BAUD_DIV) begin
                        state <= 3'd0;
                    end else begin
                        baud_counter <= baud_counter + 1'b1;
                    end
                end
            endcase
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// LED Status Indicator Module
// Maps morphic scalar state to LED outputs
// ═══════════════════════════════════════════════════════════════════════════
module led_status_opt (
    input  wire [3:0]  scalar_state,
    input  wire        scalar_in_pool,
    input  wire [1:0]  oepi_threshold,
    input  wire        collapse_valid,
    input  wire        pattern_match,
    output reg  [5:0]  led
);
    always @(*) begin
        // LED[5]: State high nibble (bit 3)
        led[5] = scalar_state[3];
        // LED[4]: State low nibble (bit 2)
        led[4] = scalar_state[2];
        // LED[3]: OEPI threshold indicator (10 = critical)
        led[3] = (oepi_threshold == 2'b10);
        // LED[2]: Pool status
        led[2] = scalar_in_pool;
        // LED[1]: Collapse valid
        led[1] = collapse_valid;
        // LED[0]: Pattern match detected
        led[0] = pattern_match;
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// MEMS Microphone Interface (SPH0645)
// I2S/PDM digital output interface for acoustic input
// ═══════════════════════════════════════════════════════════════════════════
module mems_mic_interface_opt (
    input  wire        clk,           // System clock (27MHz)
    input  wire        mic_clk,       // MEMS mic clock (typically 2.4MHz)
    input  wire        mic_data,      // MEMS mic data (PDM or I2S)
    input  wire        mic_lr,        // Left/Right select (I2S only)
    output reg  signed [31:0] audio_sample,  // Q16.16 audio sample output
    output reg         sample_valid   // Sample valid flag
    output reg  [9:0]  sample_addr    // BRAM address for pattern matching
    input  wire        pattern_we,    // Pattern match write enable
    input  wire [9:0]  pattern_addr,  // Pattern match address
    input  signed [31:0] pattern_threshold,  // Pattern match threshold
    output wire        pattern_match   // Pattern match detected
);
    // PDM to PCM conversion (simplified)
    reg signed [15:0] pdm_accumulator;
    reg [7:0]  pdm_counter;
    
    always @(posedge mic_clk) begin
        pdm_accumulator <= pdm_accumulator + {16'b0, mic_data};
        pdm_counter <= pdm_counter + 1;
        
        if (pdm_counter == 8'd255) begin
            // Convert to Q16.16 (shift by 16)
            audio_sample <= {pdm_accumulator, 16'b0};
            sample_valid <= 1'b1;
            pdm_accumulator <= 16'sd0;
            pdm_counter <= 8'd0;
        end else begin
            sample_valid <= 1'b0;
        end
    end
    
    // Pattern matching address generation
    assign sample_addr = audio_sample[9:0];  // Use lower 10 bits as address
    
    // Pattern match detection
    localparam signed [31:0] MATCH_THRESHOLD = 32'sh00008000;  // 0.5 in Q16.16
    assign pattern_match = (audio_sample >= MATCH_THRESHOLD);
    
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OPTIMIZED Testbench
// ═══════════════════════════════════════════════════════════════════════════
module morphic_scalar_tb_opt;
    reg clk;
    reg rst_n;
    
    // User input
    reg user_btn;
    
    // UART
    wire uart_tx;
    reg uart_rx;
    
    // MEMS microphone
    reg pdm_data;
    wire pdm_clk;
    
    // State machine control
    reg state_transition;
    reg [3:0] target_state;
    reg operator_available;
    
    // OEPI inputs
    reg signed [31:0] uncertainty;
    reg signed [31:0] impact;
    reg signed [31:0] time_sensitivity;
    reg signed [31:0] irreversibility;
    reg signed [31:0] live_voltage_risk;
    
    // Amplitude update inputs
    reg amplitude_update_trigger;
    reg signed [31:0] amplitude_old;
    reg signed [31:0] amplitude_delta;
    
    // Profile collapse inputs
    reg collapse_trigger;
    reg [7:0] profile_id;
    
    // Outputs
    wire [3:0] scalar_state;
    wire scalar_in_pool;
    wire signed [31:0] oepi_output;
    wire [1:0] oepi_threshold;
    wire signed [31:0] amplitude_new;
    wire collapse_valid;
    wire [7:0] collapsed_profile;
    wire [5:0] led;
    
    // Instantiate DUT
    morphic_scalar_top_opt dut (
        .clk(clk),
        .rst_n(rst_n),
        .user_btn(user_btn),
        .led(led),
        .uart_tx(uart_tx),
        .uart_rx(uart_rx),
        .pdm_data(pdm_data),
        .pdm_clk(pdm_clk),
        .state_transition(state_transition),
        .target_state(target_state),
        .operator_available(operator_available),
        .uncertainty(uncertainty),
        .impact(impact),
        .time_sensitivity(time_sensitivity),
        .irreversibility(irreversibility),
        .live_voltage_risk(live_voltage_risk),
        .amplitude_update_trigger(amplitude_update_trigger),
        .amplitude_old(amplitude_old),
        .amplitude_delta(amplitude_delta),
        .collapse_trigger(collapse_trigger),
        .profile_id(profile_id),
        .scalar_state(scalar_state),
        .scalar_in_pool(scalar_in_pool),
        .oepi_output(oepi_output),
        .oepi_threshold(oepi_threshold),
        .amplitude_new(amplitude_new),
        .collapse_valid(collapse_valid),
        .collapsed_profile(collapsed_profile)
    );
    
    // Clock generation (27MHz - 37.037ns period)
    initial clk = 0;
    always #18.5185 clk = ~clk;
    
    // Test stimulus with pipeline verification
    initial begin
        // Initialize inputs
        rst_n = 0;
        user_btn = 0;
        uart_rx = 1;
        pdm_data = 0;
        state_transition = 0;
        target_state = 4'd0;
        operator_available = 1;
        
        uncertainty = 32'sh00008000;  // 50.0 in Q16.16
        impact = 32'sh00004E00;       // 30.0
        time_sensitivity = 32'sh00003333;  // 20.0
        irreversibility = 32'sh00001A00;    // 10.0
        live_voltage_risk = 32'sh00000D00;  // 5.0
        
        amplitude_update_trigger = 0;
        amplitude_old = 32'sh00008000;  // 50.0
        amplitude_delta = 32'sh00001000;  // 10.0
        
        collapse_trigger = 0;
        profile_id = 8'h01;
        
        #100;
        rst_n = 1;
        
        #200;
        $display("Initial State: %d", scalar_state);
        $display("In Pool: %b", scalar_in_pool);
        $display("LED Status: %b", led);
        
        // Test OEPI calculation (3 cycle latency due to pipeline)
        #200;
        $display("OEPI Score: %d", oepi_output);
        $display("OEPI Threshold: %b", oepi_threshold);
        $display("LED Status: %b", led);
        
        // Test state transition
        #200;
        target_state = STATE_MEASURE_LOCAL_NEED;
        state_transition = 1;
        #20;
        state_transition = 0;
        #200;
        $display("State after transition: %d", scalar_state);
        $display("LED Status: %b", led);
        
        // Test user button press
        #200;
        user_btn = 1;
        #50;
        user_btn = 0;
        #200;
        $display("State after button press: %d", scalar_state);
        $display("LED Status: %b", led);
        
        // Test amplitude update
        #200;
        amplitude_update_trigger = 1;
        #20;
        amplitude_update_trigger = 0;
        #200;
        $display("Amplitude New: %d", amplitude_new);
        $display("LED Status: %b", led);
        
        // Test profile collapse
        #200;
        collapse_trigger = 1;
        #20;
        collapse_trigger = 0;
        #200;
        $display("Collapse Valid: %b", collapse_valid);
        $display("Collapsed Profile: %d", collapsed_profile);
        $display("LED Status: %b", led);
        
        // Test operator unavailable -> low power passive mode
        #200;
        target_state = STATE_OPERATOR_ALERT;
        state_transition = 1;
        #20;
        state_transition = 0;
        #200;
        $display("State after operator alert: %d", scalar_state);
        $display("LED Status: %b", led);
        
        #100;
        operator_available = 0;
        #200;
        $display("State after operator unavailable: %d", scalar_state);
        $display("LED Status: %b", led);
        
        #200;
        $finish;
    end
endmodule

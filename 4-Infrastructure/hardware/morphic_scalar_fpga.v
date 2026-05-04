// Morphic Scalar FPGA Implementation
// Derived from Lean: Semantics/MorphicScalar.lean
// Target: Lattice iCE40 HX8K / ECP5
// Q16.16 fixed-point arithmetic
// Implements quantum-inspired computational stem cell

`timescale 1ns / 1ps

// ═══════════════════════════════════════════════════════════════════════════
// Scalar State Encoding (4-bit state ID)
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
// Q16.16 Fixed-Point Arithmetic (32-bit signed)
// ═══════════════════════════════════════════════════════════════════════════
module q16_16_add (
    input  signed [31:0] a,
    input  signed [31:0] b,
    output signed [31:0] sum,
    output               overflow
);
    wire signed [32:0] ext = $signed({a[31], a}) + $signed({b[31], b});
    assign overflow = (a[31] == b[31]) && (ext[32] != a[31]);
    assign sum = overflow ? (a[31] ? 32'sh80000000 : 32'sh7FFFFFFF) : ext[31:0];
endmodule

module q16_16_mul (
    input  signed [31:0] a,
    input  signed [31:0] b,
    output signed [31:0] product
);
    wire signed [63:0] full = $signed(a) * $signed(b);
    assign product = full[47:16];  // Q16.16 multiply: keep middle 32 bits
endmodule

module q16_16_div (
    input  signed [31:0] numerator,
    input  signed [31:0] denominator,
    output signed [31:0] quotient
);
    assign quotient = (denominator == 0) ? 32'sh7FFFFFFF : 
                     $signed((($signed(numerator) <<< 16) / $signed(denominator)));
endmodule

module q16_16_compare (
    input  signed [31:0] a,
    input  signed [31:0] b,
    output               lt,
    output               eq,
    output               gt
);
    assign lt = (a < b);
    assign eq = (a == b);
    assign gt = (a > b);
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OEPI Calculation (Operator Escalation Percentage Index)
// Derived from Lean: Semantics/OEPI.lean
// OEPI = 0.25*uncertainty + 0.25*impact + 0.20*time_sensitivity + 
//        0.15*irreversibility + 0.15*live_voltage_risk
// ═══════════════════════════════════════════════════════════════════════════
module oepi_calculator (
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

    wire signed [31:0] w_uncertainty, w_impact, w_time, w_irreversible, w_voltage;
    wire signed [31:0] sum1, sum2, sum3, total;

    q16_16_mul mul_uncertainty (.a(uncertainty), .b(W_UNCERTAINTY), .product(w_uncertainty));
    q16_16_mul mul_impact (.a(impact), .b(W_IMPACT), .product(w_impact));
    q16_16_mul mul_time (.a(time_sensitivity), .b(W_TIME), .product(w_time));
    q16_16_mul mul_irreversible (.a(irreversibility), .b(W_IRREVERSIBLE), .product(w_irreversible));
    q16_16_mul mul_voltage (.a(live_voltage_risk), .b(W_VOLTAGE), .product(w_voltage));

    q16_16_add add1 (.a(w_uncertainty), .b(w_impact), .sum(sum1), .overflow());
    q16_16_add add2 (.a(sum1), .b(w_time), .sum(sum2), .overflow());
    q16_16_add add3 (.a(sum2), .b(w_irreversible), .sum(sum3), .overflow());
    q16_16_add add4 (.a(sum3), .b(w_voltage), .sum(total), .overflow());

    q16_16_div div_normalizer (.a(total), .b(W_DIVISOR), .quotient(oepi_score));
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OEPI Threshold Classifier
// Derived from Lean: Semantics/OEPI.lean
// ═══════════════════════════════════════════════════════════════════════════
module oepi_threshold_classifier (
    input  signed [31:0] oepi_score,
    output [1:0]         threshold    // 00=low, 01=medium, 10=critical
);
    localparam signed [31:0] THRESHOLD_MEDIUM  = 32'sh00008C00;  // 70.0
    localparam signed [31:0] THRESHOLD_CRITICAL = 32'sh0000BE00;  // 95.0

    wire score_ge_medium, score_ge_critical;
    q16_16_compare cmp_medium (.a(oepi_score), .b(THRESHOLD_MEDIUM), .lt(), .eq(), .gt(score_ge_medium));
    q16_16_compare cmp_critical (.a(oepi_score), .b(THRESHOLD_CRITICAL), .lt(), .eq(), .gt(score_ge_critical));

    assign threshold = score_ge_critical ? 2'b10 : (score_ge_medium ? 2'b01 : 2'b00);
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Scalar State Machine
// Derived from Lean: Semantics/MorphicScalar.lean
// ═══════════════════════════════════════════════════════════════════════════
module scalar_state_machine (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        transition_trigger,
    input  wire [3:0]  target_state,
    input  wire        operator_available,
    output reg  [3:0]  current_state,
    output reg         in_pool
);
    // State transition logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= STATE_SUPERPOSED;
            in_pool <= 1'b1;
        end else if (transition_trigger) begin
            current_state <= target_state;
            // Update pool status based on state
            case (target_state)
                STATE_SUPERPOSED: in_pool <= 1'b1;
                STATE_SCOUTING:   in_pool <= 1'b1;
                STATE_LOW_POWER_PASSIVE: in_pool <= 1'b1;
                default: in_pool <= 1'b0;
            endcase
        end else if (!operator_available && (current_state == STATE_OPERATOR_ALERT)) begin
            // Auto-transition to low power passive mode when operator unavailable
            current_state <= STATE_LOW_POWER_PASSIVE;
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Amplitude Update Module
// Derived from Lean: Semantics/MorphicScalar.lean
// amplitude(new) = amplitude(old) + delta
// ═══════════════════════════════════════════════════════════════════════════
module amplitude_update (
    input  signed [31:0] amplitude_old,
    input  signed [31:0] delta,
    output signed [31:0] amplitude_new
);
    q16_16_add update_inst (.a(amplitude_old), .b(delta), .sum(amplitude_new), .overflow());
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Profile Collapse Selector
// Derived from Lean: Semantics/MorphicScalar.lean
// Collapse scalar into specific profile based on measurement
// ═══════════════════════════════════════════════════════════════════════════
module profile_collapse (
    input  wire        collapse_trigger,
    input  wire [7:0]  profile_id,      // 8-bit profile ID
    output wire        collapse_valid,
    output wire [7:0]  collapsed_profile
);
    assign collapse_valid = collapse_trigger;
    assign collapsed_profile = profile_id;
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Morphic Scalar Top-Level Module
// Integrates state machine, OEPI calculation, and amplitude updates
// ═══════════════════════════════════════════════════════════════════════════
module morphic_scalar_top (
    input  wire        clk,
    input  wire        rst_n,
    
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
    
    // Outputs
    output wire [3:0]  scalar_state,
    output wire        scalar_in_pool,
    output signed [31:0] oepi_output,
    output wire [1:0]  oepi_threshold,
    output signed [31:0] amplitude_new,
    output wire        collapse_valid,
    output wire [7:0]  collapsed_profile
);
    // State machine instance
    wire [3:0] state_wire;
    wire pool_wire;
    
    scalar_state_machine state_machine_inst (
        .clk(clk),
        .rst_n(rst_n),
        .transition_trigger(state_transition),
        .target_state(target_state),
        .operator_available(operator_available),
        .current_state(state_wire),
        .in_pool(pool_wire)
    );
    
    assign scalar_state = state_wire;
    assign scalar_in_pool = pool_wire;
    
    // OEPI calculation instance
    wire signed [31:0] oepi_wire;
    
    oepi_calculator oepi_inst (
        .uncertainty(uncertainty),
        .impact(impact),
        .time_sensitivity(time_sensitivity),
        .irreversibility(irreversibility),
        .live_voltage_risk(live_voltage_risk),
        .oepi_score(oepi_wire)
    );
    
    assign oepi_output = oepi_wire;
    
    // OEPI threshold classification
    wire [1:0] threshold_wire;
    
    oepi_threshold_classifier threshold_inst (
        .oepi_score(oepi_wire),
        .threshold(threshold_wire)
    );
    
    assign oepi_threshold = threshold_wire;
    
    // Amplitude update instance
    wire signed [31:0] amplitude_wire;
    
    amplitude_update amplitude_inst (
        .amplitude_old(amplitude_old),
        .delta(amplitude_delta),
        .amplitude_new(amplitude_wire)
    );
    
    assign amplitude_new = amplitude_update_trigger ? amplitude_wire : amplitude_old;
    
    // Profile collapse instance
    wire collapse_valid_wire;
    wire [7:0] collapsed_profile_wire;
    
    profile_collapse collapse_inst (
        .collapse_trigger(collapse_trigger),
        .profile_id(profile_id),
        .collapse_valid(collapse_valid_wire),
        .collapsed_profile(collapsed_profile_wire)
    );
    
    assign collapse_valid = collapse_valid_wire;
    assign collapsed_profile = collapsed_profile_wire;
    
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Testbench
// ═══════════════════════════════════════════════════════════════════════════
module morphic_scalar_tb;
    reg clk;
    reg rst_n;
    
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
    
    // Instantiate DUT
    morphic_scalar_top dut (
        .clk(clk),
        .rst_n(rst_n),
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
    
    // Clock generation (50MHz)
    initial clk = 0;
    always #10 clk = ~clk;
    
    // Test stimulus
    initial begin
        // Initialize inputs
        rst_n = 0;
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
        
        #20;
        rst_n = 1;
        
        #100;
        $display("Initial State: %d", scalar_state);
        $display("In Pool: %b", scalar_in_pool);
        
        // Test OEPI calculation
        #100;
        $display("OEPI Score: %d", oepi_output);
        $display("OEPI Threshold: %b", oepi_threshold);
        
        // Test state transition
        #100;
        target_state = STATE_MEASURE_LOCAL_NEED;
        state_transition = 1;
        #20;
        state_transition = 0;
        #100;
        $display("State after transition: %d", scalar_state);
        
        // Test amplitude update
        #100;
        amplitude_update_trigger = 1;
        #20;
        amplitude_update_trigger = 0;
        #100;
        $display("Amplitude New: %d", amplitude_new);
        
        // Test profile collapse
        #100;
        collapse_trigger = 1;
        #20;
        collapse_trigger = 0;
        #100;
        $display("Collapse Valid: %b", collapse_valid);
        $display("Collapsed Profile: %d", collapsed_profile);
        
        // Test operator unavailable -> low power passive mode
        #100;
        target_state = STATE_OPERATOR_ALERT;
        state_transition = 1;
        #20;
        state_transition = 0;
        #100;
        $display("State after operator alert: %d", scalar_state);
        
        #50;
        operator_available = 0;
        #100;
        $display("State after operator unavailable: %d", scalar_state);
        
        #100;
        $finish;
    end
endmodule

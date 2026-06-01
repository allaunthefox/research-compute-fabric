// TMR OEPI Safety FSM
// Derived from expansion paths document: DTMR with triplicated voters per ESA FPGA-003
// Target: Gowin GW1NR-9 or iCE40 HX8K
// Q16.16 fixed-point arithmetic for OEPI score
// Safety valve: bounded-veto protocol for swarm consensus

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
// TMR Voter Module (Triplicated Redundancy)
// Votes on 3 inputs, outputs majority
// ═══════════════════════════════════════════════════════════════════════════
module tmr_voter (
    input  wire [3:0]  in0,
    input  wire [3:0]  in1,
    input  wire [3:0]  in2,
    output reg  [3:0]  voted,
    output reg         error_detected
);
    always @(*) begin
        // Majority voting: if at least 2 agree, use that value
        if (in0 == in1 || in0 == in2) begin
            voted = in0;
            error_detected = (in0 != in1) || (in0 != in2);
        end else if (in1 == in2) begin
            voted = in1;
            error_detected = 1'b1;
        end else begin
            // All different - use in0 as fallback
            voted = in0;
            error_detected = 1'b1;
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// OEPI Safety Score Calculation
// OEPI (Operator Emergency Protection Index) in Q1.7 format
// Threshold-based safety valve
// ═══════════════════════════════════════════════════════════════════════════
module oepi_calculator (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [3:0]  scalar_state,
    input  wire [31:0] s3c_j_score,
    input  wire [31:0] s3c_mass,
    input  wire        s3c_emit,
    output reg  [7:0]  oepi_score,     // Q1.7 OEPI score
    output reg         safety_violation
);
    // OEPI threshold (Q1.7 format)
    localparam OEPI_THRESHOLD = 8'd120;  // ~0.94 in Q1.7
    
    // Calculate OEPI based on state and S3C metrics
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            oepi_score <= 8'd0;
            safety_violation <= 1'b0;
        end else begin
            // Base OEPI from scalar state
            case (scalar_state)
                STATE_SUPERPOSED:      oepi_score <= 8'd20;   // Low risk
                STATE_SCOUTING:        oepi_score <= 8'd30;   // Low risk
                STATE_MEASURE_LOCAL_NEED: oepi_score <= 8'd40;
                STATE_COLLAPSED_PROFILE:   oepi_score <= 8'd50;
                STATE_EXECUTE:         oepi_score <= 8'd80;   // Medium risk
                STATE_RECEIPT:         oepi_score <= 8'd60;
                STATE_AMPLITUDE_UPDATE:   oepi_score <= 8'd70;
                STATE_QUERY_COLLECTIVE:   oepi_score <= 8'd50;
                STATE_COLLECTIVE_RESPONSE: oepi_score <= 8'd60;
                STATE_QUERY_LLM:       oepi_score <= 8'd55;
                STATE_DIRECTED:        oepi_score <= 8'd75;
                STATE_HOLD:            oepi_score <= 8'd30;
                STATE_OPERATOR_ALERT:  oepi_score <= 8'd120;  // High risk
                STATE_LOW_POWER_PASSIVE: oepi_score <= 8'd25;
                STATE_QUARANTINE:      oepi_score <= 8'd127;  // Maximum risk
                STATE_MIGRATE:         oepi_score <= 8'd45;
                default:               oepi_score <= 8'd64;
            endcase
            
            // FIX: Combine s3c_emit and s3c_j_score into single conditional
            // to prevent double-increment race when both fire in same cycle
            begin
                reg [7:0] oepi_delta;
                oepi_delta = 8'd0;
                if (s3c_emit)
                    oepi_delta = oepi_delta + 8'd10;
                if (s3c_j_score > 32'd5000)
                    oepi_delta = oepi_delta + 8'd5;
                if (oepi_delta > 8'd0 && oepi_score <= 8'd127 - oepi_delta)
                    oepi_score <= oepi_score + oepi_delta;
                else if (oepi_delta > 8'd0)
                    oepi_score <= 8'd127;
            end
            
            // Safety violation detection
            safety_violation <= (oepi_score >= OEPI_THRESHOLD);
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Triplicated Scalar State Machine (DTMR)
// Three parallel FSM instances with TMR voting
// ═══════════════════════════════════════════════════════════════════════════
module scalar_fsm_triplet (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        state_transition,
    input  wire [3:0]  target_state,
    input  wire        operator_available,
    output reg  [3:0]  fsm_state [0:2],  // Three FSM instances
    output reg  [3:0]  voted_state,
    output reg         voter_error
);
    // FSM instance 0
    reg [3:0] fsm0_state;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fsm0_state <= STATE_SUPERPOSED;
        end else if (state_transition && operator_available) begin
            fsm0_state <= target_state;
        end
    end
    assign fsm_state[0] = fsm0_state;
    
    // FSM instance 1
    reg [3:0] fsm1_state;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fsm1_state <= STATE_SUPERPOSED;
        end else if (state_transition && operator_available) begin
            fsm1_state <= target_state;
        end
    end
    assign fsm_state[1] = fsm1_state;
    
    // FSM instance 2
    reg [3:0] fsm2_state;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fsm2_state <= STATE_SUPERPOSED;
        end else if (state_transition && operator_available) begin
            fsm2_state <= target_state;
        end
    end
    assign fsm_state[2] = fsm2_state;
    
    // TMR voter
    tmr_voter state_voter (
        .in0(fsm0_state),
        .in1(fsm1_state),
        .in2(fsm2_state),
        .voted(voted_state),
        .error_detected(voter_error)
    );
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Triplicated OEPI Calculator (DTMR)
// Three parallel OEPI calculators with TMR voting
// ═══════════════════════════════════════════════════════════════════════════
module oepi_triplet (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [3:0]  scalar_state,
    input  wire [31:0] s3c_j_score,
    input  wire [31:0] s3c_mass,
    input  wire        s3c_emit,
    output reg  [7:0]  oepi_scores [0:2],  // Three OEPI instances
    output reg  [7:0]  voted_oepi,
    output reg         voter_error,
    output reg         safety_violation
);
    // OEPI instance 0
    reg [7:0] oepi0;
    wire violation0;
    oepi_calculator oepi_inst0 (
        .clk(clk),
        .rst_n(rst_n),
        .scalar_state(scalar_state),
        .s3c_j_score(s3c_j_score),
        .s3c_mass(s3c_mass),
        .s3c_emit(s3c_emit),
        .oepi_score(oepi0),
        .safety_violation(violation0)
    );
    assign oepi_scores[0] = oepi0;
    
    // OEPI instance 1
    reg [7:0] oepi1;
    wire violation1;
    oepi_calculator oepi_inst1 (
        .clk(clk),
        .rst_n(rst_n),
        .scalar_state(scalar_state),
        .s3c_j_score(s3c_j_score),
        .s3c_mass(s3c_mass),
        .s3c_emit(s3c_emit),
        .oepi_score(oepi1),
        .safety_violation(violation1)
    );
    assign oepi_scores[1] = oepi1;
    
    // OEPI instance 2
    reg [7:0] oepi2;
    wire violation2;
    oepi_calculator oepi_inst2 (
        .clk(clk),
        .rst_n(rst_n),
        .scalar_state(scalar_state),
        .s3c_j_score(s3c_j_score),
        .s3c_mass(s3c_mass),
        .s3c_emit(s3c_emit),
        .oepi_score(oepi2),
        .safety_violation(violation2)
    );
    assign oepi_scores[2] = oepi2;
    
    // TMR voter for OEPI (8-bit, vote per bit)
    integer k;
    always @(*) begin
        for (k = 0; k < 8; k = k + 1) begin
            voted_oepi[k] = (oepi0[k] & oepi1[k]) | (oepi0[k] & oepi2[k]) | (oepi1[k] & oepi2[k]);
        end
    end
    
    // Voter error detection
    always @(*) begin
        voter_error = (oepi0 != oepi1) || (oepi0 != oepi2);
    end
    
    // Safety violation (any instance triggers)
    always @(*) begin
        safety_violation = violation0 || violation1 || violation2;
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Bounded-Veto Safety Protocol
// Any node raising OEPI above threshold forces swarm to safe state
// ═══════════════════════════════════════════════════════════════════════════
module bounded_veto_protocol (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  local_oepi,
    input  wire [7:0]  remote_oepi,   // From other nodes via gossip
    input  wire        veto_request,  // Remote veto request
    output reg         safe_state_enforced,
    output reg  [3:0]  safe_state
);
    localparam OEPI_VETO_THRESHOLD = 8'd100;  // Veto threshold
    localparam SAFE_STATE = STATE_QUARANTINE;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            safe_state_enforced <= 1'b0;
            safe_state <= STATE_SUPERPOSED;
        end else begin
            // Check local OEPI
            if (local_oepi >= OEPI_VETO_THRESHOLD) begin
                safe_state_enforced <= 1'b1;
                safe_state <= SAFE_STATE;
            end
            // Check remote veto
            else if (veto_request || remote_oepi >= OEPI_VETO_THRESHOLD) begin
                safe_state_enforced <= 1'b1;
                safe_state <= SAFE_STATE;
            end
            // Clear safe state when OEPI drops
            else if (safe_state_enforced && local_oepi < OEPI_VETO_THRESHOLD && 
                     remote_oepi < OEPI_VETO_THRESHOLD && !veto_request) begin
                safe_state_enforced <= 1'b0;
                safe_state <= STATE_SUPERPOSED;
            end
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// TMR OEPI Safety FSM Top-Level
// Combines DTMR state machine, DTMR OEPI calculator, and bounded-veto protocol
// ═══════════════════════════════════════════════════════════════════════════
module tmr_oepi_safety_fsm (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        state_transition,
    input  wire [3:0]  target_state,
    input  wire        operator_available,
    input  wire [31:0] s3c_j_score,
    input  wire [31:0] s3c_mass,
    input  wire        s3c_emit,
    input  wire [7:0]  remote_oepi,
    input  wire        veto_request,
    output reg  [3:0]  scalar_state,
    output reg  [7:0]  oepi_score,
    output reg         safety_violation,
    output reg         fsm_voter_error,
    output reg         oepi_voter_error,
    output reg         safe_state_enforced
);
    // Triplicated scalar state machine
    wire [3:0] fsm_states [0:2];
    wire [3:0] voted_fsm_state;
    wire fsm_voter_err;
    
    scalar_fsm_triplet fsm_triplet (
        .clk(clk),
        .rst_n(rst_n),
        .state_transition(state_transition && !safe_state_enforced),
        .target_state(target_state),
        .operator_available(operator_available),
        .fsm_state(fsm_states),
        .voted_state(voted_fsm_state),
        .voter_error(fsm_voter_err)
    );
    
    // Triplicated OEPI calculator
    wire [7:0] oepi_scores [0:2];
    wire [7:0] voted_oepi;
    wire oepi_voter_err;
    wire safety_violation_wire;
    
    oepi_triplet oepi_triplet_inst (
        .clk(clk),
        .rst_n(rst_n),
        .scalar_state(voted_fsm_state),
        .s3c_j_score(s3c_j_score),
        .s3c_mass(s3c_mass),
        .s3c_emit(s3c_emit),
        .oepi_scores(oepi_scores),
        .voted_oepi(voted_oepi),
        .voter_error(oepi_voter_err),
        .safety_violation(safety_violation_wire)
    );
    
    // Bounded-veto protocol
    wire safe_enforced;
    wire [3:0] safe_state_wire;
    
    bounded_veto_protocol veto_protocol (
        .clk(clk),
        .rst_n(rst_n),
        .local_oepi(voted_oepi),
        .remote_oepi(remote_oepi),
        .veto_request(veto_request),
        .safe_state_enforced(safe_enforced),
        .safe_state(safe_state_wire)
    );
    
    // Output registers
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            scalar_state <= STATE_SUPERPOSED;
            oepi_score <= 8'd0;
            safety_violation <= 1'b0;
            fsm_voter_error <= 1'b0;
            oepi_voter_error <= 1'b0;
            safe_state_enforced <= 1'b0;
        end else begin
            // Apply safe state override
            if (safe_enforced) begin
                scalar_state <= safe_state_wire;
                safe_state_enforced <= 1'b1;
            end else begin
                scalar_state <= voted_fsm_state;
                safe_state_enforced <= 1'b0;
            end
            
            oepi_score <= voted_oepi;
            safety_violation <= safety_violation_wire;
            fsm_voter_error <= fsm_voter_err;
            oepi_voter_error <= oepi_voter_err;
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Testbench
// ═══════════════════════════════════════════════════════════════════════════
module tmr_oepi_testbench;
    reg clk;
    reg rst_n;
    reg state_transition;
    reg [3:0] target_state;
    reg operator_available;
    reg [31:0] s3c_j_score;
    reg [31:0] s3c_mass;
    reg s3c_emit;
    reg [7:0] remote_oepi;
    reg veto_request;
    
    wire [3:0] scalar_state;
    wire [7:0] oepi_score;
    wire safety_violation;
    wire fsm_voter_error;
    wire oepi_voter_error;
    wire safe_state_enforced;
    
    tmr_oepi_safety_fsm dut (
        .clk(clk),
        .rst_n(rst_n),
        .state_transition(state_transition),
        .target_state(target_state),
        .operator_available(operator_available),
        .s3c_j_score(s3c_j_score),
        .s3c_mass(s3c_mass),
        .s3c_emit(s3c_emit),
        .remote_oepi(remote_oepi),
        .veto_request(veto_request),
        .scalar_state(scalar_state),
        .oepi_score(oepi_score),
        .safety_violation(safety_violation),
        .fsm_voter_error(fsm_voter_error),
        .oepi_voter_error(oepi_voter_error),
        .safe_state_enforced(safe_state_enforced)
    );
    
    initial clk = 0;
    always #18.5185 clk = ~clk;
    
    initial begin
        rst_n = 0;
        state_transition = 0;
        target_state = 4'd0;
        operator_available = 1;
        s3c_j_score = 32'd0;
        s3c_mass = 32'd0;
        s3c_emit = 0;
        remote_oepi = 8'd0;
        veto_request = 0;
        
        #100;
        rst_n = 1;
        
        #100;
        
        // Test normal state transition
        $display("Test 1: Normal state transition");
        target_state = STATE_EXECUTE;
        state_transition = 1;
        #100;
        state_transition = 0;
        #500;
        $display("State: %d, OEPI: %d, Safety: %b", scalar_state, oepi_score, safety_violation);
        
        // Test high OEPI (safety violation)
        $display("Test 2: High OEPI safety violation");
        s3c_j_score = 32'd10000;
        s3c_emit = 1;
        #500;
        $display("State: %d, OEPI: %d, Safety: %b", scalar_state, oepi_score, safety_violation);
        
        // Test remote veto
        $display("Test 3: Remote veto");
        veto_request = 1;
        #500;
        $display("State: %d, Safe Enforced: %b", scalar_state, safe_state_enforced);
        veto_request = 0;
        
        #1000;
        $finish;
    end
endmodule

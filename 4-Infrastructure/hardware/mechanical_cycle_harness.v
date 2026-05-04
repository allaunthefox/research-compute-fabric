`timescale 1ns / 1ps

// =============================================================================
// MECHANICAL CYCLE HARNESS (Virtual FPGA Testbed)
// =============================================================================
// This harness simulates the three functional stages of the manifold:
// 1. Propagate (NII Surface Execution)
// 2. Collapse (Verdict Extraction)
// 3. Lift (Witness Generation)
//
// Governed by the Virtual Warp Metric and SSS Monitor logic.
// =============================================================================

module mechanical_cycle_harness;
    reg clk;
    reg reset_n;
    
    // SSS Data Inputs
    reg [15:0] routing_load;
    reg [15:0] memory_load;
    reg [15:0] extraneous_weight;
    reg [15:0] engram_length;
    reg [15:0] extraneous_gradient;
    reg [15:0] heel_dig_limit;
    
    // Virtual Warp Parameters
    reg [15:0] kappa;
    reg [15:0] opcode_efficacy;
    reg [15:0] local_velocity;
    reg [15:0] coherence;
    reg [15:0] proper_time;
    reg [15:0] entropy_displacement;
    
    // Contextual Input
    reg [15:0] cognitive_load;
    
    // Outputs from Driver
    wire [15:0] sss_constant;
    wire slip_threshold_crossed;
    wire mode_survival_trigger;
    wire [15:0] virtual_warp_value;
    wire [15:0] effective_velocity;
    wire [15:0] virtual_warp_metric;
    wire [1:0]  schedule_decision;
    wire [1:0]  topology_metric;
    
    // Instantiate the NII Surface Driver (The Core under test)
    nii_surface_driver dut (
        .clk(clk),
        .reset_n(reset_n),
        .routing_load(routing_load),
        .memory_load(memory_load),
        .extraneous_weight(extraneous_weight),
        .engram_length(engram_length),
        .extraneous_gradient(extraneous_gradient),
        .heel_dig_limit(heel_dig_limit),
        .kappa(kappa),
        .opcode_efficacy(opcode_efficacy),
        .local_velocity(local_velocity),
        .coherence(coherence),
        .proper_time(proper_time),
        .entropy_displacement(entropy_displacement),
        .torsional_stress(16'h0000),      // Tied for this test
        .interlocking_energy(16'h0000),   // Tied for this test
        .laplacian_energy(16'h0000),      // Tied for this test
        .cognitive_load(cognitive_load),
        .sss_constant_out(sss_constant),
        .slip_threshold_crossed(slip_threshold_crossed),
        .mode_survival_trigger(mode_survival_trigger),
        .virtual_warp_value_out(virtual_warp_value),
        .effective_velocity_out(effective_velocity),
        .virtual_warp_metric_out(virtual_warp_metric),
        .schedule_decision_out(schedule_decision),
        .topology_metric_out(topology_metric)
    );
    
    // Clock Generation (50 MHz)
    initial clk = 0;
    always #10 clk = ~clk;
    
    // Task: Single Mechanical Cycle Trace
    task run_mechanical_cycle;
        begin
            #100; // Allow logic to settle
            $display("[%t] Manifold State Tick:", $time);
            $display("    SSS Constant: %h", sss_constant);
            $display("    Warp Metric : %h", virtual_warp_metric);
            $display("    Decision    : %b", schedule_decision);
            if (mode_survival_trigger) $display("    *** WARNING: MODE_SURVIVAL TRIGGERED ***");
        end
    endtask
    
    initial begin
        $dumpfile("mechanical_cycle.vcd");
        $dumpvars(0, mechanical_cycle_harness);
        
        $display("=============================================================================");
        $display("INITIATING MECHANICAL CYCLE HARNESS - ZERO-TRUST HARDWARE VERIFICATION");
        $display("=============================================================================");
        
        // --- 1. RESET ---
        reset_n = 0;
        routing_load = 16'h0000;
        memory_load = 16'h0000;
        kappa = 16'h1000;           // κ = 1.0 (Q16.16)
        opcode_efficacy = 16'hFFFF;  // Ω = 1.0
        local_velocity = 16'h1000;   // v = 1.0
        coherence = 16'h0000;        // φ = 0.0
        heel_dig_limit = 16'h4000;   // σ_sys = 0.25
        proper_time = 16'h0100;      // dτ = 0.01
        entropy_displacement = 16'h0000;
        cognitive_load = 16'h0000;
        
        #50 reset_n = 1;
        
        // --- 2. BASELINE PROPAGATE (Steady State) ---
        routing_load = 16'h4000;     // 0.5
        memory_load = 16'h2000;      // 0.25
        run_mechanical_cycle();
        
        // --- 3. HARMONIC SURPRISE (Minor Torsion) ---
        // Increase extraneous weight to create torsion mismatch
        extraneous_weight = 16'h2000;   // 0.25
        engram_length = 16'h4000;       // 0.5
        extraneous_gradient = 16'h1000; // 0.125
        run_mechanical_cycle();
        
        // --- 4. EXTREME REGRET (Slip Condition) ---
        // Force SSS Constant below -σ_sys
        extraneous_weight = 16'hFFFF;   // 1.0
        engram_length = 16'hFFFF;       // 1.0
        extraneous_gradient = 16'hFFFF; // 1.0
        $display("[%t] Injecting High Torsional Stress...", $time);
        
        // Mechanical Cycles (Wait for Survival Trigger Hysteresis)
        repeat (10) begin
            run_mechanical_cycle();
        end
        
        // --- 5. LIFT - RECOVERY ---
        $display("[%t] Reducing stress for Lift/Recovery phase...", $time);
        extraneous_weight = 16'h0000;
        repeat (5) begin
            run_mechanical_cycle();
        end
        
        $display("=============================================================================");
        $display("HARNESS COMPLETE - AUDIT TRACE LOGGED TO mechanical_cycle.vcd");
        $display("=============================================================================");
        $finish;
    end

endmodule

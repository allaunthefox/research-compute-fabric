// Testbench for Meta-Manifold Prover
// Tests: Mass Number gate, Torus distance, Menger hash, Fold energy, Surface check

#include <verilated.h>
#include <verilated_vcd_c.h>
#include "VMetaManifoldProver.h"

#include <iostream>
#include <iomanip>
#include <cstdint>

// Q16.16 fixed-point conversion
int32_t float_to_q16(float f) {
    return static_cast<int32_t>(f * 65536.0f);
}

float q16_to_float(int32_t q) {
    return static_cast<float>(q) / 65536.0f;
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);  // Enable tracing before time 0

    // Instantiate DUT
    VMetaManifoldProver* dut = new VMetaManifoldProver;

    // Clock
    vluint64_t sim_time = 0;
    vluint64_t clk_period = 10;  // 10 time units per clock cycle

    // Enable VCD tracing
    VerilatedVcdC* trace = new VerilatedVcdC;
    dut->trace(trace, 99);
    trace->open("metamanifold_prover_trace.vcd");

    // Reset
    dut->clk = 0;
    dut->rst_n = 0;
    dut->start = 0;
    dut->op_select = 0;

    // Reset sequence
    for (int i = 0; i < 5; i++) {
        dut->clk = !dut->clk;
        dut->eval();
        trace->dump(sim_time);
        sim_time += clk_period / 2;
    }

    dut->rst_n = 1;

    std::cout << "=== Meta-Manifold Prover Testbench ===" << std::endl;
    std::cout << std::fixed << std::setprecision(6);

    // Test 1: Mass Number gate (op_select = 000)
    std::cout << "\n--- Test 1: Mass Number Gate ---" << std::endl;
    dut->op_select = 0b000;

    // Test case: English-German merge (C_cross = 0.97, R = 0.03, threshold = 5.0)
    dut->admissible = float_to_q16(0.97f);
    dut->residual = float_to_q16(0.03f);
    dut->epsilon = float_to_q16(1.0f / 65536.0f);  // 1/65536
    dut->threshold = float_to_q16(5.0f);

    dut->start = 1;
    dut->clk = 0;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->clk = 1;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->start = 0;

    // Wait for completion
    for (int i = 0; i < 10; i++) {
        dut->clk = !dut->clk;
        dut->eval();
        trace->dump(sim_time);
        sim_time += clk_period / 2;
    }

    std::cout << "Admissible: " << q16_to_float(dut->admissible) << std::endl;
    std::cout << "Residual: " << q16_to_float(dut->residual) << std::endl;
    std::cout << "Threshold: " << q16_to_float(dut->threshold) << std::endl;
    std::cout << "MassLe Result: " << (dut->mass_le_result ? "TRUE" : "FALSE") << std::endl;
    std::cout << "Expected: TRUE (admissible at threshold 5.0)" << std::endl;

    // Test 2: Torus distance (op_select = 001)
    std::cout << "\n--- Test 2: Torus Distance ---" << std::endl;
    dut->op_select = 0b001;

    // Test case: node1 = [0,0,0,0,0], node2 = [8,4,4,4,2]
    dut->coord1 = 0x00000;  // [0,0,0,0,0]
    dut->coord2 = 0x84442;  // [8,4,4,4,2]

    dut->start = 1;
    dut->clk = 0;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->clk = 1;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->start = 0;

    for (int i = 0; i < 10; i++) {
        dut->clk = !dut->clk;
        dut->eval();
        trace->dump(sim_time);
        sim_time += clk_period / 2;
    }

    std::cout << "Torus Distance: " << dut->torus_distance << std::endl;
    std::cout << "Expected: 22 (8+4+4+4+2)" << std::endl;

    // Test 3: Menger hash (op_select = 010)
    std::cout << "\n--- Test 3: Menger Hash ---" << std::endl;
    dut->op_select = 0b010;

    // Test case: x=10, y=20, z=30, d_H=2.7268
    dut->menger_x = 10;
    dut->menger_y = 20;
    dut->menger_z = 30;
    dut->hausdorff_dim = float_to_q16(2.7268f);

    dut->start = 1;
    dut->clk = 0;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->clk = 1;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->start = 0;

    for (int i = 0; i < 10; i++) {
        dut->clk = !dut->clk;
        dut->eval();
        trace->dump(sim_time);
        sim_time += clk_period / 2;
    }

    std::cout << "Menger Address: " << dut->menger_address << std::endl;
    std::cout << "Expected: hash ^ offset (computed value)" << std::endl;

    // Test 4: Fold energy (op_select = 011)
    std::cout << "\n--- Test 4: Fold Energy ---" << std::endl;
    dut->op_select = 0b011;

    // Test case: E_torus=0.5, E_menger=0.161, E_horn=0.072, alpha=0.4, beta=0.35, gamma=0.25
    dut->torus_energy = float_to_q16(0.5f);
    dut->menger_energy = float_to_q16(0.161f);
    dut->horn_energy = float_to_q16(0.072f);
    dut->alpha = float_to_q16(0.4f);
    dut->beta = float_to_q16(0.35f);
    dut->gamma = float_to_q16(0.25f);

    dut->start = 1;
    dut->clk = 0;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->clk = 1;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->start = 0;

    for (int i = 0; i < 10; i++) {
        dut->clk = !dut->clk;
        dut->eval();
        trace->dump(sim_time);
        sim_time += clk_period / 2;
    }

    std::cout << "Fold Energy Total: " << q16_to_float(dut->fold_energy_total) << std::endl;
    std::cout << "Expected: ~0.258 (0.4*0.5 + 0.35*0.161 + 0.25*0.072)" << std::endl;

    // Test 5: Surface check (op_select = 100)
    std::cout << "\n--- Test 5: Surface Check ---" << std::endl;
    dut->op_select = 0b100;

    // Test case: height=5.0, ridge=0.97
    dut->surface_height = float_to_q16(5.0f);
    dut->surface_ridge = float_to_q16(0.97f);

    dut->start = 1;
    dut->clk = 0;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->clk = 1;
    dut->eval();
    trace->dump(sim_time);
    sim_time += clk_period / 2;

    dut->start = 0;

    for (int i = 0; i < 10; i++) {
        dut->clk = !dut->clk;
        dut->eval();
        trace->dump(sim_time);
        sim_time += clk_period / 2;
    }

    std::cout << "Surface Height: " << q16_to_float(dut->surface_height) << std::endl;
    std::cout << "Surface Ridge: " << q16_to_float(dut->surface_ridge) << std::endl;
    std::cout << "Surface Admissible: " << (dut->surface_admissible ? "TRUE" : "FALSE") << std::endl;
    std::cout << "Expected: TRUE (height >= ridge)" << std::endl;

    // Finish
    trace->close();
    delete dut;
    delete trace;

    std::cout << "\n=== Simulation Complete ===" << std::endl;
    std::cout << "Trace file: metamanifold_prover_trace.vcd" << std::endl;

    return 0;
}

// Test harness for wavefront emitter
#include <verilated.h>
#include "Vwavefront_emitter.h"
#include <iostream>
#include <iomanip>

int main(int argc, char** argv) {
    VerilatedContext* context = new VerilatedContext;
    context->commandArgs(argc, argv);

    Vwavefront_emitter* top = new Vwavefront_emitter(context);

    // Simulation
    vluint64_t sim_time = 0;

    // Reset
    top->rst_n = 0;
    top->clk = 0;
    top->amplitude_in = 0;
    top->frequency_in = 0;
    top->phase_in = 0;
    top->position_x = 0;
    top->position_y = 0;
    top->emit_trigger = 0;
    top->emitter_id = 0;

    for (int i = 0; i < 10; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    // Release reset
    top->rst_n = 1;

    std::cout << "=== Wavefront Emitter Simulation ===" << std::endl;
    std::cout << "Testing wavefront emission with different parameters" << std::endl;
    std::cout << std::endl;

    // Test 1: Default wavefront at origin
    std::cout << "Test 1: Default wavefront at origin" << std::endl;
    top->amplitude_in = 0x7FFF;  // 1.0
    top->frequency_in = 0x0CCC;  // 0.1
    top->phase_in = 0x0000;
    top->position_x = 0x0000;
    top->position_y = 0x0000;
    top->emitter_id = 0x0001;
    top->emit_trigger = 1;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->emit_trigger = 0;

    if (top->wavefront_valid) {
        std::cout << "  Wavefront value: 0x" << std::hex << std::setw(4) << std::setfill('0') << top->wavefront_value << std::dec << std::endl;
        std::cout << "  Expected: Maximum amplitude (distance = 0)" << std::endl;
    }
    std::cout << std::endl;

    // Test 2: Wavefront at distance
    std::cout << "Test 2: Wavefront at distance (decay effect)" << std::endl;
    top->position_x = 0x0064;  // 100 units
    top->position_y = 0x0064;  // 100 units
    top->emit_trigger = 1;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->emit_trigger = 0;

    if (top->wavefront_valid) {
        std::cout << "  Wavefront value: 0x" << std::hex << std::setw(4) << std::setfill('0') << top->wavefront_value << std::dec << std::endl;
        std::cout << "  Expected: Reduced amplitude due to decay" << std::endl;
    }
    std::cout << std::endl;

    // Test 3: High frequency wavefront
    std::cout << "Test 3: High frequency wavefront" << std::endl;
    top->position_x = 0x0000;
    top->position_y = 0x0000;
    top->frequency_in = 0x3FFF;  // 0.5
    top->emit_trigger = 1;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->emit_trigger = 0;

    if (top->wavefront_valid) {
        std::cout << "  Wavefront value: 0x" << std::hex << std::setw(4) << std::setfill('0') << top->wavefront_value << std::dec << std::endl;
        std::cout << "  Expected: Maximum amplitude with high frequency" << std::endl;
    }
    std::cout << std::endl;

    // Test 4: Low amplitude wavefront
    std::cout << "Test 4: Low amplitude wavefront" << std::endl;
    top->amplitude_in = 0x2000;  // 0.25
    top->frequency_in = 0x0CCC;  // 0.1
    top->emit_trigger = 1;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->emit_trigger = 0;

    if (top->wavefront_valid) {
        std::cout << "  Wavefront value: 0x" << std::hex << std::setw(4) << std::setfill('0') << top->wavefront_value << std::dec << std::endl;
        std::cout << "  Expected: Low amplitude wavefront" << std::endl;
    }
    std::cout << std::endl;

    delete top;
    delete context;

    std::cout << "=== Simulation Complete ===" << std::endl;

    return 0;
}

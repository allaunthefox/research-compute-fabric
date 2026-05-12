// Test harness for spectral encoder
#include <verilated.h>
#include "Vspectral_encoder.h"
#include <iostream>
#include <iomanip>

int main(int argc, char** argv) {
    VerilatedContext* context = new VerilatedContext;
    context->commandArgs(argc, argv);

    Vspectral_encoder* top = new Vspectral_encoder(context);

    // Simulation
    vluint64_t sim_time = 0;

    // Reset
    top->rst_n = 0;
    top->clk = 0;
    top->data_in = 0;
    top->data_valid = 0;
    top->event_type = 0;

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

    std::cout << "=== Spectral Encoder Simulation ===" << std::endl;
    std::cout << "Testing spectral encoding for genetic events (A, T, G, C)" << std::endl;
    std::cout << std::endl;

    // Test event A (event_type = 0)
    std::cout << "Test 1: Event A" << std::endl;
    top->event_type = 0;
    top->data_in = 0x41;  // 'A'
    top->data_valid = 1;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->data_valid = 0;

    if (top->spectral_valid) {
        std::cout << "  Spectral bins: ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin0 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin1 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin2 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin3 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin4 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin5 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin6 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin7 << " ";
        std::cout << std::dec << std::endl;
        std::cout << "  Expected: bin[0] = 0x7FFF, others = 0x0000" << std::endl;
    }
    std::cout << std::endl;

    // Test event T (event_type = 1)
    std::cout << "Test 2: Event T" << std::endl;
    top->event_type = 1;
    top->data_in = 0x54;  // 'T'
    top->data_valid = 1;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->data_valid = 0;

    if (top->spectral_valid) {
        std::cout << "  Spectral bins: ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin0 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin1 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin2 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin3 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin4 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin5 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin6 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin7 << " ";
        std::cout << std::dec << std::endl;
        std::cout << "  Expected: bin[1] = 0x7FFF, others = 0x0000" << std::endl;
    }
    std::cout << std::endl;

    // Test event G (event_type = 2)
    std::cout << "Test 3: Event G" << std::endl;
    top->event_type = 2;
    top->data_in = 0x47;  // 'G'
    top->data_valid = 1;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->data_valid = 0;

    if (top->spectral_valid) {
        std::cout << "  Spectral bins: ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin0 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin1 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin2 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin3 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin4 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin5 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin6 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin7 << " ";
        std::cout << std::dec << std::endl;
        std::cout << "  Expected: bin[2] = 0x7FFF, others = 0x0000" << std::endl;
    }
    std::cout << std::endl;

    // Test event C (event_type = 3)
    std::cout << "Test 4: Event C" << std::endl;
    top->event_type = 3;
    top->data_in = 0x43;  // 'C'
    top->data_valid = 1;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->data_valid = 0;

    if (top->spectral_valid) {
        std::cout << "  Spectral bins: ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin0 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin1 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin2 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin3 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin4 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin5 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin6 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin7 << " ";
        std::cout << std::dec << std::endl;
        std::cout << "  Expected: bin[3] = 0x7FFF, others = 0x0000" << std::endl;
    }
    std::cout << std::endl;

    // Test accumulation (multiple events)
    std::cout << "Test 5: Accumulation (A then T)" << std::endl;
    top->event_type = 0;
    top->data_in = 0x41;
    top->data_valid = 1;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->event_type = 1;
    top->data_in = 0x54;

    for (int i = 0; i < 5; i++) {
        top->clk = !top->clk;
        top->eval();
        sim_time++;
        top->clk = !top->clk;
        top->eval();
        sim_time++;
    }

    top->data_valid = 0;

    if (top->spectral_valid) {
        std::cout << "  Spectral bins: ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin0 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin1 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin2 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin3 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin4 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin5 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin6 << " ";
        std::cout << "0x" << std::hex << std::setw(4) << std::setfill('0') << top->bin7 << " ";
        std::cout << std::dec << std::endl;
        std::cout << "  Expected: bin[0] = 0x7FFF, bin[1] = 0x7FFF, others = 0x0000" << std::endl;
    }
    std::cout << std::endl;

    delete top;
    delete context;

    std::cout << "=== Simulation Complete ===" << std::endl;

    return 0;
}

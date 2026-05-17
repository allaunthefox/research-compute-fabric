// Verilator test harness for braid_serial.v
// Tests braid-encoded serial communication with loopback

#include "Vbraid_serial_top.h"
#include "verilated.h"
#include <iostream>
#include <iomanip>
#include <cstdint>

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);

    // Instantiate DUT
    Vbraid_serial_top* dut = new Vbraid_serial_top;

    // Simulation state
    uint64_t sim_time = 0;
    uint32_t tx_frame_num = 0;

    // Reset sequence
    dut->clk = 0;
    dut->rst_n = 0;
    dut->tx_start = 0;
    dut->tx_packet_type = 0;
    dut->tx_seq_num = 0;
    dut->tx_payload_len = 0;
    dut->tx_payload_data = 0;
    dut->tx_frame_num = 0;
    dut->rx_frame_valid = 0;
    dut->rx_phi_phase = 0;

    for (int i = 0; i < 8; i++) {
        dut->rx_wire_phase[i] = 0;
        dut->rx_wire_slot[i] = 0;
        dut->rx_wire_parity[i] = 0;
    }

    // Reset for 20 cycles
    for (int i = 0; i < 40; i++) {
        dut->clk = !dut->clk;
        dut->eval();
        sim_time++;
    }

    dut->rst_n = 1;

    std::cout << "=== Braid Serial Verilator Test ===" << std::endl;
    std::cout << "Reset complete, starting tests..." << std::endl << std::endl;

    // Test each modulation mode
    const char* mod_names[] = {"None (Direct)", "QPSK", "QAM-16", "DMT"};
    int mod_modes[] = {0, 1, 2, 3};

    for (int mod_idx = 0; mod_idx < 4; mod_idx++) {
        int mod_mode = mod_modes[mod_idx];
        std::cout << "=== Modulation Mode: " << mod_names[mod_idx] << " ===" << std::endl;

        // Set modulation mode
        dut->tx_modulation_mode = mod_mode;
        dut->rx_modulation_mode = mod_mode;

        // Test 1: Simple packet
        std::cout << "Test 1: Simple packet (type=0x01, seq=0x0001, payload=0xDEADBEEFCAFEBABE)" << std::endl;
        dut->tx_packet_type = 0x01;
        dut->tx_seq_num = 0x0001;
        dut->tx_payload_len = 8;
        dut->tx_payload_data = 0xDEADBEEFCAFEBABEULL;
        dut->tx_frame_num = tx_frame_num;

        // Note: With 8 wires, only lower 32 bits of payload can be transmitted
        // Expected: lower 32 bits = 0xCAFEBABE
        // For QPSK/QAM-16, only lower bits are used, so expect different values

        // Wait for data to stabilize
        for (int i = 0; i < 5; i++) {
            dut->clk = !dut->clk;
            dut->eval();
            sim_time++;
            dut->clk = !dut->clk;
            dut->eval();
            sim_time++;
        }

        dut->tx_start = 1;

        // Clock cycle with encode_start asserted
        for (int i = 0; i < 5; i++) {
            dut->clk = !dut->clk;
            dut->eval();
            sim_time++;
            dut->clk = !dut->clk;
            dut->eval();
            sim_time++;

            // Loopback: connect TX to RX
            if (dut->tx_frame_valid) {
                dut->rx_frame_valid = dut->tx_frame_valid;
                dut->rx_phi_phase = dut->tx_phi_phase;
                for (int j = 0; j < 8; j++) {
                    dut->rx_wire_phase[j] = dut->tx_wire_phase[j];
                    dut->rx_wire_slot[j] = dut->tx_wire_slot[j];
                    dut->rx_wire_parity[j] = dut->tx_wire_parity[j];
                    dut->rx_wire_amplitude[j] = dut->tx_wire_amplitude[j];
                }
            } else {
                dut->rx_frame_valid = 0;
            }

            // Check for decode completion
            if (dut->rx_decode_valid) {
                std::cout << "  Decoded: type=0x" << std::hex << (uint32_t)dut->rx_packet_type
                          << ", seq=0x" << dut->rx_seq_num
                          << ", len=0x" << (uint32_t)dut->rx_payload_len
                          << ", data=0x" << dut->rx_payload_data << std::dec
                          << ", valid=" << dut->rx_decode_valid
                          << ", admissible=" << dut->rx_admissible << std::endl;

                // Verify roundtrip based on modulation mode
                uint64_t expected_data;
                uint8_t expected_type = 0x01;
                uint16_t expected_seq = 0x0001;
                uint8_t expected_len = 8;

                if (mod_mode == 0) {
                    // Direct mode: expect full byte values
                    expected_data = 0xCAFEBABEULL;
                } else if (mod_mode == 1) {
                    // QPSK: only lower 2 bits per byte are preserved
                    expected_data = 0xCAFEBABEULL & 0x03030303ULL;  // Mask to lower 2 bits
                    expected_type = 0x01 & 0x03;
                    expected_seq = 0x0001 & 0x0303;
                    expected_len = 8 & 0x03;  // 8 = 0x08 -> lower 2 bits = 0x00
                } else if (mod_mode == 2) {
                    // QAM-16: only lower 4 bits per byte are preserved
                    expected_data = 0xCAFEBABEULL & 0x0F0F0F0FULL;  // Mask to lower 4 bits
                    expected_type = 0x01 & 0x0F;
                    expected_seq = 0x0001 & 0x0F0F;
                } else {
                    // DMT: full byte with subcarrier offset - should work like direct
                    expected_data = 0xCAFEBABEULL;
                }

                bool type_match = (dut->rx_packet_type == expected_type);
                bool seq_match = (dut->rx_seq_num == expected_seq);
                bool len_match = (dut->rx_payload_len == expected_len);
                bool data_match = (dut->rx_payload_data == expected_data);

                if (type_match && seq_match && len_match && data_match && dut->rx_admissible) {
                    std::cout << "  ✓ Test 1 PASSED" << std::endl;
                } else {
                    std::cout << "  ✗ Test 1 FAILED" << std::endl;
                    std::cout << "    Type match: " << type_match << std::endl;
                    std::cout << "    Seq match: " << seq_match << std::endl;
                    std::cout << "    Len match: " << len_match << std::endl;
                    std::cout << "    Data match: " << data_match << std::endl;
                    std::cout << "    Admissible: " << dut->rx_admissible << std::endl;
                }
                break;
            }
        }

        dut->tx_start = 0;

        // Clear decoder state
        for (int k = 0; k < 10; k++) {
            dut->rx_frame_valid = 0;
            dut->clk = !dut->clk;
            dut->eval();
            sim_time++;
            dut->clk = !dut->clk;
            dut->eval();
            sim_time++;
        }

        std::cout << std::endl;
    }
    std::cout << "=== Simulation Complete ===" << std::endl;
    std::cout << "Total simulation cycles: " << sim_time << std::endl;

    dut->final();
    delete dut;

    return 0;
}

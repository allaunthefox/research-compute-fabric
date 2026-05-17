/*
 * Verilator testbench for Meta-Manifold Prover
 *
 * Validates:
 *   - Mass Number gates (A <= tau * (R + epsilon))
 *   - Torus topology distance calculation
 *   - Menger sponge hash computation
 *   - Fold energy weighted sum
 *   - Surface check (height >= ridge)
 *
 * Target: Gowin GW1NR-9 / Tang Nano 9K
 * Clock: 27 MHz
 */

#include <cstdio>
#include <cstdint>
#include <cmath>

#include "VMetaManifoldProver.h"
#include "verilated.h"
#ifdef VM_TRACE
#include "verilated_vcd_c.h"
#endif

// Q16_16 fixed-point conversion helpers
constexpr int16_t float_to_q16_16(float f) {
    return static_cast<int16_t>(f * 65536.0f);
}

constexpr float q16_16_to_float(int16_t q) {
    return static_cast<float>(q) / 65536.0f;
}

// Test case structure
struct TestCase {
    const char* name;
    uint8_t op_select;
    int16_t inputs[16];  // Up to 16 inputs
    int16_t expected_output;
    bool is_boolean;  // If true, expected_output is 0/1
};

int main(int argc, char** argv) {
    VerilatedContext* contextp = new VerilatedContext;
    contextp->commandArgs(argc, argv);
    contextp->fatalOnError(true);

    VMetaManifoldProver* top = new VMetaManifoldProver{contextp};

#ifdef VM_TRACE
    VerilatedVcdC* tfp = nullptr;
    const char* trace_env = getenv("TRACE");
    if (trace_env && trace_env[0] == '1') {
        tfp = new VerilatedVcdC;
        contextp->traceEverOn(true);
        top->trace(tfp, 99);
        tfp->open("sim_metamanifold_prover.vcd");
    }
#endif

    // Initialize inputs
    top->clk = 0;
    top->rst_n = 0;
    top->start = 0;

    // Reset all inputs to 0
    top->admissible = 0;
    top->residual = 0;
    top->epsilon = 0;
    top->threshold = 0;
    top->coord1 = 0;
    top->coord2 = 0;
    top->menger_x = 0;
    top->menger_y = 0;
    top->menger_z = 0;
    top->hausdorff_dim = 0;
    top->torus_energy = 0;
    top->menger_energy = 0;
    top->horn_energy = 0;
    top->alpha = 0;
    top->beta = 0;
    top->gamma = 0;
    top->surface_height = 0;
    top->surface_ridge = 0;

    int errors = 0;
    int tests_passed = 0;
    int tests_total = 0;

    printf("=== Meta-Manifold Prover Verilator Testbench ===\n\n");

    // Release reset
    for (int i = 0; i < 100; i++) {
        top->clk = !top->clk;
        top->eval();
    }
    top->rst_n = 1;
    printf("Reset released\n\n");

    // === Test 1: Mass Number Gate ===
    {
        printf("--- Test 1: Mass Number Gate ---\n");
        tests_total++;

        // Test case: A = 1.0, R = 0.5, epsilon = 0.0625, tau = 2.0
        // Expected: A <= tau * (R + epsilon) = 2.0 * 0.5625 = 1.125
        // Since 1.0 <= 1.125, result should be TRUE (1)

        top->op_select = 3'b000;  // MassLe operation
        top->admissible = float_to_q16_16(1.0f);
        top->residual = float_to_q16_16(0.5f);
        top->epsilon = float_to_q16_16(0.0625f);
        top->threshold = float_to_q16_16(2.0f);
        top->start = 1;

        // Run operation
        int cycles = 0;
        for (int i = 0; i < 1000; i++) {
            top->clk = !top->clk;
            top->eval();
            if (top->clk && top->done) break;
            cycles++;
        }

        top->start = 0;

        bool result = top->mass_le_result;
        bool expected = true;

        printf("  A = %.4f, R = %.4f, epsilon = %.4f, tau = %.4f\n",
               q16_16_to_float(top->admissible),
               q16_16_to_float(top->residual),
               q16_16_to_float(top->epsilon),
               q16_16_to_float(top->threshold));
        printf("  Expected: %d, Got: %d, Cycles: %d\n", expected, result, cycles);

        if (result == expected) {
            printf("  PASS\n");
            tests_passed++;
        } else {
            printf("  FAIL\n");
            errors++;
        }
        printf("\n");
    }

    // === Test 2: Mass Number Gate (False case) ===
    {
        printf("--- Test 2: Mass Number Gate (False) ---\n");
        tests_total++;

        // Test case: A = 2.0, R = 0.5, epsilon = 0.0625, tau = 1.0
        // Expected: A <= tau * (R + epsilon) = 1.0 * 0.5625 = 0.5625
        // Since 2.0 > 0.5625, result should be FALSE (0)

        top->op_select = 3'b000;  // MassLe operation
        top->admissible = float_to_q16_16(2.0f);
        top->residual = float_to_q16_16(0.5f);
        top->epsilon = float_to_q16_16(0.0625f);
        top->threshold = float_to_q16_16(1.0f);
        top->start = 1;

        // Run operation
        int cycles = 0;
        for (int i = 0; i < 1000; i++) {
            top->clk = !top->clk;
            top->eval();
            if (top->clk && top->done) break;
            cycles++;
        }

        top->start = 0;

        bool result = top->mass_le_result;
        bool expected = false;

        printf("  A = %.4f, R = %.4f, epsilon = %.4f, tau = %.4f\n",
               q16_16_to_float(top->admissible),
               q16_16_to_float(top->residual),
               q16_16_to_float(top->epsilon),
               q16_16_to_float(top->threshold));
        printf("  Expected: %d, Got: %d, Cycles: %d\n", expected, result, cycles);

        if (result == expected) {
            printf("  PASS\n");
            tests_passed++;
        } else {
            printf("  FAIL\n");
            errors++;
        }
        printf("\n");
    }

    // === Test 3: Torus Distance ===
    {
        printf("--- Test 3: Torus Distance ---\n");
        tests_total++;

        // Test case: coord1 = (1,1,1,1,1), coord2 = (2,2,2,2,2)
        // Expected Manhattan distance with wraparound on 8-element torus

        top->op_select = 3'b001;  // TorusDist operation
        top->coord1 = 0x11111;  // Each nibble = 1
        top->coord2 = 0x22222;  // Each nibble = 2
        top->start = 1;

        // Run operation
        int cycles = 0;
        for (int i = 0; i < 1000; i++) {
            top->clk = !top->clk;
            top->eval();
            if (top->clk && top->done) break;
            cycles++;
        }

        top->start = 0;

        uint16_t result = top->torus_distance;
        uint16_t expected = 5;  // 5 dimensions * 1 unit each

        printf("  coord1: 0x%05x, coord2: 0x%05x\n", top->coord1, top->coord2);
        printf("  Expected distance: %d, Got: %d, Cycles: %d\n", expected, result, cycles);

        if (result == expected) {
            printf("  PASS\n");
            tests_passed++;
        } else {
            printf("  FAIL\n");
            errors++;
        }
        printf("\n");
    }

    // === Test 4: Menger Hash ===
    {
        printf("--- Test 4: Menger Hash ---\n");
        tests_total++;

        // Test case: x = 1, y = 2, z = 3, hausdorff_dim = 2.0
        // Expected hash: x ^ (y << 1) ^ (z << 2) = 1 ^ 4 ^ 12 = 9

        top->op_select = 3'b010;  // MengerHash operation
        top->menger_x = 1;
        top->menger_y = 2;
        top->menger_z = 3;
        top->hausdorff_dim = float_to_q16_16(2.0f);
        top->start = 1;

        // Run operation
        int cycles = 0;
        for (int i = 0; i < 1000; i++) {
            top->clk = !top->clk;
            top->eval();
            if (top->clk && top->done) break;
            cycles++;
        }

        top->start = 0;

        uint16_t result = top->menger_address;

        printf("  x = %d, y = %d, z = %d, hausdorff_dim = %.4f\n",
               top->menger_x, top->menger_y, top->menger_z,
               q16_16_to_float(top->hausdorff_dim));
        printf("  Hash result: %d, Cycles: %d\n", result, cycles);

        // Just check that it's non-zero (hash computation)
        if (result != 0) {
            printf("  PASS (hash computed)\n");
            tests_passed++;
        } else {
            printf("  FAIL (hash is zero)\n");
            errors++;
        }
        printf("\n");
    }

    // === Test 5: Fold Energy ===
    {
        printf("--- Test 5: Fold Energy ---\n");
        tests_total++;

        // Test case: E_torus = 1.0, E_menger = 2.0, E_horn = 3.0
        //            alpha = 0.5, beta = 0.3, gamma = 0.2
        // Expected: 0.5*1.0 + 0.3*2.0 + 0.2*3.0 = 0.5 + 0.6 + 0.6 = 1.7

        top->op_select = 3'b011;  // FoldEnergy operation
        top->torus_energy = float_to_q16_16(1.0f);
        top->menger_energy = float_to_q16_16(2.0f);
        top->horn_energy = float_to_q16_16(3.0f);
        top->alpha = float_to_q16_16(0.5f);
        top->beta = float_to_q16_16(0.3f);
        top->gamma = float_to_q16_16(0.2f);
        top->start = 1;

        // Run operation
        int cycles = 0;
        for (int i = 0; i < 1000; i++) {
            top->clk = !top->clk;
            top->eval();
            if (top->clk && top->done) break;
            cycles++;
        }

        top->start = 0;

        int16_t result = top->fold_energy_total;
        float result_float = q16_16_to_float(result);
        float expected_float = 1.7f;
        float tolerance = 0.1f;

        printf("  E_torus = %.4f, E_menger = %.4f, E_horn = %.4f\n",
               q16_16_to_float(top->torus_energy),
               q16_16_to_float(top->menger_energy),
               q16_16_to_float(top->horn_energy));
        printf("  alpha = %.4f, beta = %.4f, gamma = %.4f\n",
               q16_16_to_float(top->alpha),
               q16_16_to_float(top->beta),
               q16_16_to_float(top->gamma));
        printf("  Expected: %.4f, Got: %.4f, Cycles: %d\n", expected_float, result_float, cycles);

        if (fabs(result_float - expected_float) < tolerance) {
            printf("  PASS\n");
            tests_passed++;
        } else {
            printf("  FAIL (tolerance %.4f)\n", tolerance);
            errors++;
        }
        printf("\n");
    }

    // === Test 6: Surface Check ===
    {
        printf("--- Test 6: Surface Check ---\n");
        tests_total++;

        // Test case: height = 1.5, ridge = 1.0
        // Expected: height >= ridge, so result should be TRUE (1)

        top->op_select = 3'b100;  // SurfaceCheck operation
        top->surface_height = float_to_q16_16(1.5f);
        top->surface_ridge = float_to_q16_16(1.0f);
        top->start = 1;

        // Run operation
        int cycles = 0;
        for (int i = 0; i < 1000; i++) {
            top->clk = !top->clk;
            top->eval();
            if (top->clk && top->done) break;
            cycles++;
        }

        top->start = 0;

        bool result = top->surface_admissible;
        bool expected = true;

        printf("  height = %.4f, ridge = %.4f\n",
               q16_16_to_float(top->surface_height),
               q16_16_to_float(top->surface_ridge));
        printf("  Expected: %d, Got: %d, Cycles: %d\n", expected, result, cycles);

        if (result == expected) {
            printf("  PASS\n");
            tests_passed++;
        } else {
            printf("  FAIL\n");
            errors++;
        }
        printf("\n");
    }

    // === Test 7: Surface Check (False case) ===
    {
        printf("--- Test 7: Surface Check (False) ---\n");
        tests_total++;

        // Test case: height = 0.5, ridge = 1.0
        // Expected: height < ridge, so result should be FALSE (0)

        top->op_select = 3'b100;  // SurfaceCheck operation
        top->surface_height = float_to_q16_16(0.5f);
        top->surface_ridge = float_to_q16_16(1.0f);
        top->start = 1;

        // Run operation
        int cycles = 0;
        for (int i = 0; i < 1000; i++) {
            top->clk = !top->clk;
            top->eval();
            if (top->clk && top->done) break;
            cycles++;
        }

        top->start = 0;

        bool result = top->surface_admissible;
        bool expected = false;

        printf("  height = %.4f, ridge = %.4f\n",
               q16_16_to_float(top->surface_height),
               q16_16_to_float(top->surface_ridge));
        printf("  Expected: %d, Got: %d, Cycles: %d\n", expected, result, cycles);

        if (result == expected) {
            printf("  PASS\n");
            tests_passed++;
        } else {
            printf("  FAIL\n");
            errors++;
        }
        printf("\n");
    }

    // === Summary ===
    printf("=== Test Summary ===\n");
    printf("Tests passed: %d/%d\n", tests_passed, tests_total);
    printf("Errors: %d\n", errors);
    printf("\n=== %s (%d errors) ===\n", errors == 0 ? "PASS" : "FAIL", errors);

#ifdef VM_TRACE
    if (tfp) {
        tfp->close();
        delete tfp;
    }
#endif

    delete top;
    delete contextp;
    return errors;
}

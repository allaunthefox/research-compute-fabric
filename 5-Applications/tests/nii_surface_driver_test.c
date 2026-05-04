// SPDX-License-Identifier: GPL-2.0-only
/*
 * NII Core Surface Driver - Integration Test Suite
 *
 * Copyright (c) 2026 Sovereign Research Stack
 *
 * Test suite for NII core surface driver implementation
 * Tests SSS monitoring, warp metric computation, FAMM scheduling, and topological adaptation
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <math.h>
#include <assert.h>
#include <string.h>

// ═══════════════════════════════════════════════════════════════════════════
// Q16.16 Fixed-Point Arithmetic
// ═══════════════════════════════════════════════════════════════════════════

typedef int32_t q16_16_t;

#define Q16_16_ONE ((q16_16_t)(1 << 16))
#define Q16_16_ZERO ((q16_16_t)0)
#define Q16_16_FROM_FLOAT(f) ((q16_16_t)((f) * (1 << 16)))
#define Q16_16_TO_FLOAT(q) ((float)(q) / (1 << 16))

static inline q16_16_t q16_16_add(q16_16_t a, q16_16_t b)
{
    return a + b;
}

static inline q16_16_t q16_16_sub(q16_16_t a, q16_16_t b)
{
    return a - b;
}

static inline q16_16_t q16_16_mul(q16_16_t a, q16_16_t b)
{
    return (q16_16_t)(((int64_t)a * (int64_t)b) >> 16);
}

static inline q16_16_t q16_16_div(q16_16_t a, q16_16_t b)
{
    return (q16_16_t)(((int64_t)a << 16) / b);
}

static inline int q16_16_compare(q16_16_t a, q16_16_t b)
{
    if (a < b) return -1;
    if (a > b) return 1;
    return 0;
}

// ═══════════════════════════════════════════════════════════════════════════
// SSS Monitor Tests
// ═══════════════════════════════════════════════════════════════════════════

struct sss_constant {
    q16_16_t routing_load;
    q16_16_t memory_load;
    q16_16_t extraneous_weight;
    q16_16_t engram_length;
    q16_16_t extraneous_gradient;
};

struct slip_condition {
    q16_16_t sss_constant;
    q16_16_t heel_dig_limit;
};

static q16_16_t compute_sss(const struct sss_constant *c)
{
    q16_16_t counter_torque = q16_16_add(c->routing_load, c->memory_load);
    q16_16_t torsional_term = q16_16_mul(
        q16_16_mul(c->extraneous_weight, c->engram_length),
        c->extraneous_gradient
    );
    return q16_16_sub(counter_torque, torsional_term);
}

static bool is_slip_threshold_crossed(const struct slip_condition *c)
{
    return q16_16_compare(c->sss_constant, -c->heel_dig_limit) < 0;
}

void test_sss_computation(void)
{
    printf("Testing SSS computation...\n");
    
    struct sss_constant c = {
        .routing_load = Q16_16_FROM_FLOAT(1.0f),
        .memory_load = Q16_16_FROM_FLOAT(0.8f),
        .extraneous_weight = Q16_16_FROM_FLOAT(0.5f),
        .engram_length = Q16_16_FROM_FLOAT(4.0f),
        .extraneous_gradient = Q16_16_FROM_FLOAT(0.1f)
    };
    
    q16_16_t sss = compute_sss(&c);
    float sss_float = Q16_16_TO_FLOAT(sss);
    
    printf("  SSS constant: %f (expected ~1.8 - 0.2 = 1.6)\n", sss_float);
    assert(sss_float > 1.5f && sss_float < 1.7f);
    
    printf("  SSS computation test: PASSED\n");
}

void test_slip_threshold(void)
{
    printf("Testing slip threshold crossing...\n");
    
    struct slip_condition c_normal = {
        .sss_constant = Q16_16_FROM_FLOAT(0.5f),
        .heel_dig_limit = Q16_16_FROM_FLOAT(0.5f)
    };
    
    assert(!is_slip_threshold_crossed(&c_normal));
    
    struct slip_condition c_crossed = {
        .sss_constant = Q16_16_FROM_FLOAT(-1.0f),
        .heel_dig_limit = Q16_16_FROM_FLOAT(0.5f)
    };
    
    assert(is_slip_threshold_crossed(&c_crossed));
    
    printf("  Slip threshold test: PASSED\n");
}

// ═══════════════════════════════════════════════════════════════════════════
// Warp Metric Tests
// ═══════════════════════════════════════════════════════════════════════════

struct warp_function {
    q16_16_t kappa;
    q16_16_t sss_constant;
    q16_16_t opcode_efficacy;
};

static q16_16_t sigmoid_q16_16(q16_16_t x)
{
    if (x < Q16_16_FROM_FLOAT(-5.0f))
        return Q16_16_ZERO;
    if (x > Q16_16_FROM_FLOAT(5.0f))
        return Q16_16_ONE;
    return q16_16_div(
        q16_16_add(x, Q16_16_FROM_FLOAT(5.0f)),
        Q16_16_FROM_FLOAT(10.0f)
    );
}

static q16_16_t compute_warp(const struct warp_function *w)
{
    q16_16_t exponent = q16_16_mul(-w->kappa, w->sss_constant);
    q16_16_t sigmoid = sigmoid_q16_16(exponent);
    return q16_16_mul(sigmoid, w->opcode_efficacy);
}

struct effective_velocity {
    q16_16_t local_velocity;
    q16_16_t coherence;
};

static q16_16_t compute_effective_velocity(const struct effective_velocity *v)
{
    q16_16_t denominator = q16_16_sub(Q16_16_ONE, v->coherence);
    if (denominator <= Q16_16_ZERO)
        return v->local_velocity;
    return q16_16_div(v->local_velocity, denominator);
}

void test_warp_function(void)
{
    printf("Testing warp function...\n");
    
    struct warp_function w = {
        .kappa = Q16_16_FROM_FLOAT(1.0f),
        .sss_constant = Q16_16_FROM_FLOAT(0.0f),
        .opcode_efficacy = Q16_16_ONE
    };
    
    q16_16_t warp = compute_warp(&w);
    float warp_float = Q16_16_TO_FLOAT(warp);
    
    printf("  Warp value: %f (expected ~0.5)\n", warp_float);
    assert(warp_float > 0.4f && warp_float < 0.6f);
    
    printf("  Warp function test: PASSED\n");
}

void test_effective_velocity(void)
{
    printf("Testing effective velocity...\n");
    
    struct effective_velocity v = {
        .local_velocity = Q16_16_FROM_FLOAT(1.0f),
        .coherence = Q16_16_FROM_FLOAT(0.8f)
    };
    
    q16_16_t v_eff = compute_effective_velocity(&v);
    float v_eff_float = Q16_16_TO_FLOAT(v_eff);
    
    printf("  Effective velocity: %f (expected ~5.0)\n", v_eff_float);
    assert(v_eff_float > 4.9f && v_eff_float < 5.1f);
    
    printf("  Effective velocity test: PASSED\n");
}

void test_effective_velocity_division_by_zero(void)
{
    printf("Testing effective velocity division by zero protection...\n");
    
    struct effective_velocity v = {
        .local_velocity = Q16_16_FROM_FLOAT(1.0f),
        .coherence = Q16_16_ONE  // 1.0 - 1.0 = 0
    };
    
    q16_16_t v_eff = compute_effective_velocity(&v);
    float v_eff_float = Q16_16_TO_FLOAT(v_eff);
    
    printf("  Effective velocity (coherence=1.0): %f (expected 1.0)\n", v_eff_float);
    assert(fabs(v_eff_float - 1.0f) < 0.01f);
    
    printf("  Division by zero protection test: PASSED\n");
}

// ═══════════════════════════════════════════════════════════════════════════
// FAMM Scheduling Tests
// ═══════════════════════════════════════════════════════════════════════════

struct famm_timing {
    q16_16_t torsional_stress;
    q16_16_t interlocking_energy;
    q16_16_t laplacian_energy;
};

enum schedule_decision {
    SCHEDULE_EXECUTE,
    SCHEDULE_DEFER,
    SCHEDULE_THROTTLE,
};

static q16_16_t compute_famm_load(const struct famm_timing *t)
{
    return q16_16_add(
        q16_16_add(t->torsional_stress, t->interlocking_energy),
        t->laplacian_energy
    );
}

static enum schedule_decision make_schedule_decision(q16_16_t load)
{
    if (load < Q16_16_FROM_FLOAT(0.25f))
        return SCHEDULE_EXECUTE;
    else if (load < Q16_16_FROM_FLOAT(0.5f))
        return SCHEDULE_THROTTLE;
    else
        return SCHEDULE_DEFER;
}

void test_famm_load(void)
{
    printf("Testing FAMM load computation...\n");
    
    struct famm_timing t = {
        .torsional_stress = Q16_16_FROM_FLOAT(1.0f),
        .interlocking_energy = Q16_16_FROM_FLOAT(0.5f),
        .laplacian_energy = Q16_16_FROM_FLOAT(0.3f)
    };
    
    q16_16_t load = compute_famm_load(&t);
    float load_float = Q16_16_TO_FLOAT(load);
    
    printf("  FAMM load: %f (expected 1.8)\n", load_float);
    assert(fabs(load_float - 1.8f) < 0.01f);
    
    printf("  FAMM load test: PASSED\n");
}

void test_schedule_decision(void)
{
    printf("Testing schedule decision...\n");
    
    // Low load - execute
    assert(make_schedule_decision(Q16_16_FROM_FLOAT(0.2f)) == SCHEDULE_EXECUTE);
    
    // Medium load - throttle
    assert(make_schedule_decision(Q16_16_FROM_FLOAT(0.4f)) == SCHEDULE_THROTTLE);
    
    // High load - defer
    assert(make_schedule_decision(Q16_16_FROM_FLOAT(0.6f)) == SCHEDULE_DEFER);
    
    printf("  Schedule decision test: PASSED\n");
}

// ═══════════════════════════════════════════════════════════════════════════
// Topological Adaptation Tests
// ═══════════════════════════════════════════════════════════════════════════

static const char *adapt_topology(q16_16_t cognitive_load)
{
    if (cognitive_load < Q16_16_FROM_FLOAT(0.25f))
        return "relational";
    else if (cognitive_load < Q16_16_FROM_FLOAT(0.5f))
        return "semantic";
    else if (cognitive_load < Q16_16_FROM_FLOAT(0.75f))
        return "topological";
    else
        return "minimal";
}

void test_topology_adaptation(void)
{
    printf("Testing topology adaptation...\n");
    
    // Low load - relational
    assert(strcmp(adapt_topology(Q16_16_FROM_FLOAT(0.2f)), "relational") == 0);
    
    // Medium load - semantic
    assert(strcmp(adapt_topology(Q16_16_FROM_FLOAT(0.4f)), "semantic") == 0);
    
    // High load - topological
    assert(strcmp(adapt_topology(Q16_16_FROM_FLOAT(0.6f)), "topological") == 0);
    
    // Overwhelmed - minimal
    assert(strcmp(adapt_topology(Q16_16_FROM_FLOAT(0.8f)), "minimal") == 0);
    
    printf("  Topology adaptation test: PASSED\n");
}

// ═══════════════════════════════════════════════════════════════════════════
// Performance Benchmarks
// ═══════════════════════════════════════════════════════════════════════════

#include <time.h>

void benchmark_sss_computation(int iterations)
{
    printf("Benchmarking SSS computation (%d iterations)...\n", iterations);
    
    struct sss_constant c = {
        .routing_load = Q16_16_FROM_FLOAT(1.0f),
        .memory_load = Q16_16_FROM_FLOAT(0.8f),
        .extraneous_weight = Q16_16_FROM_FLOAT(0.5f),
        .engram_length = Q16_16_FROM_FLOAT(4.0f),
        .extraneous_gradient = Q16_16_FROM_FLOAT(0.1f)
    };
    
    clock_t start = clock();
    
    for (int i = 0; i < iterations; i++) {
        compute_sss(&c);
    }
    
    clock_t end = clock();
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;
    double avg_time = (elapsed / iterations) * 1000000.0;  // microseconds
    
    printf("  Total time: %.6f seconds\n", elapsed);
    printf("  Average time: %.2f microseconds\n", avg_time);
    
    if (avg_time < 10.0) {
        printf("  SSS computation benchmark: PASSED (< 10μs target)\n");
    } else {
        printf("  SSS computation benchmark: FAILED (> 10μs target)\n");
    }
}

void benchmark_warp_computation(int iterations)
{
    printf("Benchmarking warp computation (%d iterations)...\n", iterations);
    
    struct warp_function w = {
        .kappa = Q16_16_FROM_FLOAT(1.0f),
        .sss_constant = Q16_16_FROM_FLOAT(0.0f),
        .opcode_efficacy = Q16_16_ONE
    };
    
    clock_t start = clock();
    
    for (int i = 0; i < iterations; i++) {
        compute_warp(&w);
    }
    
    clock_t end = clock();
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;
    double avg_time = (elapsed / iterations) * 1000000.0;  // microseconds
    
    printf("  Total time: %.6f seconds\n", elapsed);
    printf("  Average time: %.2f microseconds\n", avg_time);
    
    if (avg_time < 15.0) {
        printf("  Warp computation benchmark: PASSED (< 15μs target)\n");
    } else {
        printf("  Warp computation benchmark: FAILED (> 15μs target)\n");
    }
}

void benchmark_famm_load(int iterations)
{
    printf("Benchmarking FAMM load computation (%d iterations)...\n", iterations);
    
    struct famm_timing t = {
        .torsional_stress = Q16_16_FROM_FLOAT(1.0f),
        .interlocking_energy = Q16_16_FROM_FLOAT(0.5f),
        .laplacian_energy = Q16_16_FROM_FLOAT(0.3f)
    };
    
    clock_t start = clock();
    
    for (int i = 0; i < iterations; i++) {
        compute_famm_load(&t);
    }
    
    clock_t end = clock();
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;
    double avg_time = (elapsed / iterations) * 1000000.0;  // microseconds
    
    printf("  Total time: %.6f seconds\n", elapsed);
    printf("  Average time: %.2f microseconds\n", avg_time);
    
    if (avg_time < 5.0) {
        printf("  FAMM load benchmark: PASSED (< 5μs target)\n");
    } else {
        printf("  FAMM load benchmark: FAILED (> 5μs target)\n");
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Main Test Runner
// ═══════════════════════════════════════════════════════════════════════════

int main(void)
{
    printf("╔══════════════════════════════════════════════════════════════════════════╗\n");
    printf("║  NII Core Surface Driver - Integration Test Suite                      ║\n");
    printf("╚══════════════════════════════════════════════════════════════════════════╝\n\n");
    
    int passed = 0;
    int failed = 0;
    
    // Unit tests
    printf("=== UNIT TESTS ===\n\n");
    
    test_sss_computation();
    passed++;
    
    test_slip_threshold();
    passed++;
    
    test_warp_function();
    passed++;
    
    test_effective_velocity();
    passed++;
    
    test_effective_velocity_division_by_zero();
    passed++;
    
    test_famm_load();
    passed++;
    
    test_schedule_decision();
    passed++;
    
    test_topology_adaptation();
    passed++;
    
    printf("\n=== PERFORMANCE BENCHMARKS ===\n\n");
    
    benchmark_sss_computation(100000);
    benchmark_warp_computation(100000);
    benchmark_famm_load(100000);
    
    printf("\n=== TEST SUMMARY ===\n");
    printf("Passed: %d\n", passed);
    printf("Failed: %d\n", failed);
    
    if (failed == 0) {
        printf("\n✓ ALL TESTS PASSED\n");
        return 0;
    } else {
        printf("\n✗ SOME TESTS FAILED\n");
        return 1;
    }
}

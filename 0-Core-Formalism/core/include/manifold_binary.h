// SPDX-License-Identifier: MIT
/*
 * Manifold Binary Serialization Format
 * C struct layout + Python ctypes bindings
 *
 * Purpose: Zero-copy binary serialization of PIST/SVQF/FAMM manifold state
 * for GPU upload, network transmission, and disk persistence.
 *
 * Alignment: 8-byte aligned for SIMD/GPU compatibility
 * Endianness: Little-endian (host-native for x86_64/ARM64)
 * Version: 1
 */

#ifndef MANIFOLD_BINARY_H
#define MANIFOLD_BINARY_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ═══════════════════════════════════════════════════════════════════════════
// Header
// ═══════════════════════════════════════════════════════════════════════════

#define MANIFOLD_MAGIC 0x4D414E49  // "MANI" in ASCII
#define MANIFOLD_VERSION 1

typedef struct __attribute__((packed)) {
    uint32_t magic;          // MANIFOLD_MAGIC
    uint16_t version;        // MANIFOLD_VERSION
    uint16_t flags;          // Bitmask: 1=compressed, 2=encrypted, 4=has_frustration
    uint64_t timestamp_ns;   // Monotonic nanoseconds
    uint32_t num_shells;     // PIST shell count
    uint32_t num_points;     // Total quaternion points
    uint32_t num_edges;      // Braid / graph edges
    uint32_t reserved;       // Padding to 8-byte boundary
} ManifoldHeader;

// ═══════════════════════════════════════════════════════════════════════════
// Q16.16 Fixed-Point (matches FixedPoint.lean and nii_surface_driver.c)
// ═══════════════════════════════════════════════════════════════════════════

typedef int32_t q16_16_t;

#define Q16_16_ONE ((q16_16_t)(1 << 16))
#define Q16_16_ZERO ((q16_16_t)0)

static inline q16_16_t q16_16_from_float(float f) {
    return (q16_16_t)(f * (1 << 16));
}

static inline float q16_16_to_float(q16_16_t q) {
    return (float)q / (1 << 16);
}

// ═══════════════════════════════════════════════════════════════════════════
// Quaternion Point on S³ (4D unit sphere)
// ═══════════════════════════════════════════════════════════════════════════

typedef struct __attribute__((packed)) {
    q16_16_t w;
    q16_16_t x;
    q16_16_t y;
    q16_16_t z;
    uint32_t layer;       // Layer index for sieve counter-rotation
    uint32_t flags;       // 1=alive (post-sieve), 2=pruned (FAMM Φ>1)
} QuaternionPoint;

// ═══════════════════════════════════════════════════════════════════════════
// PIST Shell Coordinate (k, t, mass = a*b)
// Integer-based, NES-compatible
// ═══════════════════════════════════════════════════════════════════════════

typedef struct __attribute__((packed)) {
    int32_t k;            // Shell index (azimuthal)
    int32_t t;            // Time step (polar)
    int32_t mass;         // mass = a * b
    int32_t a;            // Factor 1
    int32_t b;            // Factor 2
    uint32_t shell_id;    // Unique shell identifier
    q16_16_t phase;       // Phase angle θ
} PistShell;

// ═══════════════════════════════════════════════════════════════════════════
// FAMM Frustration Node
// Stress tensor + scheduling decision
// ═══════════════════════════════════════════════════════════════════════════

typedef struct __attribute__((packed)) {
    q16_16_t torsional_stress;     // Σ²
    q16_16_t interlocking_energy;  // I_lock
    q16_16_t laplacian_energy;     // Δϕ
    q16_16_t total_frustration;    // Φ (computed)
    q16_16_t cognitive_load;       // L_total
    uint8_t  decision;             // 0=EXECUTE, 1=DEFER, 2=THROTTLE
    uint8_t  topology;             // 0=relational, 1=semantic, 2=topological, 3=minimal
    uint16_t reserved;
} FammNode;

// ═══════════════════════════════════════════════════════════════════════════
// Braid Edge (connects two quaternion points with topological weight)
// ═══════════════════════════════════════════════════════════════════════════

typedef struct __attribute__((packed)) {
    uint32_t from_idx;    // Index into point array
    uint32_t to_idx;
    q16_16_t weight;      // w_ij = coupling strength
    q16_16_t alignment;   // g = cos(Δθ·2π/16) · cos(Δφ·π/8)
    uint32_t braid_id;    // Braid group identifier
} BraidEdge;

// ═══════════════════════════════════════════════════════════════════════════
// Full Manifold Block (Header + arrays)
// Layout: Header | Shells[] | Points[] | Edges[] | FammNodes[]
// ═══════════════════════════════════════════════════════════════════════════

typedef struct {
    ManifoldHeader header;
    PistShell *shells;        // num_shells elements
    QuaternionPoint *points;  // num_points elements
    BraidEdge *edges;         // num_edges elements
    FammNode *famm_nodes;   // num_points elements (1:1 with points if flags&4)
} ManifoldBlock;

// ═══════════════════════════════════════════════════════════════════════════
// C API
// ═══════════════════════════════════════════════════════════════════════════

size_t manifold_binary_size(const ManifoldBlock *block);
int    manifold_binary_serialize(const ManifoldBlock *block, uint8_t *buffer, size_t buf_size);
int    manifold_binary_deserialize(const uint8_t *buffer, size_t buf_size, ManifoldBlock *out);
void   manifold_block_free(ManifoldBlock *block);

// Sanity check: verify all points are on S³ (unit quaternion)
int    manifold_validate_quaternions(const ManifoldBlock *block);

// Compute FAMM frustration in-place
void   manifold_compute_famm(ManifoldBlock *block);

// Apply quaternion sieve: counter-rotation band-pass
uint32_t manifold_apply_sieve(ManifoldBlock *block, q16_16_t threshold);

#ifdef __cplusplus
}
#endif

#endif // MANIFOLD_BINARY_H

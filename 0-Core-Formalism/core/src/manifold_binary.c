// SPDX-License-Identifier: MIT
/*
 * Manifold Binary Serialization — C Implementation
 *
 * Zero-copy binary format for PIST/SVQF/FAMM manifold state.
 */

#include "../include/manifold_binary.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>

// ═══════════════════════════════════════════════════════════════════════════
// Serialization
// ═══════════════════════════════════════════════════════════════════════════

size_t manifold_binary_size(const ManifoldBlock *block) {
    size_t sz = sizeof(ManifoldHeader);
    sz += block->header.num_shells * sizeof(PistShell);
    sz += block->header.num_points * sizeof(QuaternionPoint);
    sz += block->header.num_edges * sizeof(BraidEdge);
    if (block->header.flags & 0x4) {
        sz += block->header.num_points * sizeof(FammNode);
    }
    return sz;
}

int manifold_binary_serialize(const ManifoldBlock *block, uint8_t *buffer, size_t buf_size) {
    size_t need = manifold_binary_size(block);
    if (buf_size < need) return -1;

    uint8_t *p = buffer;

    // Header (32 bytes)
    memcpy(p, &block->header, sizeof(ManifoldHeader));
    p += sizeof(ManifoldHeader);

    // Shells
    if (block->header.num_shells > 0 && block->shells) {
        size_t n = block->header.num_shells * sizeof(PistShell);
        memcpy(p, block->shells, n);
        p += n;
    }

    // Points
    if (block->header.num_points > 0 && block->points) {
        size_t n = block->header.num_points * sizeof(QuaternionPoint);
        memcpy(p, block->points, n);
        p += n;
    }

    // Edges
    if (block->header.num_edges > 0 && block->edges) {
        size_t n = block->header.num_edges * sizeof(BraidEdge);
        memcpy(p, block->edges, n);
        p += n;
    }

    // FAMM nodes
    if ((block->header.flags & 0x4) && block->famm_nodes) {
        size_t n = block->header.num_points * sizeof(FammNode);
        memcpy(p, block->famm_nodes, n);
        p += n;
    }

    return (int)(p - buffer);
}

int manifold_binary_deserialize(const uint8_t *buffer, size_t buf_size, ManifoldBlock *out) {
    if (buf_size < sizeof(ManifoldHeader)) return -1;

    const uint8_t *p = buffer;
    memcpy(&out->header, p, sizeof(ManifoldHeader));
    p += sizeof(ManifoldHeader);

    if (out->header.magic != MANIFOLD_MAGIC) return -2;
    if (out->header.version != MANIFOLD_VERSION) return -3;

    size_t need = sizeof(ManifoldHeader);
    need += out->header.num_shells * sizeof(PistShell);
    need += out->header.num_points * sizeof(QuaternionPoint);
    need += out->header.num_edges * sizeof(BraidEdge);
    if (out->header.flags & 0x4) {
        need += out->header.num_points * sizeof(FammNode);
    }
    if (buf_size < need) return -4;

    // Allocate and copy arrays (zero-copy variant would mmap)
    if (out->header.num_shells > 0) {
        out->shells = malloc(out->header.num_shells * sizeof(PistShell));
        memcpy(out->shells, p, out->header.num_shells * sizeof(PistShell));
        p += out->header.num_shells * sizeof(PistShell);
    } else {
        out->shells = NULL;
    }

    if (out->header.num_points > 0) {
        out->points = malloc(out->header.num_points * sizeof(QuaternionPoint));
        memcpy(out->points, p, out->header.num_points * sizeof(QuaternionPoint));
        p += out->header.num_points * sizeof(QuaternionPoint);
    } else {
        out->points = NULL;
    }

    if (out->header.num_edges > 0) {
        out->edges = malloc(out->header.num_edges * sizeof(BraidEdge));
        memcpy(out->edges, p, out->header.num_edges * sizeof(BraidEdge));
        p += out->header.num_edges * sizeof(BraidEdge);
    } else {
        out->edges = NULL;
    }

    if (out->header.flags & 0x4) {
        out->famm_nodes = malloc(out->header.num_points * sizeof(FammNode));
        memcpy(out->famm_nodes, p, out->header.num_points * sizeof(FammNode));
        p += out->header.num_points * sizeof(FammNode);
    } else {
        out->famm_nodes = NULL;
    }

    return 0;
}

void manifold_block_free(ManifoldBlock *block) {
    if (block->shells)      { free(block->shells);      block->shells = NULL; }
    if (block->points)      { free(block->points);      block->points = NULL; }
    if (block->edges)       { free(block->edges);       block->edges = NULL; }
    if (block->famm_nodes)  { free(block->famm_nodes);  block->famm_nodes = NULL; }
    block->header.num_shells = 0;
    block->header.num_points = 0;
    block->header.num_edges = 0;
}

// ═══════════════════════════════════════════════════════════════════════════
// Validation
// ═══════════════════════════════════════════════════════════════════════════

int manifold_validate_quaternions(const ManifoldBlock *block) {
    int errors = 0;
    for (uint32_t i = 0; i < block->header.num_points; i++) {
        QuaternionPoint *q = &block->points[i];
        float w = q16_16_to_float(q->w);
        float x = q16_16_to_float(q->x);
        float y = q16_16_to_float(q->y);
        float z = q16_16_to_float(q->z);
        float norm = sqrtf(w*w + x*x + y*y + z*z);
        // Allow 1% tolerance for Q16.16 quantization
        if (fabsf(norm - 1.0f) > 0.01f) {
            errors++;
        }
    }
    return errors;
}

// ═══════════════════════════════════════════════════════════════════════════
// FAMM Frustration (CPU reference implementation)
// ═══════════════════════════════════════════════════════════════════════════

static inline float qf(q16_16_t v) { return q16_16_to_float(v); }

void manifold_compute_famm(ManifoldBlock *block) {
    if (!block->famm_nodes) return;

    for (uint32_t i = 0; i < block->header.num_points; i++) {
        FammNode *fn = &block->famm_nodes[i];
        // Φ = Σ² + I_lock + Δϕ (simplified: no neighbor stress for CPU ref)
        float phi = qf(fn->torsional_stress)
                  + qf(fn->interlocking_energy)
                  + qf(fn->laplacian_energy);
        fn->total_frustration = q16_16_from_float(phi);

        // Scheduling decision based on Φ thresholds
        if (phi < 0.25f) {
            fn->decision = 0; // EXECUTE
        } else if (phi < 0.5f) {
            fn->decision = 1; // DEFER
        } else {
            fn->decision = 2; // THROTTLE
        }

        // Topology adaptation based on cognitive load
        float load = qf(fn->cognitive_load);
        if (load < 0.25f) fn->topology = 0;      // relational
        else if (load < 0.50f) fn->topology = 1; // semantic
        else if (load < 0.75f) fn->topology = 2; // topological
        else fn->topology = 3;                    // minimal
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Quaternion Sieve: Counter-rotation band-pass
// ═══════════════════════════════════════════════════════════════════════════

uint32_t manifold_apply_sieve(ManifoldBlock *block, q16_16_t threshold) {
    uint32_t alive = 0;
    float thr = q16_16_to_float(threshold);

    for (uint32_t i = 0; i < block->header.num_points; i++) {
        QuaternionPoint *q = &block->points[i];
        float x = qf(q->x);
        float y = qf(q->y);
        float phase = atan2f(y, x);
        // Counter-rotation alignment: sin(2*phase) must exceed threshold
        float alignment = fabsf(sinf(2.0f * phase));
        if (alignment >= thr) {
            q->flags |= 1; // alive
            alive++;
        } else {
            q->flags &= ~1; // dead
        }
    }
    return alive;
}

// Manifold Render Compute Shader
// Reads binary manifold data, projects S^3 quaternions to R^3,
// applies FAMM frustration coloring, outputs vertex buffer.
//
// Bindings (matches manifold_binary.h layout):
//   @group(0) @binding(0) manifold_header:  ManifoldHeader (32 bytes)
//   @group(0) @binding(1) shells:           array<PistShell>
//   @group(0) @binding(2) points:           array<QuaternionPoint>
//   @group(0) @binding(3) edges:            array<BraidEdge>
//   @group(0) @binding(4) famm_nodes:      array<FammNode>
//   @group(0) @binding(5) out_vertices:     array<VertexOutput>
//   @group(0) @binding(6) out_draw_params:  DrawParams (indirect)
//
// Q16.16 Fixed-Point: SCALE = 65536.0
// Matches FixedPoint.lean, nii_surface_driver.c, manifold_binary.h

// ═══════════════════════════════════════════════════════════════════════════
// Struct Mirrors (must match manifold_binary.h exactly — 8-byte aligned)
// ═══════════════════════════════════════════════════════════════════════════

struct ManifoldHeader {
    magic: u32,
    version: u32,      // version (lo) | flags (hi)
    timestamp_ns: u32, // low 32 bits
    timestamp_hi: u32, // high 32 bits
    num_shells: u32,
    num_points: u32,
    num_edges: u32,
    reserved: u32,
}

struct QuaternionPoint {
    w: i32,
    x: i32,
    y: i32,
    z: i32,
    layer: u32,
    flags: u32,
}

struct PistShell {
    k: i32,
    t: i32,
    mass: i32,
    a: i32,
    b: i32,
    shell_id: u32,
    phase: i32,
}

struct BraidEdge {
    from_idx: u32,
    to_idx: u32,
    weight: i32,
    alignment: i32,
    braid_id: u32,
}

struct FammNode {
    torsional_stress: i32,
    interlocking_energy: i32,
    laplacian_energy: i32,
    total_frustration: i32,
    cognitive_load: i32,
    decision_and_topology: u32, // (decision : 8) | (topology : 8) | (reserved : 16)
}

struct VertexOutput {
    position: vec3<f32>,    // Stereographic projection of quaternion
    color: vec3<f32>,       // FAMM frustration mapped to heatmap
    flags: u32,             // Original flags (alive/pruned)
    point_idx: u32,
}

struct DrawParams {
    vertex_count: u32,
    instance_count: u32,
    first_vertex: u32,
    first_instance: u32,
}

// ═══════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════

const Q16_SCALE: f32 = 65536.0;
const Q16_ONE: i32 = 65536;
const PI: f32 = 3.141592653589793;

// ═══════════════════════════════════════════════════════════════════════════
// Fixed-Point Helpers
// ═══════════════════════════════════════════════════════════════════════════

fn q16_to_f32(v: i32) -> f32 {
    return f32(v) / Q16_SCALE;
}

fn q16_mul(a: i32, b: i32) -> i32 {
    let a64 = i64(a);
    let b64 = i64(b);
    let prod = a64 * b64;
    return i32(prod >> 16u);
}

fn q16_add(a: i32, b: i32) -> i32 {
    return a + b;
}

fn q16_sub(a: i32, b: i32) -> i32 {
    return a - b;
}

// ═══════════════════════════════════════════════════════════════════════════
// Stereographic Projection: S^3 → R^3
//   (w, x, y, z) where w^2+x^2+y^2+z^2 = 1
//   Project from North pole (w=1) to equatorial plane:
//     X = x / (1 - w), Y = y / (1 - w), Z = z / (1 - w)
//   For w ≈ 1 (near pole), clamp to avoid singularity.
// ═══════════════════════════════════════════════════════════════════════════

fn stereographic_project(q: QuaternionPoint) -> vec3<f32> {
    let w = q16_to_f32(q.w);
    let x = q16_to_f32(q.x);
    let y = q16_to_f32(q.y);
    let z = q16_to_f32(q.z);

    let denom = 1.0 - w;
    let clamped = max(denom, 0.0001);  // Avoid pole singularity

    return vec3<f32>(x / clamped, y / clamped, z / clamped);
}

// ═══════════════════════════════════════════════════════════════════════════
// Quaternion Sieve: Counter-Rotation Band-Pass
//   Alive if |sin(2 * atan2(y, x))| >= threshold
//   This implements the counter-rotation filter from manifold_binary.h
// ═══════════════════════════════════════════════════════════════════════════

fn quaternion_sieve(q: QuaternionPoint, threshold: f32) -> bool {
    let x = q16_to_f32(q.x);
    let y = q16_to_f32(q.y);
    let phase = atan2(y, x);
    let alignment = abs(sin(2.0 * phase));
    return alignment >= threshold;
}

// ═══════════════════════════════════════════════════════════════════════════
// FAMM Frustration: Compute Φ and map to color
//   Φ = torsional_stress + interlocking_energy + laplacian_energy
//   Color mapping:
//     Φ < 0.25 → green (EXECUTE)
//     Φ < 0.50 → yellow (THROTTLE)
//     else     → red (DEFER / pruned)
// ═══════════════════════════════════════════════════════════════════════════

fn compute_famm_color(fn: FammNode) -> vec3<f32> {
    let ts = q16_to_f32(fn.torsional_stress);
    let ie = q16_to_f32(fn.interlocking_energy);
    let le = q16_to_f32(fn.laplacian_energy);
    let phi = ts + ie + le;

    // Heatmap: low Φ = blue/cool, high Φ = red/hot
    if (phi < 0.25) {
        return vec3<f32>(0.0, 0.8, 0.2);   // Green — execute
    } else if (phi < 0.50) {
        return vec3<f32>(1.0, 0.9, 0.0);   // Yellow — throttle
    } else {
        return vec3<f32>(1.0, 0.2, 0.1);   // Red — defer/pruned
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Topology Name → Color Override (for debugging)
// ═══════════════════════════════════════════════════════════════════════════

fn topology_color(topology: u32) -> vec3<f32> {
    switch (topology) {
        case 0u: { return vec3<f32>(0.2, 0.6, 1.0); }  // relational: blue
        case 1u: { return vec3<f32>(0.4, 0.8, 0.4); }  // semantic: green
        case 2u: { return vec3<f32>(0.9, 0.5, 0.2); }  // topological: orange
        case 3u: { return vec3<f32>(0.5, 0.5, 0.5); }  // minimal: gray
        default: { return vec3<f32>(1.0, 0.0, 1.0); }  // unknown: magenta
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Braid Edge Visibility: Spring force for layout (optional physics step)
//   Hooke's law: F = k * (|dx| - rest_length) * dx/|dx|
// ═══════════════════════════════════════════════════════════════════════════

fn edge_spring_force(
    p0: vec3<f32>,
    p1: vec3<f32>,
    rest_length: f32,
    k: f32
) -> vec3<f32> {
    let dx = p1 - p0;
    let dist = length(dx);
    let clamped = max(dist, 0.0001);
    let displacement = dist - rest_length;
    return k * displacement * (dx / clamped);
}

// ═══════════════════════════════════════════════════════════════════════════
// Storage Bindings
// ═══════════════════════════════════════════════════════════════════════════

@group(0) @binding(0) var<storage, read> header: ManifoldHeader;
@group(0) @binding(1) var<storage, read> shells: array<PistShell>;
@group(0) @binding(2) var<storage, read> points: array<QuaternionPoint>;
@group(0) @binding(3) var<storage, read> edges: array<BraidEdge>;
@group(0) @binding(4) var<storage, read> famm_nodes: array<FammNode>;
@group(0) @binding(5) var<storage, read_write> out_vertices: array<VertexOutput>;
@group(0) @binding(6) var<storage, read_write> out_draw_params: DrawParams;

// ═══════════════════════════════════════════════════════════════════════════
// Compute Shader: One invocation per point
// ═══════════════════════════════════════════════════════════════════════════

@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let idx = gid.x;
    let num_points = header.num_points;

    if (idx >= num_points) {
        return;
    }

    let pt = points[idx];

    // ── Quaternion Sieve (band-pass) ─────────────────────────────────
    let alive = quaternion_sieve(pt, 0.3);
    let new_flags = select(pt.flags & ~1u, pt.flags | 1u, alive);

    // ── Stereographic Projection ────────────────────────────────────
    var pos = stereographic_project(pt);

    // ── FAMM Frustration Coloring ───────────────────────────────────
    var color: vec3<f32>;
    var has_famm = (header.version & 0xFF00u) != 0u; // flags in upper 16 bits
    // Actually flags are in version field as per struct layout:
    // version: u32 = version (lo) | flags (hi) — no, struct is flat.
    // Correct: flags is separate field at offset 4.
    // Re-reading struct: magic(0), version(4), timestamp_ns(8)...
    // Wait, the struct has `version: u32` which is version (lo 16) | flags (hi 16)?
    // Actually the C struct is: uint16_t version, uint16_t flags.
    // WGSL doesn't have u16. We packed as u32 with version in low 16, flags in high 16.
    let flags = (header.version >> 16u) & 0xFFFFu;
    has_famm = (flags & 0x4u) != 0u;

    if (has_famm && idx < arrayLength(&famm_nodes)) {
        let fn = famm_nodes[idx];
        color = compute_famm_color(fn);
    } else {
        // Default: layer-based gradient
        let layer_norm = f32(pt.layer) / f32(num_points);
        color = vec3<f32>(layer_norm, 0.5, 1.0 - layer_norm);
    }

    // ── If dead (sieve), fade to background ───────────────────────────
    if (!alive) {
        color = color * 0.15;  // Ghost the rejected points
    }

    // ── Write Vertex ────────────────────────────────────────────────
    out_vertices[idx] = VertexOutput(
        pos,
        color,
        new_flags,
        idx
    );

    // ── First thread writes draw params ─────────────────────────────
    if (idx == 0u) {
        out_draw_params.vertex_count = num_points;
        out_draw_params.instance_count = 1u;
        out_draw_params.first_vertex = 0u;
        out_draw_params.first_instance = 0u;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Vertex Shader (passthrough for rendered points)
// ═══════════════════════════════════════════════════════════════════════════

struct VSOutput {
    @builtin(position) position: vec4<f32>,
    @location(0) color: vec3<f32>,
    @location(1) flags: u32,
};

@vertex
fn vs_main(
    @location(0) in_pos: vec3<f32>,
    @location(1) in_color: vec3<f32>,
    @location(2) in_flags: u32,
) -> VSOutput {
    var out: VSOutput;
    out.position = vec4<f32>(in_pos * 0.1, 1.0);  // Scale for clip space
    out.color = in_color;
    out.flags = in_flags;
    return out;
}

// ═══════════════════════════════════════════════════════════════════════════
// Fragment Shader
// ═══════════════════════════════════════════════════════════════════════════

@fragment
fn fs_main(in: VSOutput) -> @location(0) vec4<f32> {
    let alive = (in.flags & 1u) != 0u;
    if (!alive) {
        discard;
    }
    return vec4<f32>(in.color, 1.0);
}

// Sovereign Informatic Manifold — RGFlow Adaptation Surface Compute Shader
// Targets WebGPU (wgpu) with Vulkan backend for broad compatibility.
//
// Precomputes a 262,144-entry adaptation surface over the 6D quantized genome space:
//   (μ, ρ, C, M, n_e, σ) × 8 bins each = 18 bits = 262,144 addresses.
//
// Four-layer lawfulness invariant:
//   1. Drake Budget:        μ_q ≤ D / C_fac
//   2. Drift Barrier:       ρ_q · N_e · Φ(M_fac) ≥ B
//   3. Error Threshold:     σ_q > 1 + λ · μ_q
//   4. RGFlow Coherence:    lim_{s→S} RGFlow_s(g) ∈ A_law
//
// Where:
//   N_e = log(1 + n_e)
//   Φ(M) = 1 − |M − M*|
//   dg_s/ds = β(g_s)  (discretized as iterative drift toward attractor)

// ═══════════════════════════════════════════════════════════════════════════
// Output structure — 28 bytes per entry (7 × u32)
// ═══════════════════════════════════════════════════════════════════════════

struct AdaptationEntry {
    flags:        u32,  // bit0: lawful_now, bit1: lawful_under_flow,
                        // bit2: lawful_attractor, bit3: noise_flow,
                        // bit4: sabotage_flow, bit5: final_lawful
    cost:         u32,  // cost_to_lawfulness (fixed-point-ish)
    margin:       u32,  // stability_margin × 65536
    rg_depth:     u32,  // first_failure_depth (0..RG_STEPS, 0 if never failed)
    recovery_depth: u32, // first_recovery_depth (0 if no recovery)
    attractor_id: u32,  // 1 if reached attractor, 0 otherwise
    failure_mask: u32,  // 0x1=Drake, 0x2=Drift, 0x4=Error, 0x8=RGFlow
}

@group(0) @binding(0)
var<storage, read_write> output_buffer: array<AdaptationEntry>;

// ═══════════════════════════════════════════════════════════════════════════
// Biophysical constants
// ═══════════════════════════════════════════════════════════════════════════

const D:            f32 = 0.003;   // Drake constant
const B:            f32 = 0.001;   // Drift-barrier constant
const LAMBDA:       f32 = 0.5;     // Error-threshold slope
const M_STAR:       f32 = 0.5;     // Optimal modularity
const RG_STEPS:     i32 = 8;       // Scale-flow iterations
const BETA_RATE:    f32 = 0.1;     // Drift rate per scale step
const ADDR_SPACE:   u32 = 262144u; // 2^18

// ═══════════════════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════════════════

// Decode 18-bit linear address into 6 dimensions (3 bits each).
fn decode_address(addr: u32,
                  out_mu: ptr<function, u32>,
                  out_rho: ptr<function, u32>,
                  out_c: ptr<function, u32>,
                  out_m: ptr<function, u32>,
                  out_ne: ptr<function, u32>,
                  out_sigma: ptr<function, u32>) {
    var a = addr;
    *out_mu    = a & 7u;  a = a >> 3u;
    *out_rho   = a & 7u;  a = a >> 3u;
    *out_c     = a & 7u;  a = a >> 3u;
    *out_m     = a & 7u;  a = a >> 3u;
    *out_ne    = a & 7u;  a = a >> 3u;
    *out_sigma = a & 7u;
}

// Mutation rate: bin 0..7 → 0.001 .. 0.008
fn mu_from_bin(bin: u32) -> f32 {
    return 0.001 * f32(bin + 1u);
}

// Verification pressure: bin 0..7 → 0.001 .. 0.008
fn rho_from_bin(bin: u32) -> f32 {
    return 0.001 * f32(bin + 1u);
}

// Connectance factor: bin 0..7 → 0.125 .. 1.0
fn c_from_bin(bin: u32) -> f32 {
    return 0.125 * f32(bin + 1u);
}

// Modularity factor: bin 0..7 → 0.125 .. 1.0
fn m_from_bin(bin: u32) -> f32 {
    return 0.125 * f32(bin + 1u);
}

// Fitness advantage: bin 0..7 → 1.25 .. 3.0
fn sigma_from_bin(bin: u32) -> f32 {
    return 1.0 + 0.25 * f32(bin + 1u);
}

// Effective observer mass: N_e = log(1 + n_e)
fn ne_effective(ne_raw: f32) -> f32 {
    return log(1.0 + ne_raw);
}

// Modularity shaping function: Φ(M) = 1 − |M − M*|
fn phi(m_fac: f32) -> f32 {
    return 1.0 - abs(m_fac - M_STAR);
}

// Three-layer local lawfulness check (Ω_law).
fn is_lawful(mu_q: f32, rho_q: f32, c_fac: f32, m_fac: f32, ne_eff: f32, sigma_q: f32) -> bool {
    let drake_ok  = mu_q <= (D / c_fac);
    let drift_ok  = (rho_q * ne_eff * phi(m_fac)) >= B;
    let error_ok  = sigma_q > (1.0 + LAMBDA * mu_q);
    return drake_ok && drift_ok && error_ok;
}

// Informatic beta function: discrete drift toward the lawful attractor basin.
fn beta_step(mu: ptr<function, f32>, rho: ptr<function, f32>, c: ptr<function, f32>,
             m: ptr<function, f32>, ne: ptr<function, f32>, sigma: ptr<function, f32>) {
    *mu    = mix(*mu,    0.001, BETA_RATE);
    *rho   = mix(*rho,   0.004, BETA_RATE);
    *c     = mix(*c,     0.500, BETA_RATE);
    *m     = mix(*m,     M_STAR, BETA_RATE);
    *ne    = mix(*ne,    6.00,  BETA_RATE);
    *sigma = mix(*sigma, 2.50,  BETA_RATE);
}

// Compute cost and failure mask for a state.
fn compute_cost(mu_q: f32, rho_q: f32, c_fac: f32, m_fac: f32, ne_eff: f32, sigma_q: f32,
                lawful_now: bool, lawful_flow: bool) -> vec2<u32> {
    var cost_f: f32 = 0.0;
    var mask: u32 = 0u;

    if (mu_q > (D / c_fac)) {
        cost_f = cost_f + (mu_q - D / c_fac) * 65536.0;
        mask = mask | 1u;
    }
    if ((rho_q * ne_eff * phi(m_fac)) < B) {
        cost_f = cost_f + (B - rho_q * ne_eff * phi(m_fac)) * 65536.0;
        mask = mask | 2u;
    }
    if (sigma_q <= (1.0 + LAMBDA * mu_q)) {
        cost_f = cost_f + 16711680.0;
        mask = mask | 4u;
    }
    if (!lawful_flow) {
        cost_f = cost_f + 4278190080.0;
        mask = mask | 8u;
    }

    return vec2<u32>(u32(cost_f), mask);
}

// ═══════════════════════════════════════════════════════════════════════════
// Main compute kernel
// ═══════════════════════════════════════════════════════════════════════════

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let addr = gid.x;
    if (addr >= ADDR_SPACE) {
        return;
    }

    // Decode 18-bit address
    var mu_bin: u32 = 0u;
    var rho_bin: u32 = 0u;
    var c_bin: u32 = 0u;
    var m_bin: u32 = 0u;
    var ne_bin: u32 = 0u;
    var sigma_bin: u32 = 0u;
    decode_address(addr, &mu_bin, &rho_bin, &c_bin, &m_bin, &ne_bin, &sigma_bin);

    let mu_q    = mu_from_bin(mu_bin);
    let rho_q   = rho_from_bin(rho_bin);
    let c_fac   = c_from_bin(c_bin);
    let m_fac   = m_from_bin(m_bin);
    let ne_raw  = f32(ne_bin);
    let ne_eff  = ne_effective(ne_raw);
    let sigma_q = sigma_from_bin(sigma_bin);

    // Layer 1–3: Local lawfulness at scale s = 0
    let lawful_now = is_lawful(mu_q, rho_q, c_fac, m_fac, ne_eff, sigma_q);

    // Layer 4: RGFlow scale coherence (full 8-step trace, no early exit)
    var mu_s    = mu_q;
    var rho_s   = rho_q;
    var c_s     = c_fac;
    var m_s     = m_fac;
    var ne_s    = ne_raw;
    var sigma_s = sigma_q;

    var first_failure_depth: i32 = 0;
    var first_recovery_depth: i32 = 0;
    var all_lawful: bool = true;

    for (var s: i32 = 0; s < RG_STEPS; s = s + 1) {
        beta_step(&mu_s, &rho_s, &c_s, &m_s, &ne_s, &sigma_s);
        let ne_eff_s = ne_effective(ne_s);
        let step_lawful = is_lawful(mu_s, rho_s, c_s, m_s, ne_eff_s, sigma_s);

        if (!step_lawful && first_failure_depth == 0) {
            first_failure_depth = s + 1;
            all_lawful = false;
        }
        if (step_lawful && !lawful_now && first_recovery_depth == 0) {
            first_recovery_depth = s + 1;
        }
    }

    let final_lawful = is_lawful(mu_s, rho_s, c_s, m_s, ne_effective(ne_s), sigma_s);
    let lawful_flow = all_lawful;
    let reached_attractor = final_lawful;

    // Cost & failure mask
    let cost_and_mask = compute_cost(mu_q, rho_q, c_fac, m_fac, ne_eff, sigma_q,
                                      lawful_now, lawful_flow);
    let cost = cost_and_mask.x;
    let failure_mask = cost_and_mask.y;

    // Stability margin
    let margin_drake  = abs(mu_q - (D / c_fac));
    let margin_drift  = abs(rho_q * ne_eff * phi(m_fac) - B);
    let margin_error  = abs(sigma_q - (1.0 + LAMBDA * mu_q));
    let margin = min(margin_drake, min(margin_drift, margin_error));

    // Pack flags
    var flags: u32 = 0u;
    if (lawful_now)          { flags = flags | 1u; }
    if (lawful_flow)         { flags = flags | 2u; }
    if (reached_attractor)   { flags = flags | 4u; }
    if (!lawful_now && !reached_attractor && first_failure_depth >= RG_STEPS / 2) {
        flags = flags | 8u;
    }
    if (!lawful_now && !lawful_flow && first_failure_depth < 3) {
        flags = flags | 16u;
    }
    if (final_lawful)        { flags = flags | 32u; }

    // Write output
    output_buffer[addr] = AdaptationEntry(
        flags,
        cost,
        u32(margin * 65536.0),
        u32(first_failure_depth),
        u32(first_recovery_depth),
        select(0u, 1u, reached_attractor),
        failure_mask
    );
}

// burgers_particles.wgsl — minimal working shader
struct Counters { proved: atomic<u32>, failed: atomic<u32>, first_fail_addr: atomic<u32>, first_lemma: atomic<u32> };
@group(0) @binding(0) var<storage, read_write> grid: array<atomic<u32>>;
@group(0) @binding(1) var<storage, read_write> cnt: Counters;
@group(0) @binding(2) var<uniform> params: vec4<u32>;
@group(0) @binding(3) var<uniform> thresholds: vec4<u32>;

fn q16_mul(a: u32, b: u32) -> u32 {
    let a_lo = a & 0xFFFFu; let a_hi = a >> 16u;
    let b_lo = b & 0xFFFFu; let b_hi = b >> 16u;
    return ((a_hi * b_hi) << 16u) + (a_hi * b_lo + a_lo * b_hi) + ((a_lo * b_lo) >> 16u);
}
fn q16_add(a: u32, b: u32) -> u32 { return select(a + b, 0xFFFFFFFFu, a + b < a); }
fn q16_sub(a: u32, b: u32) -> u32 { return select(a - b, 0u, a < b); }
fn q16_gt(a: u32, b: u32) -> bool { return i32(a) > i32(b); }

fn euler_step(u0: u32, u1: u32, u2: u32, u3: u32, dt: u32, nu: u32, dx: u32) -> array<u32, 4> {
    // dx=1.0 in Q16_16 = 65536, so b>>16 = 1, q16_div_qq = a/1 = a
    let two_dx = 0x20000u; // 2.0 in Q16_16
    var r: array<u32, 4>;
    // i=0: central_diff -> 0, second_diff -> 0, rhs = 0
    r[0] = u0;
    // i=1
    let ux1 = q16_div_qq(q16_sub(u2, u0), two_dx);
    let uxx1 = q16_div_qq(q16_add(q16_sub(u2, u1), q16_sub(u0, u1)), q16_mul(dx, dx));
    r[1] = q16_add(u1, q16_mul(dt, q16_sub(q16_mul(nu, uxx1), q16_mul(u1, ux1))));
    // i=2
    let ux2 = q16_div_qq(q16_sub(u3, u1), two_dx);
    let uxx2 = q16_div_qq(q16_add(q16_sub(u3, u2), q16_sub(u1, u2)), q16_mul(dx, dx));
    r[2] = q16_add(u2, q16_mul(dt, q16_sub(q16_mul(nu, uxx2), q16_mul(u2, ux2))));
    // i=3: central_diff -> 0, second_diff -> 0, rhs = 0
    r[3] = u3;
    return r;
}
fn q16_div_qq(a: u32, b: u32) -> u32 { return a / (b >> 16u); }

fn lemma_energy(addr: u32, nu: u32, dt: u32, dx: u32) -> bool {
    let u = unpack_ic(addr);
    let e0 = q16_add(q16_add(q16_add(q16_mul(u[0],u[0]), q16_mul(u[1],u[1])), q16_mul(u[2],u[2])), q16_mul(u[3],u[3])) >> 1u;
    var u2 = euler_step(u[0], u[1], u[2], u[3], dt, nu, dx);
    u2 = euler_step(u2[0], u2[1], u2[2], u2[3], dt, nu, dx);
    u2 = euler_step(u2[0], u2[1], u2[2], u2[3], dt, nu, dx);
    u2 = euler_step(u2[0], u2[1], u2[2], u2[3], dt, nu, dx);
    u2 = euler_step(u2[0], u2[1], u2[2], u2[3], dt, nu, dx);
    let e1 = q16_add(q16_add(q16_add(q16_mul(u2[0],u2[0]), q16_mul(u2[1],u2[1])), q16_mul(u2[2],u2[2])), q16_mul(u2[3],u2[3])) >> 1u;
    return !q16_gt(e1, e0);
}
fn unpack_ic(addr: u32) -> array<u32, 4> {
    let i = (addr / 16384u) % 128u; let j = (addr / 128u) % 128u; let k = addr % 128u;
    var u: array<u32, 4>;
    u[0] = u32((i32(i) * 2 - 128) * 512);
    u[1] = u32((i32(j) * 2 - 128) * 512);
    u[2] = u32((i32(k) * 2 - 128) * 512);
    u[3] = 0u;
    return u;
}

@compute @workgroup_size(8, 8, 4)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let addr = gid.x * 16384u + gid.y * 128u + gid.z;
    if addr >= 2097152u { return; }
    let ok = lemma_energy(addr, thresholds.x, thresholds.y, thresholds.z);
    if ok { atomicAdd(&cnt.proved, 1u); }
    else { atomicAdd(&cnt.failed, 1u); }
}

// ASCII Depth-of-Field packing shader for WebGPU.
//
// One invocation writes one ASCII cell into a packed u32:
//   bits 31..19: depth13
//   bits 18..12: luma7
//   bits 11..6:  glyph/char6
//   bits 5..2:   flags4
//   bits 1..0:   reserved2
//
// Depth, focus, aperture, and CoC are carried as unsigned Q16.16 values.
// The render pass should decode char6 with `(packed >> 6u) & 0x3Fu`.

struct AsciiDofParams {
    source_width: u32,
    source_height: u32,
    grid_width: u32,
    grid_height: u32,
    cell_width: u32,
    cell_height: u32,
    focus_q16: u32,
    aperture_q16: u32,
    coc_scale_q16: u32,
    flags: u32,
}

@group(0) @binding(0) var<storage, read_write> ascii_buffer: array<u32>;
@group(0) @binding(1) var scene_depth: texture_depth_2d;
@group(0) @binding(2) var scene_color: texture_2d<f32>;
@group(0) @binding(3) var<uniform> params: AsciiDofParams;

const Q16_ONE: u32 = 0x00010000u;
const Q16_HALF: u32 = 0x00008000u;
const DEPTH13_MAX: u32 = 0x1FFFu;
const LUMA7_MAX: u32 = 0x7Fu;
const CHAR6_MAX: u32 = 0x3Fu;

fn clamp_u32(v: u32, hi: u32) -> u32 {
    return min(v, hi);
}

fn f32_unit_to_q16(v: f32) -> u32 {
    let clamped = clamp(v, 0.0, 1.0);
    return u32(clamped * 65536.0 + 0.5);
}

fn q16_abs_diff(a: u32, b: u32) -> u32 {
    return select(b - a, a - b, a >= b);
}

// Q16.16 multiply for non-negative values in [0, 1]. This avoids u64 and keeps
// the product exact enough for normalized depth/CoC/aperture control.
fn q16_mul_unit(a: u32, b: u32) -> u32 {
    let ai = a >> 16u;
    let af = a & 0xFFFFu;
    let bi = b >> 16u;
    let bf = b & 0xFFFFu;

    let integer_term = (ai * bi) << 16u;
    let cross_terms = ai * bf + bi * af;
    let fractional_term = (af * bf) >> 16u;
    return min(integer_term + cross_terms + fractional_term, Q16_ONE);
}

fn luma_from_rgb(rgb: vec3<f32>) -> f32 {
    return dot(rgb, vec3<f32>(0.2126, 0.7152, 0.0722));
}

fn density_index(luma7: u32, coc_q16: u32) -> u32 {
    let luma_char = (luma7 * CHAR6_MAX + (LUMA7_MAX / 2u)) / LUMA7_MAX;
    let blur_char = clamp_u32(coc_q16 >> 10u, CHAR6_MAX);
    return clamp_u32((luma_char + blur_char) / 2u, CHAR6_MAX);
}

fn sample_coord(cell: vec2<u32>, offset: vec2<u32>) -> vec2<i32> {
    let max_x = max(params.source_width, 1u) - 1u;
    let max_y = max(params.source_height, 1u) - 1u;
    let px = min(cell.x * params.cell_width + offset.x, max_x);
    let py = min(cell.y * params.cell_height + offset.y, max_y);
    return vec2<i32>(i32(px), i32(py));
}

fn pack_cell(depth_q16: u32, luma7: u32, char6: u32, flags4: u32) -> u32 {
    let depth13 = clamp_u32((depth_q16 * DEPTH13_MAX + Q16_HALF) >> 16u, DEPTH13_MAX);
    return ((depth13 & 0x1FFFu) << 19u) |
           ((luma7 & 0x7Fu) << 12u) |
           ((char6 & 0x3Fu) << 6u) |
           ((flags4 & 0xFu) << 2u);
}

@compute @workgroup_size(8, 8, 1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    if (gid.x >= params.grid_width || gid.y >= params.grid_height) {
        return;
    }

    let half_cell = vec2<u32>(max(params.cell_width / 2u, 1u), max(params.cell_height / 2u, 1u));
    let last_cell = vec2<u32>(
        select(0u, params.cell_width - 1u, params.cell_width > 0u),
        select(0u, params.cell_height - 1u, params.cell_height > 0u),
    );
    let p0 = sample_coord(gid.xy, vec2<u32>(0u, 0u));
    let p1 = sample_coord(gid.xy, vec2<u32>(last_cell.x, 0u));
    let p2 = sample_coord(gid.xy, vec2<u32>(0u, last_cell.y));
    let p3 = sample_coord(gid.xy, half_cell);

    let d0 = textureLoad(scene_depth, p0, 0);
    let d1 = textureLoad(scene_depth, p1, 0);
    let d2 = textureLoad(scene_depth, p2, 0);
    let d3 = textureLoad(scene_depth, p3, 0);
    let depth_f = (d0 + d1 + d2 + d3) * 0.25;
    let depth_q16 = f32_unit_to_q16(depth_f);

    let c0 = textureLoad(scene_color, p0, 0).rgb;
    let c1 = textureLoad(scene_color, p1, 0).rgb;
    let c2 = textureLoad(scene_color, p2, 0).rgb;
    let c3 = textureLoad(scene_color, p3, 0).rgb;
    let color = (c0 + c1 + c2 + c3) * 0.25;
    let luma7 = clamp_u32(u32(clamp(luma_from_rgb(color), 0.0, 1.0) * 127.0 + 0.5), LUMA7_MAX);

    let focus = min(params.focus_q16, Q16_ONE);
    let aperture = min(params.aperture_q16, Q16_ONE);
    let scale = min(params.coc_scale_q16, Q16_ONE);
    let coc_base = q16_abs_diff(depth_q16, focus);
    let coc_aperture = q16_mul_unit(coc_base, aperture);
    let coc_q16 = q16_mul_unit(coc_aperture, scale);
    let char6 = density_index(luma7, coc_q16);

    let index = gid.y * params.grid_width + gid.x;
    ascii_buffer[index] = pack_cell(depth_q16, luma7, char6, params.flags);
}

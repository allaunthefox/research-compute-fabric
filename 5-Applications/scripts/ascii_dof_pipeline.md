# ASCII DoF WebGPU Q16.16 Pipeline

This is the concrete WebGPU adaptation surface for an ASCII depth-of-field pass.
The compute pass writes one packed `u32` per ASCII cell and the render pass treats
the active buffer as a glyph lookup table.

## Cell Word

`ascii_dof_pack_q16.wgsl` emits:

| Bits | Field | Mask |
| --- | --- | --- |
| 31..19 | `depth13` | `0x1fff` |
| 18..12 | `luma7` | `0x7f` |
| 11..6 | `char6` | `0x3f` |
| 5..2 | `flags4` | `0xf` |
| 1..0 | reserved | `0x3` |

The render-side character decode is:

```wgsl
let char_index = (packed >> 6u) & 0x3Fu;
```

## Buffer Rotation

Use four `GPUBuffer`s with `GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC`.
For frame `n`:

- write buffer: `n & 3`
- display/read buffer: `(n + 3) & 3`
- queued buffers: `(n + 2) & 3`, `(n + 1) & 3`

The helper in `ascii_dof_quad_buffer.ts` keeps that rotation explicit and writes
the uniform block expected by the compute shader.

## Q16.16 Boundary

Depth enters as a normalized depth texture sample, then becomes unsigned Q16.16:

```wgsl
let depth_q16 = u32(clamp(depth_f, 0.0, 1.0) * 65536.0 + 0.5);
```

Focus, aperture, and CoC scale are passed as Q16.16 uniforms. The shader avoids
`u64` by using a bounded Q16 multiply for non-negative values in `[0, 1]`, which
is enough for normalized depth and blur controls.

## Render Pass Contract

The render pass should bind the current read buffer as storage or readonly
storage, decode `char6`, and sample an SDF glyph atlas. `depth13`, `luma7`, and
`flags4` are available for tone, opacity, debug overlays, or temporal rejection.

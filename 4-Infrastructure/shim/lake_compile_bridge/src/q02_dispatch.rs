// ── Q0_2 GPU Dispatch ────────────────────────────────────────
// Exhaustive Q0_2 value enumeration via wgpu + WGSL
//
// Q0_2 values: {0, 1/4, 1/2, 3/4} encoded as Q16_16:
//   [0x00000000, 0x00004000, 0x00008000, 0x0000C000]
//
// Theorems:
//   10 (q0_2_mul_self_nonneg): 4 vectors (each value paired with itself)
//   11 (q0_2_mul_nonneg):      16 vectors (all 4x4 pairs)
//   12 (q0_2_add_nonneg):      16 vectors (all 4x4 pairs)

use crate::TheoremReceipt;
use std::borrow::Cow;
use wgpu::util::DeviceExt;

/// Q0_2 theorem definitions for GPU dispatch.
pub const Q02_THEOREMS: &[(&str, u32)] = &[
    ("q0_2_mul_self_nonneg", 10),
    ("q0_2_mul_nonneg", 11),
    ("q0_2_add_nonneg", 12),
];

/// The four Q0_2 values as Q16_16 fixed-point.
const Q02_VALUES: [u32; 4] = [
    0x00000000, // 0
    0x00004000, // 1/4
    0x00008000, // 1/2
    0x0000C000, // 3/4
];

/// Verify Q0_2 theorems on the GPU using exhaustive enumeration.
pub fn verify_q02_on_gpu() -> anyhow::Result<Vec<TheoremReceipt>> {
    let instance = wgpu::Instance::default();

    let adapter = pollster::block_on(instance.request_adapter(&wgpu::RequestAdapterOptions {
        power_preference: wgpu::PowerPreference::HighPerformance,
        compatible_surface: None,
        force_fallback_adapter: false,
    }))
    .ok_or_else(|| anyhow::anyhow!("No GPU adapter found"))?;

    let mut limits = wgpu::Limits::default();
    limits.max_storage_buffer_binding_size = adapter.limits().max_storage_buffer_binding_size;
    limits.max_buffer_size = adapter.limits().max_buffer_size;
    limits.max_compute_invocations_per_workgroup =
        adapter.limits().max_compute_invocations_per_workgroup;

    let (device, queue) = pollster::block_on(adapter.request_device(
        &wgpu::DeviceDescriptor {
            label: None,
            required_features: wgpu::Features::empty(),
            required_limits: limits,
        },
        None,
    ))?;

    // ── Generate test vectors ─────────────────────────────────────────
    // Exhaustive Q0_2 enumeration:
    //   theorem 10 (mul_self_nonneg): 4 vectors (value paired with itself)
    //   theorem 11 (mul_nonneg):      16 vectors (all 4x4 pairs)
    //   theorem 12 (add_nonneg):      16 vectors (all 4x4 pairs)
    //
    // We generate 16 vectors total (theorem 10 only uses first 4).

    let num_theorems = Q02_THEOREMS.len() as u32;
    let num_vectors = 16u32;

    let mut test_vectors: Vec<u32> = Vec::with_capacity((num_vectors * 3) as usize);
    for i in 0..4 {
        for j in 0..4 {
            let a = Q02_VALUES[i];
            let b = Q02_VALUES[j];
            test_vectors.push(a);
            test_vectors.push(b);
            test_vectors.push(0); // expected (unused for property-based checks)
        }
    }

    // ── Create buffers ────────────────────────────────────────────────

    let vectors_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("Q0_2 Test Vectors"),
        contents: bytemuck::cast_slice(&test_vectors),
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
    });

    let mut batch_data: Vec<u32> = Vec::with_capacity((num_theorems * 4) as usize);
    for &(_name, id) in Q02_THEOREMS {
        batch_data.push(id);
        batch_data.push(num_vectors);
        batch_data.push(0);
        batch_data.push(0);
    }
    let batches_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("Q0_2 Theorem Batches"),
        contents: bytemuck::cast_slice(&batch_data),
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
    });

    let mut results_init: Vec<u32> = Vec::with_capacity((num_theorems * 4) as usize);
    for &(_name, id) in Q02_THEOREMS {
        results_init.push(id);
        results_init.push(1);
        results_init.push(num_vectors);
        results_init.push(0);
    }
    let results_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("Q0_2 Results"),
        contents: bytemuck::cast_slice(&results_init),
        usage: wgpu::BufferUsages::STORAGE
            | wgpu::BufferUsages::COPY_SRC
            | wgpu::BufferUsages::COPY_DST,
    });

    let staging_size = (num_theorems * 4 * 4) as u64;
    let staging_buffer = device.create_buffer(&wgpu::BufferDescriptor {
        label: Some("Q0_2 Staging"),
        size: staging_size,
        usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
        mapped_at_creation: false,
    });

    // ── Shader module ─────────────────────────────────────────────────
    let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
        label: Some("Q0_2 Enumeration Shader"),
        source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(include_str!(
            "shaders/q02_enumeration.wgsl"
        ))),
    });

    // ── Bind group layout ─────────────────────────────────────────────
    let bind_group_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
        label: None,
        entries: &[
            wgpu::BindGroupLayoutEntry {
                binding: 0,
                visibility: wgpu::ShaderStages::COMPUTE,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Storage { read_only: true },
                    has_dynamic_offset: false,
                    min_binding_size: None,
                },
                count: None,
            },
            wgpu::BindGroupLayoutEntry {
                binding: 1,
                visibility: wgpu::ShaderStages::COMPUTE,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Storage { read_only: true },
                    has_dynamic_offset: false,
                    min_binding_size: None,
                },
                count: None,
            },
            wgpu::BindGroupLayoutEntry {
                binding: 2,
                visibility: wgpu::ShaderStages::COMPUTE,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Storage { read_only: false },
                    has_dynamic_offset: false,
                    min_binding_size: None,
                },
                count: None,
            },
        ],
    });

    // ── Pipeline ──────────────────────────────────────────────────────
    let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
        label: None,
        bind_group_layouts: &[&bind_group_layout],
        push_constant_ranges: &[],
    });

    let pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
        label: None,
        layout: Some(&pipeline_layout),
        module: &shader,
        entry_point: "main",
    });

    // ── Bind group ────────────────────────────────────────────────────
    let bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
        label: None,
        layout: &bind_group_layout,
        entries: &[
            wgpu::BindGroupEntry {
                binding: 0,
                resource: vectors_buffer.as_entire_binding(),
            },
            wgpu::BindGroupEntry {
                binding: 1,
                resource: batches_buffer.as_entire_binding(),
            },
            wgpu::BindGroupEntry {
                binding: 2,
                resource: results_buffer.as_entire_binding(),
            },
        ],
    });

    // ── Dispatch ──────────────────────────────────────────────────────
    let mut encoder =
        device.create_command_encoder(&wgpu::CommandEncoderDescriptor { label: None });

    {
        let mut compute_pass = encoder.begin_compute_pass(&wgpu::ComputePassDescriptor {
            label: None,
            timestamp_writes: None,
        });
        compute_pass.set_pipeline(&pipeline);
        compute_pass.set_bind_group(0, &bind_group, &[]);

        let workgroups_y = ((num_vectors + 63) / 64).max(1);
        compute_pass.dispatch_workgroups(num_theorems, workgroups_y, 1);
    }

    encoder.copy_buffer_to_buffer(&results_buffer, 0, &staging_buffer, 0, staging_size);

    queue.submit(Some(encoder.finish()));

    // ── Readback ──────────────────────────────────────────────────────
    let (sender, receiver) = std::sync::mpsc::channel();
    let buffer_slice = staging_buffer.slice(..);
    buffer_slice.map_async(wgpu::MapMode::Read, move |v| {
        let _ = sender.send(v);
    });

    device.poll(wgpu::Maintain::Wait);
    receiver
        .recv()
        .map_err(|e| anyhow::anyhow!("Q0_2 GPU readback channel error: {:?}", e))?
        .map_err(|e| anyhow::anyhow!("Q0_2 GPU buffer map error: {:?}", e))?;

    let mapped = buffer_slice.get_mapped_range();
    let result_bytes: Vec<u8> = mapped.to_vec();
    staging_buffer.unmap();

    let result_u32s: Vec<u32> = result_bytes
        .chunks_exact(4)
        .map(|chunk| u32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
        .collect();

    let mut receipts = Vec::with_capacity(Q02_THEOREMS.len());
    for (i, &(name, _id)) in Q02_THEOREMS.iter().enumerate() {
        let base = i * 4;
        let theorem_id = result_u32s[base];
        let _passed_flag = result_u32s[base + 1];
        let total = result_u32s[base + 2];
        let failed = result_u32s[base + 3];

        let passed_val = failed == 0;
        receipts.push(TheoremReceipt {
            name: name.to_string(),
            theorem_id,
            tested: total,
            passed: passed_val,
        });

        if passed_val {
            eprintln!("  Q0_2 ✓ {} passed ({} vectors)", name, total);
        } else {
            eprintln!(
                "  Q0_2 ✗ {} FAILED ({}/{} vectors failed)",
                name, failed, total
            );
        }
    }

    Ok(receipts)
}

// ── GPU Dispatch ────────────────────────────────────────────────────────
// wgpu context and theorem verification dispatch for the lake compile bridge.
//
// Follows the pattern from 5-Applications/parquet_compressor/src/gpu.rs:
//   wgpu adapter probe → WGSL compute → SSBO readback

use std::borrow::Cow;

use wgpu::util::DeviceExt;

use crate::TheoremReceipt;

/// GPU device info from adapter probe.
pub struct GpuInfo {
    pub name: String,
}

/// Probe for a GPU adapter and return device info.
pub fn probe_gpu() -> anyhow::Result<GpuInfo> {
    let instance = wgpu::Instance::default();

    // Synchronous adapter probe via pollster
    let adapter = pollster::block_on(instance.request_adapter(
        &wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            compatible_surface: None,
            force_fallback_adapter: false,
        },
    ))
    .ok_or_else(|| anyhow::anyhow!("No GPU adapter found"))?;

    let name = adapter.get_info().name.to_string();
    Ok(GpuInfo { name })
}

/// Verify FixedPoint theorems on the GPU.
///
/// Each theorem is tested against `num_vectors` random inputs.
/// Returns a Vec of TheoremReceipt, one per theorem.
pub fn verify_theorems_on_gpu(
    theorems: &[(&str, u32)],
    num_vectors: u32,
) -> anyhow::Result<Vec<TheoremReceipt>> {
    let instance = wgpu::Instance::default();

    let adapter = pollster::block_on(instance.request_adapter(
        &wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            compatible_surface: None,
            force_fallback_adapter: false,
        },
    ))
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
    // Each TestVector has (a, b, expected). We generate random pairs
    // covering edge cases and uniform random values.

    let num_theorems = theorems.len() as u32;
    let total_vectors = num_vectors;

    let mut test_vectors: Vec<u32> = Vec::with_capacity((total_vectors * 3) as usize);
    // Seed-based deterministic generation for reproducibility
    for i in 0..total_vectors {
        // Mix of edge cases and random values
        let a = match i % 8 {
            0 => 0x00000000,           // zero
            1 => 0x00010000,           // one
            2 => 0x7FFFFFFF,           // max positive
            3 => 0x80000000,           // min negative
            4 => 0xFFFFFFFF,           // -1 (infinity sentinel)
            5 => 0x00000001,           // epsilon
            6 => i.wrapping_mul(0x9E3779B9), // golden ratio hash
            _ => i.wrapping_mul(0x9E3779B9).wrapping_add(0x12345678),
        };
        let b = match (i / 8) % 8 {
            0 => 0x00000000,
            1 => 0x00010000,
            2 => 0x80000000,
            3 => 0x7FFFFFFF,
            4 => 0x00000001,
            5 => i.wrapping_mul(0x6C8E9CF5),
            6 => i.wrapping_mul(0x9E3779B9) ^ 0xDEADBEEF,
            _ => i.wrapping_mul(0x12345679),
        };
        test_vectors.push(a);
        test_vectors.push(b);
        test_vectors.push(0); // expected (unused for property-based checks)
    }

    // ── Create buffers ────────────────────────────────────────────────

    // Storage buffer: test vectors (read-only)
    let vectors_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("Test Vectors"),
        contents: bytemuck::cast_slice(&test_vectors),
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
    });

    // Storage buffer: theorem batch descriptors
    let mut batch_data: Vec<u32> = Vec::with_capacity((num_theorems * 4) as usize);
    for &(_name, id) in theorems {
        batch_data.push(id);          // theorem_id
        batch_data.push(num_vectors); // count
        batch_data.push(0);           // padding
        batch_data.push(0);           // padding
    }
    let batches_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("Theorem Batches"),
        contents: bytemuck::cast_slice(&batch_data),
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
    });

    // Storage buffer: results (read-write, initialized to zero)
    let mut results_init: Vec<u32> = Vec::with_capacity((num_theorems * 4) as usize);
    for &(_name, id) in theorems {
        results_init.push(id);    // theorem_id
        results_init.push(1);     // passed (optimistic, set to 0 on any failure)
        results_init.push(num_vectors); // total
        results_init.push(0);     // failed count
    }
    let results_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("Results"),
        contents: bytemuck::cast_slice(&results_init),
        usage: wgpu::BufferUsages::STORAGE
            | wgpu::BufferUsages::COPY_SRC
            | wgpu::BufferUsages::COPY_DST,
    });

    // Staging buffer for readback
    let staging_size = (num_theorems * 4 * 4) as u64; // 4 u32s per result
    let staging_buffer = device.create_buffer(&wgpu::BufferDescriptor {
        label: Some("Staging"),
        size: staging_size,
        usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
        mapped_at_creation: false,
    });

    // ── Shader module ─────────────────────────────────────────────────
    let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
        label: Some("Compile Bridge Shader"),
        source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(
            include_str!("shaders/compile_bridge.wgsl"),
        )),
    });

    // ── Bind group layout ─────────────────────────────────────────────
    let bind_group_layout =
        device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: None,
            entries: &[
                // binding 0: test vectors (read)
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
                // binding 1: theorem batches (read)
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
                // binding 2: results (read-write)
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
    let mut encoder = device.create_command_encoder(&wgpu::CommandEncoderDescriptor {
        label: None,
    });

    {
        let mut compute_pass = encoder.begin_compute_pass(&wgpu::ComputePassDescriptor {
            label: None,
            timestamp_writes: None,
        });
        compute_pass.set_pipeline(&pipeline);
        compute_pass.set_bind_group(0, &bind_group, &[]);

        // Dispatch: one workgroup per theorem, vectors/64 workgroups in y
        let workgroups_y = ((num_vectors + 63) / 64).max(1);
        compute_pass.dispatch_workgroups(num_theorems, workgroups_y, 1);
    }

    // Copy results to staging
    encoder.copy_buffer_to_buffer(
        &results_buffer,
        0,
        &staging_buffer,
        0,
        staging_size,
    );

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
        .map_err(|e| anyhow::anyhow!("GPU readback channel error: {:?}", e))?
        .map_err(|e| anyhow::anyhow!("GPU buffer map error: {:?}", e))?;

    let mapped = buffer_slice.get_mapped_range();
    let result_bytes: Vec<u8> = mapped.to_vec();
    staging_buffer.unmap();

    // ── Parse results ─────────────────────────────────────────────────
    // Each result is 4 u32s: theorem_id, passed, total, failed
    let result_u32s: Vec<u32> = result_bytes
        .chunks_exact(4)
        .map(|chunk| u32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
        .collect();

    let mut receipts = Vec::with_capacity(theorems.len());
    for (i, &(name, _id)) in theorems.iter().enumerate() {
        let base = i * 4;
        let theorem_id = result_u32s[base];
        let _passed_flag = result_u32s[base + 1];
        let total = result_u32s[base + 2];
        let failed = result_u32s[base + 3];

        let passed = failed == 0;
        receipts.push(TheoremReceipt {
            name: name.to_string(),
            theorem_id,
            tested: total,
            passed,
        });

        if passed {
            eprintln!("  ✓ {} passed ({} vectors)", name, total);
        } else {
            eprintln!(
                "  ✗ {} FAILED ({}/{} vectors failed)",
                name, failed, total
            );
        }
    }

    Ok(receipts)
}

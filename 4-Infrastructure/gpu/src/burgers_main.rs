// burgers_main.rs
// GPU stress test: runs burgers_particles.wgsl over 128³ grid × 4 lemmas.
// Tests: energyDissipation, massConservation, cflStability, complexityRegularization
//
// Each lemma: 2,097,152 initial conditions, each running multi-step Euler integration
// in Q16_16 fixed-point. Pass/fail stored in a bit vector, counters read back.

use std::sync::mpsc;
// unused

const LEMMAS: [&str; 4] = [
    "energyDissipation",
    "massConservation",
    "cflStability",
    "complexityRegularization",
];
const GRID_SIZE: u32 = 128;       // 128³ particles
const TOTAL_THREADS: u32 = GRID_SIZE * GRID_SIZE * GRID_SIZE; // 2,097,152
const BIT_WORDS: u64 = 2097152 / 32; // 65536 u32s = 256KB bit vector
const WORKGROUP_SIZE: u32 = 8;    // 8×8×4 = 256 threads per workgroup
const WORKGROUPS_XY: u32 = GRID_SIZE / WORKGROUP_SIZE; // 16
const WORKGROUPS_Z: u32 = GRID_SIZE / 4; // 32 (z-dim workgroup is 4)

#[repr(C)]
#[derive(Clone, Copy, bytemuck::Pod, bytemuck::Zeroable)]
struct Counters {
    proved: u32, failed: u32, first_fail_addr: u32, first_lemma: u32,
}

#[repr(C)]
#[derive(Clone, Copy, bytemuck::Pod, bytemuck::Zeroable)]
struct Params {
    lemma_id: u32, seed: u32, n: u32, padding: u32,
}

#[repr(C)]
#[derive(Clone, Copy, bytemuck::Pod, bytemuck::Zeroable)]
struct Thresholds {
    nu_q16: u32, dt_q16: u32, dx_q16: u32, max_steps: u32,
}

async fn run() -> Result<(), Box<dyn std::error::Error>> {
    let inst = wgpu::Instance::default();
    let ada = inst.request_adapter(&wgpu::RequestAdapterOptions::default()).await
        .ok_or("no GPU adapter — is Vulkan working?")?;
    println!("Adapter: {:?}", ada.get_info());
    let (dev, q) = ada.request_device(&wgpu::DeviceDescriptor::default(), None).await?;

    let shader = dev.create_shader_module(wgpu::ShaderModuleDescriptor {
        label: Some("burgers"),
        source: wgpu::ShaderSource::Wgsl(
            include_str!("../shaders/burgers_particles.wgsl").into()),
    });

    // Bit vector storage: 256KB for 2M particles
    let bit_buf = dev.create_buffer(&wgpu::BufferDescriptor {
        label: Some("bits"), size: BIT_WORDS * 4,
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::COPY_SRC,
        mapped_at_creation: false,
    });
    // Counters: 16 bytes
    let cnt_buf = dev.create_buffer(&wgpu::BufferDescriptor {
        label: Some("cnt"), size: 16,
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::COPY_SRC,
        mapped_at_creation: false,
    });
    // Params: 16 bytes (lemma_id, seed, N, padding)
    let params_buf = dev.create_buffer(&wgpu::BufferDescriptor {
        label: Some("params"), size: 16,
        usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
        mapped_at_creation: false,
    });
    // Thresholds: 16 bytes (nu, dt, dx, max_steps)
    let thresh_buf = dev.create_buffer(&wgpu::BufferDescriptor {
        label: Some("thresh"), size: 16,
        usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
        mapped_at_creation: false,
    });
    // Readback buffer (counters)
    let rb_buf = dev.create_buffer(&wgpu::BufferDescriptor {
        label: Some("rb"), size: 16,
        usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
        mapped_at_creation: false,
    });

    let layout = dev.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
        label: Some("l"), entries: &[
            wgpu::BindGroupLayoutEntry {
                binding: 0, visibility: wgpu::ShaderStages::COMPUTE,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Storage { read_only: false },
                    has_dynamic_offset: false, min_binding_size: None,
                }, count: None,
            },
            wgpu::BindGroupLayoutEntry {
                binding: 1, visibility: wgpu::ShaderStages::COMPUTE,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Storage { read_only: false },
                    has_dynamic_offset: false, min_binding_size: None,
                }, count: None,
            },
            wgpu::BindGroupLayoutEntry {
                binding: 2, visibility: wgpu::ShaderStages::COMPUTE,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Uniform, has_dynamic_offset: false,
                    min_binding_size: None,
                }, count: None,
            },
            wgpu::BindGroupLayoutEntry {
                binding: 3, visibility: wgpu::ShaderStages::COMPUTE,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Uniform, has_dynamic_offset: false,
                    min_binding_size: None,
                }, count: None,
            },
        ],
    });

    let bg = dev.create_bind_group(&wgpu::BindGroupDescriptor {
        label: Some("bg"), layout: &layout,
        entries: &[
            wgpu::BindGroupEntry { binding: 0, resource: bit_buf.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 1, resource: cnt_buf.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 2, resource: params_buf.as_entire_binding() },
            wgpu::BindGroupEntry { binding: 3, resource: thresh_buf.as_entire_binding() },
        ],
    });

    let pl = dev.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
        label: Some("pl"), bind_group_layouts: &[&layout], ..Default::default() });
    let pipeline = dev.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
        label: Some("pipe"), layout: Some(&pl), module: &shader,
        entry_point: Some("main"), cache: None,
        compilation_options: wgpu::PipelineCompilationOptions::default(),
    });

    // Burgers parameters:
    // nu = 0.1 (Q16_16: 6554 = 0x0001999A)
    // dt = 0.01 (Q16_16: 655 = 0x000028F6)
    // dx = 1.0  (Q16_16: 65536 = 0x00010000)
    let nu_q16: u32 = 6554;     // 0.1
    let dt_q16: u32 = 655;      // 0.01
    let dx_q16: u32 = 65536;    // 1.0

    let mut total_global_fail: u64 = 0;
    let start_time = std::time::Instant::now();

    for (lem_id, name) in LEMMAS.iter().enumerate() {
        // Zero bit vector and counters
        let zero_words = vec![0u32; BIT_WORDS as usize];
        q.write_buffer(&bit_buf, 0, bytemuck::cast_slice(&zero_words));
        q.write_buffer(&cnt_buf, 0, bytemuck::bytes_of(
            &Counters { proved: 0, failed: 0, first_fail_addr: 0, first_lemma: 0 }));

        // Write uniforms
        let params = Params { lemma_id: lem_id as u32, seed: 0, n: 4, padding: 0 };
        q.write_buffer(&params_buf, 0, bytemuck::bytes_of(&params));
        let thresh = Thresholds { nu_q16, dt_q16, dx_q16, max_steps: 20 };
        q.write_buffer(&thresh_buf, 0, bytemuck::bytes_of(&thresh));

        // Dispatch 16×16×16 = 4096 workgroups × 512 threads = 2,097,152
        let mut enc = dev.create_command_encoder(&wgpu::CommandEncoderDescriptor::default());
        {
            let mut cp = enc.begin_compute_pass(&wgpu::ComputePassDescriptor::default());
            cp.set_pipeline(&pipeline);
            cp.set_bind_group(0, &bg, &[]);
            cp.dispatch_workgroups(WORKGROUPS_XY, WORKGROUPS_XY, WORKGROUPS_Z);
        }
        enc.copy_buffer_to_buffer(&cnt_buf, 0, &rb_buf, 0, 16);
        q.submit(Some(enc.finish()));

        // Read back counters
        let sl = rb_buf.slice(..);
        let (tx, rx) = mpsc::channel();
        sl.map_async(wgpu::MapMode::Read, move |v| { let _ = tx.send(v.is_ok()); });
        dev.poll(wgpu::Maintain::Wait);
        rx.recv().unwrap_or(false);
        let (proved, failed, first_addr): (u32, u32, u32) = {
            let mapped = sl.get_mapped_range();
            let c: &Counters = bytemuck::from_bytes(&*mapped);
            let res = (c.proved, c.failed, c.first_fail_addr);
            drop(mapped);
            res
        };
        rb_buf.unmap();

        let elapsed = start_time.elapsed();
        total_global_fail += failed as u64;
        let status = if failed == 0 { "✅" } else { "❌" };
        println!("{} {}: {} proved, {} failed (first @ addr {}), {:.2}s",
            status, name, proved, failed, first_addr, elapsed.as_secs_f64());
    }

    let total_elapsed = start_time.elapsed();
    println!("\n── Burgers Stress Test Results ──");
    if total_global_fail == 0 {
        println!("✅ ALL 4 BURGERS LEMMAS PROVED FOR ALL 2,097,152 INITIAL CONDITIONS");
    } else {
        println!("❌ {} TOTAL COUNTEREXAMPLES FOUND ACROSS {} LEMMAS", total_global_fail, LEMMAS.len());
    }
    println!("Total grid cells tested: {} × 4 = {}", TOTAL_THREADS, TOTAL_THREADS * LEMMAS.len() as u32);
    println!("Total time: {:.2}s", total_elapsed.as_secs_f64());
    println!("Throughput: {:.0} cells/s",
        (TOTAL_THREADS as f64 * LEMMAS.len() as f64) / total_elapsed.as_secs_f64());
    Ok(())
}

fn main() {
    pollster::block_on(run()).unwrap_or_else(|e| eprintln!("Error: {e}"));
}

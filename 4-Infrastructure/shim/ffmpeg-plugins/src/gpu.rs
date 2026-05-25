use crate::avfilters::s3c::{S3CShaders, S3C_COMPUTE_SHADER};
use wgpu::util::DeviceExt;

pub struct GpuBackend {
    device: wgpu::Device,
    queue: wgpu::Queue,
    pipeline: wgpu::ComputePipeline,
    bgl: wgpu::BindGroupLayout,
}

impl GpuBackend {
    pub async fn new() -> Option<Self> {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
            backends: wgpu::Backends::VULKAN,
            flags: wgpu::InstanceFlags::default(),
            memory_budget_thresholds: wgpu::MemoryBudgetThresholds::default(),
            backend_options: wgpu::BackendOptions::default(),
            display: None,
        });
        let adapter = match instance.request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            ..Default::default()
        }).await {
            Ok(a) => a,
            Err(_) => return None,
        };
        let (device, queue) = match adapter.request_device(
            &wgpu::DeviceDescriptor {
                label: None,
                required_features: wgpu::Features::empty(),
                required_limits: wgpu::Limits::default(),
                experimental_features: wgpu::ExperimentalFeatures::default(),
                memory_hints: wgpu::MemoryHints::default(),
                trace: wgpu::Trace::Off,
            },
        ).await {
            Ok(dq) => dq,
            _ => return None,
        };

        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: None,
            source: wgpu::ShaderSource::Wgsl(std::borrow::Cow::Borrowed(S3C_COMPUTE_SHADER)),
        });

        let bgl = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
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
                        ty: wgpu::BufferBindingType::Storage { read_only: false },
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
            ],
        });

        let pl = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: None,
            bind_group_layouts: &[Some(&bgl)],
            immediate_size: 0,
        });

        let pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: None,
            layout: Some(&pl),
            module: &shader,
            entry_point: Some("main"),
            compilation_options: wgpu::PipelineCompilationOptions::default(),
            cache: None,
        });

        Some(Self { device, queue, pipeline, bgl })
    }

    pub fn process_s3c(&self, samples: &[i16]) -> Vec<S3CShaders> {
        let n = samples.len() as u32;
        if n == 0 { return vec![]; }
        let g = 256u32;
        let ng = (n + g - 1) / g;
        let osz = n as u64 * std::mem::size_of::<S3CShaders>() as u64;

        let in_u32: Vec<u32> = samples.iter().map(|&s| s as i32 as u32).collect();
        let ib = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: None, contents: bytemuck::cast_slice(&in_u32),
            usage: wgpu::BufferUsages::STORAGE,
        });
        let ob = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: None, size: osz,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let sb = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: None, size: osz,
            usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
            mapped_at_creation: false,
        });

        let bg = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: None, layout: &self.bgl,
            entries: &[
                wgpu::BindGroupEntry { binding: 0, resource: ib.as_entire_binding() },
                wgpu::BindGroupEntry { binding: 1, resource: ob.as_entire_binding() },
            ],
        });

        let mut enc = self.device.create_command_encoder(&wgpu::CommandEncoderDescriptor { label: None });
        {
            let mut cp = enc.begin_compute_pass(&wgpu::ComputePassDescriptor { label: None, timestamp_writes: None });
            cp.set_pipeline(&self.pipeline);
            cp.set_bind_group(0, &bg, &[]);
            cp.dispatch_workgroups(ng, 1, 1);
        }
        enc.copy_buffer_to_buffer(&ob, 0, &sb, 0, osz);
        self.queue.submit(std::iter::once(enc.finish()));

        let sl = sb.slice(..);
        let (tx, rx) = std::sync::mpsc::channel();
        sl.map_async(wgpu::MapMode::Read, move |v| { let _ = tx.send(v); });
        self.device.poll(wgpu::PollType::Wait { submission_index: None, timeout: None }).ok();
        let _ = rx.recv();
        let d = sl.get_mapped_range();
        let r: Vec<S3CShaders> = bytemuck::cast_slice(&d).to_vec();
        drop(d); sb.unmap();
        r
    }
}

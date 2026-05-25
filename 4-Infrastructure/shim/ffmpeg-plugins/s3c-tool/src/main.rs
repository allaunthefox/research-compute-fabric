//! s3c-tool — reads i16 PCM from stdin, processes through S3C, outputs JSON.
//! Auto-detects GPU (Vulkan) and falls back to CPU.
use std::io::{self, Read};
use clap::Parser;

#[derive(Parser)]
#[command(name = "s3c-tool", about = "S3C shell decomposition of PCM audio (GPU accelerated)")]
struct Args {
    #[arg(long, default_value = "4096")]
    chunk: usize,
    #[arg(long, default_value_t = false)]
    aggregate: bool,
    #[arg(long, default_value = "48000")]
    rate: u32,
    /// Force CPU even if GPU is available
    #[arg(long, default_value_t = false)]
    cpu: bool,
}

fn main() -> Result<(), String> {
    let args = Args::parse();

    // Read all i16 samples from stdin
    let mut stdin = io::stdin().lock();
    let mut all: Vec<i16> = Vec::new();
    let mut buf = [0u8; 8192];
    loop {
        let n = stdin.read(&mut buf).map_err(|e| format!("read: {}", e))?;
        if n == 0 { break; }
        let samples: &[i16] = bytemuck::cast_slice(&buf[..n - (n % 2)]);
        all.extend_from_slice(samples);
    }
    if all.is_empty() { return Err("no input data".into()); }

    // Try GPU backend first
    let use_gpu = if !args.cpu {
        match pollster::block_on(ffmpeg_plugins::gpu::GpuBackend::new()) {
            Some(gpu) => {
                eprintln!("[s3c] GPU backend ready (Vulkan)");
                let chunk_sz = if args.chunk == 0 { all.len() } else { args.chunk.min(all.len()) };
                let mut results = Vec::new();
                for chunk in all.chunks(chunk_sz) {
                    let handles = gpu.process_s3c(chunk);
                    if args.aggregate {
                        let stats = ffmpeg_plugins::avfilters::s3c::aggregate(&handles);
                        results.push(serde_json::json!({
                            "offset": results.len() * chunk_sz,
                            "stats": { "n": stats.n_samples, "throats": stats.n_throats, "avg_j": stats.avg_j_score, "max_j": stats.max_j_score, "min_j": stats.min_j_score, "emission_ratio": stats.emission_ratio, }
                        }));
                    } else {
                        for (i, h) in handles.iter().enumerate() {
                            results.push(serde_json::json!({"i": i, "k": h.k, "a": h.a, "b": h.b, "j": h.j_score, "t": h.throat}));
                        }
                    }
                }
                let out = serde_json::json!({"tool": "s3c-tool", "backend": "gpu", "results": results});
                println!("{}", serde_json::to_string_pretty(&out).unwrap());
                return Ok(());
            }
            None => { eprintln!("[s3c] No GPU found, using CPU"); false }
        }
    } else { false };

    // CPU fallback
    if !use_gpu {
        eprintln!("[s3c] CPU backend");
        let chunk_sz = if args.chunk == 0 { all.len() } else { args.chunk.min(all.len()) };
        let mut results = Vec::new();
        for chunk in all.chunks(chunk_sz) {
            let handles = ffmpeg_plugins::avfilters::s3c::process_chunk(chunk);
            if args.aggregate {
                let stats = ffmpeg_plugins::avfilters::s3c::aggregate(&handles);
                results.push(serde_json::json!({
                    "offset": results.len() * chunk_sz,
                    "stats": { "n": stats.n_samples, "throats": stats.n_throats, "avg_j": stats.avg_j_score, "max_j": stats.max_j_score, "min_j": stats.min_j_score, "emission_ratio": stats.emission_ratio, }
                }));
            } else {
                for (i, h) in handles.iter().enumerate() {
                    results.push(serde_json::json!({"i": i, "k": h.k, "a": h.a, "b": h.b, "j": h.j_score, "t": h.throat}));
                }
            }
        }
        let out = serde_json::json!({"tool": "s3c-tool", "backend": "cpu", "results": results});
        println!("{}", serde_json::to_string_pretty(&out).unwrap());
    }
    Ok(())
}

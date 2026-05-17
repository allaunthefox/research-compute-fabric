mod compressor;
mod gpu;
mod parquet_handler;
mod shifters;

use crate::compressor::Compressor;
use crate::gpu::GpuContext;
use crate::shifters::{get_shifter, intrinsic_load};
use clap::Parser;
use indicatif::{ProgressBar, ProgressStyle};
use rayon::prelude::*;
use serde_json::json;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use sysinfo::System;
use tokio::sync::Semaphore;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[arg(
        short,
        long,
        default_value = "3-Mathematical-Models/equations_parquet_tagged"
    )]
    input_dir: String,

    #[arg(
        short,
        long,
        default_value = "3-Mathematical-Models/equations_compressed"
    )]
    output_dir: String,

    #[arg(short, long, default_value_t = 8192)]
    memory_limit_mb: u64,

    #[arg(short, long, default_value_t = 4)]
    threads: usize,

    #[arg(long, default_value_t = false)]
    use_gpu: bool,
}

struct Stats {
    total_raw_bytes: usize,
    total_compressed_bytes: usize,
    files: Vec<serde_json::Value>,
}

fn main() -> anyhow::Result<()> {
    let args = Args::parse();
    let base_path = Path::new("/home/allaun/Documents/Research Stack");
    let input_path = base_path.join(&args.input_dir);
    let output_path = base_path.join(&args.output_dir);

    std::fs::create_dir_all(&output_path)?;

    let mut sys = System::new_all();
    sys.refresh_memory();
    let available_memory_mb = sys.available_memory() / 1024 / 1024;
    println!("Available Memory: {} MB", available_memory_mb);

    let gpu_context = if args.use_gpu {
        println!("Initializing GPU...");
        Some(Arc::new(pollster::block_on(GpuContext::new())?))
    } else {
        None
    };

    let pattern = format!("{}/*_equations_*.parquet", input_path.display());
    let files: Vec<PathBuf> = glob::glob(&pattern)?
        .filter_map(Result::ok)
        .filter(|p| !p.to_string_lossy().contains("tagging_summary"))
        .collect();

    println!("Found {} Parquet files", files.len());

    let mp = indicatif::MultiProgress::new();
    let pb = mp.add(ProgressBar::new(files.len() as u64));
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}")?
        .progress_chars("#>-"));

    pb.enable_steady_tick(std::time::Duration::from_millis(100));

    let stats = Arc::new(Mutex::new(Stats {
        total_raw_bytes: 0,
        total_compressed_bytes: 0,
        files: Vec::new(),
    }));

    let semaphore = Arc::new(Semaphore::new(args.threads));

    let rt = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(args.threads)
        .enable_all()
        .build()?;

    files.par_iter().for_each(|file_path| {
        let _permit = rt.block_on(semaphore.acquire()).expect("Semaphore closed");

        let fname = file_path.file_stem().unwrap().to_str().unwrap();
        pb.set_message(format!("Current: {}", fname));

        let sub_pb = mp.add(indicatif::ProgressBar::new_spinner());
        sub_pb.set_style(
            indicatif::ProgressStyle::default_spinner()
                .template("{spinner:.yellow} {msg}")
                .unwrap(),
        );
        sub_pb.set_message(format!("Starting {}", fname));
        sub_pb.enable_steady_tick(std::time::Duration::from_millis(100));

        match process_file_with_progress(
            file_path,
            &output_path,
            &stats,
            gpu_context.clone(),
            &sub_pb,
        ) {
            Ok(_) => {
                pb.inc(1);
                sub_pb.finish_and_clear();
            }
            Err(e) => {
                eprintln!("Error processing {}: {}", fname, e);
                sub_pb.finish_with_message(format!("Failed: {}", fname));
            }
        }
    });

    pb.finish_with_message("Compression complete");

    // Finalize stats and manifest
    let stats = stats.lock().unwrap();
    let manifest = json!({
        "version": 3,
        "timestamp": chrono::Local::now().to_rfc3339(),
        "total_size_raw_mb": stats.total_raw_bytes as f64 / 1024.0 / 1024.0,
        "total_size_compressed_mb": stats.total_compressed_bytes as f64 / 1024.0 / 1024.0,
        "compression_ratio": stats.total_raw_bytes as f64 / stats.total_compressed_bytes.max(1) as f64,
        "files": stats.files,
    });

    let manifest_path = output_path.join("compression_manifest.json");
    std::fs::write(&manifest_path, serde_json::to_string_pretty(&manifest)?)?;

    let mut index_files = json!({});
    for f in &stats.files {
        let name = f["name"].as_str().unwrap();
        index_files[name] = json!({
            "compressed": format!("{}.compressed", name),
            "raw_mb": f["raw_bytes"].as_u64().unwrap_or(0) as f64 / 1024.0 / 1024.0,
            "compressed_mb": f["compressed_bytes"].as_u64().unwrap_or(0) as f64 / 1024.0 / 1024.0,
            "ratio": f["ratio"].as_f64().unwrap_or(1.0),
            "chain": f["chain"].as_str().unwrap_or("unknown"),
        });
    }

    let index = json!({
        "manifest": "compression_manifest.json",
        "files": index_files,
    });

    let index_path = output_path.join("index.json");
    std::fs::write(&index_path, serde_json::to_string_pretty(&index)?)?;

    let parent_index = input_path
        .parent()
        .unwrap()
        .join("equations_NUVMAP_index.json");
    std::fs::copy(&index_path, parent_index)?;

    Ok(())
}

fn process_file_with_progress(
    file_path: &Path,
    output_dir: &Path,
    stats: &Arc<Mutex<Stats>>,
    gpu_context: Option<Arc<GpuContext>>,
    pb: &ProgressBar,
) -> anyhow::Result<()> {
    pb.set_message("Serializing Parquet...");
    let raw_data = parquet_handler::serialize_parquet_to_bytes(file_path)?;
    let raw_len = raw_data.len();

    pb.set_message("GPU Preprocessing...");
    let data_to_compress = if let Some(gpu) = gpu_context {
        gpu.run_xor_transform(&raw_data, 0x1F)?
    } else {
        raw_data
    };

    let chains = vec![
        ("best_general", vec!["bwt", "mtf", "lzw"]),
        ("fast_text", vec!["bwt", "run_length"]),
    ];

    let mut best_data = data_to_compress.clone();
    let mut best_ratio = 1.0;
    let mut best_chain_name = "none";

    for (name, chain) in chains {
        pb.set_message(format!("Trying chain: {}...", name));
        let shifters: Vec<Box<dyn crate::shifters::Shifter>> =
            chain.iter().map(|s| get_shifter(s).unwrap()).collect();

        if let Ok(compressed) = Compressor::compress(data_to_compress.clone(), shifters) {
            let ratio = raw_len as f64 / compressed.len().max(1) as f64;
            if ratio > best_ratio {
                best_ratio = ratio;
                best_data = compressed;
                best_chain_name = name;
            }
        }
    }

    pb.set_message("Finalizing file...");
    let fname = file_path.file_stem().unwrap().to_str().unwrap();
    let output_path = output_dir.join(format!("{}.compressed", fname));
    std::fs::write(output_path, &best_data)?;

    let mut s = stats.lock().unwrap();
    s.total_raw_bytes += raw_len;
    s.total_compressed_bytes += best_data.len();
    s.files.push(json!({
        "name": fname,
        "raw_bytes": raw_len,
        "compressed_bytes": best_data.len(),
        "raw_intrinsic_load": intrinsic_load(&data_to_compress),
        "ratio": best_ratio,
        "chain": best_chain_name,
    }));

    Ok(())
}

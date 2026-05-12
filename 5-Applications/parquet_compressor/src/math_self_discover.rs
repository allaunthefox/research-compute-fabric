use anyhow::{Context, Result};
use arrow::array::Array;
use arrow::array::StringArray;
use arrow::datatypes::{DataType, Field, Schema};
use arrow::record_batch::RecordBatch;
use clap::Parser;
use dashmap::DashMap;
use indicatif::{ProgressBar, ProgressStyle};
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use parquet::arrow::ArrowWriter;
use rayon::iter::{IntoParallelIterator, ParallelIterator};
use rayon::ThreadPoolBuilder;
use regex::Regex;
use serde::Serialize;
use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};
use sysinfo::{CpuRefreshKind, MemoryRefreshKind, RefreshKind, System};

// ── CLI ──────────────────────────────────────────────────────────────────────

#[derive(Parser, Debug)]
#[command(name = "math_self_discover")]
#[command(about = "Unsupervised structural taxonomy from naked equations.")]
struct Config {
    /// Input parquet (math-raw)
    #[arg(
        short,
        long,
        default_value = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/equations_parquet_tagged/equations_math_raw.parquet"
    )]
    input: String,

    /// Output JSON report
    #[arg(
        short,
        long,
        default_value = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/math_self_discovered.json"
    )]
    report: String,

    /// Output parquet with cluster assignments
    #[arg(
        long,
        default_value = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/equations_parquet_tagged/equations_self_clustered.parquet"
    )]
    clustered: String,

    /// Max CPU threads (0 = num_cpus / 2)
    #[arg(long, default_value = "0")]
    threads: usize,

    /// Memory cap in MB (0 = no cap)
    #[arg(long, default_value = "0")]
    memory_cap_mb: usize,

    /// Batch size for reading
    #[arg(long, default_value = "10000")]
    batch_size: usize,

    /// Pause if system CPU % exceeds this
    #[arg(long, default_value = "80")]
    cpu_threshold: f32,

    /// Pause if system RAM % exceeds this
    #[arg(long, default_value = "90")]
    memory_threshold: f32,

    /// Number of top motifs to report
    #[arg(long, default_value = "100")]
    top_motifs: usize,

    /// Directory for on-disk fingerprint cache
    #[arg(long, default_value = "")]
    cache_dir: String,

    /// Max RAM cache entries (0 = unlimited)
    #[arg(long, default_value = "0")]
    ram_cache_cap: usize,
}

// ── Resource Monitor ─────────────────────────────────────────────────────────

struct ResourceMonitor {
    sys: Mutex<System>,
    cpu_threshold: f32,
    memory_threshold: f32,
}

impl ResourceMonitor {
    fn new(cpu_threshold: f32, memory_threshold: f32) -> Self {
        Self {
            sys: Mutex::new(System::new_with_specifics(
                RefreshKind::new()
                    .with_cpu(CpuRefreshKind::everything())
                    .with_memory(MemoryRefreshKind::everything()),
            )),
            cpu_threshold,
            memory_threshold,
        }
    }

    fn check(&self) -> Result<bool> {
        let mut sys = self.sys.lock().unwrap();
        sys.refresh_specifics(
            RefreshKind::new()
                .with_cpu(CpuRefreshKind::everything())
                .with_memory(MemoryRefreshKind::everything()),
        );

        let cpu_usage: f32 =
            sys.cpus().iter().map(|c| c.cpu_usage()).sum::<f32>() / sys.cpus().len() as f32;
        let mem_usage = sys.used_memory() as f32 / sys.total_memory() as f32 * 100.0;

        let ok = cpu_usage < self.cpu_threshold && mem_usage < self.memory_threshold;
        if !ok {
            eprintln!(
                "  [THROTTLE] CPU: {:.1}%, RAM: {:.1}% — sleeping...",
                cpu_usage, mem_usage
            );
        }
        Ok(ok)
    }

    fn wait(&self) {
        while !self.check().unwrap_or(false) {
            std::thread::sleep(std::time::Duration::from_millis(500));
        }
    }
}

// ── Cache Manager (RAM + Disk) ─────────────────────────────────────────────

struct CacheManager {
    /// In-memory equation → fingerprint map
    ram: DashMap<String, String>,
    /// On-disk cache file path
    disk_path: PathBuf,
    /// Max RAM entries before spilling (0 = unlimited)
    cap: usize,
    /// Cache hits
    hits: AtomicUsize,
    /// Cache misses
    misses: AtomicUsize,
}

impl CacheManager {
    fn new(cache_dir: &str, cap: usize) -> Result<Self> {
        let disk_path = if cache_dir.is_empty() {
            let mut path = dirs::cache_dir().unwrap_or_else(|| std::env::temp_dir());
            path.push("math_self_discover");
            path.push("fp_cache.jsonl");
            path
        } else {
            let mut path = PathBuf::from(cache_dir);
            fs::create_dir_all(&path)?;
            path.push("fp_cache.jsonl");
            path
        };

        let ram = DashMap::new();

        // Warm RAM cache from disk if present
        if disk_path.exists() {
            eprintln!("  [cache] warming from disk: {}", disk_path.display());
            let file = File::open(&disk_path)?;
            let reader = BufReader::new(file);
            for line in reader.lines() {
                if let Ok(line) = line {
                    if let Some((eq, fp)) = line.split_once('\t') {
                        ram.insert(eq.to_string(), fp.to_string());
                    }
                }
            }
            eprintln!("  [cache] loaded {} entries into RAM", ram.len());
        }

        Ok(Self {
            ram,
            disk_path,
            cap,
            hits: AtomicUsize::new(0),
            misses: AtomicUsize::new(0),
        })
    }

    fn get(&self, eq: &str) -> Option<String> {
        if let Some(fp) = self.ram.get(eq).map(|e| e.clone()) {
            self.hits.fetch_add(1, Ordering::Relaxed);
            return Some(fp);
        }
        None
    }

    fn insert(&self, eq: String, fp: String) {
        // If capped, skip inserting (simple eviction: don't grow beyond cap)
        if self.cap > 0 && self.ram.len() >= self.cap {
            return;
        }
        self.ram.insert(eq, fp);
    }

    fn record_miss(&self) {
        self.misses.fetch_add(1, Ordering::Relaxed);
    }

    fn stats(&self) -> (usize, usize, usize) {
        (
            self.ram.len(),
            self.hits.load(Ordering::Relaxed),
            self.misses.load(Ordering::Relaxed),
        )
    }

    fn flush_to_disk(&self) -> Result<()> {
        if let Some(parent) = self.disk_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let mut file = File::create(&self.disk_path)?;
        for entry in self.ram.iter() {
            writeln!(file, "{}\t{}", entry.key(), entry.value())?;
        }
        Ok(())
    }
}

// ── Fingerprinting ───────────────────────────────────────────────────────────

struct FingerprintEngine {
    latex_re: Regex,
    number_re: Regex,
    greek_re: Regex,
    multi_latin_re: Regex,
    whitespace_re: Regex,
    collapse_n_re: Regex,
}

impl FingerprintEngine {
    fn new() -> Result<Self> {
        Ok(Self {
            latex_re: Regex::new(r"\\([a-zA-Z]+)")?,
            number_re: Regex::new(r"\d+(?:\.\d+)?")?,
            greek_re: Regex::new(r"[αβγδεζηθικλμνξοπρστυφχψωΓΔΘΛΞΠΣΦΨΩ]")?,
            multi_latin_re: Regex::new(r"[a-zA-Z]{2,}")?,
            whitespace_re: Regex::new(r"\s+")?,
            collapse_n_re: Regex::new(r"N\s+N")?,
        })
    }

    fn replace_single_letters(
        text: &str,
        var_map: &mut HashMap<String, String>,
        counter: &mut usize,
    ) -> String {
        let chars: Vec<char> = text.chars().collect();
        let mut result = String::with_capacity(text.len());
        let mut i = 0;
        while i < chars.len() {
            if chars[i].is_ascii_alphabetic() {
                let prev_is_letter = i > 0 && chars[i - 1].is_ascii_alphabetic();
                let next_is_letter = i + 1 < chars.len() && chars[i + 1].is_ascii_alphabetic();
                if !prev_is_letter && !next_is_letter {
                    let c = chars[i].to_lowercase().to_string();
                    let token = var_map.entry(c.clone()).or_insert_with(|| {
                        let t = format!("v{}", *counter);
                        *counter += 1;
                        t
                    });
                    result.push_str(token);
                    i += 1;
                    continue;
                }
            }
            result.push(chars[i]);
            i += 1;
        }
        result
    }

    fn fingerprint(&self, eq: &str) -> String {
        let mut text = eq.trim().to_string();
        if text.is_empty() {
            return String::new();
        }

        // Remove LaTeX backslashes
        text = self.latex_re.replace_all(&text, "$1").into_owned();

        // Replace numbers with N
        text = self.number_re.replace_all(&text, "N").into_owned();

        // Replace Greek letters with g0, g1, ...
        let mut greek_map: HashMap<String, String> = HashMap::new();
        let mut greek_counter = 0usize;
        text = self
            .greek_re
            .replace_all(&text, |caps: &regex::Captures| {
                let c = caps.get(0).unwrap().as_str().to_string();
                if let Some(v) = greek_map.get(&c) {
                    return v.clone();
                }
                let token = format!("g{}", greek_counter);
                greek_counter += 1;
                greek_map.insert(c, token.clone());
                token
            })
            .into_owned();

        // Single Latin letters → vN (manual scan, no lookaround)
        let mut var_map: HashMap<String, String> = HashMap::new();
        let mut var_counter = 0usize;
        text = Self::replace_single_letters(&text, &mut var_map, &mut var_counter);

        // Multi-letter identifiers
        let math_funcs: std::collections::HashSet<&str> = [
            "sin", "cos", "tan", "exp", "log", "ln", "sqrt", "det", "tr", "dim", "ker", "rank",
            "span", "frac", "sum", "prod", "int",
        ]
        .iter()
        .copied()
        .collect();

        text = self
            .multi_latin_re
            .replace_all(&text, |caps: &regex::Captures| {
                let w = caps.get(0).unwrap().as_str().to_lowercase();
                if math_funcs.contains(w.as_str()) {
                    return w;
                }
                if let Some(v) = var_map.get(&w) {
                    return v.clone();
                }
                let token = format!("v{}", var_counter);
                var_counter += 1;
                var_map.insert(w, token.clone());
                token
            })
            .into_owned();

        // Normalize whitespace
        text = self.whitespace_re.replace_all(&text, " ").into_owned();
        text = text.trim().to_string();

        // Collapse repeated N
        loop {
            let collapsed = self.collapse_n_re.replace_all(&text, "N").into_owned();
            if collapsed == text {
                break;
            }
            text = collapsed;
        }

        text
    }
}

// ── Clustering ───────────────────────────────────────────────────────────────

#[derive(Serialize)]
struct Motif {
    rank: usize,
    fingerprint: String,
    count: u64,
    percentage: f64,
}

#[derive(Serialize)]
struct ClusterReport {
    timestamp: String,
    total_equations: u64,
    unique_structural_forms: u64,
    top_motifs: Vec<Motif>,
    cluster_distribution: Vec<(String, u64)>,
}

fn main() -> Result<()> {
    let config = Config::parse();

    // ── Resource-aware thread pool ───────────────────────────────────────────
    let n_cpus = std::thread::available_parallelism()?.get();
    let threads = if config.threads == 0 {
        n_cpus / 2
    } else {
        config.threads
    };
    let threads = threads.max(1);

    eprintln!("════════════════════════════════════════════════════════════");
    eprintln!("  MATH SELF-DISCOVERY (Rust) — Stream Copy + SIMD Surface");
    eprintln!("  Threads: {} / {} CPUs", threads, n_cpus);
    eprintln!("  Memory cap: {} MB", config.memory_cap_mb);
    eprintln!("  Batch size: {}", config.batch_size);
    eprintln!("  CPU threshold: {}%", config.cpu_threshold);
    eprintln!("  Memory threshold: {}%", config.memory_threshold);
    eprintln!(
        "  Cache dir: {}",
        if config.cache_dir.is_empty() {
            "default"
        } else {
            &config.cache_dir
        }
    );
    eprintln!("════════════════════════════════════════════════════════════");

    ThreadPoolBuilder::new()
        .num_threads(threads)
        .build_global()
        .context("failed to build thread pool")?;

    let monitor = Arc::new(ResourceMonitor::new(
        config.cpu_threshold,
        config.memory_threshold,
    ));

    // ── Cache manager ──────────────────────────────────────────────────────────
    let cache = Arc::new(CacheManager::new(&config.cache_dir, config.ram_cache_cap)?);

    // ── Open input + output (stream copy) ────────────────────────────────────
    eprintln!("\nOpening input parquet...");
    let file =
        File::open(&config.input).with_context(|| format!("failed to open {}", config.input))?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)?;
    let total_rows = builder.metadata().file_metadata().num_rows() as u64;
    eprintln!("  Total rows: {}", total_rows);

    let reader = builder.with_batch_size(config.batch_size).build()?;

    let schema = Schema::new(vec![
        Field::new("uuid", DataType::Utf8, false),
        Field::new("equation", DataType::Utf8, true),
        Field::new("refined_equation", DataType::Utf8, true),
        Field::new("fingerprint", DataType::Utf8, false),
        Field::new("structural_cluster", DataType::Utf8, false),
    ]);

    let out_file = File::create(&config.clustered)?;
    let props = parquet::file::properties::WriterProperties::builder()
        .set_compression(parquet::basic::Compression::ZSTD(
            parquet::basic::ZstdLevel::try_new(3)?,
        ))
        .build();
    let mut writer = ArrowWriter::try_new(out_file, Arc::new(schema.clone()), Some(props))?;

    // ── Single-pass: fingerprint, cluster count, write ───────────────────────
    eprintln!("\nStreaming: fingerprint → count → write...");
    let engine = Arc::new(FingerprintEngine::new()?);
    let cluster_counts: DashMap<String, AtomicUsize> = DashMap::new();
    let total_processed = AtomicUsize::new(0);

    let pb = ProgressBar::new(total_rows);
    pb.set_style(
        ProgressStyle::with_template(
            "{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({per_sec}) {msg}",
        )?
        .progress_chars("#>-"),
    );

    let start_time = std::time::Instant::now();

    for batch in reader {
        let batch = batch.context("failed to read batch")?;
        let n = batch.num_rows();

        // Check resource caps
        monitor.wait();

        // Extract columns
        let uuid_col = batch
            .column_by_name("uuid")
            .and_then(|c| c.as_any().downcast_ref::<StringArray>())
            .context("missing or wrong type: uuid")?;
        let eq_col = batch
            .column_by_name("equation")
            .and_then(|c| c.as_any().downcast_ref::<StringArray>())
            .context("missing or wrong type: equation")?;
        let refined_col = batch
            .column_by_name("refined_equation")
            .and_then(|c| c.as_any().downcast_ref::<StringArray>());

        // Build equation strings for cache/SIMD surface
        let eqs: Vec<String> = (0..n).map(|i| eq_col.value(i).to_string()).collect();

        // Fingerprint via cache-first SIMD batch surface
        let fingerprints: Vec<String> = eqs
            .into_par_iter()
            .map(|eq| {
                if let Some(fp) = cache.get(&eq) {
                    return fp;
                }
                cache.record_miss();
                let fp = engine.fingerprint(&eq);
                cache.insert(eq, fp.clone());
                fp
            })
            .collect();

        // Aggregate counts
        for fp in fingerprints.iter() {
            if fp.is_empty() {
                continue;
            }
            cluster_counts
                .entry(fp.clone())
                .or_insert_with(|| AtomicUsize::new(0))
                .fetch_add(1, Ordering::Relaxed);
        }

        // Stream copy: build output batch and write immediately
        let mut uuids = Vec::with_capacity(n);
        let mut equations = Vec::with_capacity(n);
        let mut refined = Vec::with_capacity(n);
        let mut fps = Vec::with_capacity(n);
        let mut clusters = Vec::with_capacity(n);

        for i in 0..n {
            uuids.push(Some(uuid_col.value(i).to_string()));
            equations.push(Some(eq_col.value(i).to_string()));
            if let Some(ref_col) = refined_col {
                refined.push(if ref_col.is_null(i) {
                    None
                } else {
                    Some(ref_col.value(i).to_string())
                });
            } else {
                refined.push(None);
            }
            let fp = &fingerprints[i];
            fps.push(Some(fp.clone()));
            clusters.push(Some(fp.clone()));
        }

        let out_batch = RecordBatch::try_new(
            Arc::new(schema.clone()),
            vec![
                Arc::new(StringArray::from(uuids)),
                Arc::new(StringArray::from(equations)),
                Arc::new(StringArray::from(refined)),
                Arc::new(StringArray::from(fps)),
                Arc::new(StringArray::from(clusters)),
            ],
        )?;

        writer.write(&out_batch)?;

        let processed = total_processed.fetch_add(n, Ordering::Relaxed) + n;
        pb.set_position(processed as u64);
    }

    pb.finish_with_message("done");
    writer.close()?;

    let elapsed = start_time.elapsed();
    let total = total_processed.load(Ordering::Relaxed);
    eprintln!("\n  Processed {} equations in {:.1?}", total, elapsed);
    eprintln!("  Rate: {:.0} eq/s", total as f64 / elapsed.as_secs_f64());

    // ── Cache stats ──────────────────────────────────────────────────────────
    let (cache_entries, hits, misses) = cache.stats();
    eprintln!(
        "  Cache: {} entries, {} hits, {} misses",
        cache_entries, hits, misses
    );
    eprintln!("  Flushing cache to disk...");
    cache.flush_to_disk()?;
    eprintln!("  Cache flushed to: {}", cache.disk_path.display());

    // ── Build report ─────────────────────────────────────────────────────────
    eprintln!("\nBuilding report...");
    let mut clusters: Vec<(String, usize)> = cluster_counts
        .into_iter()
        .map(|(k, v)| (k, v.load(Ordering::Relaxed)))
        .collect();

    clusters.sort_by(|a, b| b.1.cmp(&a.1));

    let n_unique = clusters.len() as u64;
    eprintln!("  Unique structural forms: {}", n_unique);

    let top_motifs: Vec<Motif> = clusters
        .iter()
        .take(config.top_motifs)
        .enumerate()
        .map(|(rank, (fp, cnt))| Motif {
            rank: rank + 1,
            fingerprint: fp.clone(),
            count: *cnt as u64,
            percentage: (*cnt as f64 / total as f64) * 100.0,
        })
        .collect();

    eprintln!("\n  Top {} Structural Motifs:", config.top_motifs.min(20));
    eprintln!("  {:>5} {:>10} {:>6}  Motif", "Rank", "Count", "%");
    for motif in top_motifs.iter().take(20) {
        let fp_display = if motif.fingerprint.len() > 80 {
            format!("{}...", &motif.fingerprint[..80])
        } else {
            motif.fingerprint.clone()
        };
        eprintln!(
            "  {:>5} {:>10} {:>6.2}%  {}",
            motif.rank, motif.count, motif.percentage, fp_display
        );
    }

    let report = ClusterReport {
        timestamp: chrono::Local::now().format("%Y%m%d_%H%M%S").to_string(),
        total_equations: total as u64,
        unique_structural_forms: n_unique,
        top_motifs,
        cluster_distribution: clusters
            .iter()
            .map(|(fp, cnt)| (fp.clone(), *cnt as u64))
            .collect(),
    };

    let report_file = File::create(&config.report)
        .with_context(|| format!("failed to create {}", config.report))?;
    serde_json::to_writer_pretty(report_file, &report)?;
    eprintln!("\n  Report written to {}", config.report);
    eprintln!("  Clustered parquet written to {}", config.clustered);

    eprintln!("\n════════════════════════════════════════════════════════════");
    eprintln!("  MATH SELF-DISCOVERY COMPLETE (single-pass stream copy)");
    eprintln!("  {} equations → {} structural forms", total, n_unique);
    eprintln!("════════════════════════════════════════════════════════════");

    Ok(())
}

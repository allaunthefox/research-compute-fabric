//! Context compression gate for tool outputs.
//!
//! Before a tool result enters the conversation (and burns context tokens),
//! this module checks whether the output can be compressed through the local
//! substrate cache / hyperlut / soliton surfaces.
//!
//! Design principle: be offensively boring.  Prefer local compute over
//! external context tokens in every case.
//!
//! Integration: called from `conversation.rs` after tool execution and before
//! the output is wrapped in a `ConversationMessage::tool_result`.

use std::collections::HashMap;
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

/// Minimum output size (bytes) before compression is attempted.
/// Small outputs aren't worth the subprocess overhead.
const COMPRESS_THRESHOLD_BYTES: usize = 2_048;

/// In-process LRU cache so repeated identical outputs never hit Python.
const MEMORY_CACHE_CAPACITY: usize = 256;

/// Tools whose output should never be compressed (they need raw content).
const EXEMPT_TOOLS: &[&str] = &[
    "Edit",
    "Write",
    "TodoWrite",
    "NotebookEdit",
];

#[derive(Debug, Clone)]
pub struct CompressedOutput {
    pub text: String,
    pub cache_hit: bool,
    pub compression_ratio: f64,
    pub warden_ref: Option<String>,
}

#[derive(Debug)]
struct CacheEntry {
    compressed: String,
    warden_ref: Option<String>,
    ratio: f64,
    created_at: u64,
}

/// In-memory + Python-backed context compressor.
pub struct ContextCompressor {
    /// Path to cc_context_compress.py
    script_path: PathBuf,
    /// Python interpreter
    python: String,
    /// In-memory cache keyed by FNV hash of raw output
    cache: Mutex<HashMap<u64, CacheEntry>>,
    /// Whether the Python compressor is available
    available: bool,
}

impl ContextCompressor {
    /// Create a new compressor, probing for the Python script.
    #[must_use]
    pub fn new() -> Self {
        let script_path = Self::find_script();
        let available = script_path
            .as_ref()
            .map_or(false, |p| p.exists());
        Self {
            script_path: script_path.unwrap_or_default(),
            python: Self::find_python(),
            cache: Mutex::new(HashMap::new()),
            available,
        }
    }

    /// Compress a tool output if it's worth compressing.
    ///
    /// Returns `None` if the output should pass through unchanged.
    pub fn maybe_compress(
        &self,
        tool_name: &str,
        output: &str,
    ) -> Option<CompressedOutput> {
        // Skip small outputs and exempt tools
        if output.len() < COMPRESS_THRESHOLD_BYTES {
            return None;
        }
        if EXEMPT_TOOLS.iter().any(|t| tool_name == *t) {
            return None;
        }
        if !self.available {
            return None;
        }

        let hash = fnv_hash(output.as_bytes());

        // Check in-memory cache first
        if let Ok(cache) = self.cache.lock() {
            if let Some(entry) = cache.get(&hash) {
                return Some(CompressedOutput {
                    text: entry.compressed.clone(),
                    cache_hit: true,
                    compression_ratio: entry.ratio,
                    warden_ref: entry.warden_ref.clone(),
                });
            }
        }

        // Shell out to Python compressor
        let result = self.run_python_compress(output)?;

        // Cache the result
        if let Ok(mut cache) = self.cache.lock() {
            // Evict oldest if at capacity
            if cache.len() >= MEMORY_CACHE_CAPACITY {
                if let Some(oldest_key) = cache
                    .iter()
                    .min_by_key(|(_, v)| v.created_at)
                    .map(|(k, _)| *k)
                {
                    cache.remove(&oldest_key);
                }
            }
            cache.insert(hash, CacheEntry {
                compressed: result.text.clone(),
                warden_ref: result.warden_ref.clone(),
                ratio: result.compression_ratio,
                created_at: now_unix_secs(),
            });
        }

        Some(result)
    }

    fn run_python_compress(&self, output: &str) -> Option<CompressedOutput> {
        let mut child = Command::new(&self.python)
            .arg(&self.script_path)
            .arg("stdin")
            .arg("--mode")
            .arg("compress")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .ok()?;

        if let Some(mut stdin) = child.stdin.take() {
            let _ = stdin.write_all(output.as_bytes());
        }

        let out = child
            .wait_with_output()
            .ok()
            .filter(|o| o.status.success())?;

        let compressed = String::from_utf8_lossy(&out.stdout).trim().to_string();
        if compressed.is_empty() || compressed.len() >= output.len() {
            return None; // compression didn't help
        }

        let ratio = output.len() as f64 / compressed.len().max(1) as f64;
        let warden_ref = if compressed.starts_with("omni://") {
            Some(compressed.clone())
        } else {
            None
        };

        Some(CompressedOutput {
            text: compressed,
            cache_hit: false,
            compression_ratio: ratio,
            warden_ref,
        })
    }

    fn find_script() -> Option<PathBuf> {
        // Check common locations
        let candidates = [
            // Relative to home
            dirs::home_dir().map(|h| {
                h.join("Research Stack")
                    .join("scripts")
                    .join("cc_context_compress.py")
            }),
            // Via env var
            std::env::var("CONTEXT_GATE_SCRIPT")
                .ok()
                .map(PathBuf::from),
        ];

        candidates.into_iter().flatten().find(|p| p.exists())
    }

    fn find_python() -> String {
        for candidate in &["python3", "python"] {
            if Command::new(candidate)
                .arg("--version")
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status()
                .map_or(false, |s| s.success())
            {
                return (*candidate).to_string();
            }
        }
        "python3".to_string()
    }
}

impl Default for ContextCompressor {
    fn default() -> Self {
        Self::new()
    }
}

const FNV_OFFSET_BASIS: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

fn fnv_hash(bytes: &[u8]) -> u64 {
    let mut hash = FNV_OFFSET_BASIS;
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

fn now_unix_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0, |d| d.as_secs())
}

/// Helper for `dirs::home_dir()` fallback when the `dirs` crate isn't available.
mod dirs {
    use std::path::PathBuf;

    pub fn home_dir() -> Option<PathBuf> {
        std::env::var_os("HOME").map(PathBuf::from)
    }
}

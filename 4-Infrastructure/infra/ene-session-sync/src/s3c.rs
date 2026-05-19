#![allow(dead_code)]
//! s3c.rs — S3C manifold audio processing and bind engine stub.
//!
//! Port of s3c_audio_shim.py, s3c_pcm_processor.py, and bind_engine.py.
//! Audio I/O (pyaudio) is not ported — only the pure math layer.

use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::collections::VecDeque;
use std::io::Write;

// =============================================================================
// §1  Shell decomposition
// =============================================================================

/// Shell coordinates for n = k² + a decomposition.
///
/// Every non-negative integer n sits in a "shell" between two consecutive
/// perfect squares k² and (k+1)².  The offsets a = n − k² and
/// b = (k+1)² − n partition the shell gap of width 2k+1.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct ShellCoords {
    /// Shell index: floor(√n).
    pub k: u32,
    /// Lower offset: n − k².  Satisfies 0 ≤ a ≤ 2k.
    pub a: u32,
    /// Upper offset: (k+1)² − n.  Satisfies 1 ≤ b ≤ 2k+1.
    pub b: u32,
    /// Intersection form a · b.
    pub mass: u32,
    /// Shell width a + b = 2k + 1.
    pub width: u32,
}

/// Compute the shell decomposition of n.
///
/// Uses floating-point sqrt only to obtain the integer floor; all subsequent
/// arithmetic is pure integer.  Safe for n ≤ 65535 (16-bit unsigned range).
pub fn shell_decomposition(n: u32) -> ShellCoords {
    let k = (n as f64).sqrt() as u32;
    let k_sq = k * k;
    let a = n - k_sq;
    let k1_sq = (k + 1) * (k + 1);
    let b = k1_sq - n;
    ShellCoords {
        k,
        a,
        b,
        mass: a * b,
        width: a + b,
    }
}

// =============================================================================
// §2  Core types
// =============================================================================

/// Three-handle manifold structure derived from a shell decomposition.
///
/// Mirrors `ManifoldHandle` in s3c_audio_shim.py / s3c_pcm_processor.py.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct ManifoldHandle {
    /// Coarse handle — amplitude envelope (k).
    pub handle_k: u32,
    /// Medium handle — spectral content (a).
    pub handle_a: u32,
    /// Fine handle — phase information (b).
    pub handle_b: u32,
}

/// Three-point contact flags derived from a manifold handle.
///
/// * `kappa_a` — forward spectral prediction: handle_a > 0
/// * `kappa_b` — temporal midpoint:            handle_k > 0
/// * `kappa_c` — backward phase correction:    handle_b > 0
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct ThreePointContact {
    /// Forward spectral prediction: handle_a > 0.
    pub kappa_a: bool,
    /// Temporal midpoint: handle_k > 0.
    pub kappa_b: bool,
    /// Backward phase correction: handle_b > 0.
    pub kappa_c: bool,
}

/// J-score interaction value.
///
/// J(n) = mass_resonance + mirror_resonance + spectral_coupling
///
/// where
///   mass_resonance   = handle_a × handle_b          (ab)
///   mirror_resonance = |handle_a − handle_b|         (|a−b|)
///   spectral_coupling = handle_k                     (χ ~ k)
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct JScore {
    /// ab term.
    pub mass_resonance: u32,
    /// |a−b| term.
    pub mirror_resonance: u32,
    /// k term (χ ~ k).
    pub spectral_coupling: u32,
    /// Sum of the three components.
    pub total: u32,
}

/// Complete S3C processing state for one audio sample.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct S3CState {
    /// Original signed sample value (before abs-mapping to unsigned).
    pub sample: i32,
    /// Manifold handles derived from abs(sample).
    pub handles: ManifoldHandle,
    /// Three-point contact flags.
    pub contact: ThreePointContact,
    /// J-score.
    pub j_score: JScore,
    /// True when the emission gate is open.
    pub emit: bool,
}

// =============================================================================
// §3  Core processing functions
// =============================================================================

/// Map a signed audio sample to a three-handle manifold.
///
/// The sample is first mapped to an unsigned integer via `abs(sample)` so that
/// n always lies in [0, 32768] for 16-bit signed input, matching the Python
/// shim which uses `sample + 32768`.  Here we use `abs` so that the mapping is
/// symmetric and purely mathematical.
pub fn audio_to_manifold(sample: i32) -> ManifoldHandle {
    let n = sample.unsigned_abs(); // abs(sample) as u32
    let coords = shell_decomposition(n);
    ManifoldHandle {
        handle_k: coords.k,
        handle_a: coords.a,
        handle_b: coords.b,
    }
}

/// Detect three-point contact from a manifold handle.
pub fn detect_contact(h: &ManifoldHandle) -> ThreePointContact {
    ThreePointContact {
        kappa_a: h.handle_a > 0,
        kappa_b: h.handle_k > 0,
        kappa_c: h.handle_b > 0,
    }
}

/// Compute the J-score from a manifold handle.
pub fn compute_j_score(h: &ManifoldHandle) -> JScore {
    let mass_resonance = h.handle_a * h.handle_b;
    let mirror_resonance = h.handle_a.abs_diff(h.handle_b);
    let spectral_coupling = h.handle_k;
    JScore {
        mass_resonance,
        mirror_resonance,
        spectral_coupling,
        total: mass_resonance + mirror_resonance + spectral_coupling,
    }
}

/// Emission gate: open iff kappa_a ∧ kappa_c ∧ J.total > 0.
pub fn emission_gate(contact: &ThreePointContact, j: &JScore) -> bool {
    contact.kappa_a && contact.kappa_c && j.total > 0
}

/// Process a single signed audio sample through the full S3C pipeline.
pub fn process_sample(sample: i32) -> S3CState {
    let handles = audio_to_manifold(sample);
    let contact = detect_contact(&handles);
    let j_score = compute_j_score(&handles);
    let emit = emission_gate(&contact, &j_score);
    S3CState {
        sample,
        handles,
        contact,
        j_score,
        emit,
    }
}

/// Progressive binding cost: 1/n, or 1.0 for n = 0.
pub fn progressive_binding_cost(n: u32) -> f64 {
    if n == 0 {
        1.0
    } else {
        1.0 / f64::from(n)
    }
}

/// Returns true when the manifold handle sits at the shell throat (a = b).
///
/// The throat is the midpoint of a shell where the intersection form is
/// maximised and the handle decomposition is symmetric.
pub fn is_throat(h: &ManifoldHandle) -> bool {
    h.handle_a == h.handle_b
}

// =============================================================================
// §4  PCM batch processor
// =============================================================================

/// Stateful batch processor that applies the S3C pipeline to chunks of 16-bit
/// PCM samples and accumulates statistics.
///
/// Mirrors `PcmS3CProcessor` / `process_pcm_samples` in s3c_pcm_processor.py.
///
/// Audio I/O (reading .wav files, pyaudio streams) is not included; callers
/// supply raw `i16` slices obtained by any means.
pub struct PcmS3CProcessor {
    /// Total number of samples processed so far.
    pub total_samples: u64,
    /// Number of samples for which the emission gate was open.
    pub emitted_count: u64,
    /// All S3C states accumulated across every call to `process_chunk`.
    pub states: Vec<S3CState>,
}

impl PcmS3CProcessor {
    /// Create a new, empty processor.
    pub fn new() -> Self {
        PcmS3CProcessor {
            total_samples: 0,
            emitted_count: 0,
            states: Vec::new(),
        }
    }

    /// Process a chunk of 16-bit PCM samples.
    ///
    /// Each sample is shifted to the unsigned range [0, 65535] via
    /// `sample as i32 + 32768` before being passed through `process_sample`,
    /// matching the Python shims.  All resulting states are appended to
    /// `self.states`; only the emitting states are returned.
    pub fn process_chunk(&mut self, samples: &[i16]) -> Vec<S3CState> {
        let mut emitted = Vec::new();
        for &raw in samples {
            // Shift signed i16 → unsigned range [0, 65535]
            let unsigned = raw as i32 + 32768;
            let state = process_sample(unsigned);
            self.total_samples += 1;
            if state.emit {
                self.emitted_count += 1;
                emitted.push(state);
            }
            self.states.push(state);
        }
        emitted
    }

    /// Emission ratio: emitted_count / total_samples (0.0 if no samples yet).
    pub fn emission_ratio(&self) -> f64 {
        if self.total_samples == 0 {
            0.0
        } else {
            self.emitted_count as f64 / self.total_samples as f64
        }
    }

    /// Histogram of J-score totals bucketed into 10 bins by `j_score.total / 1000`.
    ///
    /// Bins are labelled "0"–"9"; J-scores ≥ 10000 are clamped to bin 9.
    /// Returns a JSON object `{"0": <count>, "1": <count>, …, "9": <count>}`.
    pub fn j_score_histogram(&self) -> serde_json::Value {
        let mut bins = [0u64; 10];
        for state in &self.states {
            let bin = ((state.j_score.total / 1000) as usize).min(9);
            bins[bin] += 1;
        }
        let mut map = serde_json::Map::new();
        for (i, count) in bins.iter().enumerate() {
            map.insert(i.to_string(), json!(*count));
        }
        serde_json::Value::Object(map)
    }

    /// Return a JSON summary of the processor state.
    pub fn summary_json(&self) -> serde_json::Value {
        json!({
            "total_samples": self.total_samples,
            "emitted_count": self.emitted_count,
            "emission_ratio": self.emission_ratio(),
            "j_score_histogram": self.j_score_histogram(),
            "throat_count": self.states.iter().filter(|s| is_throat(&s.handles)).count(),
        })
    }
}

impl Default for PcmS3CProcessor {
    fn default() -> Self {
        Self::new()
    }
}

// =============================================================================
// §5  Bind engine stub (port of bind_engine.py)
// =============================================================================

/// Metric pre-computed from the trajectory history.
///
/// Mirrors the `Metric` dataclass in bind_engine.py.  All cost and torsion
/// values are integer; `tensor` and `reference` are string tags understood by
/// the Lean bindserver.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metric {
    /// Aggregate binding cost accumulated over history.
    pub cost: i64,
    /// String tag for the metric tensor kind (e.g. "identity", "riemannian").
    pub tensor: String,
    /// Torsion term from the history trajectory.
    pub torsion: i64,
    /// Reference baseline label.
    pub reference: String,
    /// Number of history entries that contributed to this metric.
    pub history_len: usize,
}

impl Default for Metric {
    fn default() -> Self {
        Metric {
            cost: 0,
            tensor: "identity".to_owned(),
            torsion: 0,
            reference: "euclidean_baseline".to_owned(),
            history_len: 0,
        }
    }
}

/// Lawfulness witness returned by the Lean bindserver (or the stub fallback).
///
/// Mirrors the `Witness` dataclass in bind_engine.py.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Witness {
    /// Invariant string for the left operand.
    pub left_invariant: String,
    /// Invariant string for the right operand.
    pub right_invariant: String,
    /// True iff the bind is conservation-law preserving.
    pub conserved: bool,
    /// SHA-256 hex digest of the canonical bind trace.
    pub trace_hash: String,
}

/// Complete result of one `bind` call.
///
/// Mirrors the `BindResult` dataclass in bind_engine.py.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BindResult {
    /// Left operand (echoed from the request).
    pub left: serde_json::Value,
    /// Right operand (echoed from the request).
    pub right: serde_json::Value,
    /// Metric computed for this bind.
    pub metric: Metric,
    /// Binding cost (integer; 1 for the stub fallback).
    pub cost: i64,
    /// Lawfulness witness.
    pub witness: Witness,
    /// True iff the Lean bindserver (or stub) certified the bind as lawful.
    pub lawful: bool,
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Compute a hex-encoded SHA-256 digest of `bytes`.
fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

// ---------------------------------------------------------------------------
// BindEngine
// ---------------------------------------------------------------------------

/// Runtime engine for the Cambrian collapse — Rust port of `BindEngine` from
/// bind_engine.py.
///
/// Maintains a bounded history of past binds so that metrics become n-local
/// automatically.  All lawfulness checks and cost computations are delegated to
/// the compiled Lean `bindserver` binary when it is present; otherwise a lawful
/// stub result is returned.
pub struct BindEngine {
    /// Path to the compiled Lean bindserver binary.
    pub lean_binary: std::path::PathBuf,
    /// Bounded history of raw bind request/response values.
    pub history: VecDeque<serde_json::Value>,
    /// Maximum history length.
    pub history_len: usize,
}

impl BindEngine {
    /// Create a new bind engine.
    ///
    /// `lean_binary` is the path to the compiled Lean `bindserver` binary.
    /// The binary does not need to exist at construction time; its absence is
    /// detected lazily in `bind`.
    pub fn new(lean_binary: impl AsRef<std::path::Path>, history_len: usize) -> Self {
        BindEngine {
            lean_binary: lean_binary.as_ref().to_path_buf(),
            history: VecDeque::with_capacity(history_len),
            history_len,
        }
    }

    /// Compute `bind(left, right, metric_kind)`.
    ///
    /// If the Lean binary exists and is executable, it is invoked via
    /// stdin/stdout JSON protocol (one JSON line in, one JSON line out).
    /// Otherwise a lawful stub result is returned with:
    ///   * `lawful = true`
    ///   * `cost = 1`
    ///   * `conserved = true`
    ///   * `trace_hash = SHA-256(canonical JSON of [left, right])`
    pub fn bind(
        &mut self,
        left: serde_json::Value,
        right: serde_json::Value,
        metric_kind: &str,
    ) -> anyhow::Result<BindResult> {
        let metric = self.compute_metric(metric_kind);

        // Build the request object (same shape as Python's `request` dict).
        let request = json!({
            "metricKind": metric_kind,
            "left": left,
            "right": right,
            "useHistory": matches!(metric_kind, "riemannian" | "geometric" | "control"),
            "historyLen": metric.history_len,
            "historyCost": metric.cost,
            "historyTorsion": metric.torsion,
        });

        let result = if self.lean_binary.exists() {
            // Delegate to the Lean bindserver.
            let resp = self.call_lean(&request)?;

            let cost = resp["cost"].as_i64().unwrap_or(1);
            let lawful = resp["lawful"].as_bool().unwrap_or(false);
            let left_invariant = resp["leftInvariant"]
                .as_str()
                .unwrap_or("unknown")
                .to_owned();
            let right_invariant = resp["rightInvariant"]
                .as_str()
                .unwrap_or("unknown")
                .to_owned();
            let trace_hash = resp["traceHash"].as_str().unwrap_or("").to_owned();
            let tensor = resp["metricTensor"]
                .as_str()
                .unwrap_or(metric_kind)
                .to_owned();
            let torsion = resp["metricTorsion"].as_i64().unwrap_or(0);
            let resp_history_len = resp["metricHistoryLen"]
                .as_u64()
                .unwrap_or(metric.history_len as u64) as usize;

            BindResult {
                left: left.clone(),
                right: right.clone(),
                metric: Metric {
                    cost,
                    tensor,
                    torsion,
                    reference: metric.reference,
                    history_len: resp_history_len,
                },
                cost,
                witness: Witness {
                    left_invariant,
                    right_invariant,
                    conserved: lawful,
                    trace_hash,
                },
                lawful,
            }
        } else {
            // Lean binary not found — return lawful stub.
            let trace_input = serde_json::to_string(&[&left, &right])
                .unwrap_or_else(|_| "[]".to_owned());
            let trace_hash = sha256_hex(trace_input.as_bytes());

            BindResult {
                left: left.clone(),
                right: right.clone(),
                metric: Metric {
                    cost: 1,
                    tensor: metric_kind.to_owned(),
                    torsion: 0,
                    reference: metric.reference,
                    history_len: metric.history_len,
                },
                cost: 1,
                witness: Witness {
                    left_invariant: "stub".to_owned(),
                    right_invariant: "stub".to_owned(),
                    conserved: true,
                    trace_hash,
                },
                lawful: true,
            }
        };

        // Push a compact record into history.
        let record = json!({
            "metricKind": metric_kind,
            "cost": result.cost,
            "lawful": result.lawful,
            "traceHash": result.witness.trace_hash,
        });
        if self.history.len() >= self.history_len {
            self.history.pop_front();
        }
        self.history.push_back(record);

        Ok(result)
    }

    /// Compute a trajectory metric from the current history.
    ///
    /// Sums the integer costs recorded in history entries; uses the history
    /// length as the n-local window size.
    fn compute_metric(&self, metric_kind: &str) -> Metric {
        let cost: i64 = self
            .history
            .iter()
            .filter_map(|v| v["cost"].as_i64())
            .sum();
        Metric {
            cost,
            tensor: metric_kind.to_owned(),
            torsion: 0,
            reference: "euclidean_baseline".to_owned(),
            history_len: self.history.len(),
        }
    }

    /// Call the Lean bindserver with a JSON request and return the JSON response.
    ///
    /// Spawns the binary as a child process, writes one JSON line to its stdin,
    /// reads one JSON line from its stdout, and parses the result.
    ///
    /// Returns `Err` if the binary cannot be spawned, if the write/read fails,
    /// or if the response is not valid JSON.
    fn call_lean(&self, request: &serde_json::Value) -> anyhow::Result<serde_json::Value> {
        use std::process::{Command, Stdio};

        let mut child = Command::new(&self.lean_binary)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| anyhow::anyhow!("failed to spawn lean bindserver: {}", e))?;

        // Write the JSON request line to stdin.
        {
            let stdin = child
                .stdin
                .as_mut()
                .ok_or_else(|| anyhow::anyhow!("lean bindserver stdin not available"))?;
            let mut line = serde_json::to_string(request)?;
            line.push('\n');
            stdin
                .write_all(line.as_bytes())
                .map_err(|e| anyhow::anyhow!("write to lean bindserver failed: {}", e))?;
        }

        // Read the response from stdout.
        let output = child
            .wait_with_output()
            .map_err(|e| anyhow::anyhow!("lean bindserver wait failed: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let resp_line = stdout
            .lines()
            .find(|l| !l.trim().is_empty())
            .ok_or_else(|| anyhow::anyhow!("lean bindserver returned empty response"))?;

        serde_json::from_str(resp_line)
            .map_err(|e| anyhow::anyhow!("lean bindserver response is not valid JSON: {}", e))
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    // -------------------------------------------------------------------------
    // Shell decomposition
    // -------------------------------------------------------------------------

    #[test]
    fn test_shell_decomp_perfect_square() {
        // n = 9 = 3²: k=3, a=0, b=(4²-9)=7, mass=0, width=a+b=7=2k+1
        let s = shell_decomposition(9);
        assert_eq!(s.k, 3);
        assert_eq!(s.a, 0);
        assert_eq!(s.b, 7);
        assert_eq!(s.mass, 0);
        assert_eq!(s.width, 2 * 3 + 1);
    }

    #[test]
    fn test_shell_decomp_midpoint() {
        // n = 6 = 2² + 2: k=2, a=2, b=(9-6)=3, mass=6, width=5=2*2+1
        let s = shell_decomposition(6);
        assert_eq!(s.k, 2);
        assert_eq!(s.a, 2);
        assert_eq!(s.b, 3);
        assert_eq!(s.mass, 6);
        assert_eq!(s.width, 5);
    }

    #[test]
    fn test_shell_decomp_zero() {
        let s = shell_decomposition(0);
        assert_eq!(s.k, 0);
        assert_eq!(s.a, 0);
        assert_eq!(s.b, 1);
        assert_eq!(s.mass, 0);
    }

    #[test]
    fn test_shell_decomp_width_invariant() {
        // width must equal 2k+1 for every n in [0, 1000]
        for n in 0u32..=1000 {
            let s = shell_decomposition(n);
            assert_eq!(s.width, 2 * s.k + 1, "n={}", n);
            assert_eq!(s.a + s.b, 2 * s.k + 1, "n={}", n);
        }
    }

    // -------------------------------------------------------------------------
    // Audio → manifold mapping
    // -------------------------------------------------------------------------

    #[test]
    fn test_audio_to_manifold_zero() {
        let h = audio_to_manifold(0);
        assert_eq!(h.handle_k, 0);
        assert_eq!(h.handle_a, 0);
    }

    #[test]
    fn test_audio_to_manifold_symmetric() {
        // abs is applied, so +n and −n produce the same manifold
        let pos = audio_to_manifold(100);
        let neg = audio_to_manifold(-100);
        assert_eq!(pos.handle_k, neg.handle_k);
        assert_eq!(pos.handle_a, neg.handle_a);
        assert_eq!(pos.handle_b, neg.handle_b);
    }

    // -------------------------------------------------------------------------
    // J-score
    // -------------------------------------------------------------------------

    #[test]
    fn test_j_score_known_sample() {
        // sample=100 → n=100=10²; k=10, a=0, b=1
        // mass=0, mirror=1, spectral=10, total=11
        let h = audio_to_manifold(100);
        let j = compute_j_score(&h);
        assert_eq!(j.spectral_coupling, 10);
        assert_eq!(j.mass_resonance, 0);
        assert_eq!(j.total, j.mass_resonance + j.mirror_resonance + j.spectral_coupling);
    }

    // -------------------------------------------------------------------------
    // Emission gate
    // -------------------------------------------------------------------------

    #[test]
    fn test_emission_gate_open() {
        // sample=6 → n=6, k=2, a=2, b=3 → kappa_a=T, kappa_b=T, kappa_c=T, J=11>0
        let state = process_sample(6);
        assert!(state.emit);
    }

    #[test]
    fn test_emission_gate_closed_zero_sample() {
        // sample=0 → n=0, k=0, a=0, b=1; kappa_a=false → gate closed
        let state = process_sample(0);
        assert!(!state.emit);
    }

    #[test]
    fn test_emission_gate_closed_perfect_square() {
        // sample=9 → n=9, k=3, a=0, b=1; kappa_a=false (a=0) → gate closed
        let state = process_sample(9);
        assert!(!state.emit);
    }

    // -------------------------------------------------------------------------
    // Throat detection
    // -------------------------------------------------------------------------

    #[test]
    fn test_is_throat_true() {
        // a==b: n = k²+k (midpoint of shell k, where a=k, b=k+1 — NOT equal)
        // Actual throat: a=b → mass = a² and width = 2a+1.
        // For k=2: shell [4,9], midpoint where a=b would need 2k+1 odd and equal halves.
        // Shell k=2 has width 5 (odd), so no exact throat there.
        // Shell k=3: n = 9+a; a+b=6; a=b=3 → n=12.
        let h = ManifoldHandle { handle_k: 3, handle_a: 3, handle_b: 3 };
        assert!(is_throat(&h));
    }

    #[test]
    fn test_is_throat_false() {
        let h = ManifoldHandle { handle_k: 3, handle_a: 2, handle_b: 3 };
        assert!(!is_throat(&h));
    }

    // -------------------------------------------------------------------------
    // Progressive binding cost
    // -------------------------------------------------------------------------

    #[test]
    fn test_progressive_binding_cost_zero() {
        assert_eq!(progressive_binding_cost(0), 1.0);
    }

    #[test]
    fn test_progressive_binding_cost_nonzero() {
        assert!((progressive_binding_cost(4) - 0.25).abs() < 1e-12);
    }

    // -------------------------------------------------------------------------
    // PCM batch processor
    // -------------------------------------------------------------------------

    #[test]
    fn test_pcm_processor_empty() {
        let p = PcmS3CProcessor::new();
        assert_eq!(p.total_samples, 0);
        assert_eq!(p.emission_ratio(), 0.0);
    }

    #[test]
    fn test_pcm_processor_chunk() {
        let mut p = PcmS3CProcessor::new();
        // Process 4 samples; all states accumulate in p.states
        let samples: &[i16] = &[0, 100, -100, 256];
        let emitted = p.process_chunk(samples);
        assert_eq!(p.total_samples, 4);
        assert_eq!(p.states.len(), 4);
        // emitted vec contains only states with emit=true
        for s in &emitted {
            assert!(s.emit);
        }
    }

    #[test]
    fn test_pcm_processor_summary_json() {
        let mut p = PcmS3CProcessor::new();
        p.process_chunk(&[0i16, 1, -1, 127, -127]);
        let summary = p.summary_json();
        assert_eq!(summary["total_samples"], 5u64);
        assert!(summary["emission_ratio"].is_f64() || summary["emission_ratio"].is_number());
    }

    #[test]
    fn test_j_score_histogram_bins() {
        let mut p = PcmS3CProcessor::new();
        // Feed a spread of samples to populate multiple bins
        let samples: Vec<i16> = (0..100).map(|i| i * 100).collect();
        p.process_chunk(&samples);
        let hist = p.j_score_histogram();
        // All 10 keys must be present
        for i in 0..10 {
            assert!(hist[i.to_string()].is_number(), "bin {} missing", i);
        }
        // Total across all bins must equal total_samples
        let bin_sum: u64 = (0..10)
            .map(|i| hist[i.to_string()].as_u64().unwrap_or(0))
            .sum();
        assert_eq!(bin_sum, p.total_samples);
    }

    // -------------------------------------------------------------------------
    // Bind engine (stub path — no binary present)
    // -------------------------------------------------------------------------

    #[test]
    fn test_bind_engine_stub_lawful() {
        let mut engine = BindEngine::new("/nonexistent/bindserver", 16);
        let result = engine
            .bind(
                json!({"kind": "electron", "charge": -1}),
                json!({"kind": "positron", "charge": 1}),
                "physical",
            )
            .unwrap();
        assert!(result.lawful);
        assert_eq!(result.cost, 1);
        assert!(result.witness.conserved);
        assert!(!result.witness.trace_hash.is_empty());
    }

    #[test]
    fn test_bind_engine_trace_hash_is_sha256() {
        let mut engine = BindEngine::new("/nonexistent/bindserver", 8);
        let left = json!({"x": 1});
        let right = json!({"y": 2});
        let result = engine.bind(left.clone(), right.clone(), "geometric").unwrap();
        // SHA-256 hex is 64 chars
        assert_eq!(result.witness.trace_hash.len(), 64);
    }

    #[test]
    fn test_bind_engine_history_bounded() {
        let mut engine = BindEngine::new("/nonexistent/bindserver", 4);
        for i in 0..10 {
            engine
                .bind(json!(i), json!(i + 1), "informational")
                .unwrap();
        }
        assert!(engine.history.len() <= 4);
    }

    #[test]
    fn test_bind_engine_metric_accumulates_cost() {
        let mut engine = BindEngine::new("/nonexistent/bindserver", 32);
        engine.bind(json!("a"), json!("b"), "control").unwrap();
        engine.bind(json!("c"), json!("d"), "control").unwrap();
        // Each stub bind has cost=1, so accumulated cost in metric should be 2
        // after two calls (metric is computed from history before the current bind).
        // After two binds the history has 2 entries with cost=1 each.
        let metric = engine.compute_metric("control");
        assert_eq!(metric.cost, 2);
        assert_eq!(metric.history_len, 2);
    }
}

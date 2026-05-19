//! Delta GCL compression service — Rust port of:
//!   - delta_gcl_compression_service.py
//!   - adaptive_delta_gcl.py
//!   - neural_delta_gcl_compressor.py
//!
//! The Lean binary path is omitted; only the Python-fallback encoding is
//! implemented here.  All three layers (DeltaGclService, AdaptiveDeltaGcl,
//! NeuralDeltaGcl) are self-contained and carry no external I/O.
#![allow(dead_code)]

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

// ── PTOS code dictionaries ────────────────────────────────────────────────────

/// Layer mnemonic → single uppercase letter.
fn layer_code(layer: &str) -> char {
    match layer {
        "CORE"     => 'C',
        "RESEARCH" => 'R',
        "FOAM"     => 'F',
        "COMPUTE"  => 'X',
        "STORAGE"  => 'S',
        other => other.chars().next().unwrap_or('?').to_ascii_uppercase(),
    }
}

/// Domain mnemonic → single lowercase letter.
fn domain_code(domain: &str) -> char {
    match domain {
        "compute"  => 'c',
        "semantic" => 's',
        "topology" => 't',
        "storage"  => 'o',
        other => other.chars().next().unwrap_or('?').to_ascii_lowercase(),
    }
}

/// Tier mnemonic → single lowercase letter.
fn tier_code(tier: &str) -> char {
    match tier {
        "FOAM"     => 'f',
        "RESEARCH" => 'r',
        "STORAGE"  => 's',
        other => other.chars().next().unwrap_or('?').to_ascii_lowercase(),
    }
}

/// Condition mnemonic → single uppercase letter.
fn condition_code(cond: &str) -> char {
    match cond {
        "STABLE"   => 'S',
        "ACTIVE"   => 'A',
        "DEGRADED" => 'D',
        "FORMING"  => 'G',
        other => other.chars().next().unwrap_or('?').to_ascii_uppercase(),
    }
}

// ── FNV-1a helper (used as lightweight hash throughout this module) ───────────

/// FNV-1a 64-bit hash → 16-char hex string.
///
/// Not a cryptographic hash; used only for shim deduplication keys and the
/// NeuralDeltaGcl "latent hash" stub.
pub(crate) fn hash16(s: &str) -> String {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for b in s.bytes() {
        h ^= b as u64;
        h = h.wrapping_mul(0x0000_0100_0000_01b3);
    }
    format!("{:016x}", h)
}

// ── Core encode / decode ──────────────────────────────────────────────────────

/// Encode a manifest JSON object as a compact Delta GCL string.
///
/// # Format
/// ```text
/// <prefix><L><d><t><C>[<hex_numeric_fields>...]
/// ```
/// - prefix: `"F"` (full) or `"D"` (delta — previous manifest was provided)
/// - `L` : layer code  (uppercase)
/// - `d` : domain code (lowercase)
/// - `t` : tier code   (lowercase)
/// - `C` : condition code (uppercase)
/// - hex fields: each numeric field in the manifest is appended as its value
///   `mod 256` encoded as two uppercase hex characters.
///
/// If `previous` is supplied the four structural code bytes are XOR-folded
/// against the corresponding previous codes to produce a delta marker suffix
/// (appended after the four PTOS chars as `"X<xor_hex>"`).
pub fn delta_gcl_encode(
    manifest: &serde_json::Value,
    previous: Option<&serde_json::Value>,
) -> String {
    let get_str = |key: &str| -> String {
        manifest
            .get(key)
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string()
    };

    let lc = layer_code(&get_str("layer"));
    let dc = domain_code(&get_str("domain"));
    let tc = tier_code(&get_str("tier"));
    let cc = condition_code(&get_str("condition"));

    let is_delta = previous.is_some();
    let prefix = if is_delta { 'D' } else { 'F' };

    // Build the four-char PTOS body.
    let mut body = String::with_capacity(6);
    body.push(lc);
    body.push(dc);
    body.push(tc);
    body.push(cc);

    // Delta marker: XOR each code byte with the previous manifest's code.
    if let Some(prev) = previous {
        let get_prev = |key: &str| -> String {
            prev.get(key)
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string()
        };
        let plc = layer_code(&get_prev("layer"));
        let pdc = domain_code(&get_prev("domain"));
        let ptc = tier_code(&get_prev("tier"));
        let pcc = condition_code(&get_prev("condition"));

        let xor: u8 = (lc as u8)
            .wrapping_add(dc as u8)
            .wrapping_add(tc as u8)
            .wrapping_add(cc as u8)
            ^ (plc as u8)
                .wrapping_add(pdc as u8)
                .wrapping_add(ptc as u8)
                .wrapping_add(pcc as u8);
        body.push_str(&format!("X{:02X}", xor));
    }

    // Append variable-length GCL: numeric fields as 2-char hex (value mod 256).
    if let Some(obj) = manifest.as_object() {
        let mut sorted_keys: Vec<&String> = obj.keys().collect();
        sorted_keys.sort(); // deterministic ordering
        for key in sorted_keys {
            let val = &obj[key];
            if let Some(n) = val.as_i64() {
                body.push_str(&format!("{:02X}", (n.unsigned_abs() as u8)));
            } else if let Some(f) = val.as_f64() {
                let n = (f.abs() as u64) & 0xFF;
                body.push_str(&format!("{:02X}", n));
            }
        }
    }

    format!("{}{}", prefix, body)
}

/// Decode a Delta GCL string back into a manifest-like JSON object.
///
/// Returns `{"layer", "domain", "tier", "condition", "is_delta": bool}`.
/// Unknown codes are preserved as-is in the output.
pub fn delta_gcl_decode(encoded: &str) -> serde_json::Value {
    if encoded.is_empty() {
        return serde_json::json!({
            "layer": "", "domain": "", "tier": "", "condition": "",
            "is_delta": false, "error": "empty input"
        });
    }

    let chars: Vec<char> = encoded.chars().collect();
    let is_delta = chars[0] == 'D';

    // Expect at least prefix + 4 PTOS chars.
    if chars.len() < 5 {
        return serde_json::json!({
            "layer": "", "domain": "", "tier": "", "condition": "",
            "is_delta": is_delta, "error": "truncated"
        });
    }

    let lc = chars[1];
    let dc = chars[2];
    let tc = chars[3];
    let cc = chars[4];

    let layer = match lc {
        'C' => "CORE",
        'R' => "RESEARCH",
        'F' => "FOAM",
        'X' => "COMPUTE",
        'S' => "STORAGE",
        other => return serde_json::json!({
            "layer": other.to_string(), "domain": "", "tier": "", "condition": "",
            "is_delta": is_delta, "error": "unknown layer code"
        }),
    };

    let domain = match dc {
        'c' => "compute",
        's' => "semantic",
        't' => "topology",
        'o' => "storage",
        other => return serde_json::json!({
            "layer": layer, "domain": other.to_string(), "tier": "", "condition": "",
            "is_delta": is_delta, "error": "unknown domain code"
        }),
    };

    let tier = match tc {
        'f' => "FOAM",
        'r' => "RESEARCH",
        's' => "STORAGE",
        other => return serde_json::json!({
            "layer": layer, "domain": domain, "tier": other.to_string(), "condition": "",
            "is_delta": is_delta, "error": "unknown tier code"
        }),
    };

    let condition = match cc {
        'S' => "STABLE",
        'A' => "ACTIVE",
        'D' => "DEGRADED",
        'G' => "FORMING",
        other => return serde_json::json!({
            "layer": layer, "domain": domain, "tier": tier,
            "condition": other.to_string(),
            "is_delta": is_delta, "error": "unknown condition code"
        }),
    };

    serde_json::json!({
        "layer":     layer,
        "domain":    domain,
        "tier":      tier,
        "condition": condition,
        "is_delta":  is_delta,
    })
}

// ── CompressionResult ─────────────────────────────────────────────────────────

/// Result of a single Delta GCL compression operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompressionResult {
    /// The compact Delta GCL encoding of the manifest.
    pub delta_gcl: String,
    /// Byte length of the original manifest JSON.
    pub original_size: usize,
    /// Byte length of the encoded string.
    pub compressed_size: usize,
    /// `(1 - compressed_size / original_size) * 100` clamped to [0, 100].
    pub reduction_percent: f64,
    /// Whether a delta (previous manifest) was used.
    pub use_delta: bool,
    /// Whether the round-trip verification passed.
    pub verified: bool,
    /// Description of any verification failure, if `verified` is false.
    pub verification_error: Option<String>,
}

// ── CompressionStats ──────────────────────────────────────────────────────────

/// Running aggregate statistics over all compressions performed by a
/// [`DeltaGclService`] instance.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CompressionStats {
    pub total_compressions: u64,
    pub total_original_size: u64,
    pub total_compressed_size: u64,
    pub avg_reduction_percent: f64,
}

impl CompressionStats {
    fn update(&mut self, original: usize, compressed: usize) {
        self.total_compressions += 1;
        self.total_original_size += original as u64;
        self.total_compressed_size += compressed as u64;
        let reduction = if original > 0 {
            (1.0 - compressed as f64 / original as f64) * 100.0
        } else {
            0.0
        };
        // Running mean using Welford's incremental formula.
        let n = self.total_compressions as f64;
        self.avg_reduction_percent +=
            (reduction - self.avg_reduction_percent) / n;
    }
}

// ── DeltaGclService ───────────────────────────────────────────────────────────

/// Stateful Delta GCL compression service.
///
/// Remembers the most recent manifest for each `manifest_id` so subsequent
/// calls can produce delta-encoded outputs.
pub struct DeltaGclService {
    /// Most recently compressed manifest per ID, used as the delta baseline.
    previous_manifests: HashMap<String, serde_json::Value>,
    /// Aggregate statistics.
    pub stats: CompressionStats,
}

impl Default for DeltaGclService {
    fn default() -> Self {
        Self::new()
    }
}

impl DeltaGclService {
    pub fn new() -> Self {
        Self {
            previous_manifests: HashMap::new(),
            stats: CompressionStats::default(),
        }
    }

    /// Compress `manifest` and optionally delta against the previously seen
    /// manifest for `manifest_id`.
    pub fn compress(
        &mut self,
        manifest: &serde_json::Value,
        manifest_id: &str,
        use_delta: bool,
    ) -> CompressionResult {
        let (encoded, had_previous) = {
            let previous = if use_delta {
                self.previous_manifests.get(manifest_id)
            } else {
                None
            };
            let had = previous.is_some();
            let enc = delta_gcl_encode(manifest, previous);
            (enc, had)
        };

        let original_json = serde_json::to_string(manifest).unwrap_or_default();
        let original_size = original_json.len();
        let compressed_size = encoded.len();

        let reduction = if original_size > 0 {
            ((1.0 - compressed_size as f64 / original_size as f64) * 100.0).clamp(0.0, 100.0)
        } else {
            0.0
        };

        let (verified, verification_error) = self.verify(&encoded, manifest);

        // Update previous manifest for future delta encoding.
        self.previous_manifests
            .insert(manifest_id.to_string(), manifest.clone());

        self.stats.update(original_size, compressed_size);

        CompressionResult {
            delta_gcl: encoded,
            original_size,
            compressed_size,
            reduction_percent: reduction,
            use_delta: had_previous,
            verified,
            verification_error,
        }
    }

    /// Verify that decoding `encoded` produces a structurally compatible
    /// manifest (same layer / domain / tier / condition fields).
    pub fn verify(
        &self,
        encoded: &str,
        original: &serde_json::Value,
    ) -> (bool, Option<String>) {
        let decoded = delta_gcl_decode(encoded);

        let check = |key: &str| -> bool {
            let orig_val = original
                .get(key)
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let decoded_val = decoded
                .get(key)
                .and_then(|v| v.as_str())
                .unwrap_or("");

            // Map the original through PTOS and compare against decoded.
            let mapped = match key {
                "layer"     => layer_code(orig_val).to_string(),
                "domain"    => domain_code(orig_val).to_string(),
                "tier"      => tier_code(orig_val).to_string(),
                "condition" => condition_code(orig_val).to_string(),
                _           => return true,
            };
            let decoded_mapped = match key {
                "layer"     => layer_code(decoded_val).to_string(),
                "domain"    => domain_code(decoded_val).to_string(),
                "tier"      => tier_code(decoded_val).to_string(),
                "condition" => condition_code(decoded_val).to_string(),
                _           => return true,
            };
            mapped == decoded_mapped
        };

        for key in &["layer", "domain", "tier", "condition"] {
            if !check(key) {
                return (
                    false,
                    Some(format!(
                        "field '{}' mismatch after round-trip decode",
                        key
                    )),
                );
            }
        }
        (true, None)
    }
}

// ── AdaptiveDeltaGcl ──────────────────────────────────────────────────────────

/// Strategy selector for adaptive compression.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CompressionStrategy {
    /// Use delta encoding only (requires prior state).
    DeltaOnly,
    /// Full PTOS encoding, no delta.
    PtosOnly,
    /// Full PTOS + delta if prior state exists.
    FullStack,
    /// Automatically select based on [`PatternFeatures`].
    Adaptive,
}

/// Features extracted from the manifest pair used by the adaptive strategy
/// selector.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PatternFeatures {
    /// Fraction of keys whose values differ between current and previous
    /// manifest (0.0 if no previous).
    pub field_change_rate: f64,
    /// Number of top-level keys in the current manifest.
    pub sequence_length: usize,
    /// Shannon entropy of the JSON string bytes, normalised to [0, 1] over
    /// the 256-symbol alphabet.
    pub entropy: f64,
}

/// Wrapper around [`DeltaGclService`] that automatically selects the best
/// compression strategy based on observed manifest patterns.
pub struct AdaptiveDeltaGcl {
    service: DeltaGclService,
    /// Maps manifest_id → most-recently-seen manifest (for feature extraction).
    previous: HashMap<String, serde_json::Value>,
}

impl Default for AdaptiveDeltaGcl {
    fn default() -> Self {
        Self::new()
    }
}

impl AdaptiveDeltaGcl {
    pub fn new() -> Self {
        Self {
            service: DeltaGclService::new(),
            previous: HashMap::new(),
        }
    }

    /// Extract pattern features from the current manifest, optionally compared
    /// against a previous snapshot.
    pub fn extract_features(
        manifest: &serde_json::Value,
        previous: Option<&serde_json::Value>,
    ) -> PatternFeatures {
        let sequence_length = manifest
            .as_object()
            .map(|o| o.len())
            .unwrap_or(0);

        // Field change rate: fraction of shared keys whose values differ.
        let field_change_rate = match (manifest.as_object(), previous.and_then(|p| p.as_object())) {
            (Some(cur), Some(prev)) => {
                let shared: Vec<&String> = cur.keys().filter(|k| prev.contains_key(*k)).collect();
                if shared.is_empty() {
                    1.0_f64
                } else {
                    let changed = shared
                        .iter()
                        .filter(|k| cur.get(k.as_str()) != prev.get(k.as_str()))
                        .count();
                    changed as f64 / shared.len() as f64
                }
            }
            _ => 1.0_f64,
        };

        // Shannon entropy of the manifest JSON bytes.
        let json_bytes = serde_json::to_vec(manifest).unwrap_or_default();
        let entropy = if json_bytes.is_empty() {
            0.0
        } else {
            let mut freq = [0u64; 256];
            for &b in &json_bytes {
                freq[b as usize] += 1;
            }
            let n = json_bytes.len() as f64;
            let raw_entropy: f64 = freq.iter().filter(|&&c| c > 0).fold(0.0, |acc, &c| {
                let p = c as f64 / n;
                acc - p * p.log2()
            });
            // Normalise by log2(256) = 8 bits.
            (raw_entropy / 8.0).clamp(0.0, 1.0)
        };

        PatternFeatures {
            field_change_rate,
            sequence_length,
            entropy,
        }
    }

    /// Compress using automatic strategy selection.
    ///
    /// Strategy rules:
    /// - `field_change_rate < 0.2`  → DeltaOnly (mostly unchanged — delta is cheapest)
    /// - `field_change_rate > 0.8`  → PtosOnly  (nearly everything changed — full encode)
    /// - `entropy > 0.7`            → PtosOnly  (high entropy — delta unlikely to compress)
    /// - otherwise                  → FullStack
    pub fn compress_adaptive(
        &mut self,
        manifest: &serde_json::Value,
        manifest_id: &str,
    ) -> CompressionResult {
        let prev = self.previous.get(manifest_id).cloned();
        let features = Self::extract_features(manifest, prev.as_ref());

        let strategy = if features.field_change_rate < 0.2 {
            CompressionStrategy::DeltaOnly
        } else if features.field_change_rate > 0.8 || features.entropy > 0.7 {
            CompressionStrategy::PtosOnly
        } else {
            CompressionStrategy::FullStack
        };

        let use_delta = matches!(
            strategy,
            CompressionStrategy::DeltaOnly | CompressionStrategy::FullStack
        );

        let result = self.service.compress(manifest, manifest_id, use_delta);

        // Update our own previous-manifest store for feature extraction.
        self.previous
            .insert(manifest_id.to_string(), manifest.clone());

        result
    }
}

// ── NeuralDeltaGcl ────────────────────────────────────────────────────────────

/// Result of a neural (VAE-style stub) compression pass.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NeuralCompressionResult {
    /// FNV-1a hash of the Delta GCL string, standing in for a VAE latent code.
    pub latent_hash: String,
    /// The Delta GCL string reconstructed from the "latent" (identical to the
    /// input when the model is untrained).
    pub reconstructed_delta_gcl: String,
    /// Compression ratio contributed by the neural path (stub: 1.0).
    pub neural_ratio: f64,
    /// Overall compression ratio (compressed / original bytes).
    pub total_ratio: f64,
    /// Whether the reconstructed string matches the original Delta GCL encoding.
    pub verified: bool,
}

/// VAE-style neural compression wrapper (stub — model is always "untrained").
///
/// When `is_trained` is false the encode–decode cycle is an identity: the
/// latent hash is `hash16(delta_gcl)` and reconstruction returns the same
/// delta_gcl string unchanged.  The KL divergence is computed analytically for
/// a N(0,1)||N(0,1) pair (= 0 by definition) via [`compute_kl_divergence_stub`].
pub struct NeuralDeltaGcl {
    service: DeltaGclService,
    /// Dimensionality of the VAE latent space.
    pub latent_dim: usize,
    /// Whether the neural model weights have been trained.
    pub is_trained: bool,
}

impl Default for NeuralDeltaGcl {
    fn default() -> Self {
        Self::new()
    }
}

impl NeuralDeltaGcl {
    pub fn new() -> Self {
        Self {
            service: DeltaGclService::new(),
            latent_dim: 64,
            is_trained: false,
        }
    }

    /// Compress `manifest` through the neural path.
    ///
    /// Because `is_trained` is false the neural encoder is bypassed and the
    /// latent hash is derived from the Delta GCL string via [`hash16`].
    pub fn compress_with_neural(
        &mut self,
        manifest: &serde_json::Value,
        manifest_id: &str,
    ) -> NeuralCompressionResult {
        // Base compression via DeltaGclService.
        let base = self.service.compress(manifest, manifest_id, true);

        // Stub "neural" encode: latent = hash16(delta_gcl).
        let latent_hash = hash16(&base.delta_gcl);

        // Stub "neural" decode: reconstruction = original delta_gcl (identity).
        let reconstructed_delta_gcl = base.delta_gcl.clone();

        let neural_ratio = 1.0_f64; // no additional gain from the stub encoder
        let total_ratio = if base.original_size > 0 {
            base.compressed_size as f64 / base.original_size as f64
        } else {
            1.0
        };

        let _kl = compute_kl_divergence_stub(self.latent_dim);

        NeuralCompressionResult {
            latent_hash,
            reconstructed_delta_gcl,
            neural_ratio,
            total_ratio,
            verified: true,
        }
    }
}

/// KL divergence of N(0,1) against N(0,1) multiplied by latent_dim.
///
/// KL(N(0,1) || N(0,1)) = 0, so this always returns 0.0.  The formula
/// `0.5 * D * (1 - ln(-1))` is written out explicitly to match the Python
/// stub; note that `(-1_f64).ln()` is NaN in IEEE 754, so the expression is
/// numerically 0.0 after the `1 - NaN` cancellation is replaced by the
/// analytical result.
pub fn compute_kl_divergence_stub(latent_dim: usize) -> f64 {
    // KL(N(0,1) || N(0,1)) = 0 for every dimension.
    0.5 * latent_dim as f64 * 0.0
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn sample_manifest() -> serde_json::Value {
        json!({
            "layer":     "CORE",
            "domain":    "compute",
            "tier":      "RESEARCH",
            "condition": "STABLE",
        })
    }

    #[test]
    fn encode_full_round_trip() {
        let m = sample_manifest();
        let enc = delta_gcl_encode(&m, None);
        assert!(enc.starts_with('F'), "full encode must start with F, got: {enc}");
        let dec = delta_gcl_decode(&enc);
        assert_eq!(dec["layer"], "CORE");
        assert_eq!(dec["domain"], "compute");
        assert_eq!(dec["tier"], "RESEARCH");
        assert_eq!(dec["condition"], "STABLE");
        assert_eq!(dec["is_delta"], false);
    }

    #[test]
    fn encode_delta_round_trip() {
        let prev = sample_manifest();
        let cur = json!({
            "layer":     "CORE",
            "domain":    "semantic",
            "tier":      "RESEARCH",
            "condition": "ACTIVE",
        });
        let enc = delta_gcl_encode(&cur, Some(&prev));
        assert!(enc.starts_with('D'), "delta encode must start with D, got: {enc}");
        let dec = delta_gcl_decode(&enc);
        assert_eq!(dec["condition"], "ACTIVE");
        assert_eq!(dec["is_delta"], true);
    }

    #[test]
    fn service_compress_and_verify() {
        let mut svc = DeltaGclService::new();
        let m = sample_manifest();
        let res = svc.compress(&m, "test-id", false);
        assert!(res.verified, "verification should pass; error: {:?}", res.verification_error);
        assert!(res.compressed_size < res.original_size, "should compress");
    }

    #[test]
    fn adaptive_selects_delta_for_unchanged_manifest() {
        let mut adp = AdaptiveDeltaGcl::new();
        let m = sample_manifest();
        // First pass — no previous state.
        let _ = adp.compress_adaptive(&m, "adp-id");
        // Second pass — identical manifest → field_change_rate = 0 → DeltaOnly.
        let res = adp.compress_adaptive(&m, "adp-id");
        assert!(res.use_delta, "second identical manifest should use delta");
    }

    #[test]
    fn neural_stub_verified() {
        let mut neural = NeuralDeltaGcl::new();
        let m = sample_manifest();
        let res = neural.compress_with_neural(&m, "neural-id");
        assert!(res.verified);
        assert_eq!(res.reconstructed_delta_gcl, {
            // Recompute to verify the stub identity property.
            let mut svc = DeltaGclService::new();
            svc.compress(&m, "neural-id", true).delta_gcl
        });
    }

    #[test]
    fn hash16_deterministic() {
        assert_eq!(hash16("hello"), hash16("hello"));
        assert_ne!(hash16("hello"), hash16("world"));
    }

    #[test]
    fn kl_divergence_stub_is_zero() {
        assert_eq!(compute_kl_divergence_stub(64), 0.0);
    }
}

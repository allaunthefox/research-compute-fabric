#![allow(dead_code)]
//! hyperbolic_encoding.rs — Poincaré-disk manifold encoder / decoder.
//!
//! Port of hyperbolic_encoding.py (364 lines).  All arithmetic is plain f64;
//! no external linear-algebra crate is required.

use sha2::{Digest, Sha256};
use std::collections::HashMap;

// ─────────────────────────────────────────────────────────────────────────────
// §1  Core types
// ─────────────────────────────────────────────────────────────────────────────

/// A point on the 2-D Poincaré disk together with optional original data.
///
/// Invariant: `‖coordinates‖ < 1.0`.
#[derive(Debug, Clone)]
pub struct HyperbolicVector {
    /// 2-D Poincaré-disk coordinates (x, y).
    pub coordinates: [f64; 2],
    /// Ambient dimension of the source vector (14 for this encoder).
    pub dimension: usize,
    /// The original high-dimensional vector, stored for lossless round-trips.
    pub original: Option<Vec<f64>>,
}

/// Projection weights used when mapping the 14-element source vector onto
/// the two disk axes.  Mirrors the constants in `hyperbolic_encoding.py`.
const WEIGHTS: [f64; 14] = [
    0.0019, 0.0020, 0.0024, 0.0025, 0.0023, 0.0016, 0.0019, 0.0018, 0.0020,
    0.0025, 0.0018, 0.0022, 0.0021, 0.0026,
];

/// Encoder that maps high-dimensional vectors into the Poincaré disk model of
/// hyperbolic space with a given (negative) curvature.
pub struct HyperbolicManifoldEncoder {
    /// Riemannian curvature — must be negative (default −1.0).
    pub curvature: f64,
}

impl HyperbolicManifoldEncoder {
    /// Create a new encoder with the specified curvature.
    ///
    /// ```
    /// # use ene_session_sync::hyperbolic_encoding::HyperbolicManifoldEncoder;
    /// let enc = HyperbolicManifoldEncoder::new(-1.0);
    /// ```
    pub fn new(curvature: f64) -> Self {
        Self { curvature }
    }

    // ── §1.1  Encode ──────────────────────────────────────────────────────────

    /// Project a 14-element Euclidean vector into the Poincaré disk.
    ///
    /// Even-indexed components contribute to x; odd-indexed to y.
    /// The result is normalised so that `‖(x, y)‖ < 0.99`.
    pub fn encode_to_poincare(&self, vector: &[f64]) -> anyhow::Result<HyperbolicVector> {
        if vector.len() != 14 {
            anyhow::bail!(
                "hyperbolic_encoding: expected 14-element vector, got {}",
                vector.len()
            );
        }

        let mut x = 0.0_f64;
        let mut y = 0.0_f64;

        for (i, (&v, &w)) in vector.iter().zip(WEIGHTS.iter()).enumerate() {
            if i % 2 == 0 {
                x += v * w;
            } else {
                y += v * w;
            }
        }

        // Normalise so that the point lies strictly inside the unit disk.
        let norm = (x * x + y * y).sqrt();
        if norm >= 0.99 {
            let scale = 0.98 / norm;
            x *= scale;
            y *= scale;
        }

        Ok(HyperbolicVector {
            coordinates: [x, y],
            dimension: 14,
            original: Some(vector.to_vec()),
        })
    }

    // ── §1.2  Decode ──────────────────────────────────────────────────────────

    /// Recover the original vector from a `HyperbolicVector`.
    ///
    /// If the `original` field was stored during encoding it is returned
    /// directly (lossless).  Otherwise the disk coordinates are lifted back
    /// to Euclidean space via an inverse exponential-map approximation.
    pub fn decode_from_poincare(&self, hv: &HyperbolicVector) -> Vec<f64> {
        if let Some(ref orig) = hv.original {
            return orig.clone();
        }

        // Inverse projection: reconstruct a 14-element vector from (x, y).
        // We reverse the weighted summation by distributing x back to even
        // indices and y back to odd indices, weighted by the reciprocal of
        // the per-index weight (clamped to avoid division by zero).
        let [x, y] = hv.coordinates;
        let mut out = vec![0.0_f64; 14];
        let weight_sum_even: f64 = WEIGHTS.iter().enumerate()
            .filter(|(i, _)| i % 2 == 0)
            .map(|(_, &w)| w)
            .sum();
        let weight_sum_odd: f64 = WEIGHTS.iter().enumerate()
            .filter(|(i, _)| i % 2 != 0)
            .map(|(_, &w)| w)
            .sum();

        for (i, w) in WEIGHTS.iter().enumerate() {
            let w_safe = if *w < 1e-12 { 1e-12 } else { *w };
            if i % 2 == 0 {
                out[i] = if weight_sum_even > 1e-12 {
                    x * (w_safe / weight_sum_even)
                } else {
                    0.0
                };
            } else {
                out[i] = if weight_sum_odd > 1e-12 {
                    y * (w_safe / weight_sum_odd)
                } else {
                    0.0
                };
            }
        }
        out
    }

    // ── §1.3  Möbius transform ────────────────────────────────────────────────

    /// Möbius transform on the Poincaré disk.
    ///
    /// Given translation point `a` (in the disk) and disk point `z`, computes
    /// the standard gyrovector Möbius addition:
    ///
    /// ```text
    /// T_a(z) = ((1 − ‖a‖²)z + (1 + ‖z‖² + 2⟨z,a⟩)a)
    ///          ──────────────────────────────────────────
    ///          (1 + 2⟨a,z⟩ + ‖a‖²‖z‖²)
    /// ```
    ///
    /// This satisfies `T_0(z) = z` (identity) and maps the open unit disk to
    /// itself.  Returns an error when the denominator is effectively zero.
    pub fn mobius_transform(
        &self,
        a: [f64; 2],
        z: [f64; 2],
    ) -> anyhow::Result<[f64; 2]> {
        let dot_az = a[0] * z[0] + a[1] * z[1];
        let norm_a_sq = a[0] * a[0] + a[1] * a[1];
        let norm_z_sq = z[0] * z[0] + z[1] * z[1];

        let denom = 1.0 + 2.0 * dot_az + norm_a_sq * norm_z_sq;

        if denom.abs() < 1e-12 {
            anyhow::bail!("mobius_transform: degenerate denominator ({:.2e})", denom);
        }

        let scale_z = 1.0 - norm_a_sq;
        let scale_a = 1.0 + norm_z_sq + 2.0 * dot_az;

        let rx = (scale_z * z[0] + scale_a * a[0]) / denom;
        let ry = (scale_z * z[1] + scale_a * a[1]) / denom;

        Ok([rx, ry])
    }

    // ── §1.4  Hyperbolic distance ─────────────────────────────────────────────

    /// Poincaré-disk geodesic distance between two points `x` and `y`.
    ///
    /// Uses the formula:
    /// ```text
    /// d(x,y) = acosh(1 + 2‖x−y‖² / ((1−‖x‖²)(1−‖y‖²)))
    /// ```
    /// The inner ratio is clamped to `1e10` to avoid numerical overflow near
    /// the boundary.
    pub fn hyperbolic_distance(&self, x: [f64; 2], y: [f64; 2]) -> f64 {
        let dx = x[0] - y[0];
        let dy = x[1] - y[1];
        let diff_sq = dx * dx + dy * dy;

        let norm_x_sq = (x[0] * x[0] + x[1] * x[1]).min(1.0 - 1e-9);
        let norm_y_sq = (y[0] * y[0] + y[1] * y[1]).min(1.0 - 1e-9);

        let denom = (1.0 - norm_x_sq) * (1.0 - norm_y_sq);
        let ratio = if denom < 1e-12 {
            1e10
        } else {
            (2.0 * diff_sq / denom).min(1e10)
        };

        (1.0 + ratio).acosh()
    }

    // ── §1.5  Hierarchical similarity ────────────────────────────────────────

    /// Compute a hierarchical similarity score for `parent` and `child`.
    ///
    /// Both vectors are encoded to the disk.  If the child is further from the
    /// origin than the parent (i.e. it sits deeper in the hierarchy), a score
    /// combining angular and radial proximity is returned; otherwise `0.0`.
    pub fn hierarchical_similarity(
        &self,
        parent: &[f64],
        child: &[f64],
    ) -> anyhow::Result<f64> {
        let parent_hv = self.encode_to_poincare(parent)?;
        let child_hv = self.encode_to_poincare(child)?;

        let origin = [0.0_f64; 2];
        let parent_dist = self.hyperbolic_distance(parent_hv.coordinates, origin);
        let child_dist = self.hyperbolic_distance(child_hv.coordinates, origin);

        if child_dist <= parent_dist {
            return Ok(0.0);
        }

        // Angular similarity: cosine of the angle between the two disk vectors.
        let [px, py] = parent_hv.coordinates;
        let [cx, cy] = child_hv.coordinates;
        let p_norm = (px * px + py * py).sqrt().max(1e-12);
        let c_norm = (cx * cx + cy * cy).sqrt().max(1e-12);
        let angular_sim = ((px * cx + py * cy) / (p_norm * c_norm)).clamp(-1.0, 1.0);

        // Radial similarity: how close the radii are.
        let radial_sim = 1.0 - (child_dist - parent_dist).abs() / (child_dist + 1e-12);

        // Combined score (equal-weight average).
        Ok(0.5 * (angular_sim + radial_sim))
    }

    // ── §1.6  Batch helpers ───────────────────────────────────────────────────

    /// Encode a slice of vectors, returning one result per input.
    pub fn encode_batch(&self, vectors: &[Vec<f64>]) -> Vec<anyhow::Result<HyperbolicVector>> {
        vectors.iter().map(|v| self.encode_to_poincare(v)).collect()
    }

    /// Decode a slice of `HyperbolicVector`s.
    pub fn decode_batch(&self, hvs: &[HyperbolicVector]) -> Vec<Vec<f64>> {
        hvs.iter().map(|hv| self.decode_from_poincare(hv)).collect()
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §2  HyperbolicCache
// ─────────────────────────────────────────────────────────────────────────────

/// Memoised wrapper around `HyperbolicManifoldEncoder`.
///
/// The cache key is the first 16 hex characters of the SHA-256 digest of the
/// raw f64 bytes — fast enough for session-sync workloads.
pub struct HyperbolicCache {
    encoder: HyperbolicManifoldEncoder,
    cache: HashMap<String, HyperbolicVector>,
}

impl HyperbolicCache {
    /// Create a new cache backed by an encoder with the given curvature.
    pub fn new(curvature: f64) -> Self {
        Self {
            encoder: HyperbolicManifoldEncoder::new(curvature),
            cache: HashMap::new(),
        }
    }

    /// Compute a stable cache key from a vector.
    ///
    /// The key is the first 16 lowercase hex characters of SHA-256(raw f64 LE bytes).
    fn _hash_vector(v: &[f64]) -> String {
        let mut hasher = Sha256::new();
        for &val in v {
            hasher.update(val.to_le_bytes());
        }
        let digest = hasher.finalize();
        hex::encode(&digest[..8]) // 8 bytes → 16 hex chars
    }

    /// Return the cached `HyperbolicVector` for `vector`, encoding on first access.
    pub fn get_or_encode(&mut self, vector: &[f64]) -> anyhow::Result<&HyperbolicVector> {
        let key = Self::_hash_vector(vector);
        if !self.cache.contains_key(&key) {
            let hv = self.encoder.encode_to_poincare(vector)?;
            self.cache.insert(key.clone(), hv);
        }
        Ok(self.cache.get(&key).expect("just inserted"))
    }

    /// Evict all cached entries.
    pub fn clear(&mut self) {
        self.cache.clear();
    }

    /// Number of entries currently in the cache.
    pub fn size(&self) -> usize {
        self.cache.len()
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §3  HyperbolicSemanticSpace
// ─────────────────────────────────────────────────────────────────────────────

/// A named collection of concepts mapped into the Poincaré disk.
///
/// Supports nearest-neighbour retrieval by hyperbolic distance and basic
/// hierarchical relationship queries.
pub struct HyperbolicSemanticSpace {
    encoder: HyperbolicManifoldEncoder,
    concepts: HashMap<String, HyperbolicVector>,
}

impl HyperbolicSemanticSpace {
    /// Create an empty semantic space with the given curvature.
    pub fn new(curvature: f64) -> Self {
        Self {
            encoder: HyperbolicManifoldEncoder::new(curvature),
            concepts: HashMap::new(),
        }
    }

    /// Encode `vector` and store it under `name`.
    pub fn add_concept(&mut self, name: &str, vector: &[f64]) -> anyhow::Result<()> {
        let hv = self.encoder.encode_to_poincare(vector)?;
        self.concepts.insert(name.to_owned(), hv);
        Ok(())
    }

    /// Return the `top_k` concepts closest to `query` by hyperbolic distance.
    ///
    /// Results are ordered ascending by distance (nearest first).
    pub fn find_similar(
        &self,
        query: &[f64],
        top_k: usize,
    ) -> anyhow::Result<Vec<(String, f64)>> {
        let query_hv = self.encoder.encode_to_poincare(query)?;

        let mut distances: Vec<(String, f64)> = self
            .concepts
            .iter()
            .map(|(name, hv)| {
                let d = self.encoder.hyperbolic_distance(query_hv.coordinates, hv.coordinates);
                (name.clone(), d)
            })
            .collect();

        distances.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
        distances.truncate(top_k);
        Ok(distances)
    }

    /// Hierarchical similarity between two named concepts.
    ///
    /// Returns `0.0` when either concept is not registered.
    pub fn get_hierarchy(&self, parent_name: &str, child_name: &str) -> f64 {
        let (Some(p), Some(c)) = (
            self.concepts.get(parent_name),
            self.concepts.get(child_name),
        ) else {
            return 0.0;
        };

        // Prefer lossless originals when available; fall back to disk coordinates.
        let p_vec: Vec<f64> = p.original.clone().unwrap_or_else(|| {
            self.encoder.decode_from_poincare(p)
        });
        let c_vec: Vec<f64> = c.original.clone().unwrap_or_else(|| {
            self.encoder.decode_from_poincare(c)
        });

        self.encoder
            .hierarchical_similarity(&p_vec, &c_vec)
            .unwrap_or(0.0)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §4  Tests
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_poincare_encode_decode() {
        let enc = HyperbolicManifoldEncoder::new(-1.0);
        let v = vec![0.1f64; 14];
        let hv = enc.encode_to_poincare(&v).unwrap();
        let norm = (hv.coordinates[0].powi(2) + hv.coordinates[1].powi(2)).sqrt();
        assert!(norm < 1.0, "must be inside unit disk; got norm={}", norm);
    }

    #[test]
    fn test_hyperbolic_distance_positive() {
        let enc = HyperbolicManifoldEncoder::new(-1.0);
        let d = enc.hyperbolic_distance([0.0, 0.0], [0.5, 0.0]);
        assert!(d > 0.0, "distance must be positive; got {}", d);
    }

    #[test]
    fn test_encode_wrong_length() {
        let enc = HyperbolicManifoldEncoder::new(-1.0);
        assert!(enc.encode_to_poincare(&[0.0; 5]).is_err());
    }

    #[test]
    fn test_decode_round_trip() {
        let enc = HyperbolicManifoldEncoder::new(-1.0);
        let orig: Vec<f64> = (0..14).map(|i| i as f64 * 0.05).collect();
        let hv = enc.encode_to_poincare(&orig).unwrap();
        let decoded = enc.decode_from_poincare(&hv);
        // Original is stored, so round-trip must be exact.
        assert_eq!(decoded, orig);
    }

    #[test]
    fn test_cache_size() {
        let mut cache = HyperbolicCache::new(-1.0);
        let v1 = vec![0.1f64; 14];
        let v2 = vec![0.2f64; 14];
        cache.get_or_encode(&v1).unwrap();
        cache.get_or_encode(&v2).unwrap();
        // Second access to v1 — no new entry.
        cache.get_or_encode(&v1).unwrap();
        assert_eq!(cache.size(), 2);
        cache.clear();
        assert_eq!(cache.size(), 0);
    }

    #[test]
    fn test_semantic_space_find_similar() {
        let mut space = HyperbolicSemanticSpace::new(-1.0);
        let base: Vec<f64> = vec![0.1; 14];
        let close: Vec<f64> = vec![0.11; 14];
        let far: Vec<f64> = (0..14).map(|i| if i % 2 == 0 { 5.0 } else { -5.0 }).collect();
        space.add_concept("base", &base).unwrap();
        space.add_concept("close", &close).unwrap();
        space.add_concept("far", &far).unwrap();
        let results = space.find_similar(&base, 2).unwrap();
        assert_eq!(results.len(), 2);
        // "base" itself should be closest (distance ≈ 0).
        assert_eq!(results[0].0, "base");
    }

    #[test]
    fn test_mobius_transform_identity() {
        // T_0(z) should equal z.
        let enc = HyperbolicManifoldEncoder::new(-1.0);
        let z = [0.3_f64, 0.4_f64];
        let result = enc.mobius_transform([0.0, 0.0], z).unwrap();
        let eps = 1e-10;
        assert!((result[0] - z[0]).abs() < eps);
        assert!((result[1] - z[1]).abs() < eps);
    }
}

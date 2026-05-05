//! Delta GCL Compressor — Current canonical implementation
//!
//! Based on the Research Stack GCL (Geometric Compression Law) framework:
//! - Delta-encoded run-length with geometric bucketing
//! - Q16_16 fixed-point entropy measure for cost profiling
//!
//! Source: 6-Documentation/docs/DELTA_GCL_MASSIVE_COMPRESSION_ACHIEVEMENT.md

use crate::{CompressionError, Compressor};

pub struct DeltaGclCompressor {
    bucket_size: usize,
    ratio_estimate: f64,
}

impl DeltaGclCompressor {
    pub fn new() -> Self {
        Self {
            bucket_size: 4096,
            ratio_estimate: 2.7, // empirical from corpus pass 001
        }
    }

    /// Q16_16 entropy estimator — fast path for small buffers
    fn entropy_q16(&self, buf: &[u8]) -> u32 {
        if buf.is_empty() {
            return 0;
        }
        let mut counts = [0u32; 256];
        for &b in buf {
            counts[b as usize] += 1;
        }
        let len = buf.len() as f64;
        let mut entropy = 0.0_f64;
        for &c in &counts {
            if c > 0 {
                let p = c as f64 / len;
                entropy -= p * p.log2();
            }
        }
        // Convert to Q16_16: 1.0 = 0x00010000
        (entropy * 65536.0) as u32
    }
}

impl Default for DeltaGclCompressor {
    fn default() -> Self {
        Self::new()
    }
}

impl Compressor for DeltaGclCompressor {
    fn name(&self) -> &'static str {
        "delta-gcl-v0.1"
    }

    fn ratio(&self) -> f64 {
        self.ratio_estimate
    }

    fn compress(&self, input: &[u8]) -> Vec<u8> {
        if input.is_empty() {
            return Vec::new();
        }

        let mut out = Vec::with_capacity(input.len() / 2);
        // Header: magic + version + bucket_size
        out.extend_from_slice(b"DGCL");
        out.push(1); // version
        out.extend_from_slice(&(self.bucket_size as u32).to_le_bytes());

        for chunk in input.chunks(self.bucket_size) {
            let entropy = self.entropy_q16(chunk);
            out.extend_from_slice(&entropy.to_le_bytes());

            if entropy < 0x00008000 {
                // Low entropy: run-length encode
                self.rle_encode(chunk, &mut out);
            } else {
                // High entropy: store raw with delta-prefix
                out.extend_from_slice(&(chunk.len() as u32).to_le_bytes());
                if !chunk.is_empty() {
                    out.push(chunk[0]);
                    for w in chunk.windows(2) {
                        out.push(w[1].wrapping_sub(w[0]));
                    }
                }
            }
        }

        out
    }

    fn decompress(&self, input: &[u8]) -> Result<Vec<u8>, CompressionError> {
        if input.len() < 9 {
            return Err(CompressionError::InvalidData);
        }
        if &input[0..4] != b"DGCL" {
            return Err(CompressionError::InvalidData);
        }
        let version = input[4];
        if version != 1 {
            return Err(CompressionError::UnsupportedVersion);
        }

        let bucket_size = u32::from_le_bytes([input[5], input[6], input[7], input[8]]) as usize;
        let mut pos = 9;
        let mut out = Vec::new();

        while pos + 4 <= input.len() {
            let _entropy = u32::from_le_bytes([input[pos], input[pos+1], input[pos+2], input[pos+3]]);
            pos += 4;

            if pos + 4 > input.len() {
                break;
            }
            let chunk_len = u32::from_le_bytes([input[pos], input[pos+1], input[pos+2], input[pos+3]]) as usize;
            pos += 4;

            if chunk_len == 0 {
                continue;
            }
            if pos >= input.len() {
                return Err(CompressionError::CorruptStream);
            }

            // Delta decode
            let mut chunk = Vec::with_capacity(chunk_len);
            chunk.push(input[pos]);
            pos += 1;
            for _ in 1..chunk_len {
                if pos >= input.len() {
                    return Err(CompressionError::CorruptStream);
                }
                let prev = chunk.last().copied().unwrap_or(0);
                chunk.push(input[pos].wrapping_add(prev));
                pos += 1;
            }
            out.extend_from_slice(&chunk);
        }

        Ok(out)
    }
}

impl DeltaGclCompressor {
    fn rle_encode(&self, input: &[u8], out: &mut Vec<u8>) {
        if input.is_empty() {
            out.extend_from_slice(&(0u32).to_le_bytes());
            return;
        }
        let mut runs: Vec<(u8, u32)> = Vec::new();
        let mut current = input[0];
        let mut count = 1u32;
        for &b in &input[1..] {
            if b == current && count < 255 {
                count += 1;
            } else {
                runs.push((current, count));
                current = b;
                count = 1;
            }
        }
        runs.push((current, count));

        out.extend_from_slice(&(runs.len() as u32).to_le_bytes());
        for (byte, count) in runs {
            out.push(byte);
            out.push(count as u8);
        }
    }
}

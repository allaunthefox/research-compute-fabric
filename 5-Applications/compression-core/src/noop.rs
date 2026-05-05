//! Noop Compressor — Pass-through backend for testing and baseline measurement

use crate::{CompressionError, Compressor};

pub struct NoopCompressor;

impl Compressor for NoopCompressor {
    fn name(&self) -> &'static str {
        "noop"
    }

    fn ratio(&self) -> f64 {
        1.0
    }

    fn compress(&self, input: &[u8]) -> Vec<u8> {
        input.to_vec()
    }

    fn decompress(&self, input: &[u8]) -> Result<Vec<u8>, CompressionError> {
        Ok(input.to_vec())
    }
}

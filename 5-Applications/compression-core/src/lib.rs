//! Compression Core — Swappable compression backend for Research Stack apps
//!
//! Switch backends by changing the feature flag in Cargo.toml:
//!   compression-core = { path = "...", features = ["delta-gcl"] }   // current
//!   compression-core = { path = "...", features = ["noop"] }          // passthrough
//!   compression-core = { path = "...", features = ["next-gen"] }      // future

#[cfg(feature = "delta-gcl")]
pub mod delta_gcl;
#[cfg(feature = "noop")]
pub mod noop;

/// Compression backend trait — all algorithms implement this
pub trait Compressor {
    /// Compress input bytes; returns compressed bytes
    fn compress(&self, input: &[u8]) -> Vec<u8>;

    /// Decompress bytes; returns original data or error
    fn decompress(&self, input: &[u8]) -> Result<Vec<u8>, CompressionError>;

    /// Algorithm identifier for telemetry
    fn name(&self) -> &'static str;

    /// Estimated compression ratio on recent sample
    fn ratio(&self) -> f64;
}

#[derive(Debug, Clone)]
pub enum CompressionError {
    InvalidData,
    CorruptStream,
    UnsupportedVersion,
}

impl std::fmt::Display for CompressionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CompressionError::InvalidData => write!(f, "invalid compressed data"),
            CompressionError::CorruptStream => write!(f, "corrupt compression stream"),
            CompressionError::UnsupportedVersion => write!(f, "unsupported compression version"),
        }
    }
}

impl std::error::Error for CompressionError {}

/// Factory: returns the active compressor based on compile-time feature flag
pub fn default_compressor() -> Box<dyn Compressor + Send + Sync> {
    #[cfg(feature = "delta-gcl")]
    {
        Box::new(delta_gcl::DeltaGclCompressor::new())
    }
    #[cfg(feature = "noop")]
    {
        Box::new(noop::NoopCompressor)
    }
    #[cfg(feature = "next-gen")]
    {
        compile_error!("next-gen compressor not yet implemented — placeholder for future upgrade")
    }
}

//! Chunked Audio DSP - Dual-domain signal analysis platform
//! 
//! Supports both real-time streaming (PipeWire) and batch processing (FLAC).
//! Designed for extensible feature extraction and temporal analysis.

pub mod core;
pub mod io;
pub mod pipeline;

pub use core::{Config, DSPSurface, FeatureVector, WorkloadClass, StreamingConfig, AnalysisConfig};
pub use io::{Input, FeatureSink, Timestamp};
pub use pipeline::{StreamingPipeline, ChunkedPipeline};

use thiserror::Error;

#[derive(Error, Debug)]
pub enum SurfaceError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Audio decode error: {0}")]
    Decode(String),

    #[error("Realtime scheduling failed: {0}")]
    Realtime(String),

    #[error("Configuration error: {0}")]
    Config(String),
}

pub type Result<T> = std::result::Result<T, SurfaceError>;

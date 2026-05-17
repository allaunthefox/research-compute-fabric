use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub streaming: StreamingConfig,
    pub analysis: AnalysisConfig,
    pub output: OutputConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamingConfig {
    pub chunk_size: usize,
    pub hop_size: usize,
    pub sample_rate: f32,
    pub channels: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisConfig {
    pub fft_size: usize,
    pub spectral_bins: usize,
    pub history_depth: usize,
    pub enable_transient: bool,
    pub enable_information: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub compression_threshold: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputConfig {
    pub format: OutputFormat,
    pub compression: bool,
    pub threshold: f32,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum OutputFormat {
    JsonLines,
    Csv,
    Binary,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            streaming: StreamingConfig {
                chunk_size: 1024,
                hop_size: 512,
                sample_rate: 48000.0,
                channels: 2,
            },
            analysis: AnalysisConfig {
                fft_size: 2048,
                spectral_bins: 16,
                history_depth: 4,
                enable_transient: true,
                enable_information: true,
                compression_threshold: None,
            },
            output: OutputConfig {
                format: OutputFormat::JsonLines,
                compression: false,
                threshold: 0.95,
            },
        }
    }
}

impl Config {
    pub fn load(path: Option<&PathBuf>) -> Result<Self, crate::SurfaceError> {
        if let Some(p) = path {
            let content = std::fs::read_to_string(p)
                .map_err(crate::SurfaceError::Io)?;
            toml::from_str(&content)
                .map_err(|e| crate::SurfaceError::Config(e.to_string()))
        } else {
            Ok(Self::default())
        }
    }
}

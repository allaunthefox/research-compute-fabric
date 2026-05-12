use crate::core::FeatureVector;
use crate::Result;
use std::io::Write;

/// Generic output sink for feature vectors
pub trait FeatureSink {
    /// Emit a feature vector
    fn emit(&mut self, features: &FeatureVector) -> Result<()>;

    /// Optional: signal if sink is ready for backpressure handling
    fn ready(&self) -> bool { true }

    /// Flush any buffered output
    fn flush(&mut self) -> Result<()>;
}

/// Stdout JSON Lines sink
pub struct JsonlSink;

impl FeatureSink for JsonlSink {
    fn emit(&mut self, features: &FeatureVector) -> Result<()> {
        let json = serde_json::to_string(features)?;
        println!("{}", json);
        Ok(())
    }

    fn flush(&mut self) -> Result<()> {
        Ok(())
    }
}

/// CSV sink
pub struct CsvSink {
    writer: csv::Writer<std::io::Stdout>,
}

impl CsvSink {
    pub fn new() -> Result<Self> {
        let writer = csv::Writer::from_writer(std::io::stdout());
        Ok(Self { writer })
    }
}

impl FeatureSink for CsvSink {
    fn emit(&mut self, features: &FeatureVector) -> Result<()> {
        // Simplified CSV output
        let spectral_str = features.spectral.iter()
            .map(|f| f.to_string())
            .collect::<Vec<_>>()
            .join(";");
        self.writer.write_record(&[
            features.timestamp_us.to_string(),
            spectral_str,
        ])?;
        Ok(())
    }

    fn flush(&mut self) -> Result<()> {
        self.writer.flush()?;
        Ok(())
    }
}

/// Compressed binary format for large-scale storage
pub struct BinarySink {
    file: std::fs::File,
    buffer: Vec<u8>,
}

impl BinarySink {
    pub fn new(path: &std::path::Path) -> Result<Self> {
        let file = std::fs::File::create(path)?;
        Ok(Self {
            file,
            buffer: Vec::with_capacity(4096),
        })
    }
}

impl FeatureSink for BinarySink {
    fn emit(&mut self, features: &FeatureVector) -> Result<()> {
        use std::io::Write;

        self.buffer.clear();
        self.buffer.extend_from_slice(&features.timestamp_us.to_le_bytes());

        // Spectral data (compact f32 array)
        for &val in features.spectral.iter() {
            self.buffer.extend_from_slice(&val.to_le_bytes());
        }

        // Transient and info data
        for &val in features.transient.iter() {
            self.buffer.extend_from_slice(&val.to_le_bytes());
        }
        for &val in features.information.iter() {
            self.buffer.extend_from_slice(&val.to_le_bytes());
        }

        self.file.write_all(&self.buffer)?;
        Ok(())
    }

    fn flush(&mut self) -> Result<()> {
        self.file.flush()?;
        Ok(())
    }
}

// Placeholder Output trait for future extensibility
pub trait Output {}

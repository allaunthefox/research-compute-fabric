use crate::core::{DSPSurface, StreamingConfig};
use crate::io::{Input, FeatureSink};
use crate::Result;

pub struct ChunkedPipeline;

impl ChunkedPipeline {
    /// Process single file with optional progress tracking
    pub fn process_file<I: Input, S: FeatureSink>(
        input: &mut I,
        sink: &mut S,
        dsp: &mut DSPSurface,
        config: &StreamingConfig,
        total_samples: Option<u64>,
    ) -> Result<()> {
        let mut chunk_buffer = vec![0.0f32; config.chunk_size];
        let mut processed = 0u64;

        loop {
            match input.next_chunk(&mut chunk_buffer)? {
                Some((n, timestamp)) => {
                    // Zero-pad final chunk if needed
                    if n < config.chunk_size {
                        chunk_buffer[n..].fill(0.0);
                    }

                    let features = dsp.process(&chunk_buffer, timestamp);
                    sink.emit(&features)?;

                    processed += n as u64;
                }
                None => break,
            }
        }

        sink.flush()?;
        Ok(())
    }

    /// Batch process multiple files in parallel using Rayon
    pub fn batch_process(
        files: &[std::path::PathBuf],
        config: &crate::core::Config,
        output_dir: &std::path::Path,
    ) -> Result<()> {
        use rayon::prelude::*;
        use crate::io::{FlacInput, BinarySink};

        std::fs::create_dir_all(output_dir)?;

        files.par_iter().try_for_each(|file| -> Result<()> {
            let mut input = FlacInput::open(file)?;
            let output_path = output_dir.join(
                file.file_stem().unwrap_or_default()
            ).with_extension("bin");

            let mut sink = BinarySink::new(&output_path)?;
            let mut dsp = DSPSurface::new(config.analysis.clone());

            Self::process_file(&mut input, &mut sink, &mut dsp, &config.streaming, None)?;
            Ok(())
        })
    }
}

use crate::core::{DSPSurface, StreamingConfig};
use crate::io::{Input, FeatureSink, Timestamp};
use crate::Result;

pub struct StreamingPipeline<I: Input, S: FeatureSink> {
    input: I,
    sink: S,
    dsp: DSPSurface,
    config: StreamingConfig,
    overlap_buffer: Vec<f32>,
}

impl<I: Input, S: FeatureSink> StreamingPipeline<I, S> {
    pub fn new(input: I, sink: S, dsp: DSPSurface, config: StreamingConfig) -> Self {
        let overlap_size = config.chunk_size.saturating_sub(config.hop_size);
        Self {
            input,
            sink,
            dsp,
            config,
            overlap_buffer: vec![0.0f32; overlap_size],
        }
    }

    pub fn run(mut self) -> Result<()> {
        let mut chunk_buffer = vec![0.0f32; self.config.chunk_size];
        let mut total_samples = 0u64;

        loop {
            // Fill second half of buffer (first half has overlap from previous)
            let fill_start = self.config.hop_size;
            match self.input.next_chunk(&mut chunk_buffer[fill_start..])? {
                Some((n, timestamp)) => {
                    if n == 0 { 
                        std::thread::sleep(std::time::Duration::from_millis(1));
                        continue; 
                    }

                    // Copy overlap from previous chunk to start
                    chunk_buffer[..self.config.hop_size].copy_from_slice(&self.overlap_buffer);

                    // Process full chunk
                    let features = self.dsp.process(&chunk_buffer, timestamp);
                    self.sink.emit(&features)?;

                    // Save tail for next overlap
                    let overlap_start = self.config.chunk_size - self.config.hop_size;
                    self.overlap_buffer.copy_from_slice(&chunk_buffer[overlap_start..overlap_start + self.config.hop_size]);

                    total_samples += n as u64;
                }
                None => break, // Stream ended
            }
        }

        self.sink.flush()?;
        Ok(())
    }
}

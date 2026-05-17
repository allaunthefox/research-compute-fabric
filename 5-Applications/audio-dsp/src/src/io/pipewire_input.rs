use crate::io::{Input, Timestamp, Result};
use std::sync::mpsc::{channel, Receiver};

pub struct PipeWireInput {
    sample_rate: f32,
    channels: usize,
    receiver: Receiver<(Vec<f32>, Timestamp)>,
}

impl PipeWireInput {
    pub fn new(name: &str, config: &crate::core::Config) -> Result<Self> {
        let (tx, rx) = channel();

        // TODO: Initialize PipeWire stream here in production
        // For now, this is a stub that would spawn a PipeWire thread
        // feeding the channel

        Ok(Self {
            sample_rate: config.streaming.sample_rate,
            channels: config.streaming.channels,
            receiver: rx,
        })
    }
}

impl Input for PipeWireInput {
    fn next_chunk(&mut self, buf: &mut [f32]) -> Result<Option<(usize, Timestamp)>> {
        match self.receiver.try_recv() {
            Ok((samples, ts)) => {
                let n = samples.len().min(buf.len());
                buf[..n].copy_from_slice(&samples[..n]);
                Ok(Some((n, ts)))
            }
            Err(std::sync::mpsc::TryRecvError::Empty) => Ok(Some((0, 0))),
            Err(std::sync::mpsc::TryRecvError::Disconnected) => Ok(None),
        }
    }

    fn sample_rate(&self) -> f32 { self.sample_rate }
    fn channels(&self) -> usize { self.channels }
}

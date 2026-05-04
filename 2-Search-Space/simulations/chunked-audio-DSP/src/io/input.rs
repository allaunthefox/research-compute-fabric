use crate::Result;

/// Timestamp in microseconds for precise alignment
pub type Timestamp = u64;

/// Generic input trait for both real-time and batch sources
pub trait Input {
    /// Returns (samples interleaved, timestamp_us)
    /// Returns None when stream ends (batch) or disconnects (real-time)
    fn next_chunk(&mut self, buf: &mut [f32]) -> Result<Option<(usize, Timestamp)>>;

    fn sample_rate(&self) -> f32;
    fn channels(&self) -> usize;
}

pub mod teleport;
pub mod moe;
pub mod kanban;
pub mod interface;
pub mod tick_cpu;

pub use teleport::*;
pub use moe::*;
pub use kanban::*;
pub use interface::*;

/// Deterministic Strict Typing System
/// Ensures type safety and deterministic behavior for BF16 operations
pub mod deterministic {
    use super::*;

    /// Type-safe BF16 wrapper with deterministic operations
    #[derive(Debug, Clone, Copy, PartialEq)]
    pub struct DeterministicBF16 {
        value: BF16,
    }

    impl DeterministicBF16 {
        /// Create a new deterministic BF16 value
        pub fn new(value: f32) -> Self {
            Self {
                value: BF16::from_f32(value),
            }
        }

        /// Add two deterministic BF16 values with overflow checking
        pub fn add(&self, other: Self) -> Result<Self, &'static str> {
            let result = self.value.to_f32() + other.value.to_f32();
            if result.is_finite() {
                Ok(Self::new(result))
            } else {
                Err("Overflow in BF16 addition")
            }
        }

        /// Multiply two deterministic BF16 values with overflow checking
        pub fn multiply(&self, other: Self) -> Result<Self, &'static str> {
            let result = self.value.to_f32() * other.value.to_f32();
            if result.is_finite() {
                Ok(Self::new(result))
            } else {
                Err("Overflow in BF16 multiplication")
            }
        }

        /// Get the underlying BF16 value
        pub fn value(&self) -> BF16 {
            self.value
        }

        /// Get the f32 representation
        pub fn to_f32(&self) -> f32 {
            self.value.to_f32()
        }
    }

    /// Type-safe compression result with deterministic guarantees
    #[derive(Debug, Clone)]
    pub struct DeterministicCompressionResult {
        pub original_size: usize,
        pub compressed_size: usize,
        pub compression_ratio: f32,
        pub deterministic_hash: String,
    }

    impl DeterministicCompressionResult {
        /// Create a new deterministic compression result
        pub fn new(original_size: usize, compressed_size: usize) -> Self {
            let compression_ratio = original_size as f32 / compressed_size as f32;
            let deterministic_hash = blake3::hash(
                format!("{}:{}", original_size, compressed_size).as_bytes()
            ).to_hex().to_string();

            Self {
                original_size,
                compressed_size,
                compression_ratio,
                deterministic_hash,
            }
        }

        /// Verify the compression result is valid
        pub fn is_valid(&self) -> bool {
            self.original_size > 0 && 
            self.compressed_size > 0 && 
            self.compression_ratio > 0.0 &&
            !self.deterministic_hash.is_empty()
        }
    }
}

/// Performance optimization utilities
pub mod performance {
    use std::time::Instant;
    use std::sync::atomic::{AtomicU64, Ordering};

    /// High-precision performance timer
    pub struct PerformanceTimer {
        start: Instant,
        name: String,
    }

    impl PerformanceTimer {
        /// Create a new performance timer
        pub fn new(name: &str) -> Self {
            Self {
                start: Instant::now(),
                name: name.to_string(),
            }
        }

        /// Stop the timer and return elapsed time in milliseconds
        pub fn stop(self) -> f64 {
            let elapsed = self.start.elapsed();
            let ms = elapsed.as_secs_f64() * 1000.0;
            println!("⏱️ {} completed in {:.2}ms", self.name, ms);
            ms
        }
    }

    /// Performance counter for tracking operations
    pub struct PerformanceCounter {
        count: AtomicU64,
        total_time: AtomicU64,
    }

    impl PerformanceCounter {
        /// Create a new performance counter
        pub fn new() -> Self {
            Self {
                count: AtomicU64::new(0),
                total_time: AtomicU64::new(0),
            }
        }

        /// Record an operation with its duration in nanoseconds
        pub fn record(&self, duration_ns: u64) {
            self.count.fetch_add(1, Ordering::Relaxed);
            self.total_time.fetch_add(duration_ns, Ordering::Relaxed);
        }

        /// Get the average operation time in milliseconds
        pub fn avg_time_ms(&self) -> f64 {
            let count = self.count.load(Ordering::Relaxed);
            let total = self.total_time.load(Ordering::Relaxed);
            if count > 0 {
                (total as f64 / count as f64) / 1_000_000.0
            } else {
                0.0
            }
        }

        /// Get the total operation count
        pub fn count(&self) -> u64 {
            self.count.load(Ordering::Relaxed)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio;

    #[tokio::test]
    async fn test_teleport_compression() {
        let teleport = TeleportCompressor::new();
        let data = "test data for compression".to_string();
        
        let compressed = teleport.compress_semantic(&data).await.unwrap();
        let decompressed = teleport.decompress(&compressed).await.unwrap();
        
        assert_eq!(data, decompressed);
    }

    #[tokio::test]
    async fn test_moe_routing() {
        let moe = MixtureOfExperts::new();
        let input = "test input for expert routing".to_string();
        
        let result = moe.route(&input).await.unwrap();
        assert!(!result.is_empty());
    }

    #[test]
    fn test_deterministic_bf16() {
        let a = deterministic::DeterministicBF16::new(1.5);
        let b = deterministic::DeterministicBF16::new(2.5);
        
        let sum = a.add(b).unwrap();
        assert_eq!(sum.to_f32(), 4.0);
        
        let product = a.multiply(b).unwrap();
        assert_eq!(product.to_f32(), 3.75);
    }

    #[test]
    fn test_deterministic_compression_result() {
        let result = deterministic::DeterministicCompressionResult::new(100, 25);
        
        assert_eq!(result.original_size, 100);
        assert_eq!(result.compressed_size, 25);
        assert_eq!(result.compression_ratio, 4.0);
        assert!(result.is_valid());
    }
}

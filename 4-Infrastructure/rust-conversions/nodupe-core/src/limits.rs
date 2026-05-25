//! Resource limit enforcement.
//!
//! Provides memory usage monitoring, file handle tracking, rate limiting,
//! size limits, count limits, and time-limited operations.  This is the
//! Rust equivalent of the Python `limits.py` module.

use std::sync::{Arc, Condvar, Mutex};
use std::time::{Duration, Instant};

use crate::errors::{Error, Result};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/// Default number of file handles when a system-provided limit is unavailable.
pub const DEFAULT_FILE_HANDLE_LIMIT: usize = 1024;

// ---------------------------------------------------------------------------
// Memory and file-descriptor helpers
// ---------------------------------------------------------------------------

/// Read a single-line value from `/proc/self/status` on Linux.
///
/// Returns `None` when the file is unavailable or the key is not found.
fn proc_status_value(key: &str) -> Option<u64> {
    let content = std::fs::read_to_string("/proc/self/status").ok()?;
    for line in content.lines() {
        if let Some(rest) = line.strip_prefix(key) {
            if let Some(val_str) = rest.trim().strip_suffix(" kB").or_else(|| Some(rest.trim())) {
                let val: u64 = val_str.parse().ok()?;
                return Some(val);
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// Limits
// ---------------------------------------------------------------------------

/// Static helpers for resource limit enforcement.
pub struct Limits;

impl Limits {
    /// Get current process memory usage in bytes.
    ///
    /// Attempts several platform-specific strategies in order:
    /// 1. `getrusage` on Unix (macOS reports bytes, Linux reports KiB).
    /// 2. `/proc/self/status` on Linux.
    /// 3. Returns 0 as a fallback.
    pub fn get_memory_usage() -> Result<u64> {
        #[cfg(target_os = "macos")]
        {
            if let Ok(usage) = get_rusage() {
                // macOS: ru_maxrss is in bytes.
                return Ok(usage);
            }
        }

        #[cfg(target_os = "linux")]
        {
            // Try /proc/self/status first (more accurate resident set).
            if let Some(vm_rss_kb) = proc_status_value("VmRSS:") {
                return Ok(vm_rss_kb * 1024);
            }
            // Fall back to getrusage (ru_maxrss is in KiB on Linux).
            if let Ok(usage_kb) = get_rusage() {
                return Ok(usage_kb * 1024);
            }
        }

        // Non-Linux non-macOS fallback: try getrusage anyway.
        #[cfg(not(any(target_os = "linux", target_os = "macos")))]
        {
            if let Ok(usage) = get_rusage() {
                return Ok(usage);
            }
        }

        Ok(0)
    }

    /// Check if current memory usage is under `max_bytes`.
    pub fn check_memory_limit(max_bytes: u64) -> Result<bool> {
        let current = Self::get_memory_usage()?;
        if current > max_bytes {
            return Err(Error::limit(format!(
                "Memory usage {current} bytes exceeds limit {max_bytes} bytes"
            )));
        }
        Ok(true)
    }

    /// Get the number of open file descriptors.
    pub fn get_open_file_count() -> Result<usize> {
        #[cfg(target_os = "linux")]
        {
            let fd_path = std::path::Path::new("/proc/self/fd");
            if fd_path.exists() {
                let count = std::fs::read_dir(fd_path)
                    .map_err(|e| Error::limit(format!("Failed to read fd directory: {e}")))?
                    .count();
                return Ok(count);
            }
        }

        // Fallback: attempt getrlimit (available on most Unixes).
        #[cfg(unix)]
        {
            let (_, hard) = rlimit_nofile();
            return Ok(std::cmp::min(DEFAULT_FILE_HANDLE_LIMIT, hard));
        }

        // Final fallback.
        Ok(0)
    }

    /// Check file handle limits.
    ///
    /// When `max_handles` is `None`, the system soft limit is used.
    pub fn check_file_handles(max_handles: Option<usize>) -> Result<bool> {
        let limit = max_handles.unwrap_or_else(|| {
            #[cfg(unix)]
            {
                let (soft, _) = rlimit_nofile();
                soft
            }
            #[cfg(not(unix))]
            {
                DEFAULT_FILE_HANDLE_LIMIT
            }
        });

        let current = Self::get_open_file_count()?;
        if current > 0 && current >= limit {
            return Err(Error::limit(format!(
                "Open file handles {current} exceeds limit {limit}"
            )));
        }
        Ok(true)
    }

    /// Check if a file's size is under `max_bytes`.
    pub fn check_file_size(path: impl AsRef<std::path::Path>, max_bytes: u64) -> Result<bool> {
        let path = path.as_ref();
        if !path.exists() {
            return Ok(true);
        }
        let size = std::fs::metadata(path)
            .map_err(|e| Error::limit(format!("Failed to stat {path:?}: {e}")))?
            .len();
        if size > max_bytes {
            return Err(Error::limit(format!(
                "File size {size} bytes exceeds limit {max_bytes} bytes: {path:?}"
            )));
        }
        Ok(true)
    }

    /// Check if a byte slice's length is under `max_bytes`.
    pub fn check_data_size(data: &[u8], max_bytes: u64) -> Result<bool> {
        let size = data.len() as u64;
        if size > max_bytes {
            return Err(Error::limit(format!(
                "Data size {size} bytes exceeds limit {max_bytes} bytes"
            )));
        }
        Ok(true)
    }

    /// Execute a closure with a time limit.
    ///
    /// After the closure returns (or panics), the elapsed wall-clock time
    /// is compared against `max_seconds`.  This is *not* a hard deadline —
    /// it checks after the operation completes.
    pub fn time_limit<T>(
        max_seconds: f64,
        f: impl FnOnce() -> T,
    ) -> std::result::Result<T, Error> {
        let start = Instant::now();
        let result = f();
        let elapsed = start.elapsed();
        if elapsed.as_secs_f64() > max_seconds {
            return Err(Error::limit(format!(
                "Operation took {elapsed:.2}s, exceeding limit of {max_seconds}s"
            )));
        }
        Ok(result)
    }
}

// ---------------------------------------------------------------------------
// Unix helpers
// ---------------------------------------------------------------------------

#[cfg(unix)]
fn get_rusage() -> std::io::Result<i64> {
    // We use libc directly because std doesn't expose getrusage.
    let mut usage: libc::rusage = unsafe { std::mem::zeroed() };
    let ret = unsafe { libc::getrusage(libc::RUSAGE_SELF, &mut usage) };
    if ret != 0 {
        return Err(std::io::Error::last_os_error());
    }
    Ok(usage.ru_maxrss)
}

#[cfg(unix)]
fn rlimit_nofile() -> (usize, usize) {
    let mut soft: libc::rlim_t = 0;
    let mut hard: libc::rlim_t = 0;
    let ret = unsafe { libc::getrlimit(libc::RLIMIT_NOFILE, &mut soft, &mut hard) };
    if ret != 0 {
        return (DEFAULT_FILE_HANDLE_LIMIT, DEFAULT_FILE_HANDLE_LIMIT);
    }
    (soft as usize, hard as usize)
}

// Non-Unix platforms get stubs.
#[cfg(not(unix))]
fn get_rusage() -> std::io::Result<i64> {
    Err(std::io::Error::new(
        std::io::ErrorKind::Unsupported,
        "getrusage not available on this platform",
    ))
}

#[cfg(not(unix))]
fn rlimit_nofile() -> (usize, usize) {
    (DEFAULT_FILE_HANDLE_LIMIT, DEFAULT_FILE_HANDLE_LIMIT)
}

// ---------------------------------------------------------------------------
// RateLimiter
// ---------------------------------------------------------------------------

/// Token-bucket rate limiter.
///
/// Uses a [`Mutex`] and [`Condvar`] for efficient waiting.
pub struct RateLimiter {
    rate: f64,              // tokens per second
    burst: f64,             // maximum bucket capacity
    state: Mutex<BucketState>,
    cvar: Condvar,
}

struct BucketState {
    tokens: f64,
    last_update: Instant,
}

impl RateLimiter {
    /// Create a new rate limiter.
    ///
    /// - `rate`: Tokens per second.
    /// - `burst`: Maximum burst size (bucket capacity).  Defaults to 1.
    pub fn new(rate: f64, burst: f64) -> Self {
        Self {
            rate,
            burst,
            state: Mutex::new(BucketState {
                tokens: burst,
                last_update: Instant::now(),
            }),
            cvar: Condvar::new(),
        }
    }

    /// Refill tokens based on elapsed time.
    fn refill(state: &mut BucketState, rate: f64, burst: f64) {
        let elapsed = state.last_update.elapsed().as_secs_f64();
        state.tokens = (state.tokens + elapsed * rate).min(burst);
        state.last_update = Instant::now();
    }

    /// Try to consume `count` tokens without blocking.
    ///
    /// Returns `true` when tokens were consumed, `false` when the bucket is empty.
    pub fn try_consume(&self, count: f64) -> bool {
        let mut state = self.state.lock().unwrap();
        Self::refill(&mut state, self.rate, self.burst);
        if state.tokens >= count {
            state.tokens -= count;
            true
        } else {
            false
        }
    }

    /// Consume `count` tokens, blocking until they are available (or timeout).
    ///
    /// Returns `Ok(true)` when tokens were consumed.  Returns
    /// `Err(Error::Limit(…))` on timeout.
    pub fn consume(&self, count: f64, timeout: Option<Duration>) -> Result<bool> {
        let start = Instant::now();
        let mut state = self.state.lock().unwrap();
        loop {
            Self::refill(&mut state, self.rate, self.burst);
            if state.tokens >= count {
                state.tokens -= count;
                return Ok(true);
            }

            // Check timeout.
            if let Some(t) = timeout {
                let elapsed = start.elapsed();
                if elapsed >= t {
                    return Err(Error::limit(format!(
                        "Rate limit wait timeout after {elapsed:.2}s"
                    )));
                }
                let remaining = t - elapsed;
                let (state2, _) = self
                    .cvar
                    .wait_timeout(state, remaining)
                    .unwrap();
                state = state2;
            } else {
                let (state2, _) = self.cvar.wait(state).unwrap();
                state = state2;
            }
            // Loop back and check again.
        }
    }

    /// Notify waiting threads that tokens may be available.
    pub fn notify_waiters(&self) {
        self.cvar.notify_all();
    }
}

impl Default for RateLimiter {
    fn default() -> Self {
        Self::new(10.0, 5.0)
    }
}

// ---------------------------------------------------------------------------
// SizeLimit
// ---------------------------------------------------------------------------

/// Tracks cumulative byte usage against a maximum.
use std::sync::Mutex as StdMutex;

pub struct SizeLimit {
    max_bytes: u64,
    current: StdMutex<u64>,
}

impl SizeLimit {
    /// Create a new size limit tracker.
    pub fn new(max_bytes: u64) -> Self {
        Self {
            max_bytes,
            current: StdMutex::new(0),
        }
    }

    /// Try to add `bytes` to the cumulative count.
    ///
    /// Returns an error when the addition would exceed the limit.
    pub fn add(&self, bytes: u64) -> Result<bool> {
        let mut cur = self.current.lock().unwrap();
        let new_total = *cur + bytes;
        if new_total > self.max_bytes {
            return Err(Error::limit(format!(
                "Adding {bytes} bytes would exceed limit {} bytes (current: {cur})",
                self.max_bytes
            )));
        }
        *cur = new_total;
        Ok(true)
    }

    /// Reset the cumulative count to zero.
    pub fn reset(&self) {
        *self.current.lock().unwrap() = 0;
    }

    /// Remaining capacity before the limit is reached.
    pub fn remaining(&self) -> u64 {
        self.max_bytes.saturating_sub(*self.current.lock().unwrap())
    }

    /// Currently used bytes.
    pub fn used(&self) -> u64 {
        *self.current.lock().unwrap()
    }

    /// The configured maximum.
    pub fn max(&self) -> u64 {
        self.max_bytes
    }
}

// ---------------------------------------------------------------------------
// CountLimit
// ---------------------------------------------------------------------------

/// Tracks a cumulative count against a maximum.
pub struct CountLimit {
    max_count: u64,
    current: StdMutex<u64>,
}

impl CountLimit {
    /// Create a new count limit tracker.
    pub fn new(max_count: u64) -> Self {
        Self {
            max_count,
            current: StdMutex::new(0),
        }
    }

    /// Increment by `amount`.
    ///
    /// Returns an error when the increment would exceed the limit.
    pub fn increment(&self, amount: u64) -> Result<bool> {
        let mut cur = self.current.lock().unwrap();
        let new_count = *cur + amount;
        if new_count > self.max_count {
            return Err(Error::limit(format!(
                "Incrementing by {amount} would exceed limit {} (current: {cur})",
                self.max_count
            )));
        }
        *cur = new_count;
        Ok(true)
    }

    /// Reset the count to zero.
    pub fn reset(&self) {
        *self.current.lock().unwrap() = 0;
    }

    /// Remaining capacity before the limit is reached.
    pub fn remaining(&self) -> u64 {
        self.max_count.saturating_sub(*self.current.lock().unwrap())
    }

    /// Currently used count.
    pub fn used(&self) -> u64 {
        *self.current.lock().unwrap()
    }

    /// The configured maximum.
    pub fn max(&self) -> u64 {
        self.max_count
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;
    use std::time::Duration;

    // ------------------------------------------------------------------
    // Limits static methods
    // ------------------------------------------------------------------

    #[test]
    fn get_memory_usage_returns_value() {
        let usage = Limits::get_memory_usage().unwrap();
        // On any reasonable system this should be > 0, but we accept 0
        // on unsupported platforms.
        assert!(usage < 1_000_000_000_000, "memory usage seems absurd: {usage}");
    }

    #[test]
    fn check_memory_under_limit() {
        // 1 exabyte should be enough for anyone.
        let ok = Limits::check_memory_limit(1_000_000_000_000_000_000).unwrap();
        assert!(ok);
    }

    #[test]
    fn check_memory_over_limit_fails() {
        let err = Limits::check_memory_limit(1).unwrap_err();
        assert!(err.to_string().contains("Memory usage"));
    }

    #[test]
    fn get_open_file_count_returns_value() {
        let count = Limits::get_open_file_count().unwrap();
        // At least stdin/stdout/stderr.
        assert!(count >= 0);
    }

    #[test]
    fn check_file_handles_with_no_limit() {
        // Passing None should use the system limit which is >> current.
        let ok = Limits::check_file_handles(None).unwrap();
        assert!(ok);
    }

    #[test]
    fn check_file_handles_over_limit() {
        // 0 is always exceeded.
        let err = Limits::check_file_handles(Some(0)).unwrap_err();
        assert!(err.to_string().contains("exceeds"));
    }

    #[test]
    fn check_file_size_nonexistent() {
        let path = std::path::Path::new("/tmp/__nodupe_test_nonexistent__");
        let ok = Limits::check_file_size(path, 100).unwrap();
        assert!(ok);
    }

    #[test]
    fn check_file_size_under_limit() {
        let dir = std::env::temp_dir();
        let path = dir.join("__nodupe_test_size_under__");
        std::fs::write(&path, b"hello").unwrap();
        let ok = Limits::check_file_size(&path, 1_000_000).unwrap();
        assert!(ok);
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn check_file_size_over_limit() {
        let dir = std::env::temp_dir();
        let path = dir.join("__nodupe_test_size_over__");
        std::fs::write(&path, b"hello").unwrap();
        let err = Limits::check_file_size(&path, 1).unwrap_err();
        assert!(err.to_string().contains("exceeds limit"));
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn check_data_size_under() {
        let data = b"small";
        assert!(Limits::check_data_size(data, 1_000_000).unwrap());
    }

    #[test]
    fn check_data_size_over() {
        let data = b"big data";
        let err = Limits::check_data_size(data, 3).unwrap_err();
        assert!(err.to_string().contains("exceeds limit"));
    }

    #[test]
    fn time_limit_within_bound() {
        let result = Limits::time_limit(10.0, || 42).unwrap();
        assert_eq!(result, 42);
    }

    #[test]
    fn time_limit_exceeded() {
        let err = Limits::time_limit(0.001, || {
            thread::sleep(Duration::from_millis(50));
            99
        })
        .unwrap_err();
        assert!(err.to_string().contains("exceeding limit"));
    }

    // ------------------------------------------------------------------
    // RateLimiter
    // ------------------------------------------------------------------

    #[test]
    fn rate_limiter_try_consume_ok() {
        let limiter = RateLimiter::new(100.0, 10.0);
        assert!(limiter.try_consume(1.0));
    }

    #[test]
    fn rate_limiter_try_consume_exhausted() {
        let limiter = RateLimiter::new(1.0, 1.0);
        // Consume the only token.
        assert!(limiter.try_consume(1.0));
        // Should be empty now.
        assert!(!limiter.try_consume(1.0));
    }

    #[test]
    fn rate_limiter_consume_with_timeout() {
        let limiter = RateLimiter::new(1.0, 1.0);
        // Empty the bucket.
        assert!(limiter.try_consume(1.0));
        // Should timeout quickly.
        let err = limiter
            .consume(1.0, Some(Duration::from_millis(10)))
            .unwrap_err();
        assert!(err.to_string().contains("timeout"));
    }

    #[test]
    fn rate_limiter_refills() {
        let limiter = RateLimiter::new(100.0, 10.0);
        assert!(limiter.try_consume(10.0));
        assert!(!limiter.try_consume(1.0));
        // Wait for refill.
        thread::sleep(Duration::from_millis(50));
        assert!(limiter.try_consume(1.0));
    }

    #[test]
    fn rate_limiter_default() {
        let limiter = RateLimiter::default();
        assert!(limiter.try_consume(1.0));
    }

    // ------------------------------------------------------------------
    // SizeLimit
    // ------------------------------------------------------------------

    #[test]
    fn size_limit_basic() {
        let sl = SizeLimit::new(100);
        assert_eq!(sl.remaining(), 100);
        assert!(sl.add(30).unwrap());
        assert_eq!(sl.used(), 30);
        assert_eq!(sl.remaining(), 70);
    }

    #[test]
    fn size_limit_exceeded() {
        let sl = SizeLimit::new(10);
        let err = sl.add(20).unwrap_err();
        assert!(err.to_string().contains("would exceed"));
    }

    #[test]
    fn size_limit_reset() {
        let sl = SizeLimit::new(100);
        sl.add(80).unwrap();
        assert_eq!(sl.used(), 80);
        sl.reset();
        assert_eq!(sl.used(), 0);
        assert_eq!(sl.remaining(), 100);
    }

    #[test]
    fn size_limit_at_boundary() {
        let sl = SizeLimit::new(100);
        assert!(sl.add(100).unwrap());
        assert_eq!(sl.remaining(), 0);
    }

    #[test]
    fn size_limit_max() {
        let sl = SizeLimit::new(42);
        assert_eq!(sl.max(), 42);
    }

    // ------------------------------------------------------------------
    // CountLimit
    // ------------------------------------------------------------------

    #[test]
    fn count_limit_basic() {
        let cl = CountLimit::new(5);
        assert_eq!(cl.remaining(), 5);
        assert!(cl.increment(1).unwrap());
        assert_eq!(cl.used(), 1);
        assert_eq!(cl.remaining(), 4);
    }

    #[test]
    fn count_limit_exceeded() {
        let cl = CountLimit::new(2);
        cl.increment(2).unwrap();
        let err = cl.increment(1).unwrap_err();
        assert!(err.to_string().contains("would exceed"));
    }

    #[test]
    fn count_limit_reset() {
        let cl = CountLimit::new(10);
        cl.increment(7).unwrap();
        assert_eq!(cl.used(), 7);
        cl.reset();
        assert_eq!(cl.used(), 0);
    }

    #[test]
    fn count_limit_remaining() {
        let cl = CountLimit::new(3);
        cl.increment(2).unwrap();
        assert_eq!(cl.remaining(), 1);
    }

    #[test]
    fn count_limit_max() {
        let cl = CountLimit::new(7);
        assert_eq!(cl.max(), 7);
    }

    // ------------------------------------------------------------------
    // Thread safety smoke tests
    // ------------------------------------------------------------------

    #[test]
    fn size_limit_thread_safety() {
        let sl = Arc::new(SizeLimit::new(1_000_000));
        let mut handles = vec![];
        for _ in 0..10 {
            let sl = Arc::clone(&sl);
            handles.push(thread::spawn(move || {
                for _ in 0..100 {
                    sl.add(1).unwrap();
                }
            }));
        }
        for h in handles {
            h.join().unwrap();
        }
        assert_eq!(sl.used(), 1000);
    }

    #[test]
    fn count_limit_thread_safety() {
        let cl = Arc::new(CountLimit::new(10_000));
        let mut handles = vec![];
        for _ in 0..10 {
            let cl = Arc::clone(&cl);
            handles.push(thread::spawn(move || {
                for _ in 0..500 {
                    cl.increment(1).unwrap();
                }
            }));
        }
        for h in handles {
            h.join().unwrap();
        }
        assert_eq!(cl.used(), 5000);
    }
}

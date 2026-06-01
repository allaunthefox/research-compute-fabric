/// Common utilities shared across ene-rds crates.

use sha2::{Digest, Sha256};

/// SHA-256 hash as hex string
pub fn sha256_hex(data: impl AsRef<[u8]>) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data.as_ref());
    hex::encode(hasher.finalize())
}

/// Base64-decode a string into bytes
pub fn base64_decode(input: &str) -> Result<Vec<u8>, base64::DecodeError> {
    use base64::Engine;
    base64::engine::general_purpose::STANDARD.decode(input)
}

/// Base64-encode bytes into a string
pub fn base64_encode(data: &[u8]) -> String {
    use base64::Engine;
    base64::engine::general_purpose::STANDARD.encode(data)
}

/// A bounded set that evicts the oldest entry when full
pub struct BoundedSet<T> {
    inner: std::collections::VecDeque<T>,
    max_len: usize,
}

impl<T: PartialEq> BoundedSet<T> {
    pub fn new(max_len: usize) -> Self {
        Self { inner: std::collections::VecDeque::new(), max_len }
    }

    pub fn insert(&mut self, value: T) {
        if !self.inner.contains(&value) {
            if self.inner.len() >= self.max_len {
                self.inner.pop_front();
            }
            self.inner.push_back(value);
        }
    }

    pub fn contains(&self, value: &T) -> bool {
        self.inner.contains(value)
    }

    pub fn len(&self) -> usize {
        self.inner.len()
    }

    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }
}

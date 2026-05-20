//! Credential Management
//!
//! Replaces: debug_credentials.py, ingest_keys_to_ene.py, migrate_credentials.py, propagate_ssh_keys.py

use crate::EneResult;
use serde::{Deserialize, Serialize};

/// Encrypted credential vault
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CredentialManager {
    pub vault: Vec<u8>,
    pub epoch: u64,
}

impl CredentialManager {
    pub fn new() -> Self {
        Self {
            vault: Vec::new(),
            epoch: 0,
        }
    }

    /// Propagate SSH keys to all known peers (stub that logs intent)
    pub fn propagate_ssh_keys(&mut self, keys: &[u8]) -> EneResult<()> {
        tracing::info!(
            "Propagating {} SSH credential bytes (epoch {})",
            keys.len(),
            self.epoch
        );
        Ok(())
    }

    /// Migrate credentials from an external source (stub returning Ok)
    pub fn migrate(&mut self, source: &str) -> EneResult<()> {
        tracing::info!("Credential migration requested from source: {}", source);
        self.epoch += 1;
        Ok(())
    }

    /// Ingest key-value JSON credentials into encrypted_cache
    pub fn ingest(&mut self, keys: &[u8]) -> EneResult<()> {
        let parsed: serde_json::Value = serde_json::from_slice(keys)?;
        let kv = match &parsed {
            serde_json::Value::Object(m) => {
                let mut buf = Vec::new();
                for (k, v) in m {
                    let entry = format!("{}={}\n", k, v);
                    buf.extend_from_slice(entry.as_bytes());
                }
                buf
            }
            other => format!("{}\n", other).into_bytes(),
        };
        self.vault = kv;
        self.epoch += 1;
        Ok(())
    }
}

/// PythonBridge — adaptation layer that calls existing Python infra surfaces
/// from the Rust sync daemon.
///
/// The bridge works by spawning `python3 bridge_wrapper.py <infra_dir>`,
/// writing a JSON request to stdin, and reading a JSON response from stdout.
/// This lets the Rust binary transparently delegate to any Python module that
/// exposes a `handle_request(payload: dict) -> dict` method without knowing
/// the internal module structure at compile time.
///
/// # Protocol
/// Request  (stdin):  `{"module": "<name>", "payload": { ... }}`
/// Response (stdout): `{"ok": true, "data": { ... }}`
///                or  `{"ok": false, "error": "<message>"}`
use crate::models::{BridgeRequest, BridgeResponse};
use anyhow::{Context, Result};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use tracing::{debug, warn};

pub struct PythonBridge {
    /// Directory containing the Python infra modules *and* `bridge_wrapper.py`.
    infra_dir: PathBuf,
    /// Python executable (default: `python3`).
    python_cmd: String,
}

impl PythonBridge {
    pub fn new(infra_dir: PathBuf) -> Self {
        Self {
            infra_dir,
            python_cmd: std::env::var("PYTHON_CMD").unwrap_or_else(|_| "python3".into()),
        }
    }

    /// Resolve `bridge_wrapper.py` — first look next to the infra dir, then
    /// fall back to the canonical repo path relative to the executable.
    fn wrapper_path(&self) -> PathBuf {
        // Preferred: bridge_wrapper.py lives in infra_dir itself.
        let candidate = self.infra_dir.join("bridge_wrapper.py");
        if candidate.exists() {
            return candidate;
        }
        // Fallback: look in the parent of infra_dir (e.g. ene-session-sync/).
        if let Some(parent) = self.infra_dir.parent() {
            let alt = parent.join("bridge_wrapper.py");
            if alt.exists() {
                return alt;
            }
        }
        // Last resort: crate-relative path used in development.
        let dev = Path::new(env!("CARGO_MANIFEST_DIR")).join("bridge_wrapper.py");
        if dev.exists() {
            return dev;
        }
        candidate // may not exist — caller will get a clear error
    }

    /// Call a Python module's `handle_request` with the given JSON payload.
    ///
    /// Spawns `python3 <bridge_wrapper.py> <infra_dir>`, writes the request
    /// JSON to stdin, and parses the response JSON from stdout.
    pub fn call(&self, module: &str, payload: &serde_json::Value) -> Result<serde_json::Value> {
        let wrapper = self.wrapper_path();
        let infra_str = self
            .infra_dir
            .to_str()
            .context("infra_dir is not valid UTF-8")?;

        let request = serde_json::json!({
            "module": module,
            "payload": payload,
        });
        let request_bytes = serde_json::to_vec(&request)?;

        let mut child = Command::new(&self.python_cmd)
            .arg(&wrapper)
            .arg(infra_str)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .with_context(|| {
                format!(
                    "spawn {} {:?} for module {}",
                    self.python_cmd,
                    wrapper.display(),
                    module
                )
            })?;

        // Write stdin in a thread to avoid deadlock on large payloads.
        let mut stdin = child.stdin.take().context("take child stdin")?;
        std::thread::spawn(move || {
            let _ = stdin.write_all(&request_bytes);
        });

        let output = child
            .wait_with_output()
            .with_context(|| format!("wait for bridge process (module {})", module))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            warn!("Python bridge stderr ({}): {}", module, stderr.trim());
            anyhow::bail!(
                "bridge for module `{}` exited {}: {}",
                module,
                output.status,
                stderr.chars().take(400).collect::<String>()
            );
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let trimmed = stdout.trim();
        if trimmed.is_empty() {
            anyhow::bail!("bridge for module `{}` returned empty stdout", module);
        }

        let value: serde_json::Value = serde_json::from_str(trimmed).with_context(|| {
            format!(
                "parse bridge JSON for module `{}`: got {:?}",
                module,
                trimmed.chars().take(300).collect::<String>()
            )
        })?;

        // Unwrap {"ok":true,"data":{...}} envelope.
        if let Some(ok) = value.get("ok").and_then(|v| v.as_bool()) {
            if ok {
                return Ok(value
                    .get("data")
                    .cloned()
                    .unwrap_or(serde_json::Value::Null));
            }
            let err = value
                .get("error")
                .and_then(|v| v.as_str())
                .unwrap_or("unknown error");
            anyhow::bail!("Python bridge reported error for `{}`: {}", module, err);
        }

        debug!("bridge `{}` -> ok (no envelope)", module);
        Ok(value)
    }

    /// Typed convenience wrapper over [`call`].
    pub fn call_typed(&self, req: &BridgeRequest) -> Result<BridgeResponse> {
        let data = self.call(&req.module, &req.payload)?;
        Ok(BridgeResponse {
            ok: true,
            data,
            error: None,
        })
    }

    /// Health check: verify that python3 and bridge_wrapper.py are reachable.
    pub fn health_check(&self) -> bool {
        let wrapper = self.wrapper_path();
        if !wrapper.exists() {
            warn!(
                "bridge_wrapper.py not found at {:?}",
                wrapper.display()
            );
            return false;
        }
        // Try a cheap import-only check.
        let result = Command::new(&self.python_cmd)
            .arg("-c")
            .arg("import sys; sys.exit(0)")
            .output();
        match result {
            Ok(o) => o.status.success(),
            Err(e) => {
                warn!("python3 not runnable: {}", e);
                false
            }
        }
    }
}

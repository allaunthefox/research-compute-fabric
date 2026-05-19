use crate::models::{BridgeRequest, BridgeResponse};
use anyhow::{Context, Result};
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use tracing::{debug, warn};

/// Bridge to existing Python surfaces in the infra directory.
///
/// Each Python module is expected to expose a `handle_request(request: dict) -> dict`
/// function (the protocol used by ene_rds_wiki_layer, ene_rds_fractal_fold, etc.).
pub struct PythonBridge {
    infra_dir: PathBuf,
    python_cmd: String,
}

impl PythonBridge {
    pub fn new(infra_dir: PathBuf) -> Self {
        Self {
            infra_dir,
            python_cmd: "python3".into(),
        }
    }

    /// Call a Python module's `handle_request` with the given JSON payload.
    pub fn call(&self, module: &str, request: &serde_json::Value) -> Result<serde_json::Value> {
        let infra = self.infra_dir.to_str().context("infra_dir path is not UTF-8")?;
        let script = format!(
            r#"import sys, json, os
sys.path.insert(0, {!r})
os.chdir({!r})
mod = __import__({!r})
req = json.load(sys.stdin)
resp = mod.handle_request(req)
json.dump(resp, sys.stdout)
"#,
            infra, infra, module
        );
        let mut child = Command::new(&self.python_cmd)
            .arg("-c")
            .arg(&script)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .with_context(|| format!("spawn python3 for module {}", module))?;

        let stdin = child.stdin.take().context("take stdin")?;
        let request_json = serde_json::to_string(request)?;
        std::thread::spawn(move || {
            let mut stdin = stdin;
            let _ = stdin.write_all(request_json.as_bytes());
        });

        let output = child
            .wait_with_output()
            .with_context(|| format!("wait for python3 module {}", module))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            warn!(
                "Python bridge error for module {}: {}",
                module,
                stderr.trim()
            );
            anyhow::bail!(
                "Python module {} exited with {}: {}",
                module,
                output.status,
                stderr.trim()
            );
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let trimmed = stdout.trim();
        if trimmed.is_empty() {
            anyhow::bail!("Python module {} returned empty stdout", module);
        }
        let value: serde_json::Value =
            serde_json::from_str(trimmed).with_context(|| {
                format!(
                    "parse JSON from Python module {}: got {}",
                    module,
                    trimmed.chars().take(200).collect::<String>()
                )
            })?;
        debug!("bridge {} -> ok", module);
        Ok(value)
    }

    /// Convenience: call with a typed BridgeRequest.
    pub fn call_typed(&self, req: &BridgeRequest) -> Result<BridgeResponse> {
        let value = self.call(&req.module, &req.payload)?;
        let resp: BridgeResponse = serde_json::from_value(value)?;
        Ok(resp)
    }

    /// Quick health check: can we import a known module?
    pub fn health_check(&self) -> Result<bool> {
        match self.call("ene_rds_wiki_layer", &serde_json::json!({"op": "ping"})) {
            Ok(_) => Ok(true),
            Err(e) => {
                warn!("Python bridge health check failed: {}", e);
                Ok(false)
            }
        }
    }
}

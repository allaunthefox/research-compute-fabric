//! Generic execution router for Lean-owned MCP tool surfaces.
//!
//! Lean owns tool names + schemas. This module provides a *generic* shim to
//! execute Lean-defined tools by dispatching to commands declared in an
//! environment-controlled map.
//!
//! - No tool semantics live here.
//! - Routing is data-driven (`CLAW_MCP_TOOL_CMD_MAP`).
//! - Commands receive the tool `arguments` JSON on stdin.

use std::collections::BTreeMap;
use std::process::{Command, Stdio};

use serde_json::Value as JsonValue;

#[derive(Debug, Clone)]
pub struct ToolCommandMap {
    map: BTreeMap<String, Vec<String>>,
}

impl ToolCommandMap {
    pub fn from_env() -> Result<Option<Self>, String> {
        let raw = std::env::var("CLAW_MCP_TOOL_CMD_MAP").ok();
        let Some(raw) = raw else {
            return Ok(None);
        };

        let map: BTreeMap<String, Vec<String>> = serde_json::from_str(&raw)
            .map_err(|error| format!("CLAW_MCP_TOOL_CMD_MAP must be JSON object: {error}"))?;
        Ok(Some(Self { map }))
    }

    pub fn command_for(&self, tool_name: &str) -> Option<&[String]> {
        self.map.get(tool_name).map(Vec::as_slice)
    }

    pub fn handles(&self, tool_name: &str) -> bool {
        self.map.contains_key(tool_name)
    }
}

pub fn dispatch_with_map(
    map: &ToolCommandMap,
    tool_name: &str,
    arguments: &JsonValue,
) -> Result<String, String> {
    let argv = map
        .command_for(tool_name)
        .ok_or_else(|| format!("no command mapping for tool: {tool_name}"))?;
    if argv.is_empty() {
        return Err(format!("empty command mapping for tool: {tool_name}"));
    }

    let mut cmd = Command::new(&argv[0]);
    if argv.len() > 1 {
        cmd.args(&argv[1..]);
    }
    cmd.stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped());

    let mut child = cmd
        .spawn()
        .map_err(|error| format!("failed to spawn mapped command for {tool_name}: {error}"))?;

    if let Some(stdin) = child.stdin.as_mut() {
        use std::io::Write;
        let payload = serde_json::to_vec(arguments)
            .map_err(|error| format!("failed to serialize tool arguments: {error}"))?;
        stdin
            .write_all(&payload)
            .map_err(|error| format!("failed to write tool stdin: {error}"))?;
    }

    let output = child
        .wait_with_output()
        .map_err(|error| format!("failed to wait for tool {tool_name}: {error}"))?;

    if !output.status.success() {
        return Err(format!(
            "mapped tool {tool_name} failed (status={}): {}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        ));
    }

    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if stdout.is_empty() {
        return Ok("{}".to_string());
    }

    Ok(stdout)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn env_map_parses() {
        let _lock = crate::test_env_lock();
        std::env::set_var(
            "CLAW_MCP_TOOL_CMD_MAP",
            r#"{ "ene_status": ["echo", "ok"] }"#,
        );
        let map = ToolCommandMap::from_env().expect("map load").expect("present");
        assert!(map.handles("ene_status"));
        assert!(!map.handles("missing"));
        std::env::remove_var("CLAW_MCP_TOOL_CMD_MAP");
    }
}

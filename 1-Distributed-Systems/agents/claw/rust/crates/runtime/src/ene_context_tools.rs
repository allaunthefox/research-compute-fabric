//! ENE context tool dispatch (shim-only).
//!
//! Lean owns the *surface* (tool names + schemas). This module implements a
//! minimal execution adapter: dispatch each ENE context tool call to a
//! command provided via environment variables.
//!
//! This keeps Rust lean-first compliant:
//! - no semantics in Rust
//! - no invented tools
//! - execution is purely boundary I/O

use std::process::{Command, Stdio};

use serde_json::Value as JsonValue;

/// All ENE context tool names (must match Lean `Semantics.EneContextSurface`).
pub const ENE_CONTEXT_TOOL_NAMES: &[&str] = &[
    "ene_status",
    "ene_remember",
    "ene_recall",
    "ene_search",
    "ene_context",
    "ene_sessions",
    "ene_sync",
];

fn env_key_for_tool(tool_name: &str) -> Option<&'static str> {
    match tool_name {
        "ene_status" => Some("CLAW_ENE_STATUS_CMD"),
        "ene_remember" => Some("CLAW_ENE_REMEMBER_CMD"),
        "ene_recall" => Some("CLAW_ENE_RECALL_CMD"),
        "ene_search" => Some("CLAW_ENE_SEARCH_CMD"),
        "ene_context" => Some("CLAW_ENE_CONTEXT_CMD"),
        "ene_sessions" => Some("CLAW_ENE_SESSIONS_CMD"),
        "ene_sync" => Some("CLAW_ENE_SYNC_CMD"),
        _ => None,
    }
}

fn parse_cmd(json: &str, env_key: &str) -> Result<Vec<String>, String> {
    serde_json::from_str::<Vec<String>>(json)
        .map_err(|error| format!("{env_key} must be JSON array of strings: {error}"))
}

/// Dispatch a Lean-defined ENE context tool call.
///
/// Each tool is executed by spawning a command specified as a JSON argv array
/// in an env var. The tool `arguments` JSON is written to stdin.
///
/// The command must emit either:
/// - JSON on stdout (preferred), or
/// - plain text (which will be wrapped).
///
/// Return value is always a string (the MCP server wraps it as text content).
pub fn dispatch(tool_name: &str, arguments: &JsonValue) -> Result<String, String> {
    let env_key = env_key_for_tool(tool_name)
        .ok_or_else(|| format!("unknown ENE context tool: {tool_name}"))?;

    let cmd_json = std::env::var(env_key)
        .map_err(|_| format!("missing env var {env_key} for tool {tool_name}"))?;
    let argv = parse_cmd(&cmd_json, env_key)?;
    if argv.is_empty() {
        return Err(format!("{env_key} is empty"));
    }

    let mut cmd = Command::new(&argv[0]);
    if argv.len() > 1 {
        cmd.args(&argv[1..]);
    }
    cmd.stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped());

    let mut child = cmd
        .spawn()
        .map_err(|error| format!("failed to spawn tool command for {tool_name}: {error}"))?;

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
            "tool {tool_name} failed (status={}): {}",
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
    fn tool_list_is_stable() {
        assert!(ENE_CONTEXT_TOOL_NAMES.contains(&"ene_status"));
        assert!(env_key_for_tool("ene_status").is_some());
        assert!(env_key_for_tool("nope").is_none());
    }
}

#![allow(dead_code)]
//! s3c_lean_review.rs — Submit an S3C Lean source file for Gemma-4 review.
//!
//! Port of s3c_lean_review.py (86 lines).
//!
//! Reads the requested `.lean` file, constructs a high-priority `Reasoning`
//! task, submits it to [`Gemma4Integration`], executes it synchronously, and
//! returns the structured result.

use crate::gemma_integration::{Gemma4Integration, GemmaTask, GemmaTaskRequest, GemmaVariant};
use std::time::{SystemTime, UNIX_EPOCH};

// ─────────────────────────────────────────────────────────────────────────────
// §1  Public entry point
// ─────────────────────────────────────────────────────────────────────────────

/// Read `s3c_lean_path`, submit a Gemma-4 code-review task, execute it, and
/// return the result JSON.
///
/// # Errors
///
/// Returns an error if the file cannot be read, the database cannot be opened,
/// or task submission / execution fails.
///
/// # Example
///
/// ```no_run
/// use ene_session_sync::s3c_lean_review::run_s3c_lean_review;
///
/// let result = run_s3c_lean_review(
///     "0-Core-Formalism/lean/Semantics/S3C.lean",
///     "/tmp/gemma_review.db",
/// ).unwrap();
/// println!("{}", result["output"]);
/// ```
pub fn run_s3c_lean_review(
    s3c_lean_path: &str,
    db_path: &str,
) -> anyhow::Result<serde_json::Value> {
    // ── Read the Lean source file ────────────────────────────────────────────
    let code = std::fs::read_to_string(s3c_lean_path)
        .map_err(|e| anyhow::anyhow!("cannot read {}: {}", s3c_lean_path, e))?;

    // ── Construct the task ───────────────────────────────────────────────────
    let gemma = Gemma4Integration::new(db_path, GemmaVariant::E4B)?;

    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let task_id = format!("s3c_review_{}", now);

    let task = GemmaTaskRequest {
        task_id: task_id.clone(),
        task_type: GemmaTask::Reasoning,
        variant: GemmaVariant::E4B,
        input_data: serde_json::json!({
            "prompt": "Review the following Lean 4 code for S3C manifold processing. \
                       Identify any type errors, missing proofs, incomplete definitions, \
                       and suggest improvements.",
            "code": code,
            "file": "S3C.lean",
            "enable_thinking": true,
        }),
        enable_thinking: true,
        max_tokens: 2048,
        priority: 9,
    };

    // ── Submit and execute ───────────────────────────────────────────────────
    gemma.submit_task(&task)?;
    let result = gemma.execute_task(&task_id)?;
    Ok(result)
}

// ─────────────────────────────────────────────────────────────────────────────
// §2  Tests
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    /// Write a tiny fake `.lean` file and run the review pipeline against a
    /// temp SQLite database.
    #[test]
    fn test_run_s3c_lean_review_with_stub_file() {
        // Create a temporary Lean source file.
        let mut lean_file = NamedTempFile::new().unwrap();
        writeln!(
            lean_file,
            "-- S3C stub\ndef hello : Nat := 42"
        )
        .unwrap();

        // Create a temporary database.
        let db_file = NamedTempFile::new().unwrap();
        let db_path = db_file.path().to_str().unwrap().to_owned();

        let lean_path = lean_file.path().to_str().unwrap().to_owned();
        let result = run_s3c_lean_review(&lean_path, &db_path).unwrap();

        // The stub executor must produce these fields.
        assert!(result.get("task_id").is_some(), "missing task_id");
        assert!(result.get("output").is_some(), "missing output");
        assert!(result.get("tokens_generated").is_some(), "missing tokens_generated");

        // tokens_generated should be half of max_tokens (2048 / 2 = 1024).
        assert_eq!(result["tokens_generated"].as_i64().unwrap(), 1024);
    }

    #[test]
    fn test_run_s3c_lean_review_missing_file() {
        let db_file = NamedTempFile::new().unwrap();
        let db_path = db_file.path().to_str().unwrap().to_owned();
        let err = run_s3c_lean_review("/nonexistent/path/S3C.lean", &db_path);
        assert!(err.is_err(), "expected error for missing file");
        let msg = format!("{}", err.unwrap_err());
        assert!(msg.contains("cannot read"), "unexpected error: {}", msg);
    }
}

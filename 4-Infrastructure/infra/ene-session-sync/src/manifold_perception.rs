#![allow(dead_code)]
//! manifold_perception.rs — Topological manifest scanner for the research stack.
//!
//! Port of manifold_perception.py (390 lines).
//! Walks the filesystem under a given root, classifies every file, computes
//! per-file SHA-256 digests and line counts, parses Lean 4 metadata, identifies
//! structural "holes", and returns a `ManifoldReport`.
//!
//! Pure `std`-only directory walking; uses the `sha2` crate (already in Cargo.toml)
//! for file hashing.

use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::Path;

// ─────────────────────────────────────────────────────────────────────────────
// §1  Core types
// ─────────────────────────────────────────────────────────────────────────────

/// A single classified file in the research stack.
#[derive(Debug, Clone)]
pub struct ManifoldArtifact {
    /// Absolute (or relative-to-root) path string.
    pub path: String,
    /// Coarse kind: "lean", "doc", "infra", "data", "other".
    pub kind: String,
    /// Number of lines in the file.
    pub lines: usize,
    /// First 16 hex characters of the SHA-256 digest.
    pub hash: String,
}

/// A structural gap detected in the manifold.
#[derive(Debug, Clone)]
pub struct ManifoldHole {
    /// Human-readable centre / location of the gap.
    pub center: String,
    /// What kind of artifact was expected here.
    pub expected_kind: String,
    /// "low", "medium", or "high".
    pub severity: String,
    /// Free-text description.
    pub description: String,
    /// How many expected items are missing.
    pub missing_count: usize,
}

/// A topological boundary dimension of the manifold.
#[derive(Debug, Clone)]
pub struct ManifoldBoundary {
    pub dimension: String,
    pub present_count: usize,
    pub description: String,
}

/// The full manifest report produced by `build_manifold`.
#[derive(Debug, Clone)]
pub struct ManifoldReport {
    /// ISO-8601 UTC timestamp of when the report was generated.
    pub generated_at: String,
    pub lean_count: usize,
    pub doc_count: usize,
    pub infra_count: usize,
    pub total_lean_lines: usize,
    pub total_doc_lines: usize,
    pub total_theorems: usize,
    pub total_sorry: usize,
    pub holes: Vec<ManifoldHole>,
    pub boundaries: Vec<ManifoldBoundary>,
    pub artifacts: Vec<ManifoldArtifact>,
}

// ─────────────────────────────────────────────────────────────────────────────
// §2  File classification
// ─────────────────────────────────────────────────────────────────────────────

/// Classify a file path into a coarse kind string.
///
/// Priority order matches the Python port:
///   - `.lean`                  → "lean"
///   - `.md` / `.rst` / `.tex`  → "doc"
///   - `.rs` / `.py` / `.sh` / `.toml` / `.json` / `.yaml` / `.yml` → "infra"
///   - `.db` / `.sqlite` / `.bin` / `.parquet` → "data"
///   - anything else            → "other"
pub fn classify_artifact(path: &Path) -> &'static str {
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();

    match ext.as_str() {
        "lean" => "lean",
        "md" | "rst" | "tex" | "txt" => "doc",
        "rs" | "py" | "sh" | "toml" | "json" | "yaml" | "yml" | "lock" => "infra",
        "db" | "sqlite" | "sqlite3" | "bin" | "parquet" => "data",
        _ => {
            // Check filename fragments for known infrastructure files.
            if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                let lower = name.to_ascii_lowercase();
                if lower.contains("makefile")
                    || lower.contains("dockerfile")
                    || lower.contains("cargo")
                    || lower.contains("lakefile")
                {
                    return "infra";
                }
                if lower.ends_with(".olean") || lower.ends_with(".ilean") {
                    return "lean";
                }
            }
            "other"
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §3  File utilities
// ─────────────────────────────────────────────────────────────────────────────

/// Compute the SHA-256 of a file and return the first 16 hex characters.
///
/// Returns an all-zero string on read error rather than propagating.
pub fn sha256_file(path: &Path) -> String {
    let data = match std::fs::read(path) {
        Ok(d) => d,
        Err(_) => return "0000000000000000".to_string(),
    };
    let mut hasher = Sha256::new();
    hasher.update(&data);
    let digest = hasher.finalize();
    // hex::encode gives 64 chars; take first 16.
    let full = hex::encode(digest);
    full[..16].to_string()
}

/// Count the number of newline characters in a file.
///
/// Returns 0 on read error.
pub fn count_lines(path: &Path) -> usize {
    let data = match std::fs::read(path) {
        Ok(d) => d,
        Err(_) => return 0,
    };
    data.iter().filter(|&&b| b == b'\n').count()
}

// ─────────────────────────────────────────────────────────────────────────────
// §4  Lean 4 metadata
// ─────────────────────────────────────────────────────────────────────────────

/// Count Lean 4 syntactic occurrences in a source file.
///
/// Returns a JSON object:
/// ```json
/// { "theorems": 3, "defs": 7, "inductives": 1, "structures": 2,
///   "evals": 0, "sorries": 1 }
/// ```
pub fn parse_lean_metadata(path: &Path) -> Value {
    let text = match std::fs::read_to_string(path) {
        Ok(t) => t,
        Err(_) => return json!({ "theorems": 0, "defs": 0, "inductives": 0,
                                  "structures": 0, "evals": 0, "sorries": 0 }),
    };

    let theorems = count_occurrences(&text, "theorem ");
    let defs = count_occurrences(&text, "def ");
    let inductives = count_occurrences(&text, "inductive ");
    let structures = count_occurrences(&text, "structure ");
    let evals = count_occurrences(&text, "#eval");
    let sorries = count_occurrences(&text, "sorry");

    json!({
        "theorems":   theorems,
        "defs":       defs,
        "inductives": inductives,
        "structures": structures,
        "evals":      evals,
        "sorries":    sorries,
    })
}

/// Count non-overlapping occurrences of `needle` in `haystack`.
fn count_occurrences(haystack: &str, needle: &str) -> usize {
    let mut count = 0;
    let mut start = 0;
    while let Some(pos) = haystack[start..].find(needle) {
        count += 1;
        start += pos + needle.len();
    }
    count
}

// ─────────────────────────────────────────────────────────────────────────────
// §5  Directory walker
// ─────────────────────────────────────────────────────────────────────────────

/// Recursively collect all regular files under `dir`.
///
/// Silently skips unreadable directories.  Ignores hidden directories (those
/// whose name starts with `.`) to avoid traversing `.git`, `.lake`, etc.
fn walk_files(dir: &Path, out: &mut Vec<std::path::PathBuf>) {
    let rd = match std::fs::read_dir(dir) {
        Ok(r) => r,
        Err(_) => return,
    };
    for entry in rd.flatten() {
        let path = entry.path();
        let name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("");
        // Skip hidden dirs / files.
        if name.starts_with('.') {
            continue;
        }
        let meta = match entry.metadata() {
            Ok(m) => m,
            Err(_) => continue,
        };
        if meta.is_dir() {
            walk_files(&path, out);
        } else if meta.is_file() {
            out.push(path);
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §6  Hole detection
// ─────────────────────────────────────────────────────────────────────────────

/// Detect structural gaps from the parsed Lean metadata of a set of artifacts.
fn detect_holes(artifacts: &[ManifoldArtifact], lean_meta: &[(String, Value)]) -> Vec<ManifoldHole> {
    let mut holes: Vec<ManifoldHole> = Vec::new();

    for (path, meta) in lean_meta {
        let sorry_count = meta["sorries"].as_u64().unwrap_or(0) as usize;
        let theorem_count = meta["theorems"].as_u64().unwrap_or(0) as usize;
        let def_count = meta["defs"].as_u64().unwrap_or(0) as usize;
        let eval_count = meta["evals"].as_u64().unwrap_or(0) as usize;

        // Sorry without accompanying theorem — unfinished proof.
        if sorry_count > 0 && theorem_count == 0 {
            holes.push(ManifoldHole {
                center: path.clone(),
                expected_kind: "lean".to_string(),
                severity: "high".to_string(),
                description: format!(
                    "{} sorry(s) with no theorem statement — proof gap",
                    sorry_count
                ),
                missing_count: sorry_count,
            });
        }
        // Has defs but no #eval — possible dead code or untestable fragment.
        if def_count > 0 && eval_count == 0 {
            holes.push(ManifoldHole {
                center: path.clone(),
                expected_kind: "lean".to_string(),
                severity: "low".to_string(),
                description: format!(
                    "{} def(s) with no #eval — consider adding executable tests",
                    def_count
                ),
                missing_count: def_count,
            });
        }
    }

    // Structural gap: no Lean files at all.
    if artifacts.iter().all(|a| a.kind != "lean") {
        holes.push(ManifoldHole {
            center: "stack root".to_string(),
            expected_kind: "lean".to_string(),
            severity: "high".to_string(),
            description: "No Lean 4 source files found under the stack root".to_string(),
            missing_count: 1,
        });
    }

    // Gap: no documentation files.
    if artifacts.iter().all(|a| a.kind != "doc") {
        holes.push(ManifoldHole {
            center: "stack root".to_string(),
            expected_kind: "doc".to_string(),
            severity: "medium".to_string(),
            description: "No documentation files (.md / .rst / .tex) found".to_string(),
            missing_count: 1,
        });
    }

    holes
}

// ─────────────────────────────────────────────────────────────────────────────
// §7  Public API
// ─────────────────────────────────────────────────────────────────────────────

/// Walk `stack_root` and produce a `ManifoldReport`.
pub fn build_manifold(stack_root: &Path) -> ManifoldReport {
    let mut paths: Vec<std::path::PathBuf> = Vec::new();
    walk_files(stack_root, &mut paths);
    paths.sort();

    let mut artifacts: Vec<ManifoldArtifact> = Vec::with_capacity(paths.len());
    let mut lean_meta: Vec<(String, Value)> = Vec::new();

    let mut lean_count = 0usize;
    let mut doc_count = 0usize;
    let mut infra_count = 0usize;
    let mut total_lean_lines = 0usize;
    let mut total_doc_lines = 0usize;
    let mut total_theorems = 0usize;
    let mut total_sorry = 0usize;

    for path in &paths {
        let kind = classify_artifact(path);
        let lines = count_lines(path);
        let hash = sha256_file(path);

        let path_str = path.to_string_lossy().into_owned();

        match kind {
            "lean" => {
                lean_count += 1;
                total_lean_lines += lines;
                let meta = parse_lean_metadata(path);
                total_theorems += meta["theorems"].as_u64().unwrap_or(0) as usize;
                total_sorry += meta["sorries"].as_u64().unwrap_or(0) as usize;
                lean_meta.push((path_str.clone(), meta));
            }
            "doc" => {
                doc_count += 1;
                total_doc_lines += lines;
            }
            "infra" => {
                infra_count += 1;
            }
            _ => {}
        }

        artifacts.push(ManifoldArtifact {
            path: path_str,
            kind: kind.to_string(),
            lines,
            hash,
        });
    }

    let holes = detect_holes(&artifacts, &lean_meta);

    // Boundary dimensions — coarse topological summary.
    let boundaries = vec![
        ManifoldBoundary {
            dimension: "lean".to_string(),
            present_count: lean_count,
            description: format!("{} Lean 4 source files, {} lines", lean_count, total_lean_lines),
        },
        ManifoldBoundary {
            dimension: "doc".to_string(),
            present_count: doc_count,
            description: format!("{} documentation files, {} lines", doc_count, total_doc_lines),
        },
        ManifoldBoundary {
            dimension: "infra".to_string(),
            present_count: infra_count,
            description: format!("{} infrastructure files", infra_count),
        },
        ManifoldBoundary {
            dimension: "theorems".to_string(),
            present_count: total_theorems,
            description: format!("{} theorem declarations found", total_theorems),
        },
        ManifoldBoundary {
            dimension: "sorry".to_string(),
            present_count: total_sorry,
            description: format!("{} sorry occurrences (proof gaps)", total_sorry),
        },
    ];

    let generated_at = chrono::Utc::now().to_rfc3339();

    ManifoldReport {
        generated_at,
        lean_count,
        doc_count,
        infra_count,
        total_lean_lines,
        total_doc_lines,
        total_theorems,
        total_sorry,
        holes,
        boundaries,
        artifacts,
    }
}

/// Build the manifold and serialize it to a `serde_json::Value`.
pub fn build_manifold_json(stack_root: &Path) -> Value {
    let report = build_manifold(stack_root);

    let artifacts: Vec<Value> = report
        .artifacts
        .iter()
        .map(|a| {
            json!({
                "path":  a.path,
                "kind":  a.kind,
                "lines": a.lines,
                "hash":  a.hash,
            })
        })
        .collect();

    let holes: Vec<Value> = report
        .holes
        .iter()
        .map(|h| {
            json!({
                "center":        h.center,
                "expected_kind": h.expected_kind,
                "severity":      h.severity,
                "description":   h.description,
                "missing_count": h.missing_count,
            })
        })
        .collect();

    let boundaries: Vec<Value> = report
        .boundaries
        .iter()
        .map(|b| {
            json!({
                "dimension":     b.dimension,
                "present_count": b.present_count,
                "description":   b.description,
            })
        })
        .collect();

    json!({
        "schema":           "manifold_report_v1",
        "generated_at":     report.generated_at,
        "lean_count":        report.lean_count,
        "doc_count":         report.doc_count,
        "infra_count":       report.infra_count,
        "total_lean_lines":  report.total_lean_lines,
        "total_doc_lines":   report.total_doc_lines,
        "total_theorems":    report.total_theorems,
        "total_sorry":       report.total_sorry,
        "holes":             holes,
        "boundaries":        boundaries,
        "artifacts":         artifacts,
    })
}

// ─────────────────────────────────────────────────────────────────────────────
// §8  Tests
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::TempDir;

    fn make_temp_file(dir: &TempDir, name: &str, content: &str) -> std::path::PathBuf {
        let path = dir.path().join(name);
        let mut f = std::fs::File::create(&path).unwrap();
        f.write_all(content.as_bytes()).unwrap();
        path
    }

    #[test]
    fn classify_lean() {
        assert_eq!(classify_artifact(Path::new("foo.lean")), "lean");
        assert_eq!(classify_artifact(Path::new("bar.olean")), "lean");
    }

    #[test]
    fn classify_doc() {
        assert_eq!(classify_artifact(Path::new("README.md")), "doc");
        assert_eq!(classify_artifact(Path::new("paper.tex")), "doc");
    }

    #[test]
    fn classify_infra() {
        assert_eq!(classify_artifact(Path::new("main.rs")), "infra");
        assert_eq!(classify_artifact(Path::new("Cargo.toml")), "infra");
        assert_eq!(classify_artifact(Path::new("script.py")), "infra");
    }

    #[test]
    fn classify_other() {
        assert_eq!(classify_artifact(Path::new("image.png")), "other");
        assert_eq!(classify_artifact(Path::new("video.mp4")), "other");
    }

    #[test]
    fn count_lines_basic() {
        let dir = TempDir::new().unwrap();
        let path = make_temp_file(&dir, "test.txt", "line1\nline2\nline3\n");
        assert_eq!(count_lines(&path), 3);
    }

    #[test]
    fn sha256_file_len() {
        let dir = TempDir::new().unwrap();
        let path = make_temp_file(&dir, "test.txt", "hello world");
        let h = sha256_file(&path);
        assert_eq!(h.len(), 16);
        assert!(h.chars().all(|c| c.is_ascii_hexdigit()));
    }

    #[test]
    fn count_occurrences_basic() {
        let text = "theorem foo : theorem bar : sorry sorry";
        assert_eq!(count_occurrences(text, "theorem "), 2);
        assert_eq!(count_occurrences(text, "sorry"), 2);
    }

    #[test]
    fn parse_lean_metadata_counts() {
        let dir = TempDir::new().unwrap();
        let src = "theorem foo : 1 = 1 := by rfl\nsorry\ndef bar := 42\n#eval bar\n";
        let path = make_temp_file(&dir, "test.lean", src);
        let meta = parse_lean_metadata(&path);
        assert_eq!(meta["theorems"], 1);
        assert_eq!(meta["sorries"], 1);
        assert_eq!(meta["defs"], 1);
        assert_eq!(meta["evals"], 1);
    }

    #[test]
    fn build_manifold_smoke() {
        let dir = TempDir::new().unwrap();
        make_temp_file(&dir, "a.lean", "theorem foo : 1 = 1 := by rfl\n");
        make_temp_file(&dir, "README.md", "# Hello\n");
        make_temp_file(&dir, "build.rs", "fn main() {}\n");

        let report = build_manifold(dir.path());
        assert_eq!(report.lean_count, 1);
        assert_eq!(report.doc_count, 1);
        assert_eq!(report.infra_count, 1);
        assert_eq!(report.total_theorems, 1);
        assert!(!report.artifacts.is_empty());
    }

    #[test]
    fn build_manifold_json_schema() {
        let dir = TempDir::new().unwrap();
        make_temp_file(&dir, "x.lean", "sorry\n");
        let v = build_manifold_json(dir.path());
        assert_eq!(v["schema"], "manifold_report_v1");
        assert!(v["holes"].as_array().is_some());
        assert!(v["artifacts"].as_array().is_some());
    }
}

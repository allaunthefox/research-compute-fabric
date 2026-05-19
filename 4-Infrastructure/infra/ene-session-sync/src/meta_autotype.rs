/// ENE meta-autotype shim.
///
/// When ENE sees data without a defined ingestion surface, this module creates
/// contingent fields instead of pretending the schema is known. It is
/// intentionally deterministic: a tiny classifier/autotyper with receipts, not
/// an external LLM.
///
/// Ported from infra/ene_meta_autotype.py (219 lines).
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::time::{SystemTime, UNIX_EPOCH};

const VERSION: &str = "ene_meta_autotype_v1";

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────

fn iso_utc() -> String {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    // Simple ISO-8601 UTC string without chrono dep.
    let s = secs % 86400;
    let d = secs / 86400;
    let h = s / 3600;
    let m = (s % 3600) / 60;
    let sec = s % 60;
    // Days-since-epoch → approximate calendar date (good enough for receipts).
    let days_400 = d / 146097;
    let rem = d % 146097;
    let days_100 = rem.min(3 * 36524) / 36524;
    let rem = rem - days_100 * 36524;
    let days_4 = rem / 1461;
    let rem = rem % 1461;
    let days_1 = rem.min(3 * 365) / 365;
    let rem = rem - days_1 * 365;
    let year = days_400 * 400 + days_100 * 100 + days_4 * 4 + days_1 + 1970;
    // Month from day-of-year (rem).
    let leap = (days_1 == 3) && (days_4 != 24 || days_100 == 3);
    let days_in_month: [u64; 12] = [31, if leap { 29 } else { 28 }, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    let mut month = 0u64;
    let mut day_rem = rem;
    for (i, &days) in days_in_month.iter().enumerate() {
        if day_rem < days {
            month = i as u64 + 1;
            break;
        }
        day_rem -= days;
    }
    if month == 0 {
        month = 12;
    }
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}",
        year,
        month,
        day_rem + 1,
        h,
        m,
        sec
    )
}

fn sha256_hex(text: &str) -> String {
    let mut h = Sha256::new();
    h.update(text.as_bytes());
    hex::encode(h.finalize())
}

fn canonical_json(v: &Value) -> String {
    // serde_json sorts object keys by default when using BTreeMap, but
    // Value::Object uses IndexMap. We re-serialise through sorted BTreeMap.
    fn sort_value(v: &Value) -> Value {
        match v {
            Value::Object(map) => {
                let sorted: BTreeMap<_, _> =
                    map.iter().map(|(k, v)| (k.clone(), sort_value(v))).collect();
                let mut out = serde_json::Map::new();
                for (k, v) in sorted {
                    out.insert(k, v);
                }
                Value::Object(out)
            }
            Value::Array(arr) => Value::Array(arr.iter().map(sort_value).collect()),
            other => other.clone(),
        }
    }
    serde_json::to_string(&sort_value(v)).unwrap_or_default()
}

// ──────────────────────────────────────────────
// Type inference
// ──────────────────────────────────────────────

fn scalar_type(v: &Value) -> &'static str {
    match v {
        Value::Bool(_) => "boolean",
        Value::Number(n) => {
            if n.is_f64() {
                "float"
            } else {
                "integer"
            }
        }
        Value::Array(_) => "array",
        Value::Object(_) => "object",
        Value::Null => "null",
        Value::String(s) => {
            // sha256 hex
            if s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit()) {
                return "sha256_hex";
            }
            // integer string
            if s.parse::<i64>().is_ok() {
                return "integer_string";
            }
            // float string
            if s.parse::<f64>().is_ok() && s.contains('.') {
                return "float_string";
            }
            if s.starts_with("http://") || s.starts_with("https://") {
                return "url";
            }
            "string"
        }
    }
}

fn bind_class_for(name: &str, inferred_type: &str) -> &'static str {
    let lower = name.to_lowercase();
    if inferred_type == "sha256_hex"
        || lower.contains("hash")
        || lower.contains("receipt")
    {
        return "attestation_bind";
    }
    let geo_tokens = ["x", "y", "z", "coord", "manifold", "topology", "graph"];
    if geo_tokens.iter().any(|t| lower.contains(t)) {
        return "geometric_bind";
    }
    let ctrl_tokens = ["policy", "allow", "deny", "risk", "security"];
    if ctrl_tokens.iter().any(|t| lower.contains(t)) {
        return "control_bind";
    }
    "informational_bind"
}

fn surface_hint(text: &str, parsed: Option<&Value>) -> &'static str {
    let lower = text.to_lowercase();
    if let Some(Value::Object(map)) = parsed {
        let keys: std::collections::HashSet<&str> =
            map.keys().map(|k| k.as_str()).collect();
        if keys.contains("nodes") || keys.contains("edges") || lower.contains("graphml") {
            return "graph_concept_surface";
        }
        if keys.contains("archive_id")
            && keys.contains("source_type")
            && keys.contains("raw_content")
        {
            return "ene_archive_surface";
        }
        if keys.contains("pkg") && keys.contains("tier") && keys.contains("domain") {
            return "ene_package_surface";
        }
    }
    if lower.contains("<graphml") {
        return "graphml_surface";
    }
    if lower.contains("[[") && lower.contains("]]") {
        return "wiki_surface";
    }
    // Nucleotide sequence check (relaxed)
    let trimmed = text.trim();
    if trimmed.len() >= 8
        && trimmed
            .chars()
            .all(|c| matches!(c.to_ascii_uppercase(), 'A' | 'C' | 'G' | 'T' | 'U' | 'N' | 'R' | 'Y' | 'S' | 'W' | 'K' | 'M' | 'B' | 'D' | 'H' | 'V' | ' ' | '\n' | '\r' | '\t'))
    {
        return "sequence_surface";
    }
    "unknown_surface"
}

// ──────────────────────────────────────────────
// Autotype
// ──────────────────────────────────────────────

#[derive(Clone)]
pub struct ContingentField {
    pub name: String,
    pub inferred_type: String,
    pub confidence: f64,
    pub extraction_rule: String,
    pub bind_class: String,
    pub status: &'static str,
}

impl ContingentField {
    fn to_value(&self) -> Value {
        json!({
            "name": self.name,
            "inferred_type": self.inferred_type,
            "confidence": self.confidence,
            "extraction_rule": self.extraction_rule,
            "bind_class": self.bind_class,
            "status": self.status,
        })
    }
}

pub fn autotype_payload(data: &[u8], name: &str) -> Value {
    let text = String::from_utf8_lossy(data).into_owned();
    let parsed: Option<Value> = serde_json::from_str(&text).ok();
    let mut fields: Vec<ContingentField> = Vec::new();

    match &parsed {
        Some(Value::Object(map)) => {
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort();
            for key in keys {
                let value = &map[key];
                let inf = scalar_type(value).to_string();
                let bc = bind_class_for(key, &inf).to_string();
                fields.push(ContingentField {
                    name: key.clone(),
                    inferred_type: inf,
                    confidence: 0.85,
                    extraction_rule: format!("json_pointer:/{}", key),
                    bind_class: bc,
                    status: "contingent",
                });
            }
        }
        Some(Value::Array(_)) => {
            fields.push(ContingentField {
                name: "items".to_string(),
                inferred_type: "array".to_string(),
                confidence: 0.8,
                extraction_rule: "json_root_array".to_string(),
                bind_class: "informational_bind".to_string(),
                status: "contingent",
            });
        }
        _ => {
            // Token extraction from free text (mirrors Python regex)
            let mut tokens: Vec<String> = text
                .split(|c: char| !c.is_alphanumeric() && c != '_')
                .filter(|s| {
                    s.len() >= 3
                        && s.starts_with(|c: char| c.is_alphabetic() || c == '_')
                })
                .map(|s| s.to_string())
                .collect::<std::collections::BTreeSet<_>>()
                .into_iter()
                .take(64)
                .collect();
            tokens.sort();
            tokens.truncate(16);
            for token in tokens {
                let bc = bind_class_for(&token, "string").to_string();
                fields.push(ContingentField {
                    name: token.clone(),
                    inferred_type: "token".to_string(),
                    confidence: 0.45,
                    extraction_rule: "regex_identifier_token".to_string(),
                    bind_class: bc,
                    status: "contingent",
                });
            }
        }
    }

    let hint = surface_hint(&text, parsed.as_ref());

    let raw_content = json!({
        "kind": "ene_meta_autotype",
        "version": VERSION,
        "name": name,
        "surface_hint": hint,
        "byte_len": data.len(),
        "contingent_fields": fields.iter().map(|f| f.to_value()).collect::<Vec<_>>(),
        "policy": {
            "defined_ingestion_surface": hint != "unknown_surface",
            "authority": "contingent_until_bound_by_ingestion_surface",
            "required_gate": ["OBSERVE", "BIND", "ROUTE", "POLICY_CHECK", "VERIFY", "RECEIPT"],
        },
    });

    let content_hash = sha256_hex(&canonical_json(&raw_content));
    let receipt_pre = json!({ "v": VERSION, "content_hash": content_hash, "name": name });
    let receipt = sha256_hex(&canonical_json(&receipt_pre));

    json!({
        "ok": true,
        "op": "meta_autotype",
        "surface_hint": hint,
        "field_count": fields.len(),
        "archive_record": {
            "archive_id": format!("json_catalog_ene_meta_autotype_{}", &content_hash[..16]),
            "source_type": "json_catalog",
            "source_file": format!("ene-meta-autotype://{}", &content_hash[..16]),
            "raw_content": raw_content,
            "extracted_text": &text[..text.len().min(10000)],
            "extracted_at": iso_utc(),
            "content_hash": content_hash,
            "extraction_version": VERSION,
        },
        "jsonl_event": {
            "src": "ene",
            "op": "upsert",
            "data": {
                "pkg": format!("ene/meta-autotype/{}", &receipt[..16]),
                "version": VERSION,
                "tier": "RESEARCH",
                "domain": "semantic",
                "archetype": "contingent_schema",
                "tags": ["ene", "meta_autotype", hint],
                "sha256": &content_hash,
            },
            "bind": {
                "lawful": true,
                "class": "informational_bind",
                "invariant": "contingent_fields_are_not_authoritative",
            },
            "provenance": { "attestation_hash": format!("sha256:{}", receipt) },
        },
        "receipt": receipt,
    })
}

// ──────────────────────────────────────────────
// Public request handler (mirrors handle_request in Python)
// ──────────────────────────────────────────────

pub fn handle_request(request: &Value) -> Value {
    let data: Vec<u8> = if let Some(b64) = request.get("data_b64").and_then(|v| v.as_str()) {
        use base64::Engine as _;
        base64::engine::general_purpose::STANDARD
            .decode(b64)
            .unwrap_or_default()
    } else {
        request
            .get("text")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .as_bytes()
            .to_vec()
    };
    let name = request
        .get("name")
        .and_then(|v| v.as_str())
        .unwrap_or("payload");
    autotype_payload(&data, name)
}

// ──────────────────────────────────────────────
// Stand-alone entry point (mirrors __main__ in Python)
// ──────────────────────────────────────────────

pub fn run_cli(text: &str, name: &str) {
    let result = autotype_payload(text.as_bytes(), name);
    println!("{}", serde_json::to_string_pretty(&result).unwrap_or_default());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_json_object_surface() {
        let data = br#"{"nodes": [1, 2], "edges": []}"#;
        let result = autotype_payload(data, "test");
        assert_eq!(result["ok"], true);
        assert_eq!(result["surface_hint"], "graph_concept_surface");
    }

    #[test]
    fn test_unknown_surface() {
        let data = b"hello world foobar";
        let result = autotype_payload(data, "test");
        assert_eq!(result["surface_hint"], "unknown_surface");
        assert!(result["field_count"].as_u64().unwrap_or(0) > 0);
    }

    #[test]
    fn test_receipt_roundtrip() {
        let data = br#"{"pkg": "ene/test", "tier": "RESEARCH", "domain": "semantic"}"#;
        let result = autotype_payload(data, "roundtrip");
        assert_eq!(result["surface_hint"], "ene_package_surface");
        let receipt = result["receipt"].as_str().unwrap();
        assert_eq!(receipt.len(), 64);
    }
}

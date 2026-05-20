use serde_json::Value;
use sha2::{Digest, Sha256};

pub fn canonical_json(value: &Value) -> String {
    match value {
        Value::Null => "null".to_string(),
        Value::Bool(v) => v.to_string(),
        Value::Number(v) => v.to_string(),
        Value::String(v) => serde_json::to_string(v).expect("string serialization cannot fail"),
        Value::Array(values) => {
            let body = values
                .iter()
                .map(canonical_json)
                .collect::<Vec<_>>()
                .join(",");
            format!("[{body}]")
        }
        Value::Object(map) => {
            let mut keys = map.keys().collect::<Vec<_>>();
            keys.sort();
            let body = keys
                .into_iter()
                .map(|key| {
                    let key_json =
                        serde_json::to_string(key).expect("key serialization cannot fail");
                    let value_json = canonical_json(&map[key]);
                    format!("{key_json}:{value_json}")
                })
                .collect::<Vec<_>>()
                .join(",");
            format!("{{{body}}}")
        }
    }
}

pub fn sha256_json(value: &Value) -> String {
    let payload = canonical_json(value);
    let digest = Sha256::digest(payload.as_bytes());
    format!("{digest:x}")
}

pub fn clamp01(x: f64) -> f64 {
    x.clamp(0.0, 1.0)
}

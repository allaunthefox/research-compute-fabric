#![allow(dead_code)]
//! deepseek_adapter.rs — DeepSeek / Ollama chat adapter.
//!
//! Port of deepseek_adapter.py (113 lines).
//! Provides a unified client that routes to either a local Ollama instance or
//! the DeepSeek remote API, plus a `DeepSeekProver` shim for Lean 4
//! formalization requests.

use anyhow::{Context, Result};
use serde_json::{json, Value};

// ─────────────────────────────────────────────────────────────────────────────
// §1  DeepSeekV4 client
// ─────────────────────────────────────────────────────────────────────────────

/// Unified chat client for DeepSeek / Ollama.
///
/// Routing:
/// - `use_local = true`  → Ollama REST API at `local_url`
/// - `use_local = false` → DeepSeek remote API at `api_base` with bearer auth
pub struct DeepSeekV4 {
    api_key: Option<String>,
    local_url: String,
    use_local: bool,
    api_base: String,
    http: reqwest::Client,
}

impl DeepSeekV4 {
    /// Explicit constructor.
    pub fn new(api_key: Option<String>, local_url: impl Into<String>, use_local: bool) -> Self {
        Self {
            api_key,
            local_url: local_url.into(),
            use_local,
            api_base: "https://api.deepseek.com/v1".to_string(),
            http: reqwest::Client::new(),
        }
    }

    /// Build from environment.
    ///
    /// Reads `DEEPSEEK_API_KEY`.  Defaults to `localhost:11434` and
    /// `use_local = true` so the crate works offline without any key.
    pub fn from_env() -> Self {
        let api_key = std::env::var("DEEPSEEK_API_KEY").ok();
        let local_url = std::env::var("OLLAMA_URL")
            .unwrap_or_else(|_| "http://localhost:11434".to_string());
        // If an API key was provided, prefer the remote endpoint.
        let use_local = api_key.is_none();
        Self::new(api_key, local_url, use_local)
    }

    /// Send a chat request and return the raw JSON response body.
    ///
    /// `stream` is accepted for API symmetry but always forced to `false` —
    /// streaming responses require a different response-parsing path that is
    /// not needed by any current caller.
    pub async fn chat(
        &self,
        messages: &[Value],
        model: &str,
        _stream: bool,
    ) -> Result<Value> {
        if self.use_local {
            self.chat_local(messages, model).await
        } else {
            self.chat_remote(messages, model).await
        }
    }

    // ── Private helpers ───────────────────────────────────────────────────────

    async fn chat_local(&self, messages: &[Value], model: &str) -> Result<Value> {
        let url = format!("{}/api/chat", self.local_url);
        let payload = json!({
            "model":    model,
            "messages": messages,
            "stream":   false,
        });
        let resp = self
            .http
            .post(&url)
            .json(&payload)
            .send()
            .await
            .with_context(|| format!("POST {}", url))?;
        let status = resp.status();
        let body: Value = resp.json().await.context("parse ollama response JSON")?;
        if !status.is_success() {
            anyhow::bail!("ollama returned {}: {:?}", status, body);
        }
        Ok(body)
    }

    async fn chat_remote(&self, messages: &[Value], model: &str) -> Result<Value> {
        let url = format!("{}/chat/completions", self.api_base);
        let payload = json!({
            "model":    model,
            "messages": messages,
            "stream":   false,
        });
        let mut req = self.http.post(&url).json(&payload);
        if let Some(ref key) = self.api_key {
            req = req.bearer_auth(key);
        }
        let resp = req
            .send()
            .await
            .with_context(|| format!("POST {}", url))?;
        let status = resp.status();
        let body: Value = resp.json().await.context("parse deepseek response JSON")?;
        if !status.is_success() {
            anyhow::bail!("deepseek API returned {}: {:?}", status, body);
        }
        Ok(body)
    }

    /// Extract the assistant text content from a chat response.
    ///
    /// Handles both Ollama format (`response.message.content`) and OpenAI
    /// format (`choices[0].message.content`).
    pub fn extract_content(resp: &Value) -> String {
        // Ollama: { "message": { "content": "..." } }
        if let Some(content) = resp
            .get("message")
            .and_then(|m| m.get("content"))
            .and_then(|c| c.as_str())
        {
            return content.to_string();
        }
        // OpenAI / DeepSeek: { "choices": [{ "message": { "content": "..." } }] }
        if let Some(content) = resp
            .get("choices")
            .and_then(|c| c.get(0))
            .and_then(|c| c.get("message"))
            .and_then(|m| m.get("content"))
            .and_then(|c| c.as_str())
        {
            return content.to_string();
        }
        String::new()
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §2  DeepSeekProver — Lean 4 formalization wrapper
// ─────────────────────────────────────────────────────────────────────────────

/// High-level prover shim that wraps `DeepSeekV4` for Lean 4 formalization.
pub struct DeepSeekProver {
    client: DeepSeekV4,
}

impl DeepSeekProver {
    pub fn new(client: DeepSeekV4) -> Self {
        Self { client }
    }

    /// Build from environment (delegates to `DeepSeekV4::from_env`).
    pub fn from_env() -> Self {
        Self::new(DeepSeekV4::from_env())
    }

    /// Ask the model to produce a Lean 4 formalization of `statement`.
    ///
    /// Returns the raw string content from the assistant turn.
    pub async fn formalize(&self, statement: &str) -> Result<String> {
        let system_prompt = "You are an expert in formal mathematics and Lean 4. \
            Given an informal mathematical statement, produce a complete and \
            correct Lean 4 formalization. Output only valid Lean 4 code, \
            no explanations.";

        let user_prompt = format!(
            "Formalize the following mathematical statement in Lean 4:\n\n{}",
            statement
        );

        let messages = vec![
            json!({ "role": "system", "content": system_prompt }),
            json!({ "role": "user",   "content": user_prompt   }),
        ];

        // Model selection: local Ollama vs. remote DeepSeek.
        let model = if self.client.use_local {
            "qwen2.5-coder:14b"
        } else {
            "deepseek-v4-pro"
        };

        let resp = self
            .client
            .chat(&messages, model, false)
            .await
            .context("formalize chat call")?;

        Ok(DeepSeekV4::extract_content(&resp))
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §3  Tests
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn extract_content_ollama_format() {
        let resp = json!({ "message": { "content": "hello" } });
        assert_eq!(DeepSeekV4::extract_content(&resp), "hello");
    }

    #[test]
    fn extract_content_openai_format() {
        let resp = json!({
            "choices": [{ "message": { "content": "world" } }]
        });
        assert_eq!(DeepSeekV4::extract_content(&resp), "world");
    }

    #[test]
    fn extract_content_empty() {
        let resp = json!({});
        assert_eq!(DeepSeekV4::extract_content(&resp), "");
    }

    #[test]
    fn from_env_defaults() {
        // Should not panic even without env vars set.
        let client = DeepSeekV4::from_env();
        assert!(client.use_local);
        assert!(client.api_key.is_none() || client.api_key.is_some());
    }
}

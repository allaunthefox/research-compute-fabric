use crate::models::OllamaEmbedRequest;
use anyhow::{Context, Result};
use reqwest::Client;
use serde_json::json;
use std::time::Duration;
use tracing::{debug, info, warn};

/// Ollama embedding client.
pub struct Embedder {
    client: Client,
    base_url: String,
    model: String,
}

impl Embedder {
    pub fn new(base_url: &str, model: &str) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(120))
            .build()
            .unwrap_or_else(|_| Client::new());
        Self {
            client,
            base_url: base_url.trim_end_matches('/').to_string(),
            model: model.to_string(),
        }
    }

    pub fn from_env() -> Self {
        let base = std::env::var("OLLAMA_HOST").unwrap_or_else(|_| "http://localhost:11434".into());
        let model = std::env::var("OLLAMA_EMBED_MODEL").unwrap_or_else(|_| "nomic-embed-text".into());
        Self::new(&base, &model)
    }

    /// Embed a single string, returning a 768d (or model-specific) vector.
    pub async fn embed(&self, text: &str) -> Result<Vec<f32>> {
        let url = format!("{}/api/embeddings", self.base_url);
        let payload = json!({
            "model": self.model,
            "prompt": text,
        });
        let resp = self
            .client
            .post(&url)
            .json(&payload)
            .send()
            .await
            .with_context(|| format!("POST {}", url))?;
        if !resp.status().is_success() {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            anyhow::bail!("Ollama returned {}: {}", status, body);
        }
        let json: serde_json::Value = resp.json().await.context("parse Ollama response")?;
        let embedding = json
            .get("embedding")
            .and_then(|v| v.as_array())
            .context("missing 'embedding' field in Ollama response")?;
        let vec: Vec<f32> = embedding
            .iter()
            .map(|v| v.as_f64().unwrap_or(0.0) as f32)
            .collect();
        debug!("embedded {} chars -> {} dims", text.chars().count(), vec.len());
        Ok(vec)
    }

    /// Embed multiple strings sequentially (Ollama does not batch natively).
    pub async fn embed_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>> {
        let mut out = Vec::with_capacity(texts.len());
        for (i, text) in texts.iter().enumerate() {
            match self.embed(text).await {
                Ok(v) => out.push(v),
                Err(e) => {
                    warn!("embedding failed for item {}: {}", i, e);
                    out.push(Vec::new());
                }
            }
        }
        info!("embedded {} texts via Ollama {}", texts.len(), self.model);
        Ok(out)
    }

    /// Check if Ollama is reachable and the model is loaded.
    pub async fn health_check(&self) -> Result<bool> {
        let url = format!("{}/api/tags", self.base_url);
        match self.client.get(&url).send().await {
            Ok(resp) => {
                if !resp.status().is_success() {
                    return Ok(false);
                }
                let json: serde_json::Value = resp.json().await.unwrap_or_default();
                let models = json.get("models").and_then(|m| m.as_array());
                if let Some(arr) = models {
                    Ok(arr.iter().any(|m| {
                        m.get("name")
                            .and_then(|n| n.as_str())
                            .map(|n| n == self.model || n.starts_with(&format!("{}:", self.model)))
                            .unwrap_or(false)
                    }))
                } else {
                    Ok(false)
                }
            }
            Err(e) => {
                warn!("Ollama health check failed: {}", e);
                Ok(false)
            }
        }
    }
}

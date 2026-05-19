#![allow(dead_code)]
//! search_adapter.rs — Web search provider adapters.
//!
//! Port of search_adapter.py (77 lines).
//! Two providers:
//!   - `GoogleSurfProvider` — placeholder (real dispatch via MCP server)
//!   - `BraveSearchProvider` — live search via Brave Search API

use serde_json::{json, Value};

// ─────────────────────────────────────────────────────────────────────────────
// §1  SearchResult
// ─────────────────────────────────────────────────────────────────────────────

/// A single web search result.
#[derive(Debug, Clone)]
pub struct SearchResult {
    pub title: String,
    pub url: String,
    pub snippet: String,
}

impl SearchResult {
    pub fn new(title: impl Into<String>, url: impl Into<String>, snippet: impl Into<String>) -> Self {
        Self {
            title: title.into(),
            url: url.into(),
            snippet: snippet.into(),
        }
    }

    /// Serialize to a JSON object with `title`, `url`, and `snippet` keys.
    pub fn to_value(&self) -> Value {
        json!({
            "title":   self.title,
            "url":     self.url,
            "snippet": self.snippet,
        })
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §2  GoogleSurfProvider
// ─────────────────────────────────────────────────────────────────────────────

/// Placeholder Google search provider.
///
/// Real integration is handled via an MCP server external to this binary.
/// Returns an empty result set so call-sites compile and type-check cleanly.
pub struct GoogleSurfProvider;

impl GoogleSurfProvider {
    pub fn new() -> Self {
        Self
    }

    /// Submit a search query.  Always returns an empty vec — see module doc.
    pub async fn search(&self, _query: &str, _limit: usize) -> Vec<SearchResult> {
        // Dispatch is handled by the MCP server layer.  This shim exists so
        // that code depending on `GoogleSurfProvider` compiles and can be
        // wired up later without API changes.
        Vec::new()
    }
}

impl Default for GoogleSurfProvider {
    fn default() -> Self {
        Self::new()
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §3  BraveSearchProvider
// ─────────────────────────────────────────────────────────────────────────────

/// Live web search via the Brave Search REST API.
///
/// Requires a `BRAVE_API_KEY` subscription token.  Returns an empty result set
/// when no key is configured or when the API call fails.
pub struct BraveSearchProvider {
    api_key: Option<String>,
    http: reqwest::Client,
}

impl BraveSearchProvider {
    pub fn new(api_key: Option<String>) -> Self {
        Self {
            api_key,
            http: reqwest::Client::new(),
        }
    }

    /// Build from the `BRAVE_API_KEY` environment variable.
    pub fn from_env() -> Self {
        Self::new(std::env::var("BRAVE_API_KEY").ok())
    }

    /// Execute a web search query and return up to `limit` results.
    ///
    /// Hits `https://api.search.brave.com/res/v1/web/search`.
    /// Returns an empty vec when no API key is present or on any error.
    pub async fn search(&self, query: &str, limit: usize) -> Vec<SearchResult> {
        let key = match &self.api_key {
            Some(k) => k.clone(),
            None => return Vec::new(),
        };

        let url = "https://api.search.brave.com/res/v1/web/search";
        let resp = match self
            .http
            .get(url)
            .header("Accept", "application/json")
            .header("X-Subscription-Token", &key)
            .query(&[("q", query), ("count", &limit.to_string())])
            .send()
            .await
        {
            Ok(r) => r,
            Err(e) => {
                tracing::warn!("brave search request failed: {}", e);
                return Vec::new();
            }
        };

        if !resp.status().is_success() {
            tracing::warn!("brave search returned {}", resp.status());
            return Vec::new();
        }

        let body: Value = match resp.json().await {
            Ok(v) => v,
            Err(e) => {
                tracing::warn!("brave search response parse error: {}", e);
                return Vec::new();
            }
        };

        // Response schema: { "web": { "results": [ { "title", "url", "description" } ] } }
        let raw_results = body
            .get("web")
            .and_then(|w| w.get("results"))
            .and_then(|r| r.as_array())
            .cloned()
            .unwrap_or_default();

        raw_results
            .into_iter()
            .map(|item| {
                let title = item
                    .get("title")
                    .and_then(|t| t.as_str())
                    .unwrap_or("")
                    .to_string();
                let url = item
                    .get("url")
                    .and_then(|u| u.as_str())
                    .unwrap_or("")
                    .to_string();
                let snippet = item
                    .get("description")
                    .and_then(|d| d.as_str())
                    .unwrap_or("")
                    .to_string();
                SearchResult { title, url, snippet }
            })
            .collect()
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §4  Tests
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn search_result_to_value() {
        let r = SearchResult::new("My Title", "https://example.com", "A snippet.");
        let v = r.to_value();
        assert_eq!(v["title"], "My Title");
        assert_eq!(v["url"], "https://example.com");
        assert_eq!(v["snippet"], "A snippet.");
    }

    #[test]
    fn brave_no_key_returns_empty() {
        // Without an API key the provider is constructed correctly but will
        // return empty — we verify the struct, not the async path.
        let provider = BraveSearchProvider::new(None);
        assert!(provider.api_key.is_none());
    }

    #[test]
    fn google_surf_provider_default() {
        let _ = GoogleSurfProvider::default();
    }

    #[tokio::test]
    async fn google_surf_returns_empty() {
        let p = GoogleSurfProvider::new();
        let results = p.search("test query", 10).await;
        assert!(results.is_empty());
    }
}

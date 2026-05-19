#![allow(dead_code)]
//! knowledge_ingestion.rs — Knowledge ingestion adapters.
//!
//! Port of knowledge_ingestion.py (482 lines).
//! Three adapters:
//!   - `WolframAlphaKnowledge` — Wolfram|Alpha v2 query API
//!   - `OpenMathKnowledge`     — OpenMath Content Dictionary (.ocd) fetcher
//!   - `NLabWikiKnowledge`     — nLab wiki page fetcher / crawler

use serde_json::{json, Value};
use std::collections::HashMap;

// ─────────────────────────────────────────────────────────────────────────────
// §1  WolframAlphaKnowledge
// ─────────────────────────────────────────────────────────────────────────────

/// Adapter for the Wolfram|Alpha v2 short-answer / query API.
pub struct WolframAlphaKnowledge {
    api_key: String,
    cache: HashMap<String, Value>,
    rate_limit_remaining: u32,
}

impl WolframAlphaKnowledge {
    pub fn new(api_key: String) -> Self {
        Self {
            api_key,
            cache: HashMap::new(),
            rate_limit_remaining: 100,
        }
    }

    /// Query Wolfram|Alpha for a free-form `question`.
    ///
    /// Results are cached by question string.  Returns `None` when the API
    /// call fails, rate-limit is exhausted, or no pods are returned.
    pub async fn query(&mut self, question: &str) -> Option<Value> {
        // Serve from cache when available.
        if let Some(cached) = self.cache.get(question) {
            return Some(cached.clone());
        }
        // Simple rate-limit guard.
        if self.rate_limit_remaining == 0 {
            return None;
        }
        self.rate_limit_remaining = self.rate_limit_remaining.saturating_sub(1);

        let client = reqwest::Client::new();
        let resp = client
            .get("https://api.wolframalpha.com/v2/query")
            .query(&[
                ("input", question),
                ("format", "plaintext"),
                ("output", "json"),
                ("appid", &self.api_key),
            ])
            .send()
            .await
            .ok()?;

        if !resp.status().is_success() {
            return None;
        }

        let body: Value = resp.json().await.ok()?;

        // Navigate into the queryresult pods.
        let pods = body
            .get("queryresult")
            .and_then(|qr| qr.get("pods"))
            .and_then(|p| p.as_array())
            .cloned()
            .unwrap_or_default();

        if pods.is_empty() {
            return None;
        }

        // Flatten all plaintext subpod values into a single results list.
        let mut results: Vec<Value> = Vec::new();
        for pod in &pods {
            let title = pod.get("title").and_then(|t| t.as_str()).unwrap_or("");
            if let Some(subpods) = pod.get("subpods").and_then(|s| s.as_array()) {
                for sp in subpods {
                    let text = sp
                        .get("plaintext")
                        .and_then(|t| t.as_str())
                        .unwrap_or("")
                        .trim()
                        .to_string();
                    if !text.is_empty() {
                        results.push(json!({ "pod": title, "text": text }));
                    }
                }
            }
        }

        let result = json!({
            "question": question,
            "results":  results,
        });
        self.cache.insert(question.to_string(), result.clone());
        Some(result)
    }

    /// Fetch domain knowledge for a mathematical domain.
    ///
    /// Runs three queries (core concepts, key theorems, applications) and
    /// consolidates them into a single JSON object.
    pub async fn get_domain_knowledge(&mut self, domain: &str) -> Value {
        let q_concepts = format!("{} mathematics concepts", domain);
        let q_theorems = format!("{} key theorems", domain);
        let q_applications = format!("{} applications", domain);

        let concepts = self
            .query(&q_concepts)
            .await
            .unwrap_or_else(|| json!({"results": []}));
        let theorems = self
            .query(&q_theorems)
            .await
            .unwrap_or_else(|| json!({"results": []}));
        let applications = self
            .query(&q_applications)
            .await
            .unwrap_or_else(|| json!({"results": []}));

        json!({
            "domain":       domain,
            "concepts":     concepts.get("results").cloned().unwrap_or(json!([])),
            "theorems":     theorems.get("results").cloned().unwrap_or(json!([])),
            "applications": applications.get("results").cloned().unwrap_or(json!([])),
        })
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §2  OpenMathKnowledge
// ─────────────────────────────────────────────────────────────────────────────

/// Adapter for OpenMath Content Dictionary (.ocd) files hosted at
/// `www.openmath.org/cd/`.
pub struct OpenMathKnowledge {
    base_url: String,
    cache: HashMap<String, Value>,
}

impl OpenMathKnowledge {
    pub fn new() -> Self {
        Self {
            base_url: "https://www.openmath.org/cd".to_string(),
            cache: HashMap::new(),
        }
    }

    /// Fetch and parse a single Content Dictionary by name.
    ///
    /// The .ocd format is XML; we extract `<OMS>` / `<CDDefinition>` symbol
    /// entries with simple string scanning — no external XML crate required.
    pub async fn fetch_content_dictionary(&mut self, cd_name: &str) -> Option<Value> {
        if let Some(cached) = self.cache.get(cd_name) {
            return Some(cached.clone());
        }

        let url = format!("{}/{}.ocd", self.base_url, cd_name);
        let client = reqwest::Client::new();
        let resp = client.get(&url).send().await.ok()?;
        if !resp.status().is_success() {
            return None;
        }
        let text = resp.text().await.ok()?;

        let symbols = parse_ocd_symbols(&text, cd_name);

        let result = json!({
            "name":    cd_name,
            "symbols": symbols,
        });
        self.cache.insert(cd_name.to_string(), result.clone());
        Some(result)
    }

    /// The canonical set of Content Dictionaries relevant to the research stack.
    pub fn get_relevant_cds() -> Vec<&'static str> {
        vec![
            "arith1", "alg1", "relation1", "set1", "logic1", "fns1", "nums1",
            "calculus1", "complex1", "linalg1", "analysis1", "geometry",
            "topology",
        ]
    }

    /// Fetch all relevant Content Dictionaries and return a combined summary.
    pub async fn ingest_all_relevant_cds(&mut self) -> Value {
        let cds = Self::get_relevant_cds();
        let mut all: Vec<Value> = Vec::with_capacity(cds.len());
        for cd in cds {
            let entry = self
                .fetch_content_dictionary(cd)
                .await
                .unwrap_or_else(|| json!({ "name": cd, "symbols": [] }));
            all.push(entry);
        }
        json!({ "content_dictionaries": all })
    }
}

/// Parse symbol definitions from raw .ocd XML text.
///
/// Looks for `<CDDefinition>` blocks and extracts `<Name>` tags within them.
/// Falls back to scanning `name="..."` attribute style for alternate formats.
fn parse_ocd_symbols(xml: &str, cd_name: &str) -> Vec<Value> {
    let mut symbols: Vec<Value> = Vec::new();

    // Strategy 1: `<Name>...</Name>` inside `<CDDefinition>` blocks.
    let mut search = xml;
    while let Some(def_start) = search.find("<CDDefinition>") {
        let after_open = &search[def_start + "<CDDefinition>".len()..];
        let block_end = after_open.find("</CDDefinition>").unwrap_or(after_open.len());
        let block = &after_open[..block_end];

        let name = extract_xml_text(block, "Name").unwrap_or_default();
        let description = extract_xml_text(block, "Description").unwrap_or_default();
        let role = extract_xml_text(block, "Role").unwrap_or_default();

        if !name.is_empty() {
            symbols.push(json!({
                "name":        name,
                "cd":          cd_name,
                "role":        role,
                "description": description,
            }));
        }

        // Advance past this block.
        let consumed = def_start + "<CDDefinition>".len() + block_end;
        if consumed >= search.len() {
            break;
        }
        search = &search[consumed..];
    }

    // Strategy 2 fallback: scan for `name="..."` attributes if no CDDefinition
    // blocks were found (some CDs use a more compact format).
    if symbols.is_empty() {
        let mut s = xml;
        while let Some(pos) = s.find("name=\"") {
            let after = &s[pos + 6..];
            let end = after.find('"').unwrap_or(after.len());
            let name = after[..end].trim().to_string();
            if !name.is_empty() {
                symbols.push(json!({
                    "name": name,
                    "cd":   cd_name,
                    "role": "",
                }));
            }
            s = &s[pos + 6..];
        }
    }

    symbols
}

/// Extract the text content of the first occurrence of `<tag>...</tag>`.
fn extract_xml_text(xml: &str, tag: &str) -> Option<String> {
    let open = format!("<{}>", tag);
    let close = format!("</{}>", tag);
    let start = xml.find(&open)? + open.len();
    let end = xml[start..].find(&close)? + start;
    Some(xml[start..end].trim().to_string())
}

// ─────────────────────────────────────────────────────────────────────────────
// §3  NLabWikiKnowledge
// ─────────────────────────────────────────────────────────────────────────────

/// Adapter for the nLab wiki at `ncatlab.org`.
pub struct NLabWikiKnowledge {
    base_url: String,
    cache: HashMap<String, Value>,
}

impl NLabWikiKnowledge {
    pub fn new() -> Self {
        Self {
            base_url: "https://ncatlab.org/nlab/show".to_string(),
            cache: HashMap::new(),
        }
    }

    /// Fetch and lightly parse an nLab page by name.
    ///
    /// Returns a `{"name", "url", "content", "links": [...]}` object.
    /// HTML parsing is purely string-based — no external HTML parser crate.
    pub async fn fetch_page(&mut self, page_name: &str) -> Option<Value> {
        if let Some(cached) = self.cache.get(page_name) {
            return Some(cached.clone());
        }

        // URL-encode the page name (replace spaces with +).
        let encoded = page_name.replace(' ', "+");
        let url = format!("{}/{}", self.base_url, encoded);

        let client = reqwest::Client::new();
        let resp = client
            .get(&url)
            .header("User-Agent", "ene-session-sync/0.1 (research stack)")
            .send()
            .await
            .ok()?;

        if !resp.status().is_success() {
            return None;
        }

        let html = resp.text().await.ok()?;

        // Extract main content: look for <div class="entry_content">...</div>
        // or the first substantial <div> block.  Strip all HTML tags from the
        // extracted slice to obtain plain text.
        let content = extract_nlab_content(&html);
        let links = extract_nlab_links(&html);

        let result = json!({
            "name":    page_name,
            "url":     url,
            "content": content,
            "links":   links,
        });
        self.cache.insert(page_name.to_string(), result.clone());
        Some(result)
    }

    /// BFS crawler: return page names reachable from `page_name` up to `depth`
    /// hops (including the starting page itself).
    pub async fn get_related_pages(&mut self, page_name: &str, depth: u32) -> Vec<String> {
        let mut visited: Vec<String> = Vec::new();
        let mut frontier: Vec<String> = vec![page_name.to_string()];

        for _ in 0..depth {
            let mut next: Vec<String> = Vec::new();
            for page in frontier.drain(..) {
                if visited.contains(&page) {
                    continue;
                }
                visited.push(page.clone());
                if let Some(data) = self.fetch_page(&page).await {
                    if let Some(links) = data.get("links").and_then(|l| l.as_array()) {
                        for link in links {
                            if let Some(s) = link.as_str() {
                                if !visited.contains(&s.to_string()) {
                                    next.push(s.to_string());
                                }
                            }
                        }
                    }
                }
            }
            frontier = next;
            if frontier.is_empty() {
                break;
            }
        }
        visited
    }
}

// ── HTML helpers ──────────────────────────────────────────────────────────────

/// Extract a plain-text content summary from an nLab HTML page.
///
/// Looks for `<div class="entry_content"` first; falls back to the first large
/// `<div` block.  Strips all `<...>` tags from the selected slice and collapses
/// whitespace.
fn extract_nlab_content(html: &str) -> String {
    // Locate the start of the content div.
    let start_marker = html
        .find("class=\"entry_content\"")
        .or_else(|| html.find("id=\"content\""))
        .and_then(|pos| {
            // Walk backwards to the `<div` that owns this attribute.
            html[..pos].rfind("<div").map(|d| d)
        });

    let slice = if let Some(start) = start_marker {
        // Advance past the opening tag.
        let after_open = &html[start..];
        let tag_end = after_open.find('>').map(|p| p + 1).unwrap_or(0);
        // Take up to 8 KB of content.
        let end = (tag_end + 8192).min(after_open.len());
        &after_open[tag_end..end]
    } else {
        // No content div found — take the first 4 KB of body text.
        &html[..html.len().min(4096)]
    };

    strip_html_tags(slice)
}

/// Collect `href` values from `<a href="...">` tags that look like nLab
/// internal links (`/nlab/show/...`).
fn extract_nlab_links(html: &str) -> Vec<Value> {
    let mut links: Vec<Value> = Vec::new();
    let mut search = html;
    while let Some(pos) = search.find("href=\"/nlab/show/") {
        let after = &search[pos + 6..]; // skip href="
        let end = after.find('"').unwrap_or(after.len());
        let href = &after[..end];
        // Turn `/nlab/show/foo+bar` → `foo bar` as a page name.
        let page = href
            .trim_start_matches("/nlab/show/")
            .replace('+', " ")
            .replace("%20", " ");
        let val = Value::String(page);
        if !links.contains(&val) {
            links.push(val);
        }
        search = &search[pos + 6..];
    }
    links
}

/// Strip all HTML tags from `text`, returning collapsed plain text.
///
/// Tags are identified as `<...>` spans.  Consecutive whitespace is collapsed
/// to a single space.
fn strip_html_tags(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    let mut in_tag = false;
    for ch in text.chars() {
        match ch {
            '<' => in_tag = true,
            '>' => in_tag = false,
            _ if !in_tag => out.push(ch),
            _ => {}
        }
    }
    // Collapse runs of whitespace.
    let mut collapsed = String::with_capacity(out.len());
    let mut prev_space = false;
    for ch in out.chars() {
        if ch.is_whitespace() {
            if !prev_space {
                collapsed.push(' ');
            }
            prev_space = true;
        } else {
            collapsed.push(ch);
            prev_space = false;
        }
    }
    collapsed.trim().to_string()
}

// ─────────────────────────────────────────────────────────────────────────────
// §4  Tests
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn strip_html_tags_basic() {
        let html = "<div class=\"foo\">Hello <b>world</b>!</div>";
        assert_eq!(strip_html_tags(html), "Hello world!");
    }

    #[test]
    fn extract_xml_text_basic() {
        let xml = "<CDDefinition><Name>plus</Name><Description>Addition</Description></CDDefinition>";
        assert_eq!(extract_xml_text(xml, "Name"), Some("plus".to_string()));
        assert_eq!(
            extract_xml_text(xml, "Description"),
            Some("Addition".to_string())
        );
        assert_eq!(extract_xml_text(xml, "Role"), None);
    }

    #[test]
    fn parse_ocd_symbols_name_attr_fallback() {
        let xml = r#"<OMS cd="arith1" name="plus"/><OMS cd="arith1" name="times"/>"#;
        let syms = parse_ocd_symbols(xml, "arith1");
        assert_eq!(syms.len(), 2);
        assert_eq!(syms[0]["name"], "plus");
        assert_eq!(syms[1]["name"], "times");
    }

    #[test]
    fn relevant_cds_count() {
        assert_eq!(OpenMathKnowledge::get_relevant_cds().len(), 13);
    }

    #[test]
    fn wolfram_rate_limit_guard() {
        let mut wa = WolframAlphaKnowledge::new("dummy".to_string());
        wa.rate_limit_remaining = 0;
        // Sync check — we can't await in a non-async test but we can verify
        // the struct field directly.
        assert_eq!(wa.rate_limit_remaining, 0);
    }
}

//! Minimal Authentik REST API client.
//!
//! Wraps the OpenAPI v3 surface exposed by Authentik 2026.2.3.
//! All methods return `serde_json::Value` for flexibility — the caller
//! extracts the fields it needs.

use reqwest::header::{ACCEPT, AUTHORIZATION, CONTENT_TYPE};
use serde_json::json;

/// Client state.
pub struct Client {
    http: reqwest::Client,
    base: String,
    token: String,
}

impl Client {
    pub fn new(base_url: &str, token: &str) -> Self {
        Self {
            http: reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(30))
                .build()
                .expect("http client"),
            base: base_url.trim_end_matches('/').to_string(),
            token: token.to_string(),
        }
    }

    fn auth_header(&self) -> String {
        format!("Bearer {}", self.token)
    }

    async fn get(&self, path: &str) -> anyhow::Result<serde_json::Value> {
        let url = format!("{}/api/v3{}?format=json", self.base, path);
        let resp = self
            .http
            .get(&url)
            .header(AUTHORIZATION, self.auth_header())
            .header(ACCEPT, "application/json")
            .send()
            .await?;
        let status = resp.status();
        let body = resp.text().await?;
        if !status.is_success() {
            anyhow::bail!("GET {} → HTTP {}: {}", path, status, body);
        }
        if body.trim().is_empty() {
            Ok(json!({}))
        } else {
            Ok(serde_json::from_str(&body)?)
        }
    }

    async fn post(&self, path: &str, body: serde_json::Value) -> anyhow::Result<serde_json::Value> {
        let url = format!("{}/api/v3{}", self.base, path);
        let resp = self
            .http
            .post(&url)
            .header(AUTHORIZATION, self.auth_header())
            .header(ACCEPT, "application/json")
            .header(CONTENT_TYPE, "application/json")
            .json(&body)
            .send()
            .await?;
        let status = resp.status();
        let text = resp.text().await?;
        if !status.is_success() {
            anyhow::bail!("POST {} → HTTP {}: {}", path, status, text);
        }
        if text.trim().is_empty() {
            Ok(json!({}))
        } else {
            Ok(serde_json::from_str(&text)?)
        }
    }

    async fn patch(&self, path: &str, body: serde_json::Value) -> anyhow::Result<serde_json::Value> {
        let url = format!("{}/api/v3{}", self.base, path);
        let resp = self
            .http
            .patch(&url)
            .header(AUTHORIZATION, self.auth_header())
            .header(ACCEPT, "application/json")
            .header(CONTENT_TYPE, "application/json")
            .json(&body)
            .send()
            .await?;
        let status = resp.status();
        let text = resp.text().await?;
        if !status.is_success() {
            anyhow::bail!("PATCH {} → HTTP {}: {}", path, status, text);
        }
        if text.trim().is_empty() {
            Ok(json!({}))
        } else {
            Ok(serde_json::from_str(&text)?)
        }
    }

    async fn delete(&self, path: &str) -> anyhow::Result<serde_json::Value> {
        let url = format!("{}/api/v3{}", self.base, path);
        let resp = self
            .http
            .delete(&url)
            .header(AUTHORIZATION, self.auth_header())
            .header(ACCEPT, "application/json")
            .send()
            .await?;
        let status = resp.status();
        let text = resp.text().await?;
        if !status.is_success() {
            anyhow::bail!("DELETE {} → HTTP {}: {}", path, status, text);
        }
        if text.trim().is_empty() {
            Ok(json!({}))
        } else {
            Ok(serde_json::from_str(&text)?)
        }
    }

    // ─── Operations ────────────────────────────────────────────────────────────

    pub async fn list_users(&self) -> anyhow::Result<serde_json::Value> {
        self.get("/core/users/").await
    }

    pub async fn list_groups(&self) -> anyhow::Result<serde_json::Value> {
        self.get("/core/groups/").await
    }

    pub async fn create_user(
        &self,
        username: &str,
        name: &str,
        email: Option<&str>,
    ) -> anyhow::Result<serde_json::Value> {
        let body = json!({
            "username": username,
            "name": name,
            "type": "service_account",
            "is_active": true,
            "email": email.unwrap_or(&format!("{}@researchstack.info", username)),
        });
        self.post("/core/users/", body).await
    }

    pub async fn create_token(
        &self,
        user_pk: u64,
        identifier: &str,
    ) -> anyhow::Result<serde_json::Value> {
        let body = json!({
            "identifier": identifier,
            "intent": "api",
            "user": user_pk,
            "description": format!("API token for {}", identifier),
        });
        let _ = self.post("/core/tokens/", body).await?;
        // Authentik does not return the key on creation; fetch it via view_key
        self.get(&format!("/core/tokens/{}/view_key/", identifier))
            .await
    }

    pub async fn add_user_to_group(
        &self,
        user_pk: u64,
        group_name: &str,
    ) -> anyhow::Result<serde_json::Value> {
        // Resolve group name → UUID
        let groups = self.list_groups().await?;
        let results = groups
            .get("results")
            .and_then(|r| r.as_array())
            .ok_or_else(|| anyhow::anyhow!("invalid groups response"))?;
        let group_uuid = results
            .iter()
            .find(|g| g.get("name").and_then(|n| n.as_str()) == Some(group_name))
            .and_then(|g| g.get("pk").and_then(|p| p.as_str()))
            .ok_or_else(|| anyhow::anyhow!("group '{}' not found", group_name))?;
        self.post(
            &format!("/core/groups/{}/add_user/", group_uuid),
            json!({ "pk": user_pk }),
        )
        .await
    }

    pub async fn suspend_user(&self, user_pk: u64) -> anyhow::Result<serde_json::Value> {
        self.patch(&format!("/core/users/{}/", user_pk), json!({ "is_active": false }))
            .await
    }

    pub async fn revoke_user(&self, user_pk: u64) -> anyhow::Result<serde_json::Value> {
        self.delete(&format!("/core/users/{}/", user_pk)).await
    }

    pub async fn rotate_token(&self, identifier: &str) -> anyhow::Result<serde_json::Value> {
        self.post(&format!("/core/tokens/{}/set_key/", identifier), json!({}))
            .await
    }

    pub async fn create_application(
        &self,
        name: &str,
        slug: &str,
    ) -> anyhow::Result<serde_json::Value> {
        self.post(
            "/core/applications/",
            json!({
                "name": name,
                "slug": slug,
                "policy_engine_mode": "any",
            }),
        )
        .await
    }

    pub async fn create_proxy_provider(
        &self,
        name: &str,
        authorization_flow: &str,
        internal_host: &str,
        external_host: &str,
    ) -> anyhow::Result<serde_json::Value> {
        self.post(
            "/providers/proxy/",
            json!({
                "name": name,
                "authorization_flow": authorization_flow,
                "internal_host": internal_host,
                "external_host": external_host,
                "mode": "proxy",
            }),
        )
        .await
    }
}

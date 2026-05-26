use anyhow::{Context, Result};
use ene_rds_core::RdsClient;
use serde::{Deserialize, Serialize};
use serde_json::json;
use tracing::info;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WikiPage {
    pub id: i64,
    pub title: String,
    pub slug: String,
    pub content: String,
    pub concept_anchor: Option<String>,
    pub concept_vector: Option<serde_json::Value>,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WikiRevision {
    pub id: i64,
    pub page_id: i64,
    pub content: String,
    pub editor: String,
    pub summary: String,
    pub archive_id: Option<String>,
    pub created_at: String,
}

/// Wiki layer RDS surface — replaces Python ENERDSWikiLayer.
pub struct WikiSurface {
    client: RdsClient,
}

impl WikiSurface {
    pub fn new(client: RdsClient) -> Self {
        Self { client }
    }

    pub async fn init_tables(&self) -> Result<()> {
        let ddl = r#"
CREATE TABLE IF NOT EXISTS ene.wiki_pages (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL DEFAULT '',
    concept_anchor TEXT,
    concept_vector JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ene.wiki_revisions (
    id BIGSERIAL PRIMARY KEY,
    page_id BIGINT NOT NULL REFERENCES ene.wiki_pages(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    editor TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    archive_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ene.wiki_links (
    id BIGSERIAL PRIMARY KEY,
    from_page_id BIGINT NOT NULL REFERENCES ene.wiki_pages(id) ON DELETE CASCADE,
    to_page_id BIGINT NOT NULL REFERENCES ene.wiki_pages(id) ON DELETE CASCADE,
    link_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(from_page_id, to_page_id, link_text)
);

CREATE TABLE IF NOT EXISTS ene.wiki_categories (
    id BIGSERIAL PRIMARY KEY,
    page_id BIGINT NOT NULL REFERENCES ene.wiki_pages(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(page_id, category)
);

CREATE INDEX IF NOT EXISTS idx_wiki_pages_slug ON ene.wiki_pages(slug);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_title ON ene.wiki_pages USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_wiki_revisions_page ON ene.wiki_revisions(page_id, created_at DESC);

ALTER TABLE ene.wiki_pages ADD COLUMN IF NOT EXISTS concept_anchor TEXT;
ALTER TABLE ene.wiki_pages ADD COLUMN IF NOT EXISTS concept_vector JSONB;
ALTER TABLE ene.wiki_pages ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE ene.wiki_pages ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
        "#;
        self.client
            .inner()
            .batch_execute(ddl)
            .await
            .context("init wiki DDL")?;
        info!("wiki schema initialized");
        Ok(())
    }

    pub async fn put_page(
        &self,
        title: &str,
        content: &str,
        editor: &str,
        summary: &str,
    ) -> Result<WikiPage> {
        let slug = title
            .to_lowercase()
            .replace(' ', "-")
            .replace(|c: char| !c.is_alphanumeric() && c != '-', "");
        let row = self.client.inner()
            .query_one(
                "INSERT INTO ene.wiki_pages (title, slug, content, updated_at) \
                 VALUES ($1, $2, $3, now()) \
                 ON CONFLICT (title) DO UPDATE SET slug = EXCLUDED.slug, content = EXCLUDED.content, updated_at = now() \
                 RETURNING id, title, slug, content, concept_anchor, concept_vector, created_at::text, updated_at::text",
                &[&title, &slug, &content],
            )
            .await
            .context("upsert wiki page")?;
        let page = WikiPage {
            id: row.get(0),
            title: row.get(1),
            slug: row.get(2),
            content: row.get(3),
            concept_anchor: row.get(4),
            concept_vector: row.get(5),
            created_at: row.get(6),
            updated_at: row.get(7),
        };
        self.client.inner()
            .execute(
                "INSERT INTO ene.wiki_revisions (page_id, content, editor, summary) VALUES ($1, $2, $3, $4)",
                &[&page.id, &content, &editor, &summary],
            )
            .await
            .context("insert revision")?;
        Ok(page)
    }

    pub async fn get_page(&self, slug: &str) -> Result<Option<WikiPage>> {
        let row = self
            .client
            .inner()
            .query_opt(
                "SELECT id, title, slug, content, concept_anchor, concept_vector, \
                 created_at::text, updated_at::text FROM ene.wiki_pages WHERE slug = $1",
                &[&slug],
            )
            .await
            .context("get wiki page")?;
        Ok(row.map(|r| WikiPage {
            id: r.get(0),
            title: r.get(1),
            slug: r.get(2),
            content: r.get(3),
            concept_anchor: r.get(4),
            concept_vector: r.get(5),
            created_at: r.get(6),
            updated_at: r.get(7),
        }))
    }

    pub async fn search(&self, query: &str, limit: i64) -> Result<Vec<serde_json::Value>> {
        let rows = self.client.inner()
            .query(
                "SELECT id, title, slug, ts_rank(to_tsvector('english', title || ' ' || content), plainto_tsquery('english', $1)) AS rank \
                 FROM ene.wiki_pages \
                 WHERE to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', $1) \
                 ORDER BY rank DESC LIMIT $2",
                &[&query, &limit],
            )
            .await
            .context("search wiki")?;
        Ok(rows
            .iter()
            .map(|r| {
                json!({
                    "id": r.get::<_, i64>(0),
                    "title": r.get::<_, String>(1),
                    "slug": r.get::<_, String>(2),
                    "rank": r.get::<_, f32>(3),
                })
            })
            .collect())
    }

    pub async fn recent(&self, limit: i64) -> Result<Vec<WikiPage>> {
        let rows = self.client.inner()
            .query(
                "SELECT id, title, slug, content, concept_anchor, concept_vector, \
                 created_at::text, updated_at::text FROM ene.wiki_pages ORDER BY updated_at DESC LIMIT $1",
                &[&limit],
            )
            .await
            .context("recent wiki pages")?;
        Ok(rows
            .iter()
            .map(|r| WikiPage {
                id: r.get(0),
                title: r.get(1),
                slug: r.get(2),
                content: r.get(3),
                concept_anchor: r.get(4),
                concept_vector: r.get(5),
                created_at: r.get(6),
                updated_at: r.get(7),
            })
            .collect())
    }
}

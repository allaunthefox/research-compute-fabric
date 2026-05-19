use anyhow::{Context, Result};
use tokio_postgres::{Client, Config, NoTls};
use tracing::{info, warn};

pub mod types;

/// Shared PostgreSQL client with connection management.
pub struct RdsClient {
    client: Client,
}

impl RdsClient {
    /// Connect from a libpq key=value DSN string.
    pub async fn connect(dsn: &str) -> Result<Self> {
        let config: Config = dsn.parse().context("parse PostgreSQL DSN")?;
        let (client, connection) = config.connect(NoTls).await.context("connect to RDS")?;
        tokio::spawn(async move {
            if let Err(e) = connection.await {
                warn!("PostgreSQL connection error: {}", e);
            }
        });
        Ok(Self { client })
    }

    /// Build DSN from standard RDS_* environment variables.
    pub fn dsn_from_env() -> String {
        if let Ok(dsn) = std::env::var("RDS_DSN") {
            return dsn;
        }
        let host = std::env::var("RDS_HOST")
            .unwrap_or_else(|_| "database-1.cluster-c9i0w8eu8fnv.us-east-2.rds.amazonaws.com".into());
        let port = std::env::var("RDS_PORT").unwrap_or_else(|_| "5432".into());
        let user = std::env::var("RDS_USER").unwrap_or_else(|_| "postgres".into());
        let password = std::env::var("RDS_PASSWORD")
            .or_else(|_| std::env::var("RDS_IAM_TOKEN"))
            .unwrap_or_default();
        let dbname = std::env::var("RDS_DB").unwrap_or_else(|_| "postgres".into());
        format!(
            "host={} port={} dbname={} user={} password={} sslmode=require",
            host, port, dbname, user, password
        )
    }

    /// Raw query helper.
    pub async fn execute(&self, sql: &str, params: &[&(dyn tokio_postgres::types::ToSql + Sync)]) -> Result<u64> {
        let rows = self.client.execute(sql, params).await?;
        Ok(rows)
    }

    /// Raw query returning rows.
    pub async fn query(
        &self,
        sql: &str,
        params: &[&(dyn tokio_postgres::types::ToSql + Sync)],
    ) -> Result<Vec<tokio_postgres::Row>> {
        let rows = self.client.query(sql, params).await?;
        Ok(rows)
    }

    /// Ensure the ene schema exists.
    pub async fn init_schema(&self) -> Result<()> {
        self.client
            .execute("CREATE SCHEMA IF NOT EXISTS ene", &[])
            .await
            .context("create ene schema")?;
        info!("ene schema ready");
        Ok(())
    }

    /// Write an ingestion receipt.
    pub async fn write_receipt(
        &self,
        shim_name: &str,
        status: &str,
        sha256: &str,
        record_count: i64,
        source_path: &str,
        meta: &serde_json::Value,
    ) -> Result<()> {
        self.client
            .execute(
                "INSERT INTO ene.ingestion_receipts \
                 (shim_name, status, sha256, record_count, source_path, meta) \
                 VALUES ($1, $2, $3, $4, $5, $6)",
                &[
                    &shim_name,
                    &status,
                    &sha256,
                    &record_count,
                    &source_path,
                    &serde_json::to_value(meta)?,
                ],
            )
            .await
            .context("write receipt")?;
        Ok(())
    }

    pub fn inner(&self) -> &Client {
        &self.client
    }
}

/// Quick SHA-256 of text content (truncated to 64 hex chars for receipt hashes).
pub fn sha256_text(text: &str) -> String {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};
    let mut s = DefaultHasher::new();
    text.hash(&mut s);
    format!("{:016x}", s.finish())
}

/// Format a float vector as pgvector text: [0.1,0.2,...]
pub fn vec_to_pgtext(v: &[f32]) -> String {
    format!("[{}]", v.iter().map(|f| f.to_string()).collect::<Vec<_>>().join(","))
}

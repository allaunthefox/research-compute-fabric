use crate::db::get_pool;
use crate::models::*;
use clap::Subcommand;
use serde_json::json;

#[derive(Subcommand, Debug)]
pub enum Command {
    Tables,
    Schema { table: String },
    Count,
    Sample { domain: String },
    Export,
}

pub async fn run_command(command: Command) -> Result<String, Box<dyn std::error::Error>> {
    let pool = get_pool().await?;
    
    match command {
        Command::Tables => tables_cmd(&pool).await,
        Command::Schema { table } => schema_cmd(&pool, &table).await,
        Command::Count => count_cmd(&pool).await,
        Command::Sample { domain } => sample_cmd(&pool, &domain).await,
        Command::Export => export_cmd(&pool).await,
    }
}

async fn tables_cmd(pool: &sqlx::PgPool) -> Result<String, Box<dyn std::error::Error>> {
    let rows = sqlx::query_as::<_, (String, String)>(
        "SELECT table_name, table_schema 
         FROM information_schema.tables 
         WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
         ORDER BY table_schema, table_name"
    )
    .fetch_all(pool)
    .await?;

    let tables: Vec<TableInfo> = rows.into_iter()
        .map(|(table_name, table_schema)| TableInfo { table_name, table_schema })
        .collect();

    let output = json!({
        "success": true,
        "command": "tables",
        "count": tables.len(),
        "tables": tables
    });

    Ok(serde_json::to_string_pretty(&output)?)
}

async fn schema_cmd(pool: &sqlx::PgPool, table: &str) -> Result<String, Box<dyn std::error::Error>> {
    let rows = if let Some(pos) = table.find('.') {
        let schema = &table[..pos];
        let name = &table[pos + 1..];
        sqlx::query_as::<_, (String, String, String)>(
            "SELECT column_name, data_type, is_nullable 
             FROM information_schema.columns 
             WHERE table_schema = $1 AND table_name = $2
             ORDER BY ordinal_position"
        )
        .bind(schema)
        .bind(name)
        .fetch_all(pool)
        .await?
    } else {
        sqlx::query_as::<_, (String, String, String)>(
            "SELECT column_name, data_type, is_nullable 
             FROM information_schema.columns 
             WHERE table_name = $1 AND table_schema NOT IN ('pg_catalog', 'information_schema')
             ORDER BY ordinal_position"
        )
        .bind(table)
        .fetch_all(pool)
        .await?
    };

    let columns: Vec<ColumnInfo> = rows.into_iter()
        .map(|(column_name, data_type, is_nullable)| ColumnInfo {
            column_name,
            data_type,
            is_nullable,
        })
        .collect();

    let output = json!({
        "success": true,
        "command": "schema",
        "table": table,
        "columns": columns
    });

    Ok(serde_json::to_string_pretty(&output)?)
}

async fn count_cmd(pool: &sqlx::PgPool) -> Result<String, Box<dyn std::error::Error>> {
    let rows = sqlx::query_as::<_, (String, String, i64)>(
        "SELECT domain, archetype, COUNT(*) as count 
         FROM ene.packages 
         GROUP BY domain, archetype 
         ORDER BY domain, archetype"
    )
    .fetch_all(pool)
    .await?;

    let mut by_domain = serde_json::Map::new();
    for (domain, archetype, count) in rows {
        let entry = by_domain.entry(domain).or_insert_with(|| json!({}));
        entry.as_object_mut().unwrap().insert(archetype, json!(count));
    }

    let total: i64 = by_domain.values()
        .flat_map(|v| v.as_object().unwrap().values())
        .map(|v| v.as_i64().unwrap_or(0))
        .sum();

    let output = json!({
        "success": true,
        "command": "count",
        "total_records": total,
        "by_domain": by_domain
    });

    Ok(serde_json::to_string_pretty(&output)?)
}

async fn sample_cmd(pool: &sqlx::PgPool, domain: &str) -> Result<String, Box<dyn std::error::Error>> {
    let rows = sqlx::query_as::<_, (
        String, Option<String>, Option<String>, Option<String>, Option<String>,
        Option<String>, Option<serde_json::Value>, Option<String>, Option<String>
    )>(
        "SELECT pkg, version, domain, tier, archetype, description, tags, source, indexed_utc 
         FROM ene.packages 
         WHERE domain = $1 
         LIMIT 5"
    )
    .bind(domain.to_uppercase())
    .fetch_all(pool)
    .await?;

    let records: Vec<PackageRecord> = rows.into_iter()
        .map(|(pkg, version, domain, tier, archetype, description, tags, source, indexed_utc)| {
            PackageRecord { pkg, version, domain, tier, archetype, description, tags, source, indexed_utc }
        })
        .collect();

    let output = json!({
        "success": true,
        "command": "sample",
        "domain": domain.to_uppercase(),
        "count": records.len(),
        "records": records
    });

    Ok(serde_json::to_string_pretty(&output)?)
}

async fn export_cmd(pool: &sqlx::PgPool) -> Result<String, Box<dyn std::error::Error>> {
    let rows = sqlx::query_as::<_, (
        String, Option<String>, Option<String>, Option<String>, Option<String>,
        Option<String>, Option<serde_json::Value>, Option<String>, Option<String>
    )>(
        "SELECT pkg, version, domain, tier, archetype, description, tags, source, indexed_utc 
         FROM ene.packages 
         ORDER BY domain, indexed_utc DESC"
    )
    .fetch_all(pool)
    .await?;

    let records: Vec<PackageRecord> = rows.into_iter()
        .map(|(pkg, version, domain, tier, archetype, description, tags, source, indexed_utc)| {
            PackageRecord { pkg, version, domain, tier, archetype, description, tags, source, indexed_utc }
        })
        .collect();

    let output = json!({
        "success": true,
        "command": "export",
        "total_records": records.len(),
        "records": records
    });

    Ok(serde_json::to_string_pretty(&output)?)
}

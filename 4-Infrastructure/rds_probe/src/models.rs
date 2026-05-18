use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct TableInfo {
    pub table_name: String,
    pub table_schema: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ColumnInfo {
    pub column_name: String,
    pub data_type: String,
    pub is_nullable: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CountResult {
    pub domain: String,
    pub archetype: String,
    pub count: i64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PackageRecord {
    pub pkg: String,
    pub version: Option<String>,
    pub domain: Option<String>,
    pub tier: Option<String>,
    pub archetype: Option<String>,
    pub description: Option<String>,
    pub tags: Option<serde_json::Value>,
    pub source: Option<String>,
    pub indexed_utc: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CommandOutput {
    pub success: bool,
    pub data: serde_json::Value,
}

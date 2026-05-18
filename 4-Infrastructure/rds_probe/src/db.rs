use sqlx::{postgres::PgPoolOptions, PgPool};
use std::env;
use std::process::Command;

pub struct DbConfig {
    pub host: String,
    pub port: u16,
    pub user: String,
    pub password: String,
    pub dbname: String,
}

fn get_iam_token(host: &str, user: &str, region: &str) -> Option<String> {
    let output = Command::new("aws")
        .args(&[
            "rds", "generate-db-auth-token",
            "--hostname", host,
            "--port", "5432",
            "--username", user,
            "--region", region,
        ])
        .output()
        .ok()?;
    
    if output.status.success() {
        let token = String::from_utf8_lossy(&output.stdout).trim().to_string();
        if !token.is_empty() {
            return Some(token);
        }
    }
    None
}

impl DbConfig {
    pub fn from_env() -> Self {
        let host = env::var("RDS_HOST")
            .unwrap_or("database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com".to_string());
        let user = env::var("RDS_USER").unwrap_or("postgres".to_string());
        let region = env::var("AWS_DEFAULT_REGION").unwrap_or("us-east-1".to_string());
        
        let password = if let Ok(pwd) = env::var("RDS_PASSWORD") {
            if !pwd.is_empty() {
                pwd
            } else {
                get_iam_token(&host, &user, &region).unwrap_or_default()
            }
        } else {
            get_iam_token(&host, &user, &region).unwrap_or_default()
        };
        
        Self {
            host,
            port: env::var("RDS_PORT")
                .unwrap_or("5432".to_string())
                .parse()
                .unwrap_or(5432),
            user,
            password,
            dbname: env::var("RDS_DB").unwrap_or("postgres".to_string()),
        }
    }

    pub fn dsn(&self) -> String {
        format!(
            "postgres://{}:{}@{}:{}/{}?sslmode=require",
            self.user, 
            urlencoding(&self.password),
            self.host, 
            self.port, 
            self.dbname
        )
    }
}

fn urlencoding(s: &str) -> String {
    let mut encoded = String::new();
    for c in s.chars() {
        match c {
            'a'..='z' | 'A'..='Z' | '0'..='9' | '-' | '_' | '.' | '~' => {
                encoded.push(c);
            }
            _ => {
                encoded.push('%');
                encoded.push_str(&format!("{:02X}", c as u8));
            }
        }
    }
    encoded
}

pub async fn create_pool(config: &DbConfig) -> Result<PgPool, sqlx::Error> {
    PgPoolOptions::new()
        .max_connections(1)
        .acquire_timeout(std::time::Duration::from_secs(30))
        .connect(&config.dsn()).await
}

pub async fn get_pool() -> Result<PgPool, Box<dyn std::error::Error>> {
    let config = DbConfig::from_env();
    let pool = create_pool(&config).await?;
    Ok(pool)
}

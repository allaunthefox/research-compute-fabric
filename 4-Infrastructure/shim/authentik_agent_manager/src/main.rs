//! Authentik Agent Manager — Rust shim with DAG execution.
//!
//! # Authentication requirement
//!
//! **You must be authenticated by Authentik to use this tool.**
//! Every operation requires a valid Authentik API token passed via
//! `--token` or the `AUTHENTIK_TOKEN` environment variable.
//! The account associated with the token must have appropriate Authentik
//! permissions (the `llm-agent-controller` service account is in the
//! `authentik Admins` group for this purpose).
//!
//! # Quick start
//!
//! ## 1. Obtain a token
//! The token is stored in SOPS-encrypted secrets:
//! ```bash
//! export AUTHENTIK_TOKEN=$(sops -d --extract '["authentik"]["api_token"]' \
//!   4-Infrastructure/infra/secrets/credentials.json)
//! ```
//!
//! ## 2. Individual commands (familiar CLI)
//! ```bash
//! cargo run --bin authentik_agent_manager -- --token "$AUTHENTIK_TOKEN" list-users
//! cargo run --bin authentik_agent_manager -- --token "$AUTHENTIK_TOKEN" create-agent openclaw-7 "OpenClaw Instance 7"
//! cargo run --bin authentik_agent_manager -- --token "$AUTHENTIK_TOKEN" create-token 42 openclaw-7-token
//! cargo run --bin authentik_agent_manager -- --token "$AUTHENTIK_TOKEN" suspend 42
//! cargo run --bin authentik_agent_manager -- --token "$AUTHENTIK_TOKEN" revoke 42
//! ```
//!
//! ## 2. DAG mode (the primary feature)
//! ```bash
//! cargo run --bin authentik_agent_manager -- execute plan.json
//! ```
//!
//! where `plan.json` is:
//! ```json
//! {
//!   "nodes": [
//!     {
//!       "id": "create_user",
//!       "op": "create_user",
//!       "params": {
//!         "username": "openclaw-7",
//!         "name": "OpenClaw Instance 7"
//!       }
//!     },
//!     {
//!       "id": "create_token",
//!       "op": "create_token",
//!       "depends_on": ["create_user"],
//!       "params": { "identifier": "openclaw-7-token" },
//!       "input_mapping": { "user_pk": "create_user.pk" }
//!     },
//!     {
//!       "id": "add_to_group",
//!       "op": "add_to_group",
//!       "depends_on": ["create_user"],
//!       "params": { "group_name": "AgentManager" },
//!       "input_mapping": { "user_pk": "create_user.pk" }
//!     }
//!   ]
//! }
//! ```
//!
//! # Design
//!
//! - **DAG**: A collection of nodes (operations) with dependency edges.
//! - **Topological execution**: Nodes run in dependency order.
//! - **Input mapping**: Outputs from completed nodes feed into dependent node params.
//! - **Receipts**: Every execution writes a JSON line to
//!   `~/.cache/authentik-dag-receipts.jsonl`.

use authentik_agent_manager::{authentik, execute_dag, load_dag};
use clap::{Parser, Subcommand};
use serde_json::json;

const DEFAULT_BASE_URL: &str = "https://researchstack.info";

#[derive(Parser, Debug)]
#[command(name = "authentik-agent-manager")]
#[command(about = "Manage Authentik identities via CLI or DAG plans")]
struct Cli {
    /// Authentik API token (or set AUTHENTIK_TOKEN env var).
    #[arg(long)]
    token: String,

    /// Authentik base URL.
    #[arg(long, default_value = DEFAULT_BASE_URL)]
    base_url: String,

    #[command(subcommand)]
    cmd: Command,
}

#[derive(Subcommand, Debug)]
enum Command {
    /// Execute a DAG plan from a JSON file.
    Execute {
        /// Path to the DAG JSON file.
        plan: String,
    },
    /// List all users.
    ListUsers,
    /// List all groups.
    ListGroups,
    /// Create a service-account user.
    CreateAgent {
        username: String,
        name: String,
        #[arg(long)]
        email: Option<String>,
    },
    /// Create an API token for a user.
    CreateToken {
        user_pk: u64,
        identifier: String,
    },
    /// Add a user to a group.
    AddToGroup {
        user_pk: u64,
        group_name: String,
    },
    /// Deactivate (soft-delete) a user.
    Suspend {
        user_pk: u64,
    },
    /// Hard-delete a user.
    Revoke {
        user_pk: u64,
    },
    /// Rotate a token key.
    RotateToken {
        identifier: String,
    },
    /// Create an application.
    CreateApplication {
        name: String,
        slug: String,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    let mut cli = Cli::parse();
    if cli.token.is_empty() {
        if let Ok(t) = std::env::var("AUTHENTIK_TOKEN") {
            cli.token = t;
        }
    }
    if cli.token.is_empty() {
        anyhow::bail!("Set --token or AUTHENTIK_TOKEN environment variable");
    }
    let client = authentik::Client::new(&cli.base_url, &cli.token);

    match cli.cmd {
        Command::Execute { plan } => {
            let dag = load_dag(&plan)?;
            execute_dag(&client, &dag).await?;
        }
        Command::ListUsers => {
            let resp = client.list_users().await?;
            println!("{}", serde_json::to_string_pretty(&resp)?);
        }
        Command::ListGroups => {
            let resp = client.list_groups().await?;
            println!("{}", serde_json::to_string_pretty(&resp)?);
        }
        Command::CreateAgent {
            username,
            name,
            email,
        } => {
            let resp = client.create_user(&username, &name, email.as_deref()).await?;
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "pk": resp["pk"],
                    "username": resp["username"],
                    "uuid": resp.get("uuid"),
                }))?
            );
        }
        Command::CreateToken { user_pk, identifier } => {
            let resp = client.create_token(user_pk, &identifier).await?;
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "identifier": identifier,
                    "key": resp.get("key"),
                    "warning": "Store immediately — shown once",
                }))?
            );
        }
        Command::AddToGroup { user_pk, group_name } => {
            let _ = client.add_user_to_group(user_pk, &group_name).await?;
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "ok": true,
                    "user_pk": user_pk,
                    "group": group_name,
                }))?
            );
        }
        Command::Suspend { user_pk } => {
            let resp = client.suspend_user(user_pk).await?;
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "ok": true,
                    "pk": resp["pk"],
                    "is_active": resp["is_active"],
                }))?
            );
        }
        Command::Revoke { user_pk } => {
            let _ = client.revoke_user(user_pk).await?;
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "ok": true,
                    "pk": user_pk,
                    "status": "deleted",
                }))?
            );
        }
        Command::RotateToken { identifier } => {
            let resp = client.rotate_token(&identifier).await?;
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "identifier": resp["identifier"],
                    "key": resp.get("key"),
                    "warning": "Old key invalidated immediately",
                }))?
            );
        }
        Command::CreateApplication { name, slug } => {
            let resp = client.create_application(&name, &slug).await?;
            println!("{}", serde_json::to_string_pretty(&resp)?);
        }
    }

    Ok(())
}

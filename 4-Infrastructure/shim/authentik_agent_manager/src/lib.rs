//! Authentik Agent Manager — library crate.
//!
//! Re-exports the Authentik client, DAG engine, receipt emitter,
//! and shared DAG execution logic so multiple binaries can reuse them.

pub mod authentik;
pub mod dag;
pub mod receipt;

use anyhow::Context;
use serde_json::json;
use std::collections::HashMap;
use tracing::{info, warn};

/// Load and validate a DAG plan from a JSON file.
pub fn load_dag(path: &str) -> anyhow::Result<dag::Dag> {
    let raw = std::fs::read_to_string(path)
        .with_context(|| format!("reading DAG plan from {}", path))?;
    let dag: dag::Dag = serde_json::from_str(&raw)
        .with_context(|| format!("parsing DAG JSON from {}", path))?;
    dag.validate()?;
    Ok(dag)
}

/// Execute a DAG plan against Authentik.
///
/// 1. Compute topological order.
/// 2. For each node, resolve input mappings from already-completed nodes.
/// 3. Execute the Authentik API call.
/// 4. Store the raw output so downstream nodes can reference it.
/// 5. Emit a receipt.
pub async fn execute_dag(
    client: &authentik::Client,
    dag: &dag::Dag,
) -> anyhow::Result<()> {
    let order = dag.topological_order()?;
    let mut outputs: HashMap<String, serde_json::Value> = HashMap::new();
    let mut completed = 0usize;
    let mut failed = 0usize;

    info!("DAG execution starting — {} nodes", order.len());

    for node_id in &order {
        let node = dag.get(node_id).expect("validated DAG has all nodes");
        let mut params = node.params.clone();

        // Resolve input mappings
        for (param_key, mapping) in &node.input_map {
            let parts: Vec<&str> = mapping.splitn(2, '.').collect();
            if parts.len() != 2 {
                anyhow::bail!(
                    "node '{}' input_mapping '{}': bad syntax (expected 'node_id.field')",
                    node.id,
                    mapping
                );
            }
            let src_id = parts[0];
            let src_field = parts[1];
            let src_output = outputs.get(src_id).ok_or_else(|| {
                anyhow::anyhow!(
                    "node '{}' cannot resolve '{}' — upstream node '{}' failed or produced no output",
                    node.id,
                    mapping,
                    src_id
                )
            })?;
            let src_val = src_output.get(src_field).cloned().ok_or_else(|| {
                anyhow::anyhow!(
                    "node '{}' cannot resolve '{}' — field '{}' not found in output of '{}' (available keys: {:?})",
                    node.id,
                    mapping,
                    src_field,
                    src_id,
                    src_output.as_object().map(|o| o.keys().collect::<Vec<_>>())
                )
            })?;

            // Inject into params object
            if let Some(obj) = params.as_object_mut() {
                obj.insert(param_key.clone(), src_val);
            } else {
                anyhow::bail!(
                    "node '{}' params is not a JSON object — cannot inject mapped field '{}'",
                    node.id,
                    param_key
                );
            }
        }

        let result = execute_node(client, node, &params).await;
        let success = result.is_ok();
        let output_val = result.as_ref().ok().cloned();
        let error_msg = result.as_ref().err().map(|e| e.to_string());

        if let Some(ref val) = output_val {
            outputs.insert(node.id.clone(), val.clone());
        }

        // Extract commonly-used fields for the receipt
        let extracted = output_val.as_ref().and_then(|v| {
            let mut m = HashMap::new();
            if let Some(pk) = v.get("pk") {
                m.insert("pk".to_string(), pk.clone());
            }
            if v.get("key").is_some() {
                m.insert("key".to_string(), json!("***"));
            }
            if m.is_empty() { None } else { Some(m) }
        });

        receipt::emit_node(&receipt::NodeReceipt {
            ts: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs(),
            dag_id: "dag".to_string(),
            node_id: node.id.clone(),
            op: format!("{:?}", node.op),
            success,
            error: error_msg,
            outputs: output_val,
            extracted,
        });

        if success {
            info!("node '{}' succeeded", node.id);
            completed += 1;
        } else {
            warn!("node '{}' failed: {}", node.id, result.unwrap_err());
            failed += 1;
        }
    }

    receipt::emit_dag(&receipt::DagReceipt {
        ts: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs(),
        dag_id: "dag".to_string(),
        success: failed == 0,
        nodes_completed: completed,
        nodes_failed: failed,
        error: if failed > 0 {
            Some(format!("{} of {} nodes failed", failed, order.len()))
        } else {
            None
        },
    });

    info!("DAG complete: {}/{} nodes succeeded", completed, order.len());
    if failed > 0 {
        anyhow::bail!("{} node(s) failed", failed);
    }
    Ok(())
}

/// Execute a single node against the Authentik API.
pub async fn execute_node(
    client: &authentik::Client,
    node: &dag::Node,
    params: &serde_json::Value,
) -> anyhow::Result<serde_json::Value> {
    match node.op {
        dag::Operation::ListUsers => client.list_users().await,
        dag::Operation::ListGroups => client.list_groups().await,
        dag::Operation::CreateUser => {
            let username = params["username"]
                .as_str()
                .ok_or_else(|| anyhow::anyhow!("create_user missing 'username'"))?;
            let name = params["name"]
                .as_str()
                .ok_or_else(|| anyhow::anyhow!("create_user missing 'name'"))?;
            let email = params.get("email").and_then(|v| v.as_str());
            client.create_user(username, name, email).await
        }
        dag::Operation::CreateToken => {
            let user_pk = params["user_pk"]
                .as_u64()
                .ok_or_else(|| anyhow::anyhow!("create_token missing 'user_pk'"))?;
            let identifier = params["identifier"]
                .as_str()
                .ok_or_else(|| anyhow::anyhow!("create_token missing 'identifier'"))?;
            client.create_token(user_pk, identifier).await
        }
        dag::Operation::AddToGroup => {
            let user_pk = params["user_pk"]
                .as_u64()
                .ok_or_else(|| anyhow::anyhow!("add_to_group missing 'user_pk'"))?;
            let group_name = params["group_name"]
                .as_str()
                .ok_or_else(|| anyhow::anyhow!("add_to_group missing 'group_name'"))?;
            client.add_user_to_group(user_pk, group_name).await
        }
        dag::Operation::SuspendUser => {
            let user_pk = params["user_pk"]
                .as_u64()
                .ok_or_else(|| anyhow::anyhow!("suspend_user missing 'user_pk'"))?;
            client.suspend_user(user_pk).await
        }
        dag::Operation::RevokeUser => {
            let user_pk = params["user_pk"]
                .as_u64()
                .ok_or_else(|| anyhow::anyhow!("revoke_user missing 'user_pk'"))?;
            client.revoke_user(user_pk).await
        }
        dag::Operation::RotateToken => {
            let identifier = params["identifier"]
                .as_str()
                .ok_or_else(|| anyhow::anyhow!("rotate_token missing 'identifier'"))?;
            client.rotate_token(identifier).await
        }
        dag::Operation::CreateApplication => {
            let name = params["name"]
                .as_str()
                .ok_or_else(|| anyhow::anyhow!("create_application missing 'name'"))?;
            let slug = params["slug"]
                .as_str()
                .ok_or_else(|| anyhow::anyhow!("create_application missing 'slug'"))?;
            client.create_application(name, slug).await
        }
    }
}

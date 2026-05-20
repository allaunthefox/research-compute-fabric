use anyhow::Result;
use clap::Parser;
use ene_node::{EneNode, GossipMessage};
use std::net::SocketAddr;
use std::path::PathBuf;
use tracing::{info, warn};

#[derive(Parser, Debug)]
#[command(name = "ene-node")]
#[command(about = "ENE distributed mesh node — replaces ene_distributed_node.py")]
struct Cli {
    #[arg(long)]
    node_id: Option<String>,
    #[arg(long, default_value = "0.0.0.0:7947")]
    bind: SocketAddr,
    #[arg(long, default_value = "/var/lib/ene/node.db")]
    db: PathBuf,
    #[arg(long, value_delimiter = ',')]
    seed: Vec<String>,
    #[arg(long, default_value = "60")]
    heartbeat_interval: u64,
    #[arg(long)]
    cluster_secret: Option<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let cli = Cli::parse();

    if let Some(parent) = cli.db.parent() {
        let _ = std::fs::create_dir_all(parent);
    }

    let cluster_secret = cli
        .cluster_secret
        .or_else(|| std::env::var("ENE_CLUSTER_SECRET").ok());
    let node = EneNode::new(
        cli.node_id,
        &cli.db,
        cli.bind,
        cli.seed.clone(),
        cluster_secret,
    )
    .await?;
    let node = std::sync::Arc::new(node);

    info!(
        "ENE node {} starting on {}",
        node.identity.node_id, cli.bind
    );

    // ── UDP listener task ────────────────────────────────────────────────
    let listen_node = node.clone();
    let listener = tokio::spawn(async move {
        let mut buf = vec![0u8; 65535];
        loop {
            match listen_node.gossip_socket.recv_from(&mut buf).await {
                Ok((len, from)) => {
                    if let Err(e) = listen_node.process_incoming_gossip(&buf[..len], from).await {
                        warn!("gossip from {}: {}", from, e);
                    }
                }
                Err(e) => {
                    warn!("UDP recv error: {}", e);
                }
            }
        }
    });

    // ── Discovery to seed nodes ────────────────────────────────────────────
    if !cli.seed.is_empty() {
        tokio::time::sleep(std::time::Duration::from_millis(100)).await;
        let payload = serde_json::json!({
            "node_id": &node.identity.node_id,
            "capabilities": &node.identity.capabilities,
        });
        let mut msg = GossipMessage::new(&node.identity.node_id, "discovery", payload);
        msg.sign(&node.cluster_secret);
        for seed in &cli.seed {
            if let Ok(addr) = seed.parse::<SocketAddr>() {
                let data = serde_json::to_vec(&msg).unwrap_or_default();
                let _ = node.gossip_socket.send_to(&data, addr).await;
            } else {
                warn!("invalid seed address: {}", seed);
            }
        }
        info!("sent signed discovery to {} seed nodes", cli.seed.len());
    }

    // ── Heartbeat loop ────────────────────────────────────────────────────
    let beat_node = node.clone();
    let heartbeat = tokio::spawn(async move {
        let mut interval =
            tokio::time::interval(std::time::Duration::from_secs(cli.heartbeat_interval));
        interval.tick().await; // skip immediate first tick
        loop {
            interval.tick().await;
            if let Err(e) = beat_node.send_heartbeat().await {
                warn!("heartbeat failed: {}", e);
            }
        }
    });

    // ── Health/status reporter ────────────────────────────────────────────
    let report_node = node.clone();
    let reporter = tokio::spawn(async move {
        let mut interval = tokio::time::interval(std::time::Duration::from_secs(300));
        loop {
            interval.tick().await;
            let status = report_node.get_status().await;
            let health = report_node.get_mesh_health().await;
            info!(
                "status: {}",
                serde_json::to_string(&status).unwrap_or_default()
            );
            info!(
                "health: {}",
                serde_json::to_string(&health).unwrap_or_default()
            );
        }
    });

    tokio::select! {
        _ = listener => {},
        _ = heartbeat => {},
        _ = reporter => {},
    }

    Ok(())
}

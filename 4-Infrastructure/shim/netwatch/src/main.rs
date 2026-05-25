use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::{Duration, Instant};
use serde::Serialize;

#[derive(Serialize)]
struct ProbeResult {
    target: String,
    kind: String,
    ok: bool,
    elapsed_ms: u64,
    error: Option<String>,
}

fn probe_tcp(host: &str, port: u16, timeout: Duration) -> ProbeResult {
    let start = Instant::now();
    let addr = format!("{}:{}", host, port);
    let ok = match addr.to_socket_addrs() {
        Ok(mut addrs) => match addrs.next() {
            Some(sock_addr) => match TcpStream::connect_timeout(&sock_addr, timeout) {
                Ok(_) => true,
                Err(e) => { eprintln!("tcp {} fail: {}", addr, e); false }
            },
            None => { eprintln!("tcp {}: no address resolved", addr); false }
        },
        Err(e) => { eprintln!("tcp {} resolve failed: {}", addr, e); false }
    };
    ProbeResult {
        target: addr,
        kind: "tcp".into(),
        ok,
        elapsed_ms: start.elapsed().as_millis() as u64,
        error: if ok { None } else { Some("connect failed".into()) },
    }
}

fn probe_http(url: &str, timeout: Duration) -> ProbeResult {
    let start = Instant::now();
    let url_clean = url.trim_start_matches("http://").trim_start_matches("https://");
    let (host_with_port, path) = if let Some(pos) = url_clean.find('/') {
        let path_part = &url_clean[pos..];
        if path_part.is_empty() { (&url_clean[..pos], "/") } else { (&url_clean[..pos], path_part) }
    } else {
        (url_clean, "/")
    };
    let (host, port) = if let Some(pos) = host_with_port.find(':') {
        let p: u16 = host_with_port[pos+1..].parse().unwrap_or(80);
        (&host_with_port[..pos], p)
    } else {
        let p = if url.starts_with("https://") { 443u16 } else { 80u16 };
        (host_with_port, p)
    };

    let addr = format!("{}:{}", host, port);
    let sock_addr = match addr.to_socket_addrs() {
        Ok(mut addrs) => addrs.next(),
        Err(_) => None
    };
    let sock_addr = match sock_addr {
        Some(a) => a,
        None => return ProbeResult {
            target: url.into(),
            kind: "http".into(),
            ok: false,
            elapsed_ms: start.elapsed().as_millis() as u64,
            error: Some("dns resolution failed".into()),
        }
    };
    match TcpStream::connect_timeout(&sock_addr, timeout) {
        Ok(mut stream) => {
            let req = format!("GET {} HTTP/1.0\r\nHost: {}\r\nConnection: close\r\n\r\n", path, host);
            let _ = stream.write_all(req.as_bytes());
            let mut resp = String::new();
            let _ = stream.read_to_string(&mut resp);
            let status = resp.lines().next().unwrap_or("").to_string();
            let ok = status.contains("200") || status.contains("302") || status.contains("301");
            ProbeResult {
                target: url.into(),
                kind: "http".into(),
                ok,
                elapsed_ms: start.elapsed().as_millis() as u64,
                error: if ok { None } else { Some(status) },
            }
        }
        Err(e) => ProbeResult {
            target: url.into(),
            kind: "http".into(),
            ok: false,
            elapsed_ms: start.elapsed().as_millis() as u64,
            error: Some(e.to_string()),
        },
    }
}

fn main() {
    let timeout = Duration::from_secs(5);
    let probes: Vec<ProbeResult> = vec![
        // Cluster nodes
        probe_tcp("100.88.57.96", 22, timeout),       // qfox-1 SSH
        probe_tcp("100.102.173.61", 6443, timeout),    // k3s control plane
        probe_tcp("100.85.244.73", 22, timeout),       // steamdeck
        probe_tcp("100.110.163.82", 22, timeout),      // 361395-1
        probe_tcp("100.80.39.40", 22, timeout),        // self (microvm SSH)
        // Critical services
        probe_http("http://100.80.39.40:8444/health", timeout), // rs-surface
        // DNS resolution
        probe_tcp("1.1.1.1", 53, timeout),              // upstream DNS
    ];

    let results_json = serde_json::to_string_pretty(&probes).unwrap();
    println!("{}", results_json);

    let failures: Vec<&ProbeResult> = probes.iter().filter(|p| !p.ok).collect();
    if !failures.is_empty() {
        eprintln!("FAILED probes: {}", failures.len());
        std::process::exit(1);
    }
}

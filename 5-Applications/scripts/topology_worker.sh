#!/bin/bash
# topology_worker.sh — Connect this node as a worker to the cooperative topology
#
# Usage:  ssh allaun@<node-ip> 'bash -s' < topology_worker.sh
# Or run directly on the worker node.

set -euo pipefail

HEAD_IP="100.88.57.96"
HEAD_PORT=6379

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Cooperative Compute Topology — Worker Join              ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Head Node : ${HEAD_IP}:${HEAD_PORT}                     ║"
echo "║  This Node : $(hostname)                                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"

# Check if ray is installed
if ! command -v ray &>/dev/null; then
    echo "[!] Ray not found. Installing..."
    pip install --user 'ray[default]'
fi

# Check if already connected
if ray status --address="${HEAD_IP}:${HEAD_PORT}" &>/dev/null 2>&1; then
    echo "[✓] Already connected to topology head."
    ray status --address="${HEAD_IP}:${HEAD_PORT}"
    exit 0
fi

# Stop any existing ray processes
ray stop --force 2>/dev/null || true

# Start as worker
echo "[*] Connecting to head node at ${HEAD_IP}:${HEAD_PORT}..."
ray start --address="${HEAD_IP}:${HEAD_PORT}" --block

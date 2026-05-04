#!/usr/bin/env python3
"""
Blockchain RGFlow Proxy — Hierarchical Multicast Swarm

Address space partitioned into IP multicast subnets:
    239.255.<chain_id>.<bucket+1>
    bucket = genome.address >> 15  (top 3 bits, 0..7)

This creates 8 subnets per chain. Peers subscribe only to buckets they care
about, exactly like BitTorrent DHT buckets but deterministic from the
RGFlow surface topology.
"""

import argparse
import asyncio
import json
import socket
import struct
import sqlite3, threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Set

import requests
import zmq

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BTC_ZMQ_HASHBLOCK = "tcp://127.0.0.1:28332"
BTC_RPC_URL = "http://127.0.0.1:8332"
ETH_WS_URL = "ws://127.0.0.1:8546"
ETH_RPC_URL = "http://127.0.0.1:8545"
BTC_CONF_PATH = Path.home() / ".bitcoin" / "bitcoin.conf"
PROXY_OUTPUT_DIR = Path("/home/allaun/Documents/Research Stack/data/crypto_rgflow")
SWARM_MCAST_BASE = "239.255"
SWARM_SERVE_PORT = 28335

CHAIN_ID = {"btc": 1, "eth": 2}
NUM_BUCKETS = 8

# ---------------------------------------------------------------------------
# RPC clients
# ---------------------------------------------------------------------------

def _parse_bitcoin_conf(path: Path) -> Dict[str, str]:
    cfg: Dict[str, str] = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg


class BitcoinRpc:
    def __init__(self, url: str = BTC_RPC_URL, conf_path: Path = BTC_CONF_PATH):
        self.url = url
        cfg = _parse_bitcoin_conf(conf_path)
        self.user = cfg.get("rpcuser", "rgflow")
        self.password = cfg.get("rpcpassword", "rgflow")
        self._session = requests.Session()

    def call(self, method: str, *params) -> Any:
        payload = {"jsonrpc": "1.0", "id": method, "method": method, "params": list(params)}
        r = self._session.post(self.url, json=payload, auth=(self.user, self.password),
                               headers={"Content-Type": "application/json"}, timeout=30)
        r.raise_for_status()
        result = r.json()
        if "error" in result and result["error"] is not None:
            raise RuntimeError(f"BTC RPC error: {result['error']}")
        return result["result"]

    def get_best_block_hash(self) -> str:
        return self.call("getbestblockhash")

    def get_block(self, block_hash: str, verbosity: int = 2) -> Dict[str, Any]:
        return self.call("getblock", block_hash, verbosity)


class EthereumRpc:
    def __init__(self, url: str = ETH_RPC_URL):
        self.url = url
        self._session = requests.Session()
        self._id = 0

    def call(self, method: str, params: List[Any] = None) -> Any:
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or []}
        r = self._session.post(self.url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        r.raise_for_status()
        result = r.json()
        if "error" in result and result["error"] is not None:
            raise RuntimeError(f"ETH RPC error: {result['error']}")
        return result["result"]

    def eth_block_number(self) -> int:
        raw = self.call("eth_blockNumber")
        return int(raw, 16) if isinstance(raw, str) else 0

    def eth_get_block_by_number(self, number: int, full_tx: bool = False) -> Dict[str, Any]:
        return self.call("eth_getBlockByNumber", [hex(number), full_tx])

    def eth_get_block_by_hash(self, block_hash: str, full_tx: bool = False) -> Dict[str, Any]:
        return self.call("eth_getBlockByHash", [block_hash, full_tx])


# ---------------------------------------------------------------------------
# Genome
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RGFlowGenome:
    muBin: int; rhoBin: int; cBin: int; mBin: int; neBin: int; sigBin: int

    def to_dict(self) -> Dict[str, int]:
        return {"muBin": self.muBin, "rhoBin": self.rhoBin, "cBin": self.cBin,
                "mBin": self.mBin, "neBin": self.neBin, "sigBin": self.sigBin}

    @property
    def address(self) -> int:
        return (((((self.muBin * 8 + self.rhoBin) * 8 + self.cBin) * 8 + self.mBin) * 8 + self.neBin) * 8 + self.sigBin)

    @property
    def bucket(self) -> int:
        return self.address >> 15  # top 3 bits → 0..7


def quantize_value(val: float, bins: int = 8, min_val: float = 0.0, max_val: float = 1.0) -> int:
    if max_val <= min_val:
        return 0
    clamped = max(min_val, min(max_val, val))
    norm = (clamped - min_val) / (max_val - min_val)
    return int(norm * (bins - 1)) & 0xFF


def bitcoin_block_to_genome(block: Dict[str, Any], prev_block: Optional[Dict[str, Any]] = None) -> RGFlowGenome:
    time_cur = block.get("time", 0)
    time_prev = prev_block.get("time", time_cur) if prev_block else time_cur
    interblock = max(1, time_cur - time_prev)
    n_tx = block.get("nTx", len(block.get("tx", [])))
    weight = block.get("weight", 0)
    difficulty = block.get("difficulty", 1.0)
    fees = block.get("fees", 0) or 0.0
    import math
    mu = quantize_value(min(interblock, 3600) / 3600.0, 8, 0.0, 1.0)
    rho = quantize_value(min(n_tx, 4000) / 4000.0, 8, 0.0, 1.0)
    c = quantize_value(min(weight, 4_000_000) / 4_000_000.0, 8, 0.0, 1.0)
    m = quantize_value(math.log2(max(1.0, difficulty)) / 90.0, 8, 0.0, 1.0)
    ne = quantize_value(math.log2(max(1, n_tx)) / 12.0, 8, 0.0, 1.0)
    sig = quantize_value(1.0 / (1.0 + fees / 1e6), 8, 0.0, 1.0)
    return RGFlowGenome(mu, rho, c, m, ne, sig)


def ethereum_block_to_genome(block: Dict[str, Any], prev_block: Optional[Dict[str, Any]] = None) -> RGFlowGenome:
    time_cur = int(block.get("timestamp", "0x0"), 16)
    time_prev = int(prev_block.get("timestamp", "0x0"), 16) if prev_block else time_cur
    interblock = max(1, time_cur - time_prev)
    gas_used = int(block.get("gasUsed", "0x0"), 16)
    gas_limit = int(block.get("gasLimit", "0x0"), 16)
    tx_count = len(block.get("transactions", []))
    base_fee = int(block.get("baseFeePerGas", "0x0"), 16)
    import math
    mu = quantize_value(min(interblock, 60) / 60.0, 8, 0.0, 1.0)
    rho = quantize_value(gas_used / max(gas_limit, 1), 8, 0.0, 1.0)
    c = quantize_value(gas_limit / 30_000_000.0, 8, 0.0, 1.0)
    base_fee_gwei = base_fee / 1e9
    m = quantize_value(math.log2(max(1.0, base_fee_gwei + 1.0)) / 20.0, 8, 0.0, 1.0)
    ne = quantize_value(math.log2(max(1, tx_count)) / 12.0, 8, 0.0, 1.0)
    sig = quantize_value(1.0 / (1.0 + base_fee_gwei / 100.0), 8, 0.0, 1.0)
    return RGFlowGenome(mu, rho, c, m, ne, sig)


# ---------------------------------------------------------------------------
# Content store
# ---------------------------------------------------------------------------

class ContentStore:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "btc").mkdir(exist_ok=True)
        (self.output_dir / "eth").mkdir(exist_ok=True)
        self._manifest = open(self.output_dir / "manifest.jsonl", "a")
        self._lock = threading.Lock()
        self._seen_hashes: Set[str] = set()

    def put(self, chain: str, height: int, block_hash: str, genome: RGFlowGenome,
            timestamp: int, raw: Dict[str, Any]) -> Optional[int]:
        if block_hash in self._seen_hashes:
            return None
        self._seen_hashes.add(block_hash)
        addr = genome.address
        entry = {
            "chain": chain, "height": height, "hash": block_hash,
            "timestamp": timestamp, "genome": genome.to_dict(),
            "address": addr, "bucket": genome.bucket, "raw": raw,
        }
        with self._lock:
            addr_path = self.output_dir / chain / f"{addr:05x}.jsonl"
            with open(addr_path, "a") as f:
                f.write(json.dumps(entry, default=str) + "\n")
            self._manifest.write(json.dumps({
                "t": time.time(), "chain": chain, "height": height,
                "address": addr, "bucket": genome.bucket, "hash": block_hash,
            }, default=str) + "\n")
            self._manifest.flush()
            self._insert_swarm_manifest(chain, height, block_hash, genome)
        return addr

    def _insert_swarm_manifest(self, chain: str, height: int, block_hash: str, genome: RGFlowGenome):
        try:
            db_path = Path.home() / "Documents" / "Research Stack" / "data" / "substrate_index.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                """INSERT OR IGNORE INTO swarm_manifest (t, chain, height, block_hash, address, bucket, genome, node)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (time.time(), chain, height, block_hash, genome.address, genome.bucket,
                 json.dumps(genome.to_dict()), "qfox")
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def close(self):
        self._manifest.close()


# ---------------------------------------------------------------------------
# Hierarchical multicast swarm
# ---------------------------------------------------------------------------

def mcast_addr(chain: str, bucket: int) -> str:
    return f"{SWARM_MCAST_BASE}.{CHAIN_ID[chain]}.{bucket + 1}"


class SwarmGossip:
    def __init__(self, store: ContentStore, serve_port: int = SWARM_SERVE_PORT):
        self.store = store
        self.serve_port = serve_port
        self._stop = threading.Event()
        self._sockets: List[socket.socket] = []

    def announce_have(self, chain: str, address: int, bucket: int, height: int):
        msg = json.dumps({"type": "HAVE", "chain": chain, "address": address,
                          "bucket": bucket, "height": height, "t": time.time()})
        group = mcast_addr(chain, bucket)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.sendto(msg.encode(), (group, 28334))
            sock.close()
        except Exception as e:
            print(f"[SWARM] Announce error: {e}")

    def _mcast_listener(self, chain: str, bucket: int):
        group = mcast_addr(chain, bucket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((group, 28334))
        mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(1.0)
        self._sockets.append(sock)
        print(f"[SWARM] Listening {group}:28334 for {chain} bucket {bucket}")
        while not self._stop.is_set():
            try:
                data, addr = sock.recvfrom(4096)
                msg = json.loads(data.decode())
                if msg.get("type") == "HAVE":
                    print(f"[SWARM] {addr[0]} HAS {msg['chain']}#{msg['height']} bucket={msg['bucket']} addr={msg['address']}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[SWARM] Listener error: {e}")
        sock.close()

    def _tcp_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.serve_port))
        server.listen(5)
        server.settimeout(1.0)
        print(f"[SWARM] TCP server on port {self.serve_port}")
        while not self._stop.is_set():
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue
            try:
                data = conn.recv(4096)
                req = json.loads(data.decode())
                if req.get("type") == "WANT":
                    chain = req["chain"]
                    address = req["address"]
                    path = self.store.output_dir / chain / f"{address:05x}.jsonl"
                    if path.exists():
                        with open(path, "r") as f:
                            conn.sendall(f.read().encode())
                    else:
                        conn.sendall(b"{}")
                conn.close()
            except Exception as e:
                print(f"[SWARM] TCP handler error: {e}")
                conn.close()
        server.close()

    def start(self, chains: List[str]):
        for chain in chains:
            for bucket in range(NUM_BUCKETS):
                t = threading.Thread(target=self._mcast_listener, args=(chain, bucket), daemon=True)
                t.start()
        t = threading.Thread(target=self._tcp_server, daemon=True)
        t.start()

    def stop(self):
        self._stop.set()
        for sock in self._sockets:
            try:
                sock.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

def _btc_zmq_worker(store: ContentStore, swarm: SwarmGossip):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(BTC_ZMQ_HASHBLOCK)
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    print("[BTC-ZMQ] Connected to " + BTC_ZMQ_HASHBLOCK)
    btc = BitcoinRpc()
    last_block = None
    while True:
        try:
            msg = socket.recv()
            if len(msg) == 32:
                block_hash = msg[::-1].hex()
                block = btc.get_block(block_hash, verbosity=2)
                genome = bitcoin_block_to_genome(block, last_block)
                addr = store.put("btc", block.get("height"), block_hash, genome,
                                 block.get("time"),
                                 {"nTx": block.get("nTx"), "weight": block.get("weight"),
                                  "difficulty": block.get("difficulty")})
                if addr is not None:
                    swarm.announce_have("btc", addr, genome.bucket, block.get("height"))
                    print(f"[BTC-ZMQ] Block {block['height']} → bucket={genome.bucket} addr={addr}")
                last_block = block
        except zmq.Again:
            continue
        except Exception as e:
            print(f"[BTC-ZMQ] Error: {e}")
            time.sleep(1.0)


def _btc_poller_worker(store: ContentStore, swarm: SwarmGossip):
    btc = BitcoinRpc()
    last_hash = None
    last_block = None
    print("[BTC-POLL] Starting tip poller (30s interval)")
    while True:
        try:
            best_hash = btc.get_best_block_hash()
            if best_hash != last_hash:
                block = btc.get_block(best_hash, verbosity=2)
                genome = bitcoin_block_to_genome(block, last_block)
                addr = store.put("btc", block.get("height"), best_hash, genome,
                                 block.get("time"),
                                 {"nTx": block.get("nTx"), "weight": block.get("weight"),
                                  "difficulty": block.get("difficulty")})
                if addr is not None:
                    swarm.announce_have("btc", addr, genome.bucket, block.get("height"))
                    print(f"[BTC-POLL] Block {block['height']} → bucket={genome.bucket} addr={addr}")
                last_hash = best_hash
                last_block = block
            time.sleep(30.0)
        except Exception as e:
            print(f"[BTC-POLL] Error: {e}")
            time.sleep(60.0)


async def _eth_ws_worker(store: ContentStore, swarm: SwarmGossip):
    import websockets
    eth = EthereumRpc()
    last_block = None
    print(f"[ETH-WS] Connecting to {ETH_WS_URL}")
    async with websockets.connect(ETH_WS_URL) as ws:
        await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1,
                                  "method": "eth_subscribe", "params": ["newHeads"]}))
        resp = await ws.recv()
        print(f"[ETH-WS] Subscribed: {resp}")
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=60.0)
                data = json.loads(msg)
                if "params" in data and "result" in data["params"]:
                    result = data["params"]["result"]
                    block_hash = result.get("hash")
                    block = eth.eth_get_block_by_hash(block_hash, full_tx=False)
                    if block is None:
                        continue
                    genome = ethereum_block_to_genome(block, last_block)
                    height = int(block.get("number", "0x0"), 16)
                    addr = store.put("eth", height, block_hash, genome,
                                     int(block.get("timestamp", "0x0"), 16),
                                     {"gasUsed": block.get("gasUsed"),
                                      "gasLimit": block.get("gasLimit"),
                                      "txCount": len(block.get("transactions", [])),
                                      "baseFeePerGas": block.get("baseFeePerGas")})
                    if addr is not None:
                        swarm.announce_have("eth", addr, genome.bucket, height)
                        print(f"[ETH-WS] Block {height} → bucket={genome.bucket} addr={addr}")
                    last_block = block
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[ETH-WS] Error: {e}")
                await asyncio.sleep(1.0)


def _eth_poller_worker(store: ContentStore, swarm: SwarmGossip):
    eth = EthereumRpc()
    last_hash = None
    last_block = None
    print("[ETH-POLL] Starting tip poller (15s interval)")
    while True:
        try:
            head = eth.eth_block_number()
            block = eth.eth_get_block_by_number(head, full_tx=False)
            if block and block.get("hash") != last_hash:
                genome = ethereum_block_to_genome(block, last_block)
                addr = store.put("eth", head, block.get("hash"), genome,
                                 int(block.get("timestamp", "0x0"), 16),
                                 {"gasUsed": block.get("gasUsed"),
                                  "gasLimit": block.get("gasLimit"),
                                  "txCount": len(block.get("transactions", [])),
                                  "baseFeePerGas": block.get("baseFeePerGas")})
                if addr is not None:
                    swarm.announce_have("eth", addr, genome.bucket, head)
                    print(f"[ETH-POLL] Block {head} → bucket={genome.bucket} addr={addr}")
                last_hash = block.get("hash")
                last_block = block
            time.sleep(15.0)
        except Exception as e:
            print(f"[ETH-POLL] Error: {e}")
            time.sleep(30.0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_proxy(assets: List[str], output_dir: Path):
    store = ContentStore(output_dir)
    swarm = SwarmGossip(store)
    swarm.start(assets)

    threads: List[threading.Thread] = []
    if "btc" in assets:
        threads.append(threading.Thread(target=_btc_zmq_worker, args=(store, swarm), daemon=True))
        threads.append(threading.Thread(target=_btc_poller_worker, args=(store, swarm), daemon=True))
    if "eth" in assets:
        threads.append(threading.Thread(target=_eth_poller_worker, args=(store, swarm), daemon=True))
        def run_ws():
            asyncio.run(_eth_ws_worker(store, swarm))
        threads.append(threading.Thread(target=run_ws, daemon=True))
    for t in threads:
        t.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("[PROXY] Shutting down...")
        swarm.stop()
        store.close()


def main():
    parser = argparse.ArgumentParser(description="Blockchain RGFlow Proxy — Hierarchical Swarm")
    parser.add_argument("--assets", type=str, default="btc,eth")
    parser.add_argument("--output", type=Path, default=PROXY_OUTPUT_DIR / "proxy_swarm")
    args = parser.parse_args()
    assets = [a.strip().lower() for a in args.assets.split(",")]
    run_proxy(assets, args.output)


if __name__ == "__main__":
    main()

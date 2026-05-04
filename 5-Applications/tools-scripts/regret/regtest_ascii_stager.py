# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
"""Regtest PoC: chunk an ASCII art file into OP_RETURN txns, mine blocks with controlled times, and reassemble."""
import argparse
import json
# import subprocess (REMOVED BY WARDEN)
import sys
from pathlib import Path
from scripts.regtest_ascii_tools import chunk_bytes
import time


def cli_call(datadir, *args):
    cmd = ["bitcoin-cli", "-regtest", f"-datadir={datadir}"] + [str(a) for a in args]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        if out == "":
            return None
        try:
            return json.loads(out)
        except Exception:
            return out
    except subprocess.CalledProcessError as e:
        print(f"ERROR running: {' '.join(cmd)}")
        print(e.stdout)
        print(e.stderr)
        raise


def chunk_bytes(b, size):
    for i in range(0, len(b), size):
        yield b[i:i+size]


def create_and_send_opreturn(datadir, hexdata):
    # outputs: a JSON object where key 'data' => hex payload
    outputs = json.dumps({"data": hexdata})
    psbt = cli_call(datadir, "walletcreatefundedpsbt", "[]", outputs)
    if not psbt or "psbt" not in psbt:
        raise RuntimeError("walletcreatefundedpsbt failed or returned no psbt")
    psbt_str = psbt["psbt"]
    processed = cli_call(datadir, "walletprocesspsbt", psbt_str)
    processed_psbt = processed["psbt"] if isinstance(processed, dict) and "psbt" in processed else processed
    finalized = cli_call(datadir, "finalizepsbt", processed_psbt)
    if not finalized or (isinstance(finalized, dict) and not finalized.get("complete", False)):
        raise RuntimeError("finalizepsbt failed to finalize")
    raw = finalized["hex"] if isinstance(finalized, dict) else finalized
    txid = cli_call(datadir, "sendrawtransaction", raw)
    return txid


def mine_block_with_time(datadir, timestamp, blocks=1):
    # setnode time for regtest
    cli_call(datadir, "setmocktime", int(timestamp))
    addr = cli_call(datadir, "getnewaddress")
    return cli_call(datadir, "generatetoaddress", blocks, addr)


def reassemble_from_chain(datadir, start_height=None):
    height = cli_call(datadir, "getblockcount")
    if start_height is None:
        start_height = 0
    chunks = []
    for h in range(start_height, height+1):
        bh = cli_call(datadir, "getblockhash", h)
        blk = cli_call(datadir, "getblock", bh, 2)
        # verbosity=2 gives txs inline
        for tx in blk.get("tx", []):
            for vout in tx.get("vout", []):
                spk = vout.get("scriptPubKey", {})
                if spk.get("type") == "nulldata":
                    asm = spk.get("asm", "")
                    parts = asm.split()
                    if len(parts) >= 2 and parts[0] == "OP_RETURN":
                        data_hex = parts[1]
                        chunks.append(data_hex)
    if not chunks:
        return b""
    joined = bytes.fromhex("".join(chunks))
    return joined


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--datadir", default="5-Applications/out/bitcoind_regtest")
    p.add_argument("--ascii-file", default="5-Applications/scripts/sample_art.txt")
    p.add_argument("--chunk-bytes", type=int, default=60)
    p.add_argument("--mine", action="store_true")
    p.add_argument("--blocks-per-chunk", type=int, default=1)
    p.add_argument("--start-time", type=int, default=int(time.time()))
    p.add_argument("--start-height", type=int, default=0)
    args = p.parse_args()

    datadir = args.datadir
    art = Path(args.ascii_file).read_bytes()
    chunks = list(chunk_bytes(art, args.chunk_bytes))
    print(f"Read {len(art)} bytes; {len(chunks)} chunks (chunk_bytes={args.chunk_bytes})")

    timestamps = []
    t = int(args.start_time)
    for i, c in enumerate(chunks):
        hexdata = c.hex()
        print(f"Creating OP_RETURN tx for chunk {i+1}/{len(chunks)} ({len(c)} bytes)")
        txid = create_and_send_opreturn(datadir, hexdata)
        print("  sent txid:", txid)
        if args.mine:
            mine_block_with_time(datadir, t, blocks=args.blocks_per_chunk)
            print(f"  mined {args.blocks_per_chunk} block(s) at time {t}")
            timestamps.append(t)
            t += 600 * args.blocks_per_chunk

    print("All chunks broadcast")
    print("Reassembling from chain...")
    data = reassemble_from_chain(datadir, start_height=args.start_height)
    out_path = Path("out") / "regtest_reassembled_art.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    print("Wrote reassembled art to:", out_path)


if __name__ == '__main__':
    main()

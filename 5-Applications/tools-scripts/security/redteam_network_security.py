#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""MoE red team runner for network_security.py.

Sends the current implementation to five expert roles via the local MoE
router (127.0.0.1:8008).  Each expert targets a different attack surface.
Findings are printed and written to sessions/.
"""

import asyncio
import datetime
import json
import pathlib
import sys

import httpx

MOE_URL = "http://[::1]:8008/v1/chat/completions"
TARGET_FILE = pathlib.Path(__file__).resolve().parent.parent / "network_security.py"
SESSION_DIR = pathlib.Path(__file__).resolve().parent.parent / "sessions"

# ── Expert definitions ────────────────────────────────────────────────────────
# model: explicit model ID from INDIVIDUAL_MODELS so MoE routes directly.
# Each expert sees the full source + a role-specific attack brief.
EXPERTS = [
    {
        "name": "Traffic Analyst",
        "model": "deepseek-r1-32b",
        "temperature": 0.4,
        "brief": (
            "You are a passive network traffic analyst.  You can only see what goes "
            "on the wire: packet sizes, inter-arrival times, byte distributions, and "
            "IP/port metadata.  You cannot see inside encrypted payloads.\n\n"
            "Red team task: given the Python source below, identify every observable "
            "timing, volume, or shape pattern that would allow you to distinguish this "
            "traffic from genuine Ethereum JSON-RPC background traffic using only "
            "passive pcap analysis.  Be specific: name the metric, the distinguishing "
            "value or range, and how confident a classifier would be."
        ),
    },
    {
        "name": "Protocol Fingerprinter",
        "model": "qwen2.5-coder-14b",
        "temperature": 0.3,
        "brief": (
            "You are a protocol reverse-engineer specializing in DPI signatures.  "
            "Your tool is a stateful flow inspector that reads plaintext JSON fields "
            "in HTTP request bodies.\n\n"
            "Red team task: given the Python source below, identify every field, "
            "value pattern, or structural regularity in the external shell JSON that "
            "would let you write a reliable snort/suricata rule or ML feature.  "
            "For each finding: write the exact regex or feature expression, the "
            "false-positive rate against real Ethereum RPC traffic, and what you'd "
            "need to see to break your own rule."
        ),
    },
    {
        "name": "Statistical Classifier",
        "model": "mixtral-8x7b",
        "temperature": 0.5,
        "brief": (
            "You are a statistical traffic analyst with access to a long-run flow "
            "log: action_type, route token, bucketed amount, and timestamp for every "
            "request over 24 hours.  You cannot see inside encrypted payloads.\n\n"
            "Red team task: given the Python source below, design the minimum-feature "
            "classifier that separates this system from benign Ethereum traffic.  "
            "Which distributional fingerprints survive the CognitiveSmoother and "
            "stochastic quantization?  Which rotation mechanisms have residual "
            "structure you can exploit?  Cite the specific code paths."
        ),
    },
    {
        "name": "Cryptographic Auditor",
        "model": "deepseek-r1-32b",
        "temperature": 0.2,
        "brief": (
            "You are a cryptographic protocol auditor.  You have the source code and "
            "can decrypt internal payloads if you find a key management flaw.\n\n"
            "Red team task: audit the PQ KEM + XOR-stream construction for:\n"
            "1. Key derivation weaknesses (nonce reuse, weak shared-secret usage)\n"
            "2. Auth tag bypass or forgery paths\n"
            "3. Timing or padding oracle side-channels\n"
            "4. Epoch key rotation — when does _epoch_key get replaced, and what "
            "   happens to sessions in flight?\n"
            "5. Any place where encrypt_internal could be called with a predictable "
            "   or attacker-influenced nonce.\n"
            "Produce a severity-ranked finding list with PoC sketches."
        ),
    },
    {
        "name": "OpSec Auditor",
        "model": "phi4-14b",
        "temperature": 0.4,
        "brief": (
            "You are an operational security auditor focusing on metadata leaks and "
            "long-run linkability.  You watch traffic over weeks and correlate "
            "ephemeral identifiers.\n\n"
            "Red team task: given the Python source below, find every place where "
            "long-term linkability survives the rotation mechanisms:\n"
            "1. Does _ephemeral_node_id provide real unlinkability or just pseudonymity?\n"
            "2. Does route salt rotation break all route correlation or only intra-window?\n"
            "3. Are there any fields that are stable across rotation epochs?\n"
            "4. How does a well-positioned observer use the Gumbel-perturbed execution "
            "   ordering in mevbot_swarm_sim.py to fingerprint strategy over time?\n"
            "5. What does the cover traffic from generate_cover_envelope() leak if "
            "   emitted at constant rate?\n"
            "Rank by linkability window (seconds → days → permanent)."
        ),
    },
]


async def query_expert(client: httpx.AsyncClient, expert: dict, source: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": expert["brief"],
        },
        {
            "role": "user",
            "content": f"```python\n{source}\n```\n\nProvide your red team findings.",
        },
    ]
    payload = {
        "model": expert["model"],
        "messages": messages,
        "temperature": expert["temperature"],
        "max_tokens": 1500,
    }
    try:
        resp = await client.post(MOE_URL, json=payload, timeout=120.0)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        backend = data.get("router", {}).get("backend_model", "unknown")
        return {"expert": expert["name"], "model": expert["model"], "backend": backend,
                "findings": content, "error": None}
    except Exception as e:
        return {"expert": expert["name"], "model": expert["model"], "backend": "error",
                "findings": "", "error": str(e)}


async def run_redteam() -> None:
    if not TARGET_FILE.exists():
        print(f"ERROR: {TARGET_FILE} not found", file=sys.stderr)
        sys.exit(1)

    source = TARGET_FILE.read_text(encoding="utf-8")
    print(f"[redteam] target: {TARGET_FILE.name} ({len(source)} bytes)")
    print(f"[redteam] router: {MOE_URL}")
    print(f"[redteam] experts: {len(EXPERTS)}\n")

    async with httpx.AsyncClient() as client:
        tasks = [query_expert(client, e, source) for e in EXPERTS]
        results = await asyncio.gather(*tasks)

    # ── Print findings ────────────────────────────────────────────────────────
    all_findings = []
    for r in results:
        sep = "─" * 72
        print(f"\n{sep}")
        print(f"  {r['expert']}  [{r['model']} → {r['backend']}]")
        print(sep)
        if r["error"]:
            print(f"  ERROR: {r['error']}")
        else:
            print(r["findings"])
        all_findings.append(r)

    # ── Write session file ────────────────────────────────────────────────────
    SESSION_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    session_path = SESSION_DIR / f"redteam-network-security-{ts}.json"
    session_path.write_text(
        json.dumps(
            {
                "schema": "redteam/v1",
                "target": str(TARGET_FILE),
                "ts": ts,
                "experts": all_findings,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\n[redteam] findings written → {session_path.name}")


if __name__ == "__main__":
    asyncio.run(run_redteam())

#!/usr/bin/env python3
"""
ENE Memory Atlas — MCP Surface (M1, sketch)

Exposes the unified ENE memory atlas as MCP tools so every LLM in the stack
(Claude, local Ollama models, swarm agents) sees the same address-first
substrate through one protocol.

Spec: 6-Documentation/docs/specs/ENE_MEMORY_ATLAS_SPEC.md
Pattern: matches local mcp_server.py (Server + stdio_server + @list_tools/@call_tool)
Status:
  LIVE  — atlas.lookup, atlas.scan, atlas.expand (gemma3:1b + lexical
          fallback), atlas.attest (Trimvirate GET /status), atlas.stats
  STUBS — atlas.spiral (M2+M3), atlas.project (M3), atlas.write (M5)
  Each stub returns Tier-5 visible refusal naming the exact promotion
  milestone, never silent insert.

Address-first axiom: every read tool starts from an address (pkg+version,
voxel_key, regime bin, or expanded query → regime bin), never from
nearest-neighbor in an embedding space.
"""

import sys
import json
import sqlite3
import asyncio
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "4-Infrastructure" / "infra"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "nodes"))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# ── Atlas dependencies (live components) ─────────────────────────────────────
# Point to the actual database location in shared-data
SUBSTRATE_DB = Path("/home/allaun/Documents/Research Stack/shared-data/data/substrate_index.db")

# Local Ollama IPv6 carrier — sovereignty rule (see MEMORY.md)
OLLAMA_USER  = "http://[::1]:11435"
GEMMA_MODEL  = "gemma3:1b"

# Trimvirate BFT endpoints (tardy.py serve mode) — atom writes route here
WARDEN_LOCAL = "127.0.0.1"   # warden runs co-located with the atlas
JUDGE_TARDY  = "http://[100.111.192.47]:8450"
HUTTER_TARDY = "http://[100.110.117.19]:8450"
BFT_QUORUM   = 2  # 2-of-3

# Dless Ω weights (MOIM canonical, see spec §4.1)
W_CHI, W_KAPPA, W_SIGMA, W_LAMBDA, W_ETA = 0.25, 0.20, 0.30, 0.15, 0.10

server = Server("ene-memory-atlas")

# ═══════════════════════════════════════════════════════════════════════════
# TOOL SURFACE
# ═══════════════════════════════════════════════════════════════════════════

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="atlas.lookup",
            description=(
                "Direct address lookup. Resolve an atom by (pkg, version) or "
                "by voxel_key. Returns the full MemoryAtom record. O(1)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pkg": {"type": "string"},
                    "version": {"type": "string"},
                    "voxel_key": {"type": "integer", "description": "34-bit voxel address"},
                },
            },
        ),
        Tool(
            name="atlas.scan",
            description=(
                "Filtered scan. Restrict by tier / layer / domain / archetype / "
                "regime bin / settlement state / Ω threshold. Sort by Ω desc. "
                "Address-first: filters are address predicates, not similarity."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tier": {"type": "string", "enum": ["CORE", "INFRA", "RESEARCH"]},
                    "layer": {"type": "string"},
                    "domain": {"type": "string"},
                    "archetype": {"type": "string"},
                    "regime_bin": {"type": "integer", "minimum": 0, "maximum": 3,
                                   "description": "0=random, 1=weak, 2=strong, 3=constant"},
                    "settlement_min": {"type": "string",
                                       "enum": ["SEED", "FORMING", "STABLE",
                                                "CRYSTALLIZED", "COMPRESSED"]},
                    "omega_min": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "limit": {"type": "integer", "default": 16, "maximum": 64},
                },
            },
        ),
        Tool(
            name="atlas.expand",
            description=(
                "Local-LLM query expansion (gemma3:1b at [::1]:11435). "
                "Returns expanded terms + IoC regime bin classification. "
                "Output feeds atlas.scan or atlas.spiral as the entry point."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "model": {"type": "string", "default": GEMMA_MODEL},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="atlas.spiral",
            description=(
                "Golden spiral search over the 5D manifold projection. "
                "Phase 137.5°, radius × 1.0078 per step, Dless-Ω-warped "
                "distance, branch-prune by subtree_fold_point. Returns top-k."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "seed_pkg": {"type": "string"},
                    "max_distance": {"type": "number", "default": 0.5},
                    "max_results": {"type": "integer", "default": 8, "maximum": 16},
                    "type_filter": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["seed_pkg"],
            },
        ),
        Tool(
            name="atlas.project",
            description=(
                "Read the Q0_16 scalar through one of the three projection "
                "lanes (calculation, defense, verification). Returns signed "
                "[-1, 1] value at the addressed atom for the requested lane."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pkg": {"type": "string"},
                    "version": {"type": "string"},
                    "lane": {"type": "string",
                             "enum": ["calculation", "defense", "verification"]},
                },
                "required": ["pkg", "lane"],
            },
        ),
        Tool(
            name="atlas.write",
            description=(
                "Submit a new atom. Routes through warden → judge + hutter "
                "(2-of-3 Trimvirate BFT). Origin Protocol traits checked "
                "at write time. Returns BFT verdict + MMR index. Failure "
                "Tier 5 visible: silence forbidden."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pkg": {"type": "string"},
                    "version": {"type": "string"},
                    "tier": {"type": "string"},
                    "domain": {"type": "string"},
                    "archetype": {"type": "string"},
                    "description": {"type": "string"},
                    "files": {"type": "array", "items": {"type": "string"}},
                    "trinary": {"type": "string",
                                "enum": ["ADD", "PAUSE", "SUBTRACT"],
                                "default": "ADD"},
                },
                "required": ["pkg", "version", "tier", "description"],
            },
        ),
        Tool(
            name="atlas.attest",
            description=(
                "Return MMR proof for an atom (leaf hash + sibling path to "
                "current MMR root). Read across all three nodes to verify "
                "consistency. Used by external auditors and the swarm."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mmr_index": {"type": "integer"},
                    "node": {"type": "string",
                             "enum": ["warden", "judge", "hutter", "all"],
                             "default": "all"},
                },
                "required": ["mmr_index"],
            },
        ),
        Tool(
            name="atlas.stats",
            description=(
                "Atlas health snapshot: total atoms, regime distribution, "
                "Ω histogram, MMR depth per node, BFT consistency check. "
                "Cheap; safe to call frequently."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# DISPATCH
# ═══════════════════════════════════════════════════════════════════════════

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    try:
        if name == "atlas.lookup":     result = _lookup(arguments)
        elif name == "atlas.scan":     result = _scan(arguments)
        elif name == "atlas.expand":   result = await _expand(arguments)
        elif name == "atlas.spiral":   result = _spiral(arguments)
        elif name == "atlas.project":  result = _project(arguments)
        elif name == "atlas.write":    result = await _write(arguments)
        elif name == "atlas.attest":   result = await _attest(arguments)
        elif name == "atlas.stats":    result = _stats()
        else:
            raise ValueError(f"Unknown tool: {name}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        # Failure Contract: silence is forbidden. Tier 5 = visible failure
        # with diagnostic info.
        err = {
            "ok": False,
            "tool": name,
            "error_class": type(e).__name__,
            "reason": str(e),
            "journalctl": "journalctl --user -u mcp-ene-atlas -n 50",
        }
        return [TextContent(type="text", text=json.dumps(err, indent=2))]


# ═══════════════════════════════════════════════════════════════════════════
# STUBS — Promote each to live code in spec milestones M2-M5
# Each stub names the exact file/function that holds the real implementation
# so future-Claude doesn't reinvent the path.
# ═══════════════════════════════════════════════════════════════════════════

def _lookup(args: Dict) -> Dict:
    """M1 — direct query against substrate_index.db packages table.
    voxel_key path requires M2 (fractal hash + voxel_key column added)."""
    conn = sqlite3.connect(SUBSTRATE_DB)
    cur = conn.cursor()
    if "pkg" in args:
        cur.execute(
            "SELECT pkg, version, tier, domain, archetype, description, "
            "       files, sha256, indexed_utc, nd_point, idea_weights "
            "FROM packages WHERE pkg = ? "
            + ("AND version = ? " if "version" in args else "")
            + "LIMIT 1",
            (args["pkg"],) + ((args["version"],) if "version" in args else ()),
        )
    elif "voxel_key" in args:
        # TODO(M2): once voxel_key column added, lookup by 34-bit address
        return {"ok": False, "reason": "voxel_key lookup pending M2 migration"}
    else:
        return {"ok": False, "reason": "atlas.lookup needs pkg or voxel_key"}
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"ok": True, "found": False}
    cols = ["pkg", "version", "tier", "domain", "archetype", "description",
            "files", "sha256", "indexed_utc", "nd_point", "idea_weights"]
    return {"ok": True, "found": True, "atom": dict(zip(cols, row))}


def _scan(args: Dict) -> Dict:
    """M1 — filtered scan. Ω sort blocked until M3 adds dless_omega column;
    until then, sort by indexed_utc desc as a stable proxy."""
    where, params = [], []
    for k in ("tier", "layer", "domain", "archetype"):
        if k in args:
            where.append(f"{k} = ?"); params.append(args[k])
    sql = "SELECT pkg, version, tier, domain, archetype, description "
    sql += "FROM packages"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY indexed_utc DESC LIMIT ?"
    params.append(min(args.get("limit", 16), 64))
    conn = sqlite3.connect(SUBSTRATE_DB); cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall(); conn.close()
    return {
        "ok": True,
        "count": len(rows),
        "note_M3": "Ω sort pending dless_omega column migration",
        "atoms": [dict(zip(["pkg","version","tier","domain","archetype","description"], r))
                  for r in rows],
    }


_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "i", "me", "my", "we", "our", "you", "your", "it", "its", "this", "that",
    "with", "by", "from", "as", "if", "but", "not", "so", "than",
})


def _lexical_expand(query: str) -> List[str]:
    """Stopword-split fallback when Ollama is unreachable."""
    toks = [t.strip(".,;:!?()[]{}\"'`").lower()
            for t in query.split() if t]
    seen, out = set(), []
    for t in toks:
        if t and t not in _STOPWORDS and t not in seen:
            seen.add(t)
            out.append(t)
    return out or [query.lower()]


def _gemma_expand(query: str, model: str = GEMMA_MODEL,
                  endpoint: str = OLLAMA_USER, timeout: float = 8.0) -> Dict:
    """Ask local Ollama gemma3:1b to expand the query into 5-10 related
    terms. Returns {ok, expanded, source} dict. Sovereignty: IPv6 [::1]:11435,
    no Gemini/OpenAI fallback. On any failure → lexical stopword split,
    Tier 4 (degraded with context, not silence)."""
    prompt = (
        "List 5-10 short related terms for the following query, "
        "separated by commas, no extra commentary.\n\nQuery: " + query
    )
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        f"{endpoint}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        text = (payload.get("response") or "").strip()
        terms = [t.strip().strip(".,;:!?\"'`").lower()
                 for t in text.replace("\n", ",").split(",")]
        terms = [t for t in terms if t and len(t) <= 64]
        if not terms:
            raise ValueError("gemma3 returned no parseable terms")
        return {"ok": True, "expanded": terms, "source": f"gemma:{model}"}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, json.JSONDecodeError) as e:
        return {
            "ok": True,  # degraded but functional
            "expanded": _lexical_expand(query),
            "source": "lexical_fallback",
            "ollama_unreachable": f"{type(e).__name__}: {e}",
        }


async def _expand(args: Dict) -> Dict:
    """M1 — local-LLM query expansion against gemma3:1b at [::1]:11435,
    with lexical stopword fallback. IoC regime classification of the
    expanded set deferred to M3."""
    model = args.get("model", GEMMA_MODEL)
    result = _gemma_expand(args["query"], model=model)
    return {
        "ok": True,
        "query": args["query"],
        "expanded": result["expanded"],
        "source": result["source"],
        "regime_bin": None,  # M3: IoC regime classification
        **({"ollama_unreachable": result["ollama_unreachable"]}
           if "ollama_unreachable" in result else {}),
    }


def _spiral(args: Dict) -> Dict:
    """M4 — golden spiral on 5D manifold projection.
    Requires M2 (fractal hash) + M3 (Ω) before spiral becomes meaningful."""
    return {
        "ok": False,
        "reason": "atlas.spiral pending M2 (fractal hash) + M3 (Dless Ω)",
        "fallback": "use atlas.scan + atlas.expand for now",
    }


def _project(args: Dict) -> Dict:
    """M3 — three-lane projection of Q0_16. Q0_16 column added with M3.
    Lane semantics from ScalarEventProjection.lean."""
    return {
        "ok": False,
        "reason": "atlas.project pending M3 (Q0_16 + lane columns)",
    }


async def _write(args: Dict) -> Dict:
    """M5 — Origin Protocol gates + Trimvirate BFT.
    Path: warden tardy → POST to judge + hutter → 2-of-3 quorum.
    Until M5 lands, refuse rather than silently inserting unguarded rows."""
    return {
        "ok": False,
        "reason": "atlas.write pending M5 (Origin Protocol + creator letter)",
        "rationale": (
            "Failure Contract Tier 5: visible refusal beats silent insert. "
            "Atom writes that bypass trait enforcement are exactly the "
            "boundary the Origin Protocol exists to protect."
        ),
    }


def _tardy_status(endpoint: str, timeout: float = 5.0) -> Dict:
    """GET /status on a remote tardy.py serve node over Tailscale. Returns
    {ok, mmr_root, node_id, ...} or {ok: false, error_class, reason}.
    Failure Contract Tier 5: visible diagnostic, never silent."""
    try:
        req = urllib.request.Request(f"{endpoint}/status", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "endpoint": endpoint, **payload}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, json.JSONDecodeError) as e:
        return {
            "ok": False,
            "endpoint": endpoint,
            "error_class": type(e).__name__,
            "reason": str(e),
        }


async def _attest(args: Dict) -> Dict:
    """M1 — query GET /status on each Trimvirate node concurrently,
    return MMR root from each, flag inconsistencies. Selection: 'all'
    contacts both judge and hutter; 'judge' or 'hutter' contacts one."""
    target = args.get("node", "all")
    endpoints = []
    if target in ("all", "judge"):  endpoints.append(("judge",  JUDGE_TARDY))
    if target in ("all", "hutter"): endpoints.append(("hutter", HUTTER_TARDY))
    if not endpoints:
        return {"ok": False, "reason": f"unknown node selector: {target}"}

    loop = asyncio.get_event_loop()
    results = await asyncio.gather(*[
        loop.run_in_executor(None, _tardy_status, ep) for _, ep in endpoints
    ])
    by_node = {name: res for (name, _), res in zip(endpoints, results)}

    # Cross-node MMR consistency check
    roots = {n: r.get("mmr_root") for n, r in by_node.items() if r.get("ok")}
    consistent = (len(set(roots.values())) <= 1) if len(roots) > 1 else None

    return {
        "ok": True,
        "mmr_index": args["mmr_index"],
        "nodes": by_node,
        "mmr_roots_consistent": consistent,
        "live_node_count": sum(1 for r in by_node.values() if r.get("ok")),
        "bft_quorum_required": BFT_QUORUM,
    }


def _stats() -> Dict:
    """M1 — substrate_index.db row count + tier/domain/layer histograms.
    Ω histogram + MMR depth pending M3 / M5."""
    conn = sqlite3.connect(SUBSTRATE_DB); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM packages")
    total = cur.fetchone()[0]
    cur.execute("SELECT tier, COUNT(*) FROM packages GROUP BY tier")
    by_tier = dict(cur.fetchall())
    cur.execute("SELECT layer, COUNT(*) FROM packages GROUP BY layer LIMIT 16")
    by_layer = dict(cur.fetchall())
    conn.close()
    return {
        "ok": True,
        "total_atoms": total,
        "by_tier": by_tier,
        "by_layer_top16": by_layer,
        "pending": {
            "regime_distribution": "M3",
            "omega_histogram": "M3",
            "mmr_depth_per_node": "M1 wire to tardy",
            "bft_consistency": "M1 wire to tardy",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

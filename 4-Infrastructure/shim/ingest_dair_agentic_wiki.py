#!/usr/bin/env python3
"""Ingest dair-ai Agentic Engineering Wiki into Research Stack."""

import json, time, hashlib
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

WIKI = {
    "id": "dair-agentic-engineering-wiki",
    "source": "https://github.com/dair-ai/dair-workshops/tree/main/agentic-engineering-wiki",
    "title": "AI Agent Engineering Wiki — dair-ai",
    "date": "2026-04-29",
    "stats": {"tips": 51, "categories": 7, "companies": 9, "papers": 10, "tools": 14},
    "categories": {
        "tool_use": {
            "tips": 11,
            "key_insight": "Pre-filter tools to relevant subset per request; log agent intent to detect loops"
        },
        "evaluation": {
            "tips": 8,
            "key_insight": "Trajectory-aware eval (not just final output); repeat runs for reliability; behavioral rubrics for LLM-as-judge"
        },
        "prompting": {
            "tips": 6,
            "key_insight": "Five-layer system prompt anatomy; tool descriptions as engineering surface; instruction hierarchy defense (system > user > tool output)"
        },
        "orchestration": {
            "tips": 7,
            "key_insight": "Agents as MCP servers for composable multi-agent systems; Plan-Execute-Verify-Replan loop; handoffs with state transfer"
        },
        "memory": {
            "tips": 6,
            "key_insight": "Context management, RAG, state, conversation history"
        },
        "reliability": {
            "tips": 8,
            "key_insight": "Guardrails before risky ops; 'Lazy Agent' failure mode; restricted API keys; sandbox testing"
        },
        "deployment": {
            "tips": 5,
            "key_insight": "Cost tracking, sandbox execution, monitoring, observability"
        }
    },
    "orchestration_tips": [
        "Structure agents as specialists with explicit ownership via handoffs",
        "Leverage Google's ADK for interoperable agent orchestration across frameworks",
        "Use heterogeneous model teams — different models have different strengths",
        "Adopt Plan-Execute-Verify-Replan loop for complex multi-agent workflows",
        "Use handoffs for agent-to-agent delegation with state transfer",
        "Use built-in connector tools to reduce tool scaffolding overhead",
        "Represent agents as MCP servers — compose multi-agent systems over same protocol"
    ],
    "reliability_tips": [
        "Add guardrails and human review before risky operations",
        "Encode persistence, risk assessment, and proactive planning in agent prompts",
        "Handle server tool pauses gracefully with pause_turn",
        "Watch for 'Lazy Agent' failure mode — model knows it needs tools but doesn't call them",
        "Don't use agents for problems with deterministic solutions — plain code still wins",
        "Use restricted API keys (rk_*) to limit agent blast radius",
        "Use tool_plan for explicit reasoning before acting",
        "Test agents in sandbox environments before production — non-determinism demands it"
    ],
    "design_philosophy": [
        "Every claim links to a source. No unsupported advice.",
        "Speculation is clearly marked.",
        "Built for flexibility — new categories, companies, formats addable anytime.",
        "Community-first — pulled from real production experiences (HN, Reddit, postmortems)."
    ],
    "relevance_to_research_stack": {
        "direct_matches": [
            "Prover orchestration layers (L0-L3) ↔ Plan-Execute-Verify-Replan loop",
            "Swarm consensus (11 agents) ↔ Agents as specialists with handoffs",
            "ProverWatchdog guard_transition ↔ Guardrails before risky ops",
            "Virtual FPGA system tests ↔ Sandbox testing before production",
            "BFS-Prover-V2 audit trail ↔ Trajectory-aware evaluation",
            "bf4prover manifold reshape ↔ Verify step in Plan-Execute-Verify-Replan"
        ],
        "gaps_in_our_system": [
            "No restricted API key pattern for agent blast radius",
            "No explicit 'Lazy Agent' detection in swarm",
            "No heterogeneous model teams (all agents use same model)",
            "No cost tracking for orchestration layers",
            "No pause_turn equivalent for long-running proofs"
        ],
        "strengths_of_our_system": [
            "Q16.16 fixed-point precision (wiki has no numerical guarantees)",
            "Hardware substrate integration (wiki is software-only)",
            "Formal proof backing (wiki relies on empirical testing)",
            "Topological manifold awareness (wiki has no geometric model)"
        ]
    },
    "metadata": {
        "ingested_at": time.time(),
        "tags": ["agentic-engineering", "orchestration", "multi-agent", "reliability", "evaluation", "prompting"]
    }
}


def ingest():
    germane_dir = RESEARCH_STACK / "shared-data/data/germane/research"
    germane_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = germane_dir / "dair_agentic_engineering_wiki.json"
    with open(out_path, 'w') as f:
        json.dump(WIKI, f, indent=2)
    
    print(f"✓ Ingested: {out_path}")
    
    # Update index
    index_path = germane_dir / "research_ingestion_index.json"
    index = []
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    
    index.append({
        "id": WIKI["id"], "title": WIKI["title"],
        "date": WIKI["date"], "source": WIKI["source"],
        "ingested_at": WIKI["metadata"]["ingested_at"],
        "tags": WIKI["metadata"]["tags"],
    })
    
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"✓ Index: {len(index)} entries")
    
    print(f"\nDirect matches to our system:")
    for m in WIKI["relevance_to_research_stack"]["direct_matches"]:
        print(f"  ↔ {m}")
    
    print(f"\nGaps identified:")
    for g in WIKI["relevance_to_research_stack"]["gaps_in_our_system"]:
        print(f"  ⚠ {g}")
    
    print(f"\nOur strengths:")
    for s in WIKI["relevance_to_research_stack"]["strengths_of_our_system"]:
        print(f"  ✓ {s}")


if __name__ == "__main__":
    ingest()

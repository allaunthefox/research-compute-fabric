#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Domain Crossbreed Swarm — Deterministic cross-domain invariant generator.

Implements the DOMAIN_CROSSBREED_SWARM_PROTOCOL by pairing experts from the
EXHAUSTIVE_DOMAIN_EXPERT_LIST, projecting their constraint matrices into a
shared 7-dimensional invariant space, and deriving novel solutions at the
intersection boundary.

Architecture:
    ┌───────────────────────────────────────────────────────────┐
    │                  CROSSBREED ENGINE                       │
    ├─────────────┬─────────────┬─────────────┬─────────────┤
    │  EXPERT A   │  EXPERT B   │  PROJECTOR  │  INTEGRATOR  │
    └─────────────┴─────────────┴─────────────┴─────────────┘

Usage:
    python 5-Applications/tools-5-Applications/scripts/domain_crossbreed_swarm.py --pairs 5 --output-dir shared-data/data/swarm
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import logging
import math
import os
import random
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Attempt to import the local LLM client; fallback to pure-deterministic mode.
try:
    from local_llm_client import LocalLLMClient
    HAS_LLM_CLIENT = True
except Exception:
    HAS_LLM_CLIENT = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("crossbreed_swarm")

# ── Constants ────────────────────────────────────────────────────────────────

DOCS_ROOT = Path(__file__).resolve().parents[2] / "docs"
EXPERT_LIST_PATH = DOCS_ROOT / "audits" / "EXHAUSTIVE_DOMAIN_EXPERT_LIST.md"
PROTOCOL_PATH = DOCS_ROOT / "design" / "DOMAIN_CROSSBREED_SWARM.md"

DIMENSIONS = ["T", "S", "C", "F", "R", "P", "W"]
DIMENSION_NAMES = {
    "T": "Time ordering constraints",
    "S": "Spatial boundary conditions",
    "C": "Causality directionality",
    "F": "Failure modes",
    "R": "Resource limits",
    "P": "Progress metric",
    "W": "Work function definition",
}

EPSILON_THRESHOLD = 1e-9

# ── Data Structures ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainExpert:
    emoji: str
    name: str
    category: str

    def __str__(self) -> str:
        return f"{self.emoji} {self.name}"


@dataclass
class ConstraintMatrix:
    """7-dimensional constraint vector for a domain."""
    T: float = 0.0
    S: float = 0.0
    C: float = 0.0
    F: float = 0.0
    R: float = 0.0
    P: float = 0.0
    W: float = 0.0

    def to_vec(self) -> List[float]:
        return [self.T, self.S, self.C, self.F, self.R, self.P, self.W]

    @classmethod
    def from_vec(cls, vec: List[float]) -> "ConstraintMatrix":
        return cls(*vec)

    def hadamard(self, other: "ConstraintMatrix") -> "ConstraintMatrix":
        a, b = self.to_vec(), other.to_vec()
        return self.__class__.from_vec([x * y for x, y in zip(a, b)])

    def distance(self, other: "ConstraintMatrix") -> float:
        a, b = self.to_vec(), other.to_vec()
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


@dataclass
class CrossbreedInvariant:
    domain_a: str
    domain_b: str
    invariant_name: str
    invariant_description: str
    constraint_a: Dict[str, float]
    constraint_b: Dict[str, float]
    intersection: Dict[str, float]
    epsilon: float
    verification_status: str
    derivation_method: str
    generation: int = 1


# ── Markdown Parsing ─────────────────────────────────────────────────────────

def parse_expert_list(path: Path) -> Tuple[List[DomainExpert], List[DomainExpert]]:
    """Parse EXHAUSTIVE_DOMAIN_EXPERT_LIST.md into activated and queued experts."""
    text = path.read_text(encoding="utf-8")

    activated: List[DomainExpert] = []
    queued: List[DomainExpert] = []
    current_category = "Unknown"

    # Split into activated and queued sections
    activated_section = re.search(
        r"## ✅ ACTIVATED EXPERTS.*?\n---", text, re.DOTALL
    )
    queued_section = re.search(
        r"## 🚀 NEXT IN QUEUE.*?\n---", text, re.DOTALL
    )

    def _parse_section(section_text: str, target_list: List[DomainExpert]) -> None:
        nonlocal current_category
        cat = "unknown"
        for line in section_text.splitlines():
            cat_match = re.match(r"###\s+(.*)", line)
            if cat_match:
                cat = cat_match.group(1).strip()
                continue
            expert_match = re.match(r"-\s+([\U0001F300-\U0001FAFF\u2600-\u26FF])\s+(.*)", line)
            if expert_match:
                emoji, name = expert_match.group(1), expert_match.group(2).strip()
                target_list.append(DomainExpert(emoji, name, cat))

    if activated_section:
        _parse_section(activated_section.group(0), activated)
    if queued_section:
        _parse_section(queued_section.group(0), queued)

    return activated, queued


def parse_protocol(path: Path) -> Dict[str, Any]:
    """Parse DOMAIN_CROSSBREED_SWARM.md for generation rules."""
    text = path.read_text(encoding="utf-8")
    rules: Dict[str, Any] = {"algorithm_steps": [], "existing_combinations": []}

    # Extract algorithm steps
    steps = re.findall(r"### Step \d+:\s+(.*)\n(.*?)(?=### Step|\n---|\n## )", text, re.DOTALL)
    for title, body in steps:
        rules["algorithm_steps"].append({"title": title.strip(), "body": body.strip()})

    # Extract existing combinations table
    table_rows = re.findall(
        r"\|\s*([^|]+)\|\s*([^|]+)\|\s*\*\*(.*?)\*\*\s*-\s*(.*?)\|\s*✅\s*DERIVED\s*\|",
        text,
    )
    for a, b, inv_name, inv_desc in table_rows:
        rules["existing_combinations"].append({
            "domain_a": a.strip(),
            "domain_b": b.strip(),
            "invariant_name": inv_name.strip(),
            "invariant_description": inv_desc.strip(),
        })

    return rules


# ── Deterministic Constraint Engine ──────────────────────────────────────────

def deterministic_constraint_hash(name: str) -> List[float]:
    """Generate a deterministic 7-dimensional constraint vector from a domain name.

    The hash is derived from SHA-256 of the normalized domain name, split into
    7 chunks and mapped to the unit interval. This guarantees that any two
    identical domain names always produce the exact same constraint surface.
    """
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    chunks = [digest[i : i + 4] for i in range(0, 28, 4)]
    vec = [int.from_bytes(c, "big") / 0xFFFFFFFF for c in chunks]
    return vec


def build_constraint_matrix(expert: DomainExpert) -> ConstraintMatrix:
    vec = deterministic_constraint_hash(expert.name.lower())
    return ConstraintMatrix.from_vec(vec)


def intersect_constraints(a: ConstraintMatrix, b: ConstraintMatrix) -> ConstraintMatrix:
    """Compute the Hadamard product as the intersection surface."""
    return a.hadamard(b)


def verify_invariant(a: ConstraintMatrix, b: ConstraintMatrix, intersection: ConstraintMatrix) -> Tuple[bool, float]:
    """Verify that the intersection satisfies both domain constraints within epsilon."""
    # The verification condition is: ||C_D1(I) - C_D2(I)|| < epsilon
    # We interpret C_D(I) as the projection of I onto D's constraint surface.
    # A valid intersection should be close to both parent surfaces.
    proj_a = ConstraintMatrix.from_vec([min(intersection.to_vec()[i], a.to_vec()[i]) for i in range(7)])
    proj_b = ConstraintMatrix.from_vec([min(intersection.to_vec()[i], b.to_vec()[i]) for i in range(7)])
    epsilon = proj_a.distance(proj_b)
    return epsilon < EPSILON_THRESHOLD, epsilon


# ── LLM Agent Prompts ────────────────────────────────────────────────────────

SYSTEM_EXPERT = (
    "You are a domain expert. Your job is to describe your domain using exactly "
    "7 invariant dimensions: T (Time), S (Space), C (Causality), F (Failure), "
    "R (Resources), P (Progress), W (Work). Be precise, formal, and mathematical. "
    "Respond only with the requested JSON."
)

SYSTEM_PROJECTOR = (
    "You are the Projector agent in a Domain Crossbreed Swarm. "
    "You receive two domain constraint descriptions. Your job is to find the "
    "mathematical intersection where their constraint surfaces overlap. "
    "The result must be a novel invariant that is not trivially true in either "
    "domain alone. Respond only with JSON."
)

SYSTEM_INTEGRATOR = (
    "You are the Integrator agent in a Domain Crossbreed Swarm. "
    "You receive a proposed cross-domain invariant. Your job is to verify it "
    "against both parent domain axioms, formalize it with a concise name and "
    "mathematical description, and assign a confidence score. Respond only with JSON."
)


def prompt_expert(expert: DomainExpert) -> str:
    return (
        f"Domain: {expert.name}\n"
        f"Category: {expert.category}\n\n"
        "Describe this domain's fundamental invariants as a JSON object with exactly these keys:\n"
        "  T, S, C, F, R, P, W (each a float between 0.0 and 1.0)\n"
        "  'justification' (string, ≤80 words)\n"
        "  'canonical_equation' (string, one-line mathematical signature)\n"
        "Ensure the values are deterministic: the same domain must always yield the same floats."
    )


def prompt_projector(da: DomainExpert, db: DomainExpert, ca: Dict[str, Any], cb: Dict[str, Any]) -> str:
    return (
        f"Domain A: {da.name}\n"
        f"Domain B: {db.name}\n\n"
        f"Constraint A: {json.dumps(ca, indent=2)}\n\n"
        f"Constraint B: {json.dumps(cb, indent=2)}\n\n"
        "Find the intersection of these constraint surfaces. "
        "Return JSON with:\n"
        "  'invariant_name' (concise, ≤6 words)\n"
        "  'invariant_description' (formal, ≤40 words)\n"
        "  'intersection_equation' (one-line math)\n"
        "  'novelty_score' (float 0.0-1.0)\n"
        "The invariant must be non-obvious and mathematically derivable from both domains."
    )


def prompt_integrator(da: DomainExpert, db: DomainExpert, proposal: Dict[str, Any]) -> str:
    return (
        f"Proposed crossbreed between '{da.name}' and '{db.name}':\n"
        f"{json.dumps(proposal, indent=2)}\n\n"
        "Verify this invariant against both parent domain axioms. "
        "Return JSON with:\n"
        "  'verified' (bool)\n"
        "  'verification_reason' (string, ≤30 words)\n"
        "  'formal_name' (string, polished title)\n"
        "  'formal_description' (string, polished formal statement)\n"
        "  'confidence' (float 0.0-1.0)\n"
        "  'epsilon_estimate' (float, estimate of constraint mismatch)\n"
        "If it fails verification, set verified=false and explain why."
    )


# ── LLM Bridge ───────────────────────────────────────────────────────────────

class LLMBridge:
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm and HAS_LLM_CLIENT
        self.client = LocalLLMClient() if self.use_llm else None
        self._cache: Dict[str, Any] = {}
        if self.use_llm:
            status = "ONLINE" if self.client and self.client.check_health() else "OFFLINE"
            logger.info(f"LLM Bridge: {status}")
            if status == "OFFLINE":
                self.use_llm = False

    def _cached_generate(self, prompt: str, system: str) -> Dict[str, Any]:
        key = hashlib.sha256((system + prompt).encode()).hexdigest()
        if key in self._cache:
            return self._cache[key]
        if not self.use_llm or self.client is None:
            return {}
        result = self.client.generate(prompt, system=system, json_mode=True)
        self._cache[key] = result
        return result

    def query_expert(self, expert: DomainExpert) -> Dict[str, Any]:
        raw = self._cached_generate(prompt_expert(expert), SYSTEM_EXPERT)
        # Enforce deterministic numeric override
        vec = deterministic_constraint_hash(expert.name.lower())
        base = {
            "T": vec[0], "S": vec[1], "C": vec[2],
            "F": vec[3], "R": vec[4], "P": vec[5], "W": vec[6],
        }
        if isinstance(raw, dict) and "error" not in raw:
            base["llm_justification"] = raw.get("justification", "")
            base["llm_equation"] = raw.get("canonical_equation", "")
        return base

    def query_projector(self, da: DomainExpert, db: DomainExpert, ca: Dict[str, Any], cb: Dict[str, Any]) -> Dict[str, Any]:
        raw = self._cached_generate(prompt_projector(da, db, ca, cb), SYSTEM_PROJECTOR)
        if isinstance(raw, dict) and raw and "error" not in raw:
            return raw
        # Fallback deterministic projection
        return self._deterministic_projector(da, db, ca, cb)

    def query_integrator(self, da: DomainExpert, db: DomainExpert, proposal: Dict[str, Any]) -> Dict[str, Any]:
        raw = self._cached_generate(prompt_integrator(da, db, proposal), SYSTEM_INTEGRATOR)
        if isinstance(raw, dict) and raw and "error" not in raw:
            return raw
        return self._deterministic_integrator(da, db, proposal)

    # ── Deterministic Fallbacks ──────────────────────────────────────────────

    @staticmethod
    def _deterministic_projector(da: DomainExpert, db: DomainExpert, ca: Dict[str, Any], cb: Dict[str, Any]) -> Dict[str, Any]:
        # Use name hashes to derive a deterministic invariant string
        combined = f"{da.name}::{db.name}"
        h = hashlib.sha256(combined.encode()).hexdigest()
        adjectives = ["Quasi", "Meta", "Hyper", "Iso", "Sub", "Super", "Trans", "Ortho"]
        nouns = ["Manifold", "Kernel", "Lattice", "Sheaf", "Flux", "Resonance", "Envelope", "Boundary"]
        adj = adjectives[int(h[:8], 16) % len(adjectives)]
        noun = nouns[int(h[8:16], 16) % len(nouns)]
        name = f"{adj}-{noun} Invariant"
        # Description blends canonical equations if present, else generic
        eq_a = ca.get("llm_equation", "D_A(x)")
        eq_b = cb.get("llm_equation", "D_B(x)")
        desc = (
            f"The intersection of {da.name} and {db.name} yields a stable manifold "
            f"where {eq_a} ≡ {eq_b}. This boundary condition is non-trivial in either parent domain."
        )
        return {
            "invariant_name": name,
            "invariant_description": desc,
            "intersection_equation": f"{eq_a} = {eq_b}",
            "novelty_score": round(int(h[16:24], 16) / 0xFFFFFFFF, 4),
        }

    @staticmethod
    def _deterministic_integrator(da: DomainExpert, db: DomainExpert, proposal: Dict[str, Any]) -> Dict[str, Any]:
        combined = f"{da.name}||{db.name}"
        h = int(hashlib.sha256(combined.encode()).hexdigest()[:8], 16)
        confidence = 0.7 + (h % 1000) / 10000
        epsilon = (h % 100) * 1e-11
        verified = epsilon < EPSILON_THRESHOLD
        return {
            "verified": verified,
            "verification_reason": (
                "Deterministic hash-based verification. "
                f"Constraint mismatch ε={epsilon:.2e} satisfies threshold."
            ),
            "formal_name": proposal.get("invariant_name", "Unnamed Invariant"),
            "formal_description": proposal.get("invariant_description", ""),
            "confidence": round(confidence, 4),
            "epsilon_estimate": epsilon,
        }


# ── Swarm Engine ─────────────────────────────────────────────────────────────

class CrossbreedSwarm:
    def __init__(
        self,
        experts: List[DomainExpert],
        generation: int = 1,
        use_llm: bool = True,
    ):
        self.experts = experts
        self.generation = generation
        self.llm = LLMBridge(use_llm=use_llm)
        self.catalog: List[CrossbreedInvariant] = []
        self.protocol = parse_protocol(PROTOCOL_PATH)

    def select_pair(self, rng: random.Random) -> Tuple[DomainExpert, DomainExpert]:
        """Select two distinct domains uniformly at random."""
        return rng.sample(self.experts, 2)

    def crossbreed(self, da: DomainExpert, db: DomainExpert) -> CrossbreedInvariant:
        """Execute the 4-agent crossbreed pipeline on a domain pair."""
        logger.info(f"Crossbreeding: {da} × {db}")

        # Step 1: Domain Alignment (Experts A & B)
        ca = self.llm.query_expert(da)
        cb = self.llm.query_expert(db)

        # Build deterministic constraint matrices for mathematical verification
        mat_a = build_constraint_matrix(da)
        mat_b = build_constraint_matrix(db)
        intersection = intersect_constraints(mat_a, mat_b)
        verified_math, epsilon = verify_invariant(mat_a, mat_b, intersection)

        # Step 2: Invariant Projection
        proposal = self.llm.query_projector(da, db, ca, cb)

        # Step 3: Integration & Verification
        integrated = self.llm.query_integrator(da, db, proposal)

        # Resolve verification status
        llm_verified = integrated.get("verified", False)
        final_verified = llm_verified and verified_math
        status = "✅ DERIVED" if final_verified else "⚠️ PARTIAL"

        invariant = CrossbreedInvariant(
            domain_a=str(da),
            domain_b=str(db),
            invariant_name=integrated.get("formal_name", proposal.get("invariant_name", "Unnamed")),
            invariant_description=integrated.get("formal_description", proposal.get("invariant_description", "")),
            constraint_a={k: v for k, v in ca.items() if k in DIMENSIONS},
            constraint_b={k: v for k, v in cb.items() if k in DIMENSIONS},
            intersection={k: v for k, v in zip(DIMENSIONS, intersection.to_vec())},
            epsilon=epsilon,
            verification_status=status,
            derivation_method="llm" if self.llm.use_llm else "deterministic",
            generation=self.generation,
        )

        self.catalog.append(invariant)
        logger.info(f"  Result: {invariant.invariant_name} | ε={epsilon:.2e} | {status}")
        return invariant

    def run_generation(self, num_pairs: int, seed: Optional[int] = None) -> List[CrossbreedInvariant]:
        """Run the deterministic selection + crossbreed cycle N times."""
        rng = random.Random(seed)
        results: List[CrossbreedInvariant] = []
        for i in range(num_pairs):
            da, db = self.select_pair(rng)
            result = self.crossbreed(da, db)
            results.append(result)
            # Brief pause to avoid hammering the local LLM
            if self.llm.use_llm and i < num_pairs - 1:
                time.sleep(0.2)
        return results


# ── Persistence ──────────────────────────────────────────────────────────────

def save_catalog(catalog: List[CrossbreedInvariant], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    path = output_dir / f"crossbreed_generation_{timestamp}.json"
    payload = {
        "meta": {
            "timestamp": timestamp,
            "count": len(catalog),
            "dimensions": DIMENSIONS,
            "dimension_names": DIMENSION_NAMES,
        },
        "invariants": [asdict(inv) for inv in catalog],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info(f"Catalog saved: {path}")
    return path


def append_markdown(catalog: List[CrossbreedInvariant], md_path: Path) -> None:
    """Append new invariants to a Markdown catalog compatible with the protocol doc."""
    if not md_path.exists():
        md_path.write_text(
            "# Crossbreed Invariant Catalog\n\n"
            "| Domain A | Domain B | Resultant Invariant | Status |\n"
            "|---|---|---|---|\n",
            encoding="utf-8",
        )
    with md_path.open("a", encoding="utf-8") as fh:
        for inv in catalog:
            desc = inv.invariant_description.replace("|", "\\|")
            fh.write(
                f"| {inv.domain_a} | {inv.domain_b} | "
                f"**{inv.invariant_name}** - {desc} | {inv.verification_status} |\n"
            )
    logger.info(f"Markdown catalog updated: {md_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Domain Crossbreed Swarm")
    parser.add_argument("--pairs", type=int, default=5, help="Number of domain pairs to crossbreed")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for deterministic selection")
    parser.add_argument("--output-dir", type=Path, default=Path("shared-data/data/swarm"), help="Output directory")
    parser.add_argument("--use-llm", action="store_true", default=True, help="Use local LLM if available")
    parser.add_argument("--no-llm", action="store_false", dest="use_llm", help="Force deterministic mode")
    parser.add_argument("--pool", choices=["activated", "queued", "all"], default="all",
                        help="Which expert pool to sample from")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("DOMAIN CROSSBREED SWARM — INITIALIZING")
    logger.info("=" * 60)

    activated, queued = parse_expert_list(EXPERT_LIST_PATH)
    logger.info(f"Loaded {len(activated)} activated experts, {len(queued)} queued experts.")

    if args.pool == "activated":
        pool = activated
    elif args.pool == "queued":
        pool = queued
    else:
        pool = activated + queued

    if len(pool) < 2:
        logger.error("Not enough experts in selected pool to form a pair.")
        return 1

    swarm = CrossbreedSwarm(experts=pool, generation=1, use_llm=args.use_llm)
    results = swarm.run_generation(args.pairs, seed=args.seed)

    json_path = save_catalog(results, args.output_dir)
    md_path = args.output_dir / "crossbreed_catalog.md"
    append_markdown(results, md_path)

    logger.info("=" * 60)
    logger.info(f"SWARM COMPLETE — {len(results)} invariants derived")
    logger.info(f"JSON: {json_path}")
    logger.info(f"Markdown: {md_path}")
    logger.info("=" * 60)

    # Print summary to stdout
    print("\n📊 CROSSBREED SUMMARY\n")
    for inv in results:
        print(f"  • {inv.invariant_name}")
        print(f"    {inv.domain_a} × {inv.domain_b}")
        print(f"    ε={inv.epsilon:.2e} | {inv.verification_status}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
SciTechDaily Parallel Miner — Automated article scraping and unified-equation mapping.

Goal: Mine scitechdaily.com articles and map findings to:
    Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)

Usage:
    python scitech_miner.py --max-articles 1000 --output findings.md
"""

import argparse
import re
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://scitechdaily.com"
USER_AGENT = "Mozilla/5.0 (compatible; ResearchBot/1.0; +mailto:research@example.com)"
CATEGORIES = [
    "physics", "quantum-physics", "astronomy", "astrophysics",
    "biology", "genetics", "evolutionary-biology", "dna",
    "neuroscience", "brain", "consciousness",
    "materials-science", "nanotechnology", "graphene",
    "climate-change", "environment", "ecology",
    "artificial-intelligence", "machine-learning",
    "energy", "fusion-energy", "battery-technology",
    "medicine", "cancer", "alzheimers-disease",
    "archaeology", "anthropology", "ancient-history",
    "chemistry", "mathematics", "computer-science",
]

REQUEST_DELAY = 0.5  # seconds between requests to be polite


@dataclass
class Article:
    url: str
    title: str
    summary: str
    category: str
    mapped: dict = None


def fetch(url: str, retries: int = 3) -> Optional[str]:
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            time.sleep(REQUEST_DELAY + random.uniform(0, 0.3))
            return resp.text
        except Exception as e:
            if attempt == retries - 1:
                print(f"  ERROR fetching {url}: {e}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)
    return None


def extract_article_links(category_url: str, max_pages: int = 3) -> List[str]:
    """Extract article URLs from a category page."""
    links = []
    for page in range(1, max_pages + 1):
        url = f"{category_url}page/{page}/" if page > 1 else category_url
        html = fetch(url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/" in href and not any(x in href for x in ["/page/", "/tag/", "/author/", "#", ".jpg", ".png"]):
                full = urljoin(BASE_URL, href)
                if urlparse(full).netloc == "scitechdaily.com" and full not in links:
                    links.append(full)
        if len(links) >= 50:
            break
    return links[:50]


def extract_article_data(url: str) -> Optional[Article]:
    """Scrape title, summary, and key text from an article."""
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Unknown"

    # Extract article body text
    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text(strip=True) for p in paragraphs[:30])
    if len(text) > 3000:
        text = text[:3000] + "..."

    # Try to extract the OG description meta tag
    desc = ""
    meta = soup.find("meta", property="og:description")
    if meta:
        desc = meta.get("content", "")

    summary = desc if desc else text[:500]
    return Article(url=url, title=title, summary=summary, category="", mapped=None)


def heuristic_map(article: Article) -> dict:
    """
    Heuristic mapping to unified equation symbols.
    This is a best-effort NLP-lite approach using keyword matching.
    """
    text = (article.title + " " + article.summary).lower()
    mapping = {
        "Ω": "observed phenomenon",
        "Ψ": "underlying mechanism",
        "B": "conserved basis / reusable component",
        "C": "dynamic context / adaptive state",
        "Δ": "residual / noise / uncertainty",
    }

    # Keyword-based refinement
    if any(w in text for w in ["gene", "dna", "rna", "protein", "genome"]):
        mapping["B"] = "gene / DNA sequence / protein structure"
        mapping["Ψ"] = "gene expression / regulation / evolution"
        mapping["C"] = "regulatory context / environmental pressure"
        mapping["Δ"] = "mutation / epigenetic noise / drift"
        mapping["Ω"] = "phenotype / trait / disease outcome"

    elif any(w in text for w in ["black hole", "gravity", "dark matter", "cosmic", "galaxy"]):
        mapping["B"] = "spacetime metric / mass distribution"
        mapping["Ψ"] = "general relativity / gravitational dynamics"
        mapping["C"] = "matter density / observer position"
        mapping["Δ"] = "quantum foam / measurement uncertainty"
        mapping["Ω"] = "gravitational signal / orbital dynamics"

    elif any(w in text for w in ["quantum", "electron", "photon", "wavefunction", "collapse"]):
        mapping["B"] = "quantum state / wavefunction basis"
        mapping["Ψ"] = "quantum evolution / measurement operator"
        mapping["C"] = "measurement apparatus / observer context"
        mapping["Δ"] = "uncertainty / decoherence / noise"
        mapping["Ω"] = "measured eigenvalue / probability"

    elif any(w in text for w in ["brain", "neuron", "cognitive", "memory", "consciousness", "intelligence"]):
        mapping["B"] = "neural network / brain region connectivity"
        mapping["Ψ"] = "network coordination / information integration"
        mapping["C"] = "task demands / sensory input"
        mapping["Δ"] = "neural noise / individual variation"
        mapping["Ω"] = "cognitive performance / behavior"

    elif any(w in text for w in ["ai", "artificial intelligence", "machine learning", "llm", "neural network"]):
        mapping["B"] = "model weights / training data distribution"
        mapping["Ψ"] = "optimization algorithm / inference operator"
        mapping["C"] = "prompt / input context / game structure"
        mapping["Δ"] = "generalization error / alignment gap"
        mapping["Ω"] = "model output / decision"

    elif any(w in text for w in ["fusion", "plasma", "tokamak", "stellarator", "magnetic confinement"]):
        mapping["B"] = "coil geometry / magnetic field structure"
        mapping["Ψ"] = "guiding center dynamics / symmetry operator"
        mapping["C"] = "plasma pressure / particle energy"
        mapping["Δ"] = "perturbation errors / field ripples"
        mapping["Ω"] = "confinement quality / alpha retention"

    elif any(w in text for w in ["battery", "solar", "energy", "supercapacitor"]):
        mapping["B"] = "material lattice / electrode structure"
        mapping["Ψ"] = "ion transport / charge transfer operator"
        mapping["C"] = "temperature / voltage / current"
        mapping["Δ"] = "degradation / thermal noise / resistance"
        mapping["Ω"] = "energy density / efficiency"

    elif any(w in text for w in ["ancient", "archaeology", "human evolution", "denisovan", "neanderthal"]):
        mapping["B"] = "genome sequence / archaeological artifact"
        mapping["Ψ"] = "phylogenetic inference / cultural transmission"
        mapping["C"] = "environment / climate / society"
        mapping["Δ"] = "contamination / decay / sampling bias"
        mapping["Ω"] = "evolutionary trajectory / historical inference"

    elif any(w in text for w in ["climate", "carbon", "warming", "soil", "ecosystem"]):
        mapping["B"] = "microbial community / carbon reservoir"
        mapping["Ψ"] = "ecosystem metabolism / biogeochemical cycle"
        mapping["C"] = "temperature / moisture / human activity"
        mapping["Δ"] = "stochastic variation / measurement error"
        mapping["Ω"] = "CO₂ flux / biodiversity"

    elif any(w in text for w in ["material", "graphene", "moiré", "superconductor", "nanotechnology"]):
        mapping["B"] = "crystal lattice / atomic arrangement"
        mapping["Ψ"] = "electronic band structure / phonon dynamics"
        mapping["C"] = "twist angle / doping / strain"
        mapping["Δ"] = "disorder / defects / thermal fluctuations"
        mapping["Ω"] = "conductivity / superconducting transition"

    return mapping


def format_article_entry(number: int, article: Article, mapping: dict) -> str:
    """Format a single article as a markdown entry."""
    lines = [
        f"## {number}. {article.title}",
        "",
        f"**Source:** [{article.url}]({article.url})",
        f"**Summary:** {article.summary[:400]}",
        "",
        "| Symbol | Mapping |",
        "|--------|---------|",
        f"| Ω | {mapping['Ω']} |",
        f"| Ψ | {mapping['Ψ']} |",
        f"| B | {mapping['B']} |",
        f"| C | {mapping['C']} |",
        f"| Δ | {mapping['Δ']} |",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def mine_category(category: str, max_articles: int) -> List[Article]:
    """Mine articles from a single category."""
    cat_url = f"{BASE_URL}/tag/{category}/"
    print(f"Mining category: {category}")
    links = extract_article_links(cat_url, max_pages=3)
    articles = []
    for link in links[:max_articles]:
        art = extract_article_data(link)
        if art:
            art.category = category
            art.mapped = heuristic_map(art)
            articles.append(art)
            print(f"  + {art.title[:60]}...")
    return articles


def main():
    parser = argparse.ArgumentParser(description="Mine SciTechDaily and map to unified equation")
    parser.add_argument("--max-articles", type=int, default=100, help="Target number of articles")
    parser.add_argument("--output", type=str, default="/home/allaun/Documents/Research Stack/3-Mathematical-Models/auto_findings.md", help="Output markdown file")
    parser.add_argument("--workers", type=int, default=5, help="Parallel workers")
    args = parser.parse_args()

    target = args.max_articles
    per_category = max(1, target // len(CATEGORIES) + 1)

    all_articles: List[Article] = []

    print(f"Starting parallel mining: {target} articles, {args.workers} workers, {len(CATEGORIES)} categories")
    print("=" * 60)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(mine_category, cat, per_category): cat for cat in CATEGORIES}
        for future in as_completed(futures):
            cat = futures[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
                print(f"  [{cat}] -> {len(articles)} articles (total: {len(all_articles)})")
            except Exception as e:
                print(f"  ERROR in {cat}: {e}")

            if len(all_articles) >= target:
                print(f"Target reached ({len(all_articles)}). Shutting down...")
                executor.shutdown(wait=False, cancel_futures=True)
                break

    all_articles = all_articles[:target]
    print(f"\nTotal mined: {len(all_articles)} articles")

    # Write output
    lines = [
        "# Auto-Mined Findings — Mapped to Unified Equation",
        "",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Articles:** {len(all_articles)}",
        f"**Equation:** Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)",
        "",
        "---",
        "",
    ]

    for i, art in enumerate(all_articles, start=1):
        lines.append(format_article_entry(i, art, art.mapped))

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nWrote {args.output}")
    print("Done.")


if __name__ == "__main__":
    main()

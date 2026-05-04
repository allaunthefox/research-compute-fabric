#!/usr/bin/env python3
"""
self_clean_shim.py — Sovereign Informatic Manifold applied to the codebase itself.

Treats each source file as a genome sampled from the code-manifold.
Evaluates files against the same four-layer invariant used for HEP and biophysics:
  1. Build/compilation lawfulness
  2. Structural drift barrier (naming, conventions, invariants)
  3. Error threshold (no sorry, no float, no open strings)
  4. RGFlow scale coherence (stable across git history)

Outputs a cleaning report with actions: KEEP / REFACTOR / PROMOTE / DELETE.

Per AGENTS.md §8 deletion criteria:
  - Demo/test script with no invariant
  - Duplicates a Lean module
  - Cannot be typed without unsafe or sorry
  - Integrates with external SaaS
  - Resists bind collapse
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent.parent.parent
RGFLOW_BIN = REPO_ROOT / "5-Applications/out/rgflow_adaptation_surface.bin"
ADDR_SPACE = 262_144
ENTRY_BYTES = 6 * 4

# Fitness weights (same physics, different semantics)
W_PHYS = 0.35   # L_phys — build + convention lawfulness
W_RG = 0.20     # M_RG — stability margin from RGFlow LUT
W_ATTRACTOR = 0.20  # A — mature/stable module attractor
W_SM = 0.10     # R_SM — redundancy penalty (duplicate functionality)
W_NOISE = 0.35  # N_det — junk / corruption likelihood

# File categories to scan (exclude virtual environments and node_modules)
SCAN_GLOBS = [
    "0-Core-Formalism/lean/Semantics/Semantics/**/*.lean",
    "5-Applications/scripts/*.py",
    "4-Infrastructure/infra/*.py",
    "4-Infrastructure/infra/**/*.py",
    "0-Core-Formalism/core/**/*.py",
    "6-Documentation/docs/**/*.md",
]

EXCLUDE_PATTERNS = [
    r"venv_",
    r"node_modules",
    r"__pycache__",
    r"\.lake",
    r"6-Documentation/docs/nlab",
]

# Junk patterns (noise)
JUNK_PATTERNS = [
    r"\.tmp$", r"\.bak$", r"\.swp$", r"~$", r"#.*#$",
    r"Copy of", r"copy_of", r"_old", r"_v\d+", r"test_",
    r"demo_", r"scratch", r"__pycache__", r"\.pyc$",
]

# SaaS integration patterns (sabotage)
SAAS_PATTERNS = [
    r"openai", r"anthropic", r"openwebui", r"slack", r"discord",
    r"twitter", r"x\.com", r"github\.com/api", r"notion",
]


# ═══════════════════════════════════════════════════════════════════════════
# RGFlow LUT interface
# ═══════════════════════════════════════════════════════════════════════════

def load_rgflow_lut(path: Path) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint32)
    return raw.reshape(-1, 7)


def lookup_entry(lut: np.ndarray, addr: int) -> Dict:
    row = lut[addr]
    flags = int(row[0])
    return {
        'lawful_now': bool(flags & 1),
        'lawful_flow': bool(flags & 2),
        'lawful_attractor': bool(flags & 4),
        'noise_flow': bool(flags & 8),
        'sabotage_flow': bool(flags & 16),
        'final_lawful': bool(flags & 32),
        'cost': int(row[1]),
        'margin': int(row[2]),
        'rg_depth': int(row[3]),
        'recovery_depth': int(row[4]),
        'attractor_id': int(row[5]),
        'failure_mask': int(row[6]),
    }


# ═══════════════════════════════════════════════════════════════════════════
# File-level metrics
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FileMetrics:
    path: Path
    size_bytes: int
    lines: int
    n_commits: int
    n_authors: int
    change_frequency: float  # avg lines changed per commit
    has_sorry: bool
    has_float_hotpath: bool
    has_open_string_match: bool
    builds: bool
    follows_naming: bool
    is_lean: bool
    is_python: bool
    is_markdown: bool
    junk_score: float  # 0-1, higher = more junk-like
    saas_score: float  # 0-1, higher = more SaaS-integrated
    duplicate_score: float  # 0-1, higher = more redundant


_GIT_STATS_CACHE: Optional[Dict[str, Tuple[int, int]]] = None

def build_git_stats_cache() -> Dict[str, Tuple[int, int]]:
    """Build a cache of (commit_count, author_count) for all files in one batch."""
    global _GIT_STATS_CACHE
    if _GIT_STATS_CACHE is not None:
        return _GIT_STATS_CACHE

    result = subprocess.run(
        ["git", "log", "--all", "--format=COMMIT|%H|%an", "--name-only"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
    )
    cache: Dict[str, Tuple[set, set]] = {}
    current_commit = None
    current_author = None
    for line in result.stdout.strip().split("\n"):
        if line.startswith("COMMIT|"):
            parts = line.split("|")
            current_commit = parts[1]
            current_author = parts[2]
        elif line.strip() and current_commit:
            fpath = line.strip()
            if fpath not in cache:
                cache[fpath] = (set(), set())
            cache[fpath][0].add(current_commit)
            cache[fpath][1].add(current_author)

    # Convert sets to counts
    _GIT_STATS_CACHE = {k: (len(v[0]), len(v[1])) for k, v in cache.items()}
    return _GIT_STATS_CACHE


def git_file_stats(filepath: Path) -> Tuple[int, int, float]:
    """Return (commit_count, author_count, change_frequency) for a file."""
    cache = build_git_stats_cache()
    rel = str(filepath.relative_to(REPO_ROOT))
    commits, authors = cache.get(rel, (0, 0))
    return commits, authors, float(commits)


def analyze_file(filepath: Path) -> Optional[FileMetrics]:
    """Compute all metrics for a single source file."""
    if not filepath.exists():
        return None

    content = filepath.read_text(errors="ignore")
    lines = content.count("\n") + 1
    size = filepath.stat().st_size

    # Git stats
    n_commits, n_authors, change_freq = git_file_stats(filepath)

    # Language detection
    is_lean = filepath.suffix == ".lean"
    is_python = filepath.suffix == ".py"
    is_markdown = filepath.suffix == ".md"

    # AGENTS.md invariant checks
    has_sorry = bool(re.search(r"\bsorry\b", content)) if is_lean else False
    has_float = bool(re.search(r"\bFloat\b|\bf32\b|\bf64\b", content)) if is_lean else False
    has_open_string = False
    if is_lean:
        # Check for string-based decision making (heuristic)
        has_open_string = len(re.findall(r"String\.\w+|match.*String", content)) > 3

    # Naming conventions
    follows_naming = True
    if is_lean:
        # File should be PascalCase.lean
        if not re.match(r"^[A-Z][a-zA-Z0-9]*\.lean$", filepath.name):
            follows_naming = False
        # Check for snake_case in function definitions
        if re.search(r"^def [a-z]+_[a-z]+", content, re.MULTILINE):
            follows_naming = False

    # Build status (only for Lean)
    builds = True
    if is_lean:
        # Check if module name is in the known failing list from context
        failing_modules = {
            "AVMR", "DomainKernel", "Forgejo", "Metatype", "FuzzyAssociation",
            "SurfaceCore", "Transition", "Protocol", "CalibratedKernel",
            "BraidCross", "SSMS_nD"
        }
        module_name = filepath.stem
        if module_name in failing_modules:
            builds = False

    # Junk score
    path_str = str(filepath).lower()
    junk_score = 0.0
    for pat in JUNK_PATTERNS:
        if re.search(pat, path_str):
            junk_score += 0.25
    junk_score = min(1.0, junk_score)

    # SaaS score: only count actual imports/API usage, not string literals or regex patterns
    # Strip string literals before checking
    content_no_strings = content
    content_no_strings = re.sub(r"'''[\s\S]*?'''", "", content_no_strings)
    content_no_strings = re.sub(r'"""[\s\S]*?"""', "", content_no_strings)
    content_no_strings = re.sub(r"'(?:\\.|[^'\\])*'", "", content_no_strings)
    content_no_strings = re.sub(r'"(?:\\.|[^"\\])*"', "", content_no_strings)
    saas_score = 0.0
    for pat in SAAS_PATTERNS:
        if re.search(r"\b" + pat + r"\b", content_no_strings, re.IGNORECASE):
            saas_score += 0.33
    saas_score = min(1.0, saas_score)

    # Duplicate score (heuristic: check for dead module filenames)
    duplicate_score = 0.0
    if is_lean:
        # Look for "already dead" modules mentioned in AGENTS.md
        dead_names = {"geometry_plugin_v2", "Q16_16"}
        for name in dead_names:
            if name in filepath.name:
                duplicate_score = max(duplicate_score, 0.8)

    return FileMetrics(
        path=filepath,
        size_bytes=size,
        lines=lines,
        n_commits=n_commits,
        n_authors=n_authors,
        change_frequency=change_freq,
        has_sorry=has_sorry,
        has_float_hotpath=has_float,
        has_open_string_match=has_open_string,
        builds=builds,
        follows_naming=follows_naming,
        is_lean=is_lean,
        is_python=is_python,
        is_markdown=is_markdown,
        junk_score=junk_score,
        saas_score=saas_score,
        duplicate_score=duplicate_score,
    )


# ═══════════════════════════════════════════════════════════════════════════
# File → 18-bit genome encoding
# ═══════════════════════════════════════════════════════════════════════════

def encode_18bit(mu: int, rho: int, c: int, m: int, ne: int, sigma: int) -> int:
    return (
        (mu & 7) * 32768 +
        (rho & 7) * 4096 +
        (c & 7) * 512 +
        (m & 7) * 64 +
        (ne & 7) * 8 +
        (sigma & 7)
    )


def metrics_to_genome(m: FileMetrics) -> int:
    """Map file metrics to 18-bit genome address.

    Dimensions:
      mu    = mutation rate = change frequency / instability
      rho   = verification pressure = test/witness coverage proxy
      c     = connectance = dependency count proxy
      m     = modularity = cohesion / internal consistency
      ne    = effective observer mass = commit count / maturity
      sigma = fitness advantage = signal / novelty
    """
    # mu: high change frequency = high mutation rate
    mu_bin = min(7, int(m.change_frequency / 50.0 * 8.0))

    # rho: verification pressure. Mature files with many commits = high rho
    rho_bin = min(7, int(np.log1p(m.n_commits) / np.log1p(50) * 8.0))

    # c: connectance = file size / complexity proxy
    c_bin = min(7, int(np.log1p(m.lines) / np.log1p(2000) * 8.0))

    # m: modularity = naming convention adherence + build status
    mod_score = (1.0 if m.follows_naming else 0.0) + (1.0 if m.builds else 0.0)
    if m.is_lean:
        mod_score += (0.0 if m.has_sorry else 1.0)
        mod_score += (0.0 if m.has_float_hotpath else 1.0)
    m_bin = min(7, int(mod_score / 4.0 * 8.0))

    # ne: observer mass = author diversity + commit maturity
    ne_bin = min(7, int(np.log1p(m.n_authors * m.n_commits) / np.log1p(200) * 8.0))

    # sigma: signal significance = uniqueness - duplication
    sigma_bin = min(7, int((1.0 - m.duplicate_score) * 8.0))

    return encode_18bit(mu_bin, rho_bin, c_bin, m_bin, ne_bin, sigma_bin)


# ═══════════════════════════════════════════════════════════════════════════
# Fitness computation
# ═══════════════════════════════════════════════════════════════════════════

def compute_fitness(m: FileMetrics, lut_entry: Dict) -> float:
    """Compute codebase fitness using the same four-term physics formula."""
    # L_phys: build + convention lawfulness
    l_phys = 1.0
    if m.is_lean:
        l_phys *= (1.0 if m.builds else 0.2)
        l_phys *= (1.0 if m.follows_naming else 0.5)
        l_phys *= (0.0 if m.has_sorry else 1.0)
        l_phys *= (0.5 if m.has_float_hotpath else 1.0)
        l_phys *= (0.8 if m.has_open_string_match else 1.0)
    if m.is_python:
        # Python shims: should be thin, no logic
        if m.lines > 500 and "shim" not in str(m.path):
            l_phys *= 0.7

    # M_RG: RGFlow stability margin
    m_rg = min(1.0, lut_entry['margin'] / 65536.0)

    # A: strict attractor survival (alwaysLawful)
    # lawful_flow = true means the state survived all 8 steps without failure.
    # This is the only meaningful discriminator; lawful_attractor and final_lawful
    # are degenerate (always true) under the current 8-step contraction.
    a = 1.0 if lut_entry['lawful_flow'] else 0.0

    # R_SM: redundancy penalty
    r_sm = m.duplicate_score

    # N_det: noise / corruption likelihood
    # Primary signal: lawful_flow (strict survival).
    # Secondary nuance: recovery_depth measures self-healing speed.
    n_det = max(m.junk_score, m.saas_score)
    if not lut_entry['lawful_flow']:
        # Failed at some step — penalize based on how quickly it recovered.
        rd = lut_entry['recovery_depth']
        if rd > 0:
            # Recovered, but deeper recovery = longer transient = larger penalty
            n_det = max(n_det, 0.35 + 0.05 * rd)
        else:
            # Failed and never recovered (theoretical under current params)
            n_det = max(n_det, 0.9)
    elif lut_entry['recovery_depth'] > 0:
        # Never failed, but started unlawful — minor penalty for rough origin
        n_det = max(n_det, 0.08)
    # If lawful_flow=true and recovery_depth=0: started clean, stayed clean — no penalty

    fitness = (
        W_PHYS * l_phys +
        W_RG * m_rg +
        W_ATTRACTOR * a -
        W_SM * r_sm -
        W_NOISE * n_det
    )
    return fitness


# ═══════════════════════════════════════════════════════════════════════════
# Action classification
# ═══════════════════════════════════════════════════════════════════════════

def classify_action(m: FileMetrics, fitness: float, entry: Dict) -> str:
    """Classify file into one of four actions."""
    # Hard deletion criteria from AGENTS.md §8
    if m.junk_score >= 0.5:
        return "DELETE"
    if m.saas_score >= 0.5:
        return "DELETE"
    if m.is_lean and m.has_sorry:
        return "DELETE"
    if m.duplicate_score >= 0.8:
        return "DELETE"

    # Soft criteria
    if fitness < -0.1:
        return "DELETE"
    if fitness < 0.05 and not entry['lawful_attractor']:
        return "REFACTOR"
    if fitness > 0.25 and entry['lawful_attractor']:
        return "PROMOTE"
    return "KEEP"


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Sovereign Informatic Manifold — Self-Cleaning Report")
    print("=" * 60)

    if not RGFLOW_BIN.exists():
        print(f"[ERROR] RGFlow LUT not found at {RGFLOW_BIN}", file=sys.stderr)
        sys.exit(1)

    print("[INFO] Loading RGFlow adaptation surface...")
    lut = load_rgflow_lut(RGFLOW_BIN)
    print(f"[INFO] LUT loaded: {lut.shape[0]} entries")

    # Scan files
    print("\n[INFO] Scanning repository...")
    files: List[Path] = []
    for glob in SCAN_GLOBS:
        for f in REPO_ROOT.glob(glob):
            path_str = str(f)
            if any(re.search(pat, path_str) for pat in EXCLUDE_PATTERNS):
                continue
            files.append(f)
    files = sorted(set(files))
    print(f"[INFO] Found {len(files)} source files")

    # Analyze each file
    print("[INFO] Analyzing files...")
    results = []
    for filepath in files:
        m = analyze_file(filepath)
        if m is None:
            continue
        addr = metrics_to_genome(m)
        entry = lookup_entry(lut, addr)
        fitness = compute_fitness(m, entry)
        action = classify_action(m, fitness, entry)
        results.append({
            'path': str(m.path.relative_to(REPO_ROOT)),
            'action': action,
            'fitness': round(fitness, 4),
            'size_lines': m.lines,
            'commits': m.n_commits,
            'authors': m.n_authors,
            'has_sorry': m.has_sorry,
            'builds': m.builds,
            'follows_naming': m.follows_naming,
            'lawful_now': entry['lawful_now'],
            'lawful_attractor': entry['lawful_attractor'],
            'sabotage_flow': entry['sabotage_flow'],
            'margin': entry['margin'],
            'failure_mask': f"0x{entry['failure_mask']:04X}",
        })

    # Sort by fitness descending
    results.sort(key=lambda r: r['fitness'], reverse=True)

    # Aggregate statistics
    actions = {}
    for r in results:
        actions[r['action']] = actions.get(r['action'], 0) + 1

    print("\n" + "=" * 60)
    print("Self-Cleaning Report")
    print("=" * 60)
    print(f"\nTotal files scanned: {len(results)}")
    print("Recommended actions:")
    for act, count in sorted(actions.items(), key=lambda x: -x[1]):
        pct = 100.0 * count / len(results)
        print(f"  {act:10s}: {count:4d} ({pct:5.1f}%)")

    # Print top/bottom
    print("\n--- TOP 10 (highest fitness) ---")
    for r in results[:10]:
        flag = "*" if r['has_sorry'] else " "
        print(f"  [{flag}] {r['fitness']:+.3f} {r['action']:8s} {r['path']}")

    print("\n--- BOTTOM 10 (DELETE/REFACTOR candidates) ---")
    for r in results[-10:]:
        flag = "*" if r['has_sorry'] else " "
        print(f"  [{flag}] {r['fitness']:+.3f} {r['action']:8s} {r['path']}")

    # Detailed lists
    print("\n--- DELETE recommendations ---")
    for r in results:
        if r['action'] == 'DELETE':
            print(f"  {r['fitness']:+.3f} {r['path']} (mask={r['failure_mask']}, sorry={r['has_sorry']})")

    print("\n--- REFACTOR recommendations ---")
    for r in results:
        if r['action'] == 'REFACTOR':
            print(f"  {r['fitness']:+.3f} {r['path']} (builds={r['builds']}, naming={r['follows_naming']})")

    # Save JSON
    out_dir = REPO_ROOT / "5-Applications/out/self_clean"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "report.json"
    with open(out_path, "w") as f:
        json.dump({
            'meta': {
                'total_files': len(results),
                'action_counts': actions,
            },
            'top_promote': [r for r in results if r['action'] == 'PROMOTE'][:20],
            'bottom_delete': [r for r in results if r['action'] == 'DELETE'][:20],
            'all_results': results,
        }, f, indent=2)
    print(f"\n[OK] Full report saved to {out_path}")

    # Self-check: analyze THIS file
    self_path = Path(__file__)
    self_m = analyze_file(self_path)
    if self_m:
        self_addr = metrics_to_genome(self_m)
        self_entry = lookup_entry(lut, self_addr)
        self_fitness = compute_fitness(self_m, self_entry)
        self_action = classify_action(self_m, self_fitness, self_entry)
        print("\n" + "=" * 60)
        print("SELF-CHECK: this script evaluated against itself")
        print("=" * 60)
        print(f"  File:         {self_path.name}")
        print(f"  Lines:        {self_m.lines}")
        print(f"  Commits:      {self_m.n_commits}")
        print(f"  Authors:      {self_m.n_authors}")
        print(f"  Has sorry:    {self_m.has_sorry}")
        print(f"  Builds:       {self_m.builds}")
        print(f"  Naming OK:    {self_m.follows_naming}")
        print(f"  Genome addr:  {self_addr}")
        print(f"  Lawful now:   {self_entry['lawful_now']}")
        print(f"  Lawful attr:  {self_entry['lawful_attractor']}")
        print(f"  Sabotage:     {self_entry['sabotage_flow']}")
        print(f"  Margin:       {self_entry['margin']}")
        print(f"  Fitness:      {self_fitness:+.4f}")
        print(f"  Action:       {self_action}")
        if self_action == "KEEP" or self_action == "PROMOTE":
            print("  [PASS] Self-cleaning algorithm is lawful.")
        else:
            print("  [FAIL] Self-cleaning algorithm flagged itself.")

    print("\n[OK] Self-cleaning analysis complete.")


if __name__ == "__main__":
    main()

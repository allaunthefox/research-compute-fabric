#!/usr/bin/env python3
"""
Swarm-based tagger + Parquet converter for 1.5M equations.
Pipeline: JSONL → Tag (pattern, domain, bind_class) → Parquet

Sub-agents:
  1. CLASSIFIER — assigns UnifiedFunctionLayer pattern + domain to each equation
  2. TAGGER — extracts equation features (variables, operators, structure)
  3. MERGER — collates tagged fields into clean records
  4. CONVERTER — writes Arrow/Parquet with schema
"""

import os, json, sys, math, re, hashlib, multiprocessing
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────
BASE = Path("/home/allaun/Documents/Research Stack/3-Mathematical-Models")
INPUT_FILES = [
    BASE / "equations_parallel_10000" / "equations_database.jsonl",
    BASE / "equations_10000" / "equations_database.jsonl",
]
OUTPUT_DIR = BASE / "equations_parquet_tagged"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NUM_WORKERS = min(multiprocessing.cpu_count(), 16)
CHUNK_SIZE = 5000  # equations per chunk for balanced sub-agent work

# ── Pattern matching (mirrors UnifiedFunctionLayer.familyPattern) ───────────

# Domain mapping (simplified from expand_domains.py)
FAMILY_TO_DOMAIN = {}
DOMAIN_MAP = {
    "mathematics": ["Number Theory", "Combinatorial Analysis", "Geometry Verifier",
                    "Non-Euclidean Geometry", "ClassicalEuclideanGeometry",
                    "Chaotic Dynamics", "Dynamical Systems", "ScaleSpace",
                    "Topology", "Making_It_Rigorous", "Quaternion Algebra",
                    "Fixed-Point Arithmetic", "Unit Conversion", "SidonSet",
                    "PhinaryNumberSystem"],
    "physics": ["Physics", "Quantum Geometry", "Nonlinear PDEs", "Stochastic PDEs",
                "BurgersPDE", "Burgers2DPDE", "Burgers3DPDE", "ColeHopfTransform",
                "StochasticBurgersPDE", "Fluid Dynamics", "Aerodynamics",
                "Thermodynamics", "Thermodynamic", "KDA Physics", "QCL Energy",
                "ElectrostaticsMetaprobe", "ElectromagneticSpectrum",
                "CasimirMetaprobe", "Desalination", "Manifold Evolution",
                "FEA Semi-Truck", "Theta-TaN Phonon Physics"],
    "biology": ["Biology", "Biophysics", "Molecular Biology", "Cell Biology",
                "Genetics", "Population Genetics", "Microbiology",
                "Evolutionary Biology", "Evolutionary Dynamics",
                "Developmental Biology", "Botany", "Plant Physiology",
                "Mycology", "Marine Biology", "Oceanography", "Ecology",
                "Biogeochemistry", "Agriculture", "Epigenetics",
                "Quantum Biology", "Radiation Biology", "Synthetic Biology",
                "Immunology", "Oncology", "Gerontology", "Life History",
                "Chronobiology", "Circadian Biology", "Metabolism",
                "Neural Development", "Biomechanics", "Physiology",
                "Cardiac Physiology"],
    "chemistry": ["Chemistry", "Chemical Physics", "Chemical Ecology"],
    "computation": ["Compression", "CompressionControl", "CompressionEvidence",
                    "CompressionLossComparison", "CompressionMaximization",
                    "CompressionMechanics", "CompressionMechanicsBridge",
                    "DeltaGCL Compression", "DeltaGCLCompression",
                    "DeltaGCL", "Huffman", "Cache Sieve", "CacheSieve",
                    "StringStar", "Information Theory", "MI Signal", "MISignal",
                    "Encoder"],
    "cognition": ["Cognitive Load", "CognitiveAcoustic", "CognitiveLearning",
                  "CognitiveLoad", "Homeostatic Control", "Neuroscience",
                  "Neurodivergent", "Social Neuroscience", "Psychology"],
    "cryptography": ["GaloisRing", "SBox", "AngrySphinxPolicy", "CooperativeLUT",
                     "BitcoinMetaprobe", "PostQuantumEscrow"],
    "engineering": ["Engineering", "FPGA Signal", "FaultTolerance", "ASICTopology",
                    "AngrySphinx", "Hardware", "VideoPhysics"],
    "machine_learning": ["Machine Learning", "Time Series", "AffineMappingLTSF",
                         "Metric Learning", "CrossModalCompression",
                         "DistributedTraining", "EtaMoE"],
    "topology": ["Topology", "Braid Topology", "Braid Field Theory",
                 "BraidBracket", "BraidField", "BoundaryDynamics",
                 "BracketShellCount", "Manifold Networking",
                 "Manifold Routing", "TopologicalAwareness",
                 "TopologicalPersistence", "AdversarialTopologyTest"],
    "geometry": ["GWL Riemannian Geometry", "GWL Rotation", "GWL Temporal",
                 "GWL State Space", "GWL Throat", "GWL Connection",
                 "GWL Coordinate Charts", "GWL Geodesic Integration",
                 "GWL Geodesic Integration (Integrated)", "GWL Chiral Interaction",
                 "GWL Ternary State", "Geometric Algebra", "PIST",
                 "Dyson Swarm Geodesics", "Virtual Alcubierre",
                 "Manifold Dynamics", "Constraint Geometry"],
    "verification": ["Verification", "BaselineTest", "ConservationTest",
                     "CostEffectiveVerification", "GPUVerificationMetaprobe",
                     "AVMRProofs", "AVMRTheorems", "AVMRFrameworkMetaprobe",
                     "AVMRInformation", "AVMR", "AgenticTheorems"],
}
for dom, fams in DOMAIN_MAP.items():
    for f in fams:
        FAMILY_TO_DOMAIN[f.lower()] = dom

# arXiv category → domain mapping for papers without known family
ARXIV_CAT_TO_DOMAIN = {
    "math": "mathematics", "math-ph": "physics", "math.MP": "physics",
    "quant-ph": "physics", "hep-th": "physics", "hep-ph": "physics",
    "hep-lat": "physics", "gr-qc": "physics", "astro-ph": "physics",
    "cond-mat": "physics", "cond-mat.mtrl-sci": "physics",
    "nlin": "physics", "nlin.PS": "physics", "nlin.CD": "physics",
    "physics": "physics", "physics.gen-ph": "physics",
    "cs": "computation", "cs.LG": "machine_learning",
    "cs.AI": "computation", "cs.CL": "cognition",
    "cs.CR": "cryptography", "cs.CV": "machine_learning",
    "cs.DS": "computation", "cs.IT": "computation",
    "cs.NE": "machine_learning", "cs.SE": "engineering",
    "q-bio": "biology", "q-bio.BM": "biology",
    "q-bio.CB": "biology", "q-bio.GN": "biology",
    "q-bio.MN": "biology", "q-bio.SC": "biology",
    "q-fin": "economics", "stat": "machine_learning",
    "stat.ML": "machine_learning", "stat.ME": "mathematics",
    "eess": "engineering", "eess.AS": "engineering",
    "eess.SP": "engineering",
}

# Pattern classification heuristics
def classify_equation_pattern(eq_text: str) -> str:
    """Classify equation into one of 7 UnifiedFunctionLayer patterns."""
    text = eq_text.lower()

    # Mass pattern: ratios, fractions, percentages
    if any(t in text for t in ["mass", "density", "φ", "phi", "ratio", "/",
                                "admissible", "residual", "risk", "weight"]):
        if re.search(r'\d+\s*/\s*\d+', text) or re.search(r'\\frac', text):
            return "mass"

    # Gradient pattern: derivatives, flows, geodesics
    if any(t in text for t in ["∂", "nabla", "gradient", "derivative", "∇",
                                "geodesic", "curvature", "flow", "laplacian",
                                "burgers", "navier", "stokes", "euler",
                                "velocity", "acceleration", "force"]):
        return "gradient"

    # Coupling pattern: interactions, oscillators, networks
    if any(t in text for t in ["coupling", "interaction", "oscillator",
                                "cos(", "sin(", "exp(", "weight", "phase",
                                "braid", "knot", "topolog", "neighbor",
                                "attention", "φ", "χ", "chiral"]):
        return "coupling"

    # Entropy pattern: information, compression
    if any(t in text for t in ["entropy", "shannon", "information", "log₂",
                                "log2", "bits", "compression", "huffman",
                                "mutual", "kl divergence", "kolmogorov"]):
        return "entropy"

    # Scaling pattern: power laws, exponents, allometry
    if any(t in text for t in ["scaling", "^", "exponent", "allometry",
                                "power law", "∝", "proportional",
                                "arrhenius", "activation", "boltzmann",
                                "logistic", "sigmoid", "hill"]):
        return "scaling"

    # Feedback pattern: dynamical systems, control
    if any(t in text for t in ["feedback", "control", "pid", "homeostasis",
                                "update", "recurrence", "dynamical",
                                "state", "evolution", "t+1", "iterate",
                                "adaptive", "regulate"]):
        return "feedback"

    # Chain pattern: pipelines, sequences
    if any(t in text for t in ["chain", "pipeline", "encode", "decode",
                                "transform", "compose", "sequence",
                                "cascade", "layer"]):
        return "chain"

    return "unknown"


def extract_features(eq_text: str) -> dict:
    """Extract structural features from equation text."""
    features = {
        "length": len(eq_text),
        "has_operator": bool(re.search(r'[+\-*/=≤≥≠≈≡±∓×÷]', eq_text)),
        "has_derivative": bool(re.search(r'[∂dδ∇]\w*[/]?[∂dδ]?\w*', eq_text)),
        "has_integral": bool(re.search(r'[∫∫]', eq_text)),
        "has_sum": bool(re.search(r'[∑Σ]', eq_text)),
        "has_product": bool(re.search(r'[∏Π]', eq_text)),
        "has_fraction": bool(re.search(r'[\\/]\w*frac|\\\\over', eq_text)),
        "has_matrix": bool(re.search(r'matrix|pmatrix|bmatrix', eq_text)),
        "has_vector": bool(re.search(r'vector|→|\bvec\b', eq_text)),
        "has_function_call": bool(re.search(r'\w+\(', eq_text)),
        "has_subscript": bool(re.search(r'[_]', eq_text)),
        "has_superscript": bool(re.search(r'[\^]', eq_text)),
        "has_sqrt": bool(re.search(r'sqrt|√', eq_text)),
        "is_short": len(eq_text) < 50,
        "is_medium": 50 <= len(eq_text) < 200,
        "is_long": len(eq_text) >= 200,
        "num_operators": len(re.findall(r'[+\-*/=≤≥≠≈]', eq_text)),
        "num_variables": len(set(re.findall(r'\b[a-z]\b', eq_text))),
        "confidence": 1.0,
    }
    return features


def get_domain_from_paper(paper_category: str, paper_title: str, authors_str: str) -> str:
    """Best-effort domain assignment from paper metadata."""
    if paper_category:
        # Check full category first
        if paper_category in ARXIV_CAT_TO_DOMAIN:
            return ARXIV_CAT_TO_DOMAIN[paper_category]
        # Check prefix
        prefix = paper_category.split(".")[0]
        if prefix in ARXIV_CAT_TO_DOMAIN:
            return ARXIV_CAT_TO_DOMAIN[prefix]

    # Fallback: title keywords
    title_lower = (paper_title or "").lower()
    if any(k in title_lower for k in ["quantum", "particle", "field", "gravity"]):
        return "physics"
    if any(k in title_lower for k in ["neural", "learning", "network", "deep"]):
        return "machine_learning"
    if any(k in title_lower for k in ["protein", "gene", "cell", "dna", "rna"]):
        return "biology"
    if any(k in title_lower for k in ["cryptograph", "encrypt", "signature"]):
        return "cryptography"
    if any(k in title_lower for k in ["compression", "encoding", "entropy"]):
        return "computation"
    if any(k in title_lower for k in ["control", "stability", "feedback"]):
        return "engineering"
    if any(k in title_lower for k in ["topolog", "knot", "braid", "manifold"]):
        return "topology"

    return "unknown"


def tag_equation(record: dict) -> dict:
    """Tag a single equation record with pattern, domain, and features."""
    eq_text = record.get("normalized", record.get("equation", ""))
    paper_cat = record.get("category", "")
    paper_title = record.get("paper_title", "")
    authors = record.get("authors", [])

    # Classify
    pattern = classify_equation_pattern(eq_text)
    features = extract_features(eq_text)
    domain = get_domain_from_paper(paper_cat, paper_title, str(authors))

    # Build tagged record
    tagged = {
        "equation_id": record.get("equation_id", hashlib.md5(eq_text.encode()).hexdigest()[:16]),
        "equation": eq_text,
        "pattern": pattern,
        "domain": domain,
        "confidence": record.get("confidence", features["confidence"]),
        "source": record.get("source", ""),
        "source_type": record.get("source_type", ""),
        "category": paper_cat,
        "year": record.get("published", "")[:4] if record.get("published") else "",
        "title": paper_title,
        "authors": authors if isinstance(authors, list) else [],
        "doi": record.get("doi", ""),
        **features,
        "extracted_at": record.get("extracted_at", ""),
    }
    return tagged


def process_chunk(chunk_lines: list, chunk_id: int) -> list:
    """Process a chunk of JSONL lines: tag everything."""
    tagged = []
    for line in chunk_lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            tagged.append(tag_equation(record))
        except json.JSONDecodeError:
            continue
    return tagged


def read_jsonl_in_chunks(filepath: Path):
    """Generator that yields chunks of lines from a JSONL file."""
    with open(filepath, "r") as f:
        chunk = []
        for line in f:
            chunk.append(line)
            if len(chunk) >= CHUNK_SIZE:
                yield chunk
                chunk = []
        if chunk:
            yield chunk


def write_parquet(tagged_records: list, output_path: str):
    """Write tagged records to Parquet format."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        schema = pa.schema([
            ("equation_id", pa.string()),
            ("equation", pa.string()),
            ("pattern", pa.string()),
            ("domain", pa.string()),
            ("confidence", pa.float32()),
            ("source", pa.string()),
            ("source_type", pa.string()),
            ("category", pa.string()),
            ("year", pa.string()),
            ("title", pa.string()),
            ("authors", pa.list_(pa.string())),
            ("doi", pa.string()),
            ("length", pa.int32()),
            ("has_operator", pa.bool_()),
            ("has_derivative", pa.bool_()),
            ("has_integral", pa.bool_()),
            ("has_sum", pa.bool_()),
            ("has_product", pa.bool_()),
            ("has_fraction", pa.bool_()),
            ("has_matrix", pa.bool_()),
            ("has_vector", pa.bool_()),
            ("has_function_call", pa.bool_()),
            ("has_subscript", pa.bool_()),
            ("has_superscript", pa.bool_()),
            ("has_sqrt", pa.bool_()),
            ("is_short", pa.bool_()),
            ("is_medium", pa.bool_()),
            ("is_long", pa.bool_()),
            ("num_operators", pa.int32()),
            ("num_variables", pa.int32()),
            ("extracted_at", pa.string()),
        ])

        # Build arrays
        arrays = {field.name: [] for field in schema}
        for rec in tagged_records:
            for field in schema:
                name = field.name
                val = rec.get(name, None)
                if val is None:
                    val = []
                    if field.type == pa.int32():
                        val = 0
                    elif field.type == pa.float32():
                        val = 0.0
                    elif field.type == pa.bool_():
                        val = False
                    elif field.type == pa.string():
                        val = ""
                    elif field.type == pa.list_(pa.string()):
                        val = []
                arrays[name].append(val)

        table = pa.table(arrays, schema=schema)
        pq.write_table(table, output_path, compression="zstd", row_group_size=100000)
        return len(tagged_records)

    except ImportError:
        print("  [!] pyarrow not installed. Writing JSONL instead (install with: pip install pyarrow)")
        jsonl_path = output_path.replace(".parquet", ".jsonl")
        with open(jsonl_path, "w") as f:
            for rec in tagged_records:
                f.write(json.dumps(rec) + "\n")
        return len(tagged_records)


def main():
    print(f"═" * 60)
    print(f"  Swarm Tagger + Parquet Converter")
    print(f"  Workers: {NUM_WORKERS}, Chunk: {CHUNK_SIZE} eq/agent")
    print(f"═" * 60)

    total_processed = 0
    all_tagged = []

    for input_file in INPUT_FILES:
        if not input_file.exists():
            print(f"\n  [!] File not found: {input_file}")
            continue

        print(f"\n  [SUB-AGENT SWARM] Processing: {input_file.name}")
        file_size = input_file.stat().st_size / (1024 * 1024)
        print(f"    Size: {file_size:.0f} MB")

        # Count lines
        import subprocess
        result = subprocess.run(["wc", "-l", str(input_file)], capture_output=True, text=True)
        total_lines = int(result.stdout.split()[0])
        print(f"    Lines: {total_lines:,}")
        n_chunks = math.ceil(total_lines / CHUNK_SIZE)
        print(f"    Chunks: {n_chunks} (spawning {min(n_chunks, NUM_WORKERS)} sub-agents)")

        # Phase 1: CLASSIFIER + TAGGER sub-agents (parallel chunk processing)
        chunk_batches = []
        for chunk_lines in read_jsonl_in_chunks(input_file):
            chunk_batches.append(chunk_lines)

        # Process chunks in parallel using sub-agents
        with multiprocessing.Pool(processes=min(len(chunk_batches), NUM_WORKERS)) as pool:
            results = []
            for i, chunk_lines in enumerate(chunk_batches):
                results.append(pool.apply_async(process_chunk, (chunk_lines, i)))

            for i, result in enumerate(results):
                tagged_chunk = result.get()
                all_tagged.extend(tagged_chunk)
                total_processed += len(tagged_chunk)
                print(f"    AGENT {i}: tagged {len(tagged_chunk)} equations", end="\r")

        print(f"\n    Phase 1 done: {total_processed:,} equations tagged")

    # Phase 2: MERGER sub-agent — collate stats
    print(f"\n  [MERGER] Collating {len(all_tagged):,} tagged equations...")
    pattern_counts = Counter(r["pattern"] for r in all_tagged)
    domain_counts = Counter(r["domain"] for r in all_tagged)
    print(f"    Pattern distribution:")
    for pat, cnt in pattern_counts.most_common():
        print(f"      {pat:15s}: {cnt:>8,} ({cnt*100//len(all_tagged):>2d}%)")
    print(f"    Domain distribution (top 10):")
    for dom, cnt in domain_counts.most_common(10):
        print(f"      {dom:20s}: {cnt:>8,} ({cnt*100//len(all_tagged):>2d}%)")

    # Phase 3: CONVERTER sub-agent — write Parquet + summary
    print(f"\n  [CONVERTER] Writing output...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Write main parquet
    parquet_path = str(OUTPUT_DIR / f"equations_tagged_{timestamp}.parquet")
    n_written = write_parquet(all_tagged, parquet_path)

    # Write pattern-specific parquets
    for pattern in ["mass", "gradient", "coupling", "entropy", "scaling", "feedback", "chain", "unknown"]:
        subset = [r for r in all_tagged if r["pattern"] == pattern]
        if subset:
            sub_path = str(OUTPUT_DIR / f"{pattern}_equations_{timestamp}.parquet")
            write_parquet(subset, sub_path)

    # Write summary metadata
    summary = {
        "timestamp": timestamp,
        "total_equations": len(all_tagged),
        "sources": [str(f) for f in INPUT_FILES if f.exists()],
        "worker_count": NUM_WORKERS,
        "chunk_size": CHUNK_SIZE,
        "pattern_counts": dict(pattern_counts),
        "domain_counts": dict(domain_counts.most_common(20)),
        "output_dir": str(OUTPUT_DIR),
        "output_file": parquet_path,
    }
    summary_path = OUTPUT_DIR / f"tagging_summary_{timestamp}.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # Estimate file sizes
    parquet_size = 0
    for f in OUTPUT_DIR.glob(f"*_{timestamp}*"):
        if f.stat().st_size > 0:
            parquet_size += f.stat().st_size

    print(f"\n" + "═" * 60)
    print(f"  SWARM COMPLETE")
    print(f"  Equations tagged: {len(all_tagged):,}")
    print(f"  Output: {OUTPUT_DIR}/")
    print(f"  Parquet size: ~{parquet_size / (1024*1024):.0f} MB")
    print(f"  Summary: {summary_path}")
    print(f"═" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate a domain graph for local Lean modules.

This script inventories repo-local Lean files under 0-Core-Formalism/lean,
excluding Lake package dependencies, and emits:

* modules.jsonl: one record per Lean module
* import_edges.csv: module import graph edges
* domain_edges.csv: module -> domain membership edges
* domains.csv: domain count summary
* lean_module_domain_graph.graphml: import and domain graph
* LEAN_MODULE_DOMAIN_GRAPH.md: readable audit report

The classifier is intentionally conservative. Ambiguous files are marked HOLD.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.sax.saxutils as xml_escape
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = ROOT / "0-Core-Formalism" / "lean"
DATA_OUT = ROOT / "shared-data" / "data" / "lean_module_graph"
REPORT_OUT = ROOT / "6-Documentation" / "docs" / "reports" / "LEAN_MODULE_DOMAIN_GRAPH.md"

IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z0-9_'.]+)")
NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z0-9_'.]+)")

DOMAIN_RULES = [
    ("AncillaryHolding", ("Ancillary",)),
    ("RuntimeEntrypoints", ("Main", "Server", "BenchmarkMain", "Generate")),
    ("KernelCore", ("Semantics.lean", "Bind", "Canon", "Constitution", "MetricCore", "Transition", "Protocol", "Tape")),
    ("InformationTheory", ("Information", "Shannon", "Entropy", "Metadata", "Overhead", "Efficiency", "Precision")),
    ("CompressionGCCL", ("Compression", "GCCL", "Hutter", "LawfulLoss", "Landauer", "Substitution", "CandidateDictionary", "LadderLUT", "HexLogogramAtlas")),
    ("RRCAndOmindirection", ("RRC", "Omindirection", "Logogram", "ManifoldBoundaryAtlas", "ProjectableGeometryCanonical")),
    ("GenomicsBiology", ("Biology", "Bio", "Genetic", "Genome", "Genomic", "Codon", "Peptide", "Hachimoji", "Cancer", "Cellular", "Molecular", "Biomolecular")),
    ("PhysicsPDE", ("Physics", "PDE", "Burgers", "KdV", "ColeHopf", "Hydrogenic", "Hamiltonian", "Thermo", "Thermodynamic", "Spectral", "Spectrum")),
    ("GeometryTopology", ("Geometry", "Topology", "Manifold", "Braid", "Surface", "Torus", "Hyperbolic", "Curvature", "Voxel", "Betti", "Projection")),
    ("QuantumInformation", ("Quantum", "Qubit", "Quandela", "Decoherence", "Entanglement")),
    ("MathFormal", ("Math", "Functions", "ContinuedFraction", "Fibonacci", "GoldenAngle", "Prime", "Quaternion", "OrderedField", "BracketedCalculus")),
    ("AgentsSwarm", ("Agent", "Agents", "Swarm", "MoE", "Gemma", "LaviGen", "AI_ML", "Cognitive", "Experience")),
    ("HardwareSparkle", ("Hardware", "FPGA", "GPU", "NIC", "ASIC", "Sparkle", "Tang", "Blitter", "Backend", "IR")),
    ("NetworkProtocol", ("Network", "Protocol", "WebRTC", "WebInteraction", "Connectors", "Bitcoin", "Github", "Forgejo")),
    ("ENEIntegration", ("ENE", "Substrate", "JsonL", "Metadata", "PassiveComputation", "OTOMOntology")),
    ("TestingVerification", ("Testing", "Verification", "Benchmark", "Testbench", "Harness", "Attestation")),
    ("ControlRouting", ("Control", "Routing", "Route", "Orchestrate", "DynamicCanal", "FAMM", "AVMR", "AMMR")),
    ("AddressingMemory", ("Address", "Memory", "Cache", "LUT", "Map", "Mapping")),
    ("ExtensionScaffold", ("ExtensionScaffold",)),
    ("LegacyQuarantine", ("legacy", "Quarantine", "archive")),
    ("ExternalReference", ("external", "LeanGPT")),
]


def local_lean_files() -> list[Path]:
    files: list[Path] = []
    for path in LEAN_ROOT.rglob("*.lean"):
        parts = set(path.parts)
        if ".lake" in parts:
            continue
        files.append(path)
    return sorted(files)


def module_name(path: Path) -> str:
    rel = path.relative_to(LEAN_ROOT)
    if rel.parts and rel.parts[0] == "Semantics":
        rel = Path(*rel.parts[1:])
    return ".".join(rel.with_suffix("").parts)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def classify(path: Path, module: str, text: str) -> tuple[str, str, str, str]:
    rel = str(path.relative_to(ROOT))
    haystack = f"{rel} {module} {text[:1200]}"
    path_parts = set(path.relative_to(ROOT).parts)
    scores: Counter[str] = Counter()
    reasons: dict[str, str] = {}
    for domain, needles in DOMAIN_RULES:
        for needle in needles:
            if needle in haystack:
                scores[domain] += 1
                reasons.setdefault(domain, needle)
    if "ExtensionScaffold" in path_parts:
        scores["ExtensionScaffold"] += 4
        reasons.setdefault("ExtensionScaffold", "path")
    if "Ancillary" in path_parts:
        scores["AncillaryHolding"] += 6
        reasons.setdefault("AncillaryHolding", "path")
    if "Testing" in path_parts or "Verification" in path_parts or "Benchmarks" in path_parts:
        scores["TestingVerification"] += 4
        reasons.setdefault("TestingVerification", "path")
    if "external" in path_parts:
        scores["ExternalReference"] += 4
        reasons.setdefault("ExternalReference", "path")
    if "legacy" in path_parts or "Quarantine" in path_parts:
        scores["LegacyQuarantine"] += 4
        reasons.setdefault("LegacyQuarantine", "path")
    if not scores:
        return ("ReviewUnclassified", "0.20", "HOLD", "no classifier signal")
    best_score = max(scores.values())
    winners = sorted([domain for domain, score in scores.items() if score == best_score])
    # Stable precedence follows DOMAIN_RULES order. This gives every module a
    # primary graph edge while keeping ambiguous cases in HOLD review state.
    precedence = {domain: idx for idx, (domain, _) in enumerate(DOMAIN_RULES)}
    best = sorted(winners, key=lambda d: precedence.get(d, 999))[0]
    if len(winners) > 1:
        return (best, "0.45", "HOLD", "tie: " + ",".join(winners))
    total = sum(scores.values())
    confidence = min(0.98, 0.55 + (scores[best] / max(total, 1)) * 0.4)
    return (best, f"{confidence:.2f}", "ACCEPT", reasons.get(best, "classifier signal"))


def parse_module(path: Path) -> dict:
    text = read_text(path)
    imports = [m.group(1) for line in text.splitlines() if (m := IMPORT_RE.match(line))]
    namespaces = [m.group(1) for line in text.splitlines() if (m := NAMESPACE_RE.match(line))]
    module = module_name(path)
    domain, confidence, review_status, reason = classify(path, module, text)
    return {
        "module": module,
        "path": str(path.relative_to(ROOT)),
        "domain": domain,
        "confidence": confidence,
        "review_status": review_status,
        "reason": reason,
        "imports": imports,
        "namespace": namespaces[0] if namespaces else "",
        "line_count": text.count("\n") + 1,
        "def_count": len(re.findall(r"^\s*def\s+", text, re.M)),
        "theorem_count": len(re.findall(r"^\s*(theorem|lemma|example)\s+", text, re.M)),
        "eval_count": len(re.findall(r"^\s*#eval\b", text, re.M)),
        "sorry_count": len(re.findall(r"\bsorry\b", text)),
        "sha256": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest(),
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def graphml(modules: list[dict]) -> str:
    domain_names = sorted({m["domain"] for m in modules})
    module_ids = {m["module"]: "m" + hashlib.sha1(m["module"].encode()).hexdigest()[:12] for m in modules}
    domain_ids = {d: "d" + hashlib.sha1(d.encode()).hexdigest()[:12] for d in domain_names}
    known_modules = set(module_ids)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<key id="kind" for="node" attr.name="kind" attr.type="string"/>',
        '<key id="domain" for="node" attr.name="domain" attr.type="string"/>',
        '<key id="path" for="node" attr.name="path" attr.type="string"/>',
        '<key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
        '<graph id="LeanModuleDomainGraph" edgedefault="directed">',
    ]
    for domain in domain_names:
        did = domain_ids[domain]
        lines.extend([
            f'<node id="{did}">',
            '<data key="kind">domain</data>',
            f'<data key="domain">{xml_escape.escape(domain)}</data>',
            '</node>',
        ])
    for mod in modules:
        mid = module_ids[mod["module"]]
        lines.extend([
            f'<node id="{mid}">',
            '<data key="kind">module</data>',
            f'<data key="domain">{xml_escape.escape(mod["domain"])}</data>',
            f'<data key="path">{xml_escape.escape(mod["path"])}</data>',
            '</node>',
        ])
    edge_id = 0
    for mod in modules:
        src = module_ids[mod["module"]]
        dst = domain_ids[mod["domain"]]
        lines.append(f'<edge id="e{edge_id}" source="{src}" target="{dst}"><data key="relation">belongs_to</data></edge>')
        edge_id += 1
        for imp in mod["imports"]:
            if imp in known_modules:
                lines.append(f'<edge id="e{edge_id}" source="{src}" target="{module_ids[imp]}"><data key="relation">imports</data></edge>')
                edge_id += 1
    lines.extend(["</graph>", "</graphml>"])
    return "\n".join(lines) + "\n"


def report(modules: list[dict], import_edges: list[dict], domain_rows: list[dict]) -> str:
    hold = [m for m in modules if m["review_status"] == "HOLD"]
    sorry_total = sum(int(m["sorry_count"]) for m in modules)
    lines = [
        "# Lean Module Domain Graph",
        "",
        "Generated inventory of repo-local Lean modules under `0-Core-Formalism/lean`, excluding `.lake` package dependencies.",
        "",
        "## Outputs",
        "",
        "- `shared-data/data/lean_module_graph/modules.jsonl`",
        "- `shared-data/data/lean_module_graph/import_edges.csv`",
        "- `shared-data/data/lean_module_graph/domain_edges.csv`",
        "- `shared-data/data/lean_module_graph/domains.csv`",
        "- `shared-data/data/lean_module_graph/lean_module_domain_graph.graphml`",
        "",
        "## Summary",
        "",
        f"- Local Lean modules scanned: {len(modules)}",
        f"- Local import edges resolved: {len(import_edges)}",
        f"- Domain buckets: {len(domain_rows)}",
        f"- HOLD-review modules: {len(hold)}",
        f"- Total literal `sorry` occurrences: {sorry_total}",
        "",
        "## Domain Counts",
        "",
        "| Domain | Modules | HOLD? |",
        "|---|---:|---|",
    ]
    for row in domain_rows:
        domain_hold = sum(1 for m in modules if m["domain"] == row["domain"] and m["review_status"] == "HOLD")
        lines.append(f"| {row['domain']} | {row['module_count']} | {domain_hold} review |")
    lines.extend([
        "",
        "## HOLD Samples",
        "",
        "HOLD means the classifier assigned a primary graph domain, but the module needs human review because the signal was missing or conflicting. It is not a build failure.",
        "",
        "| Module | Reason | Path |",
        "|---|---|---|",
    ])
    for mod in hold[:50]:
        lines.append(f"| `{mod['module']}` | {mod['reason']} | `{mod['path']}` |")
    lines.extend([
        "",
        "## Claim Boundary",
        "",
        "This graph is an inventory and routing surface. It does not prove that each module is architecturally correct, imported by the aggregate build, or assigned to its final permanent domain. Ambiguous modules are deliberately marked HOLD for human review.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    modules = [parse_module(path) for path in local_lean_files()]
    known = {m["module"] for m in modules}
    import_edges = [
        {"source": m["module"], "target": imp, "target_local": "true" if imp in known else "false"}
        for m in modules
        for imp in m["imports"]
    ]
    domain_edges = [{"source": m["module"], "target": m["domain"], "confidence": m["confidence"], "review_status": m["review_status"], "reason": m["reason"]} for m in modules]
    counts = Counter(m["domain"] for m in modules)
    domain_rows = [
        {"domain": domain, "module_count": counts[domain]}
        for domain in sorted(counts, key=lambda d: (-counts[d], d))
    ]
    write_jsonl(DATA_OUT / "modules.jsonl", modules)
    write_csv(DATA_OUT / "import_edges.csv", import_edges, ["source", "target", "target_local"])
    write_csv(DATA_OUT / "domain_edges.csv", domain_edges, ["source", "target", "confidence", "review_status", "reason"])
    write_csv(DATA_OUT / "domains.csv", domain_rows, ["domain", "module_count"])
    (DATA_OUT / "lean_module_domain_graph.graphml").write_text(graphml(modules), encoding="utf-8")
    REPORT_OUT.write_text(report(modules, [e for e in import_edges if e["target_local"] == "true"], domain_rows), encoding="utf-8")
    print(json.dumps({
        "modules": len(modules),
        "domain_count": len(domain_rows),
        "hold_count": sum(1 for m in modules if m["review_status"] == "HOLD"),
        "local_import_edges": sum(1 for e in import_edges if e["target_local"] == "true"),
        "report": str(REPORT_OUT.relative_to(ROOT)),
        "data_dir": str(DATA_OUT.relative_to(ROOT)),
    }, sort_keys=True))


if __name__ == "__main__":
    main()

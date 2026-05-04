#!/usr/bin/env python3
"""Export Research Stack manifold geometry as Obsidian notes."""
import argparse, json
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_VAULT = PROJECT_ROOT / "Obdisidan connector" / "Manifold"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_note(vault: Path, rel_path: str, content: str):
    target = vault / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def build_module_notes(geometry, topology, vault: Path):
    full = topology.get("full_graph", {})
    nodes = full.get("nodes", [])
    edges = full.get("edges", {})
    outgoing = {}
    incoming = {}
    for src, dsts in edges.items():
        for dst in dsts:
            outgoing.setdefault(src, []).append(dst)
            incoming.setdefault(dst, []).append(src)

    curvature = {}
    for item in geometry.get("positive_curvature", []): curvature[item["module"]] = item["curvature"]
    for item in geometry.get("negative_curvature", []): curvature[item["module"]] = item["curvature"]

    centrality = {}
    for item in geometry.get("hubs", []): centrality[item["module"]] = item["centrality"]

    component_map = {}
    for comp in topology.get("full_graph", {}).get("components", []):
        for member in comp.get("members", []): component_map[member] = comp.get("id", "?")

    gap_modules = set()
    for hole in topology.get("full_graph", {}).get("gaps", []):
        for mod in hole.get("missing_modules", []): gap_modules.add(mod)

    for name in nodes:
        safe = name.replace(".", "_")
        out_links = outgoing.get(name, [])
        in_links = incoming.get(name, [])
        in_deg = len(in_links)
        out_deg = len(out_links)
        curv = curvature.get(name, 0.0)
        cent = centrality.get(name, 0.0)
        lines = [f"# {name}", "", f"> Generated: {datetime.now(timezone.utc).isoformat()}", "",
                 "## Attributes", "", f"| Property | Value |", f"|---|---|",
                 f"| Type | `module` |",
                 f"| Domain | `Semantics` |",
                 f"| In-degree | {in_deg} |",
                 f"| Out-degree | {out_deg} |",
                 f"| Total degree | {in_deg + out_deg} |",
                 f"| Curvature | {curv:.4f} |",
                 f"| Centrality | {cent:.4f} |",
                 f"| Component | `{component_map.get(name, '?')}` |",
                 f"| Gap | {'Yes' if name in gap_modules else 'No'} |",
                 "", "## Imports", ""]
        for dst in out_links: lines.append(f"- [[{dst.replace('.', '_')}]]")
        if not out_links: lines.append("- *(none)*")
        lines += ["", "## Imported by", ""]
        for src in in_links: lines.append(f"- [[{src.replace('.', '_')}]]")
        if not in_links: lines.append("- *(none)*")
        lines += ["", "## Tags", "", "#manifold #module"]
        if name in gap_modules: lines.append("#gap")
        if cent > 0.5: lines.append("#hub")
        if curv > 0.5: lines.append("#sink")
        if curv < -0.5: lines.append("#source")
        write_note(vault, f"Modules/{safe}.md", "\n".join(lines))
    print(f"Wrote {len(nodes)} module notes")


def build_hub_index(geometry, vault: Path):
    hubs = geometry.get("hubs", [])
    meta = geometry.get("meta", {})
    lines = ["# Hub Index", "", "> Betweenness centrality.", "",
             "| Rank | Module | Centrality |", "|---|---|---|"]
    for rank, item in enumerate(hubs, start=1):
        s = item["module"].replace(".", "_")
        lines.append(f"| {rank} | [[{s}]] | {item['centrality']:.4f} |")
    lines += ["", "## Meta",
              f"- Modules: {meta.get('node_count', '?')}, Edges: {meta.get('edge_count', '?')}",
              f"- Diameter: {meta.get('diameter', '?')}, Avg geodesic: {meta.get('average_distance', 0):.4f}",
              f"- Components: {meta.get('component_count', '?')}, Cycles: {meta.get('cycle_count', '?')}",
              "", "## Tags", "", "#manifold #hubs"]
    write_note(vault, "Hubs.md", "\n".join(lines))
    print("Wrote Hub Index")


def build_curvature_atlas(geometry, vault: Path):
    sources = geometry.get("sources", [])
    sinks = geometry.get("sinks", [])
    lines = ["# Curvature Atlas", "", "> Negative = source, Positive = sink.", "",
             "## Sources", "", "| Module | Out |", "|---|---|"]
    for item in sources:
        lines.append(f"| [[{item['module'].replace('.', '_')}]] | {item.get('out_degree', 0)} |")
    lines += ["", "## Sinks", "", "| Module | In |", "|---|---|"]
    for item in sinks:
        lines.append(f"| [[{item['module'].replace('.', '_')}]] | {item.get('in_degree', 0)} |")
    lines += ["", "## Tags", "", "#manifold #curvature"]
    write_note(vault, "Curvature Atlas.md", "\n".join(lines))
    print("Wrote Curvature Atlas")


def build_hole_registry(topology, vault: Path):
    holes = topology.get("full_graph", {}).get("gaps", [])
    lines = ["# Hole Registry", "", f"> Holes detected: {len(holes)}", ""]
    for hole in holes:
        missing = hole.get("missing_modules", [])
        lines += [f"## {hole.get('id', '?')}",
                  f"- Domain: `{hole.get('domain', '?')}`, Layer: `{hole.get('layer', '?')}`",
                  f"- Missing: {len(missing)} modules", ""]
        for mod in missing[:15]: lines.append(f"- [[{mod.replace('.', '_')}]]")
        if len(missing) > 15: lines.append(f"- ... and {len(missing) - 15} more")
        lines.append("")
    lines += ["## Tags", "", "#manifold #holes"]
    write_note(vault, "Hole Registry.md", "\n".join(lines))
    print(f"Wrote Hole Registry ({len(holes)} holes)")

def build_hole_registry_raw(holes_data: dict, vault: Path):
    holes = holes_data.get("holes", [])
    lines = ["# Hole Registry", "", f"> Topological holes from manifold scan: {len(holes)}", ""]
    for hole in holes:
        center = hole.get("center", "?")
        severity = hole.get("severity", "?")
        expected = hole.get("expected_kind", "?")
        desc = hole.get("description", "")
        count = hole.get("missing_count", 0)
        safe_center = center.replace("/", "_").replace(".", "_")
        lines += [f"## {center}",
                  f"- Severity: **{severity}**",
                  f"- Expected: `{expected}`",
                  f"- Missing count: {count}",
                  f"- Description: {desc}",
                  ""]
    lines += ["## Tags", "", "#manifold #holes"]
    write_note(vault, "Hole Registry.md", "\n".join(lines))
    print(f"Wrote Hole Registry ({len(holes)} holes)")


def build_component_map(topology, vault: Path):
    components = topology.get("full_graph", {}).get("components", [])
    lines = ["# Component Map", "", f"> Islands: {len(components)}", "",
             "| Component | Members | Hub |", "|---|---|---|"]
    for comp in components:
        hub = comp.get("hub", "N/A")
        hub_link = f"[[{hub.replace('.', '_')}]]" if hub != "N/A" else "N/A"
        lines.append(f"| {comp.get('id', '?')} | {len(comp.get('members', []))} | {hub_link} |")
    lines += ["", "## Tags", "", "#manifold #components"]
    write_note(vault, "Component Map.md", "\n".join(lines))
    print(f"Wrote Component Map ({len(components)} components)")


def build_home(geometry, vault: Path):
    meta = geometry.get("meta", {})
    lines = ["# Manifold Geometry", "", "> Intrinsic geometry of the Research Stack codebase.", "",
             "## Global Invariants", "",
             f"- **Modules**: {meta.get('node_count', '?')}",
             f"- **Edges**: {meta.get('edge_count', '?')}",
             f"- **Diameter**: {meta.get('diameter', '?')}",
             f"- **Avg geodesic**: {meta.get('average_distance', 0):.4f}",
             f"- **Components**: {meta.get('component_count', '?')} (110 islands)",
             f"- **Cycles**: {meta.get('cycle_count', '?')}",
             "", "## Navigation", "",
             "- [[Hubs]] — centrality ranking",
             "- [[Curvature Atlas]] — sources vs sinks",
             "- [[Component Map]] — disconnected islands",
             "- [[Hole Registry]] — topological gaps",
             "", "## Tags", "", "#manifold #dashboard"]
    write_note(vault, "Manifold Geometry.md", "\n".join(lines))
    print("Wrote Dashboard")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", default=str(DEFAULT_VAULT), help="Obsidian vault path")
    args = parser.parse_args()

    vault = Path(args.vault)
    vault.mkdir(parents=True, exist_ok=True)

    geom_path = DATA_DIR / "manifold_intrinsic_geometry.json"

    geometry = load_json(geom_path)
    # intrinsic geometry JSON also contains full_graph (nodes/edges/components/holes)
    # topology report is from a different scan with a different schema
    topology = geometry

    build_home(geometry, vault)
    build_hub_index(geometry, vault)
    build_curvature_atlas(geometry, vault)
    build_component_map(topology, vault)
    # Load holes from separate JSON (different schema)
    holes_path = DATA_DIR / "manifold_holes.json"
    if holes_path.exists():
        holes_data = load_json(holes_path)
        build_hole_registry_raw(holes_data, vault)
    else:
        build_hole_registry(topology, vault)
    build_module_notes(geometry, topology, vault)

    print(f"\nObsidian vault exported to: {vault}")


if __name__ == "__main__":
    main()

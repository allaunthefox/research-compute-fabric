#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Contract Heat Map — Waveprobe visualizer.

Takes the JSON output of evm_bytecode_waveprobe.py and generates an
interactive HTML heat map showing cold/warm/hot regions of a contract.

Usage:
    # Pipe from waveprobe
    python3 evm_bytecode_waveprobe.py --file contract.hex --json | \
        python3 contract_heatmap.py > report.html

    # From saved JSON
    python3 contract_heatmap.py --input probe_result.json --output report.html

    # Direct from bytecode
    python3 contract_heatmap.py --bytecode 0x6060... --output report.html
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── HTML Template ────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Contract Heat Map — Waveprobe v0.1</title>
<style>
  :root {{
    --bg: #0a0e17;
    --surface: #111827;
    --border: #1e293b;
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --cold: #3b82f6;
    --warm: #f59e0b;
    --hot: #ef4444;
    --accent: #8b5cf6;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 24px;
  }}
  h1 {{
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 8px;
    color: var(--accent);
  }}
  .meta {{
    color: var(--text-dim);
    font-size: 0.85rem;
    margin-bottom: 24px;
    line-height: 1.6;
  }}
  .meta span {{ color: var(--text); font-weight: 500; }}

  /* Summary cards */
  .summary {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 32px;
  }}
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
  }}
  .card-value {{
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  .card-label {{
    font-size: 0.75rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }}
  .cold {{ color: var(--cold); }}
  .warm {{ color: var(--warm); }}
  .hot {{ color: var(--hot); }}

  /* Heat strip */
  .heat-strip-container {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 24px;
  }}
  .heat-strip-label {{
    font-size: 0.85rem;
    color: var(--text-dim);
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }}
  .heat-strip {{
    display: flex;
    height: 48px;
    border-radius: 4px;
    overflow: hidden;
    cursor: crosshair;
  }}
  .heat-cell {{
    flex: 1;
    transition: opacity 0.15s;
    position: relative;
  }}
  .heat-cell:hover {{
    opacity: 0.8;
    outline: 2px solid white;
    outline-offset: -2px;
    z-index: 1;
  }}
  .heat-legend {{
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 0.75rem;
    color: var(--text-dim);
  }}

  /* Chunk detail grid */
  .chunks-label {{
    font-size: 0.85rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
  }}
  .chunks-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 12px;
    margin-bottom: 32px;
  }}
  .chunk-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    transition: border-color 0.2s, transform 0.15s;
  }}
  .chunk-card:hover {{
    border-color: var(--accent);
    transform: translateY(-1px);
  }}
  .chunk-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }}
  .chunk-id {{
    font-weight: 600;
    font-size: 0.9rem;
  }}
  .chunk-badge {{
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .badge-cold {{ background: rgba(59,130,246,0.15); color: var(--cold); }}
  .badge-warm {{ background: rgba(245,158,11,0.15); color: var(--warm); }}
  .badge-hot  {{ background: rgba(239,68,68,0.15);  color: var(--hot); }}

  .chunk-metrics {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    font-size: 0.8rem;
  }}
  .metric-name {{ color: var(--text-dim); }}
  .metric-val {{ text-align: right; font-weight: 500; }}

  /* Feature bars */
  .feature-bars {{
    margin-top: 12px;
  }}
  .feature-bar-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
    font-size: 0.72rem;
  }}
  .feature-name {{
    width: 90px;
    color: var(--text-dim);
    text-align: right;
    flex-shrink: 0;
  }}
  .feature-track {{
    flex: 1;
    height: 6px;
    background: rgba(255,255,255,0.05);
    border-radius: 3px;
    overflow: hidden;
  }}
  .feature-fill {{
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s;
  }}
  .feature-value {{
    width: 40px;
    text-align: right;
    color: var(--text-dim);
    flex-shrink: 0;
  }}

  /* Probe table */
  .probes-section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 24px;
  }}
  .probes-label {{
    font-size: 0.85rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
  }}
  th {{
    text-align: left;
    color: var(--text-dim);
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    font-weight: 500;
    text-transform: uppercase;
    font-size: 0.7rem;
    letter-spacing: 0.05em;
  }}
  td {{
    padding: 8px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
  }}
  tr:hover td {{ background: rgba(255,255,255,0.02); }}

  /* KOT cost indicator */
  .kot-section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 24px;
  }}
  .kot-label {{
    font-size: 0.85rem;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
  }}
  .kot-bar {{
    display: flex;
    gap: 4px;
    height: 32px;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 8px;
  }}
  .kot-segment {{
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 600;
    color: rgba(0,0,0,0.7);
  }}

  .footer {{
    color: var(--text-dim);
    font-size: 0.7rem;
    text-align: center;
    margin-top: 32px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
  }}

  /* Tooltip */
  .tooltip {{
    display: none;
    position: fixed;
    background: #1e293b;
    border: 1px solid var(--accent);
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 0.75rem;
    pointer-events: none;
    z-index: 100;
    max-width: 280px;
    line-height: 1.5;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  }}
</style>
</head>
<body>

<h1>&#x1f9ec; Contract Heat Map</h1>
<div class="meta">
  SHA-256: <span>{sha256}</span><br>
  Length: <span>{length} bytes</span> &nbsp;|&nbsp;
  Chunks: <span>{chunk_count}</span> &nbsp;|&nbsp;
  Waveprobe: <span>{version}</span>
</div>

<div class="summary">
  <div class="card">
    <div class="card-value {overall_class}">{overall_heat}</div>
    <div class="card-label">Overall Heat</div>
  </div>
  <div class="card">
    <div class="card-value {overall_class}">{overall_class_upper}</div>
    <div class="card-label">Classification</div>
  </div>
  <div class="card">
    <div class="card-value cold">{cold_count}</div>
    <div class="card-label">&#x1f9ca; Cold Regions</div>
  </div>
  <div class="card">
    <div class="card-value warm">{warm_count}</div>
    <div class="card-label">&#x1f321;&#xfe0f; Warm Regions</div>
  </div>
  <div class="card">
    <div class="card-value hot">{hot_count}</div>
    <div class="card-label">&#x1f525; Hot Regions</div>
  </div>
</div>

<div class="heat-strip-container">
  <div class="heat-strip-label">Bytecode Heat Map (offset &rarr;)</div>
  <div class="heat-strip" id="heatStrip">{heat_strip_html}</div>
  <div class="heat-legend">
    <span>&#x1f9ca; Cold (heat &lt; 0.05)</span>
    <span>&#x1f321;&#xfe0f; Warm (0.05 &le; heat &lt; 0.25)</span>
    <span>&#x1f525; Hot (heat &ge; 0.25)</span>
  </div>
</div>

<div class="kot-section">
  <div class="kot-label">&#x26a1; KOT Action Cost Estimate</div>
  <div class="kot-bar" id="kotBar">{kot_bar_html}</div>
  <div style="font-size:0.8rem; color:var(--text-dim);">
    Estimated traversal cost breakdown by region classification.
    Hot regions cost more KOT to interact with (higher probe complexity).
  </div>
</div>

<div class="chunks-label">Per-Chunk Analysis</div>
<div class="chunks-grid" id="chunksGrid">{chunks_html}</div>

<div class="probes-section">
  <div class="probes-label">Probe Family Response (Chunk 0)</div>
  <table>
    <thead>
      <tr>
        <th>Probe Family</th>
        <th>Feature Displacement</th>
        <th>Compression Displacement</th>
      </tr>
    </thead>
    <tbody id="probeTable">{probe_table_html}</tbody>
  </table>
</div>

<div class="footer">
  Waveprobe v0.1-evm &nbsp;|&nbsp;
  Operational Spec: OPERATIONAL_SPEC.md &nbsp;|&nbsp;
  Murphy's Law is the uncle you can't not invite to the table.
</div>

<div class="tooltip" id="tooltip"></div>

<script>
const probeData = {probe_data_json};

// Tooltip on heat strip
document.querySelectorAll('.heat-cell').forEach(function(cell) {{
  cell.addEventListener('mouseenter', function(e) {{
    const tip = document.getElementById('tooltip');
    const idx = parseInt(this.dataset.idx);
    const d = probeData.chunks[idx];
    if (!d) return;
    tip.innerHTML = '<b>Chunk ' + idx + '</b> (offset ' + d.chunk_offset + ')<br>' +
      'Heat: ' + d.aggregate.heat.toFixed(6) + '<br>' +
      'Anisotropy: ' + d.aggregate.anisotropy.toFixed(4) + '<br>' +
      'Class: ' + d.classification;
    tip.style.display = 'block';
  }});
  cell.addEventListener('mousemove', function(e) {{
    const tip = document.getElementById('tooltip');
    tip.style.left = (e.clientX + 12) + 'px';
    tip.style.top = (e.clientY + 12) + 'px';
  }});
  cell.addEventListener('mouseleave', function() {{
    document.getElementById('tooltip').style.display = 'none';
  }});
}});
</script>
</body>
</html>"""

# ── Feature names ────────────────────────────────────────────────────────────

FEATURE_NAMES = [
    "entropy",
    "opcode_dens",
    "call_dens",
    "ctrl_flow",
    "push_ratio",
    "jd_spacing",
    "repetition",
    "compress",
]

FEATURE_COLORS = [
    "#8b5cf6",  # purple
    "#06b6d4",  # cyan
    "#ef4444",  # red
    "#f59e0b",  # amber
    "#10b981",  # emerald
    "#3b82f6",  # blue
    "#ec4899",  # pink
    "#6366f1",  # indigo
]


# ── Rendering ────────────────────────────────────────────────────────────────

def _heat_to_color(heat: float) -> str:
    """Map heat value to an RGB color string."""
    if heat >= 0.25:
        # Hot: red
        t = min(1.0, (heat - 0.25) / 0.75)
        r = int(239 + t * 16)
        g = int(68 - t * 40)
        b = int(68 - t * 40)
    elif heat >= 0.05:
        # Warm: amber
        t = (heat - 0.05) / 0.20
        r = int(59 + t * 186)
        g = int(130 + t * 28)
        b = int(246 - t * 178)
    else:
        # Cold: blue
        t = heat / 0.05
        r = int(30 + t * 29)
        g = int(64 + t * 66)
        b = int(175 + t * 71)
    return f"rgb({min(255,r)},{min(255,g)},{min(255,b)})"


def _render_heat_strip(data: Dict[str, Any]) -> str:
    """Render the horizontal heat strip cells."""
    cells = []
    for i, heat in enumerate(data.get("heat_map", [])):
        color = _heat_to_color(heat)
        cells.append(
            f'<div class="heat-cell" data-idx="{i}" '
            f'style="background:{color};" '
            f'title="Chunk {i}: heat={heat:.6f}"></div>'
        )
    return "".join(cells)


def _render_kot_bar(data: Dict[str, Any]) -> str:
    """Render the KOT cost estimate bar."""
    cold = data.get("cold_region_count", 0)
    warm = data.get("warm_region_count", 0)
    hot = data.get("high_heat_region_count", 0)
    total = cold + warm + hot
    if total == 0:
        return '<div class="kot-segment" style="flex:1;background:#333;">No data</div>'

    # KOT cost weights (cold=1x, warm=4x, hot=16x)
    cold_kot = cold * 1
    warm_kot = warm * 4
    hot_kot = hot * 16
    total_kot = cold_kot + warm_kot + hot_kot

    parts = []
    if cold_kot > 0:
        pct = cold_kot / total_kot * 100
        parts.append(
            f'<div class="kot-segment" style="flex:{cold_kot};background:var(--cold);">'
            f'{cold_kot} KOT ({pct:.0f}%)</div>'
        )
    if warm_kot > 0:
        pct = warm_kot / total_kot * 100
        parts.append(
            f'<div class="kot-segment" style="flex:{warm_kot};background:var(--warm);">'
            f'{warm_kot} KOT ({pct:.0f}%)</div>'
        )
    if hot_kot > 0:
        pct = hot_kot / total_kot * 100
        parts.append(
            f'<div class="kot-segment" style="flex:{hot_kot};background:var(--hot);">'
            f'{hot_kot} KOT ({pct:.0f}%)</div>'
        )
    return "".join(parts)


def _render_feature_bars(features: List[float]) -> str:
    """Render feature bar chart for a chunk."""
    bars = []
    for i, val in enumerate(features):
        name = FEATURE_NAMES[i] if i < len(FEATURE_NAMES) else f"f{i}"
        color = FEATURE_COLORS[i] if i < len(FEATURE_COLORS) else "#888"
        pct = min(100, max(0, val * 100))
        bars.append(
            f'<div class="feature-bar-row">'
            f'<div class="feature-name">{name}</div>'
            f'<div class="feature-track">'
            f'<div class="feature-fill" style="width:{pct:.1f}%;background:{color};"></div>'
            f'</div>'
            f'<div class="feature-value">{val:.3f}</div>'
            f'</div>'
        )
    return "".join(bars)


def _render_chunk_card(idx: int, chunk: Dict[str, Any]) -> str:
    """Render a single chunk detail card."""
    cls = chunk.get("classification", "cold")
    badge_cls = f"badge-{cls}"
    agg = chunk.get("aggregate", {})
    features = chunk.get("base_features", [])

    return (
        f'<div class="chunk-card">'
        f'<div class="chunk-header">'
        f'  <div class="chunk-id">Chunk {idx} '
        f'  <span style="color:var(--text-dim);font-weight:400;">'
        f'    (offset {chunk.get("chunk_offset", 0)})</span></div>'
        f'  <div class="chunk-badge {badge_cls}">{cls}</div>'
        f'</div>'
        f'<div class="chunk-metrics">'
        f'  <div class="metric-name">Heat</div>'
        f'  <div class="metric-val">{agg.get("heat", 0):.6f}</div>'
        f'  <div class="metric-name">Sensitivity</div>'
        f'  <div class="metric-val">{agg.get("sensitivity", 0):.6f}</div>'
        f'  <div class="metric-name">Anisotropy</div>'
        f'  <div class="metric-val">{agg.get("anisotropy", 0):.4f}</div>'
        f'  <div class="metric-name">Comp. Sens.</div>'
        f'  <div class="metric-val">{agg.get("compression_sensitivity", 0):.6f}</div>'
        f'</div>'
        f'<div class="feature-bars">'
        f'{_render_feature_bars(features)}'
        f'</div>'
        f'</div>'
    )


def _render_chunks(data: Dict[str, Any]) -> str:
    """Render all chunk cards."""
    cards = []
    for i, chunk in enumerate(data.get("chunks", [])):
        cards.append(_render_chunk_card(i, chunk))
    return "".join(cards)


def _render_probe_table(data: Dict[str, Any]) -> str:
    """Render probe response table for chunk 0."""
    chunks = data.get("chunks", [])
    if not chunks:
        return "<tr><td colspan='3'>No chunks</td></tr>"

    rows = []
    for probe in chunks[0].get("probes", []):
        mag = probe.get("feature_displacement_magnitude", 0)
        comp = probe.get("compression_displacement", 0)
        # Color intensity by magnitude
        mag_color = _heat_to_color(min(0.5, mag * 10))
        comp_color = _heat_to_color(min(0.5, comp * 10))
        rows.append(
            f'<tr>'
            f'<td>{probe.get("probe_family", "")}</td>'
            f'<td style="color:{mag_color};">{mag:.8f}</td>'
            f'<td style="color:{comp_color};">{comp:.8f}</td>'
            f'</tr>'
        )
    return "".join(rows)


def render_heatmap(data: Dict[str, Any]) -> str:
    """Render the full heat map HTML from waveprobe JSON data."""
    overall_class = data.get("overall_classification", "cold")

    return HTML_TEMPLATE.format(
        sha256=data.get("bytecode_sha256", "unknown"),
        length=data.get("total_length", 0),
        chunk_count=data.get("chunk_count", 0),
        version=data.get("waveprobe_version", "0.1-evm"),
        overall_heat=f'{data.get("overall_heat", 0):.6f}',
        overall_class=overall_class,
        overall_class_upper=overall_class.upper(),
        cold_count=data.get("cold_region_count", 0),
        warm_count=data.get("warm_region_count", 0),
        hot_count=data.get("high_heat_region_count", 0),
        heat_strip_html=_render_heat_strip(data),
        kot_bar_html=_render_kot_bar(data),
        chunks_html=_render_chunks(data),
        probe_table_html=_render_probe_table(data),
        probe_data_json=json.dumps(data),
    )


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Contract Heat Map — Waveprobe visualizer"
    )
    parser.add_argument("--input", "-i",
                        help="Path to waveprobe JSON output file")
    parser.add_argument("--bytecode", "-b",
                        help="Hex-encoded bytecode (runs waveprobe first)")
    parser.add_argument("--bytecode-file", "-f",
                        help="File containing hex-encoded bytecode")
    parser.add_argument("--output", "-o",
                        help="Output HTML file path (default: stdout)")

    args = parser.parse_args()

    probe_data: Optional[Dict[str, Any]] = None

    if args.input:
        with open(args.input) as f:
            probe_data = json.load(f)
    elif args.bytecode or args.bytecode_file:
        # Import and run the waveprobe
        sys.path.insert(0, str(Path(__file__).parent))
        from evm_bytecode_waveprobe import EVMBytecodeWaveprobe

        if args.bytecode_file:
            bc_hex = Path(args.bytecode_file).read_text().strip()
        else:
            bc_hex = args.bytecode

        probe = EVMBytecodeWaveprobe(bytecode_hex=bc_hex)
        result = probe.analyze()
        probe_data = json.loads(probe.to_json(result))
    else:
        # Read from stdin
        raw = sys.stdin.read().strip()
        if not raw:
            print("Error: no input. Use --input, --bytecode, or pipe JSON.",
                  file=sys.stderr)
            sys.exit(1)
        probe_data = json.loads(raw)

    html = render_heatmap(probe_data)

    if args.output:
        Path(args.output).write_text(html)
        print(f"Wrote heat map to {args.output}", file=sys.stderr)
    else:
        print(html)

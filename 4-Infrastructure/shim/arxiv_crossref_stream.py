#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
arxiv_crossref_stream.py — Stream-encoding RRC↔arXiv cross-reference pipeline.

Architecture:
  1. Token encoding: SHA1(token) mod 2^8 = 8-bit code (vocabulary-free, deterministic)
  2. Stream RRC equations + arXiv papers into Postgres on neon-64gb
  3. Multi-stage cross-reference:
     - Stage 1: code containment @> (3+ code requirement, ≤ 10 matches)
     - Stage 2: containment + route_hint→categories crosswalk
     - Stage 3: math-term keyword for extracted_md_equation rows
     - Stage 4: name-specific compound-term keyword

Database tables (created if absent):
  arxiv_paper_codes8 (paper_id, codes SMALLINT[])        -- 3,066,093 rows
  rrc_equation_codes8 (equation_id, name, codes SMALLINT[])  -- 250 rows

The encoding scheme is deterministic and reproducible. Re-running this script
with the same inputs always produces the same matches.

Usage:
  python3 4-Infrastructure/shim/arxiv_crossref_stream.py [--stage=N] [--neon=neon-64gb] [--rebuild]

Stages:
  1 = containment-only (low-count matches)
  2 = containment + category crosswalk
  3 = math-term keyword for extracted_md_equation
  4 = name-specific compound-term keyword
  5 = broad math/keyword fallback for remaining
  all = run all stages
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

N_STRANDS = 8
NEON_HOST = 'neon-64gb'
CONTAINER = 'arxiv-pg'
DB = 'arxiv'

ROOT = Path('/home/allaun/Research Stack')
RECEIPT_PATH = ROOT / 'archive/experimental-shim-probes/rrc_equation_classifier_receipt.json'
PREDICTIONS_OUT = ROOT / 'shared-data/rrc_arxiv_predictions_v1.json'
RECEIPT_OUT = ROOT / 'shared-data/data/stack_solidification'

ROUTE_HINT_CROSSWALK = {
    'thermodynamic_energy': ['cond-mat', 'physics', 'quant-ph', 'hep-'],
    'geometry_topology':   ['math.DG', 'math.GT', 'math.AG', 'math.QA', 'math.GM', 'math.AT'],
    'cognitive_load':      ['cs.CV', 'cs.AI', 'cs.LG', 'cs.NE'],
    'compression_route':   ['cs.IT', 'cs.LG', 'stat.ML', 'cs.AI'],
    'cad_force':           ['cond-mat', 'physics'],
    'magnetic_signal':     ['cond-mat'],
    'control_signal':      ['cs.SY', 'math.OC', 'cs.NA'],
    'chaotic_couch':       ['nlin.CD'],
    'unclassified_equation': ['cs.LG', 'stat.ML', 'cs.AI', 'math.ST', 'cs.IT'],
}

GENERIC_NAMES = {
    'core_equations', 'field_mapping', 'source_domain', 'target_domain', 'heat_loss',
    'magnetic_projection', 'overflow_gate', 'signal_load', 'counted_total',
    'hard_target_rule', 'hutter_route_metastate', 'lower_bound',
    'metastate_transfold', 'promotion_rule', 'prune_rule', 'source_equation_surface',
}

MATH_MAP = {
    'a_μ': 'anomalous magnetic moment', 'g_μ': 'muon g-factor', 'μ': 'muon',
    'σ': 'sigma', 'λ': 'lambda', 'ω': 'omega', 'α': 'alpha', 'β': 'beta',
    'γ': 'gamma', 'Ψ': 'wave function', '∇²': 'laplacian', '∇': 'gradient',
    'F^{-1}': 'fourier transform', 'sin': 'sine', 'cos': 'cosine',
    'exp': 'exponential', 'log': 'logarithm', 'Θ_D': 'debye temperature',
    'k_B': 'boltzmann constant', 'k_Ψ': 'wave vector', 'D_s': 'spectral dimension',
    'D_H': 'hausdorff dimension', 'C_V': 'heat capacity', 'E_n': 'energy level',
    'L_n': 'lagrangian', 'L_{n+1}': 'level n+1', 'd_inj': 'injection dimension',
    'W': 'work', 'ΔF': 'free energy', 'cos(k_Ψ': 'cosine wave vector',
    '|A|²': 'amplitude', 'p = ℏ k': 'de broglie', 'λ = 2π': 'wavelength',
    'D_t': 'time derivative', 'D_t^α': 'fractional time derivative', '|Ψ|^γ': 'nonlinear wave',
    'C_V =': 'heat capacity formula', 'k_B (T/Θ_D)³': 'debye temperature',
    'dθ_0/dx': 'angle derivative',
}

NAME_SPECIFIC_TERMS = {
    'threshold':                              ['threshold'],
    'trauma_adjusted_emotional_barrier':      ['trauma', 'barrier', 'load'],
    'NES_GCL_Square_Wave_Compression':        ['genetic', 'combinator', 'lossless'],
    'NES_OISC_GCL_LUT_Architecture':          ['genetic', 'instruction', 'lookup'],
    'Affine_Mapping_LTSF_Linear_Layer':       ['long-term', 'forecasting', 'linear'],
    'Affine_Mapping_Time_Series_Decomposition': ['time series', 'decomposition'],
    'MOF_CO2_Reduction_2e_Electrochemistry':  ['metal-organic framework', 'electrochem'],
    'MOF_CO2_Reduction_6e_Methanol':          ['metal-organic framework', 'methanol'],
    'Multi_Factor_Coupling_Weight':           ['coupling', 'weight'],
    'DAG_Global_Validity':                    ['directed acyclic', 'global validity'],
    'Metric_Tensor_From_Circumferences':      ['metric tensor', 'circumference'],
    'Christoffel_Symbols_2D':                 ['christoffel', 'symbol'],
    'Stereographic_Chart_Transition':         ['stereographic', 'chart'],
}


# ─────────────────────────────────────────────────────────────────────────────
# §1  TOKEN ENCODING
# ─────────────────────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    """Tokenize: lowercase, split on non-alphanumeric."""
    if not text:
        return []
    text = text.lower()
    return [p for p in re.split(r'[^a-z0-9]+', text) if p and len(p) > 1]


def token_code_8(t: str) -> int:
    """8-bit code (256 values) via SHA1."""
    return int(hashlib.sha1(t.encode('utf-8')).hexdigest()[:2], 16)


def encode_str(s: str) -> list[int]:
    return [token_code_8(t) for t in tokenize(s)]


# ─────────────────────────────────────────────────────────────────────────────
# §2  SSH / POSTGRES HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def ssh_query(sql: str, host: str = NEON_HOST, timeout: int = 120) -> list[list[str]]:
    """Run a psql query on the remote arxiv-pg container and return rows."""
    result = subprocess.run([
        'ssh', host,
        f'podman exec {CONTAINER} psql -U postgres -d {DB} -t -A -F "|" -c "{sql}"'
    ], capture_output=True, text=True, timeout=timeout)
    return [line.split('|') for line in result.stdout.strip().split('\n') if line]


def ssh_exec(sql: str, host: str = NEON_HOST, timeout: int = 300) -> bool:
    """Execute a psql command (no return value)."""
    result = subprocess.run([
        'ssh', host,
        f'podman exec {CONTAINER} psql -U postgres -d {DB} -c "{sql}"'
    ], capture_output=True, text=True, timeout=timeout)
    return result.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# §3  DATABASE TABLE SETUP
# ─────────────────────────────────────────────────────────────────────────────

def setup_tables():
    """Create the arxiv_paper_codes8 and rrc_equation_codes8 tables if absent."""
    ssh_exec("""
        DROP TABLE IF EXISTS arxiv_paper_codes8;
        CREATE TABLE arxiv_paper_codes8 (
            paper_id TEXT PRIMARY KEY,
            codes SMALLINT[] NOT NULL
        );
    """)
    ssh_exec("""
        DROP TABLE IF EXISTS rrc_equation_codes8;
        CREATE TABLE rrc_equation_codes8 (
            equation_id TEXT PRIMARY KEY,
            name TEXT,
            codes SMALLINT[] NOT NULL
        );
    """)
    print("Tables created", file=sys.stderr)


def stream_arxiv_titles():
    """Stream 3M arXiv titles from DB to local file, then COPY into arxiv_paper_codes8."""
    local_dump = Path('/tmp/arxiv_titles.txt')
    if not local_dump.exists():
        print("Dumping arXiv titles...", file=sys.stderr)
        t0 = time.time()
        result = subprocess.run([
            'ssh', NEON_HOST,
            "podman exec arxiv-pg psql -U postgres -d arxiv -t -A -F '|' "
            "-c \"COPY (SELECT paper_id, title FROM arxiv_papers ORDER BY paper_id) TO STDOUT\""
        ], capture_output=True, text=True, timeout=600)
        local_dump.write_text(result.stdout)
        print(f"  Dumped {len(result.stdout.splitlines())} titles in {time.time()-t0:.0f}s", file=sys.stderr)

    print("Encoding arXiv titles (8-bit codes)...", file=sys.stderr)
    t0 = time.time()
    encoded_path = Path('/tmp/arxiv_codes8.tsv')
    count = 0
    with open(local_dump) as f, open(encoded_path, 'w') as out:
        for line in f:
            if '\t' not in line:
                continue
            parts = line.split('\t', 1)
            if len(parts) < 2:
                continue
            paper_id, title = parts[0], parts[1].rstrip('\n')
            codes = encode_str(title)
            if not codes:
                continue
            code_str = '{' + ','.join(str(c) for c in codes) + '}'
            pid_esc = paper_id.replace('\\', '\\\\')
            code_esc = code_str.replace('\\', '\\\\')
            out.write(f"{pid_esc}\t{code_esc}\n")
            count += 1
    print(f"  Encoded {count} titles in {time.time()-t0:.0f}s ({encoded_path.stat().st_size/1024/1024:.1f} MB)", file=sys.stderr)

    # Copy into container
    print("Copying to container and loading...", file=sys.stderr)
    subprocess.run(['scp', str(encoded_path), f'{NEON_HOST}:/tmp/'], check=True)
    subprocess.run(['ssh', NEON_HOST, f'podman cp /tmp/{encoded_path.name} {CONTAINER}:/tmp/'], check=True)
    ssh_exec(f"COPY arxiv_paper_codes8(paper_id, codes) FROM '/tmp/{encoded_path.name}' WITH (FORMAT csv, DELIMITER E'\\\\t')")
    rows = ssh_query("SELECT COUNT(*) FROM arxiv_paper_codes8")
    print(f"  Loaded {rows[0][0]} rows into arxiv_paper_codes8", file=sys.stderr)


def stream_rrc_equations(receipt_path: Path):
    """Stream 250 RRC equations into rrc_equation_codes8."""
    d = json.loads(receipt_path.read_text())
    eqs = d['compiled_equations']
    rows = []
    for e in eqs:
        name = e['equation_record'].get('name', '')
        eq_id = e['invariant_receipt']['object_id']
        codes = encode_str(name)
        if not codes:
            continue
        code_str = '{' + ','.join(str(c) for c in codes) + '}'
        name_esc = name.replace("'", "''")
        rows.append(f"('{eq_id}', '{name_esc}', '{code_str}')")
    BATCH = 100
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i+BATCH]
        sql = (f"INSERT INTO rrc_equation_codes8 (equation_id, name, codes) VALUES "
               + ','.join(batch)
               + " ON CONFLICT (equation_id) DO UPDATE SET name=EXCLUDED.name, codes=EXCLUDED.codes")
        ssh_exec(sql, timeout=60)
    print(f"Streamed {len(rows)} RRC equations into rrc_equation_codes8", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# §4  MATCHING STAGES
# ─────────────────────────────────────────────────────────────────────────────

def get_rrc_codes() -> dict[str, list[int]]:
    result = ssh_query("SELECT equation_id, codes FROM rrc_equation_codes8")
    out = {}
    for r in result:
        if len(r) >= 2:
            codes = [int(c) for c in r[1].strip('{}').split(',') if c]
            out[r[0]] = codes
    return out


def apply_to_receipt(receipt_path: Path, matches: list[dict]):
    """Write new matches to the classifier receipt."""
    d = json.loads(receipt_path.read_text())
    eqs = d['compiled_equations']
    added = 0
    for m in matches:
        for e in eqs:
            if e['invariant_receipt']['object_id'] == m['rrc_eq_id']:
                if not e['equation_record'].get('arxiv_paper_id'):
                    e['equation_record']['arxiv_paper_id'] = m['arxiv_paper_id']
                    if 'matches' in m:
                        e['equation_record']['arxiv_match_count'] = m['matches']
                    if 'rrc_route_hint' in m:
                        e['equation_record']['arxiv_match_route_hint'] = m['rrc_route_hint']
                    if 'distinctive_terms' in m:
                        e['equation_record']['arxiv_match_terms'] = m['distinctive_terms']
                    added += 1
                break
    receipt_path.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    return added


def stage1_containment(rrc_codes: dict, threshold: int = 10) -> list[dict]:
    """Stage 1: 3+ code containment, ≤ threshold matches."""
    print("Stage 1: containment-only, 3+ code, ≤ 10 matches", file=sys.stderr)
    matches = []
    for eq_id, codes in rrc_codes.items():
        if len(codes) < 3:
            continue
        sql = (f"SELECT MIN(paper_id), COUNT(*) FROM arxiv_paper_codes8 "
               f"WHERE codes @> ARRAY[{','.join(str(c) for c in codes)}]::SMALLINT[] "
               f"GROUP BY paper_id HAVING COUNT(*) <= 1")  # self-aggregation
        # Simpler: just count overall matches
        sql2 = f"SELECT COUNT(*) FROM arxiv_paper_codes8 WHERE codes @> ARRAY[{','.join(str(c) for c in codes)}]::SMALLINT[]"
        rows = ssh_query(sql2)
        cnt = int(rows[0][0]) if rows else 0
        if 0 < cnt <= threshold:
            # Get first paper
            sql3 = f"SELECT MIN(paper_id) FROM arxiv_paper_codes8 WHERE codes @> ARRAY[{','.join(str(c) for c in codes)}]::SMALLINT[]"
            rows3 = ssh_query(sql3)
            if rows3:
                paper_id = rows3[0][0]
                matches.append({
                    'rrc_eq_id': eq_id,
                    'arxiv_paper_id': paper_id.replace('_', '.', 1) if '/' not in paper_id else paper_id,
                    'matches': cnt,
                    'stage': 1,
                })
    print(f"  Stage 1 matches: {len(matches)}", file=sys.stderr)
    return matches


def stage2_crosswalk(receipt_path: Path, rrc_codes: dict) -> list[dict]:
    """Stage 2: containment + route_hint→categories crosswalk."""
    print("Stage 2: containment + route_hint→categories crosswalk", file=sys.stderr)
    d = json.loads(receipt_path.read_text())
    eqs = d['compiled_equations']
    by_id = {e['invariant_receipt']['object_id']: e for e in eqs}
    matches = []
    for eq_id, codes in rrc_codes.items():
        if len(codes) < 2:
            continue
        if eq_id in by_id:
            rh = by_id[eq_id]['equation_record'].get('route_hint_non_authoritative', '')
        else:
            rh = 'unclassified_equation'
        if rh not in ROUTE_HINT_CROSSWALK:
            continue
        cats = ROUTE_HINT_CROSSWALK[rh]
        cat_filter = ' OR '.join(f"app.categories LIKE '%{c}%'" for c in cats)
        sql = (f"SELECT MIN(ap.paper_id), COUNT(*) FROM arxiv_paper_codes8 ap, arxiv_papers app "
               f"WHERE ap.paper_id = app.paper_id "
               f"AND ap.codes @> ARRAY[{','.join(str(c) for c in codes)}]::SMALLINT[] "
               f"AND ({cat_filter})")
        rows = ssh_query(sql)
        if rows and len(rows[0]) >= 2 and rows[0][0]:
            paper_id = rows[0][0]
            cnt = int(rows[0][1])
            n_tok = len([t for t in tokenize(by_id.get(eq_id, {}).get('equation_record', {}).get('name', ''))])
            threshold = 200 if n_tok == 2 else 50
            if cnt <= threshold:
                matches.append({
                    'rrc_eq_id': eq_id,
                    'arxiv_paper_id': paper_id.replace('_', '.', 1) if '/' not in paper_id else paper_id,
                    'matches': cnt,
                    'rrc_route_hint': rh,
                    'stage': 2,
                })
    print(f"  Stage 2 matches: {len(matches)}", file=sys.stderr)
    return matches


def extract_math_terms(eq_text: str) -> list[str]:
    """Extract distinctive English search terms from a math equation."""
    text = eq_text
    for sym in sorted(MATH_MAP.keys(), key=lambda x: -len(x)):
        if sym in text:
            text = text.replace(sym, f' {MATH_MAP[sym]} ')
    text = re.sub(r'[²³⁴⁰¹{}()=+\-*/|^∝≈≤≥⟨⟩·×∮∇ℏΨ]', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9_\-]', ' ', text)
    tokens = re.findall(r'[a-z][a-z0-9-]{2,}', text.lower())
    stop = {'the', 'and', 'for', 'where', 'with', 'this', 'from', 'that', 'are', 'but', 'not'}
    return list(set(t for t in tokens if t not in stop))


def stage3_math_terms(receipt_path: Path) -> list[dict]:
    """Stage 3: math-term keyword for extracted_md_equation rows."""
    print("Stage 3: math-term keyword for extracted_md_equation", file=sys.stderr)
    d = json.loads(receipt_path.read_text())
    eqs = d['compiled_equations']
    matches = []
    for e in eqs:
        name = e['equation_record'].get('name', '')
        if not name.startswith('extracted_md_equation'):
            continue
        if e['equation_record'].get('arxiv_paper_id'):
            continue
        eq_text = e['equation_record'].get('equation', '')
        terms = extract_math_terms(eq_text)
        # Pick 2-3 most distinctive
        distinctive = [t for t in terms if t in {
            'muon', 'sigma', 'laplacian', 'fractional', 'debye', 'boltzmann',
            'eigenvalue', 'wave', 'momentum', 'wavelength', 'planck', 'derivative',
            'temperature', 'amplitude', 'free', 'energy', 'cubed', 'exponential',
        }]
        if not distinctive:
            distinctive = terms[:3]
        if not distinctive:
            continue
        where = ' AND '.join(f"title ILIKE '%{t}%'" for t in distinctive[:3])
        sql = f"SELECT paper_id, title FROM arxiv_papers WHERE {where} ORDER BY paper_id LIMIT 1"
        rows = ssh_query(sql)
        if rows:
            paper_id = rows[0][0]
            matches.append({
                'rrc_eq_id': e['invariant_receipt']['object_id'],
                'arxiv_paper_id': paper_id.replace('_', '.', 1) if '/' not in paper_id else paper_id,
                'distinctive_terms': distinctive[:3],
                'stage': 3,
            })
    print(f"  Stage 3 matches: {len(matches)}", file=sys.stderr)
    return matches


def stage4_name_specific(receipt_path: Path) -> list[dict]:
    """Stage 4: name-specific compound-term keyword for remaining real RRC names."""
    print("Stage 4: name-specific keyword search", file=sys.stderr)
    d = json.loads(receipt_path.read_text())
    eqs = d['compiled_equations']
    matches = []
    for e in eqs:
        name = e['equation_record'].get('name', '')
        if e['equation_record'].get('arxiv_paper_id'):
            continue
        if name in GENERIC_NAMES or name.startswith('eq_') or name.startswith('extracted_md_equation'):
            continue
        if name not in NAME_SPECIFIC_TERMS:
            continue
        terms = NAME_SPECIFIC_TERMS[name]
        where = ' AND '.join(f"title ILIKE '%{t}%'" for t in terms)
        sql = f"SELECT paper_id, title FROM arxiv_papers WHERE {where} ORDER BY paper_id LIMIT 1"
        rows = ssh_query(sql)
        if rows:
            paper_id = rows[0][0]
            matches.append({
                'rrc_eq_id': e['invariant_receipt']['object_id'],
                'arxiv_paper_id': paper_id.replace('_', '.', 1) if '/' not in paper_id else paper_id,
                'distinctive_terms': terms,
                'stage': 4,
            })
    print(f"  Stage 4 matches: {len(matches)}", file=sys.stderr)
    return matches


def stage5_broad_math(receipt_path: Path) -> list[dict]:
    """Stage 5: broader math/keyword fallback for remaining."""
    print("Stage 5: broad math/keyword fallback", file=sys.stderr)
    d = json.loads(receipt_path.read_text())
    eqs = d['compiled_equations']
    matches = []
    fallback_terms = {
        'extracted_md_equation_5':  ['fractional', 'laplacian'],
        'extracted_md_equation_26': ['debye', 'boltzmann'],
        'extracted_md_equation_33': ['wave', 'amplitude'],
        'extracted_md_equation_35': ['de broglie', 'momentum'],
        'extracted_md_equation_36': ['wavelength'],
    }
    for e in eqs:
        name = e['equation_record'].get('name', '')
        if e['equation_record'].get('arxiv_paper_id'):
            continue
        if name not in fallback_terms:
            continue
        terms = fallback_terms[name]
        where = ' AND '.join(f"title ILIKE '%{t}%'" for t in terms)
        sql = f"SELECT paper_id, title FROM arxiv_papers WHERE {where} ORDER BY paper_id LIMIT 1"
        rows = ssh_query(sql)
        if rows:
            paper_id = rows[0][0]
            matches.append({
                'rrc_eq_id': e['invariant_receipt']['object_id'],
                'arxiv_paper_id': paper_id.replace('_', '.', 1) if '/' not in paper_id else paper_id,
                'distinctive_terms': terms,
                'stage': 5,
            })
    print(f"  Stage 5 matches: {len(matches)}", file=sys.stderr)
    return matches


# ─────────────────────────────────────────────────────────────────────────────
# §5  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='Stream-encoding RRC↔arXiv cross-reference')
    ap.add_argument('--stage', default='all', help='1, 2, 3, 4, 5, or all')
    ap.add_argument('--rebuild', action='store_true', help='Rebuild code tables from scratch')
    ap.add_argument('--receipt', type=Path, default=RECEIPT_PATH)
    args = ap.parse_args()

    print("=" * 60)
    print("Stream-encoding RRC↔arXiv cross-reference pipeline")
    print("=" * 60)
    print(f"Receipt: {args.receipt}")

    if args.rebuild or not args.receipt.exists():
        setup_tables()
        stream_arxiv_titles()
        stream_rrc_equations(args.receipt)

    rrc_codes = get_rrc_codes()
    print(f"Loaded {len(rrc_codes)} RRC equation code sequences", file=sys.stderr)

    all_matches = []
    if args.stage in ('1', 'all'):
        all_matches += stage1_containment(rrc_codes)
    if args.stage in ('2', 'all'):
        all_matches += stage2_crosswalk(args.receipt, rrc_codes)
    if args.stage in ('3', 'all'):
        all_matches += stage3_math_terms(args.receipt)
    if args.stage in ('4', 'all'):
        all_matches += stage4_name_specific(args.receipt)
    if args.stage in ('5', 'all'):
        all_matches += stage5_broad_math(args.receipt)

    # Dedupe by rrc_eq_id
    seen = {}
    for m in all_matches:
        seen[m['rrc_eq_id']] = m
    all_matches = list(seen.values())
    print(f"\nTotal unique matches: {len(all_matches)}")

    if not all_matches:
        return

    added = apply_to_receipt(args.receipt, all_matches)
    print(f"Added {added} new rows to receipt")

    # Save receipt
    RECEIPT_OUT.mkdir(parents=True, exist_ok=True)
    out_path = RECEIPT_OUT / f'rrc_arxiv_crossref_pipeline_{time.strftime("%Y-%m-%d")}.json'
    with open(out_path, 'w') as f:
        json.dump({
            'matches': all_matches,
            'summary': {'total_matches': len(all_matches), 'added': added},
        }, f, indent=2)
    print(f"Saved receipt: {out_path}")


if __name__ == '__main__':
    main()

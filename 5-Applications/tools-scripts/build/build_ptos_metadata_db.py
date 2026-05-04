#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
import os
import glob
import sqlite3
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'graph_os_metadata.db'
METADATA_REPORT = ROOT / 'metadata_report.json'
EXTERNAL_JSON = ROOT / 'graph_os_metadata_external.json'
BASELINES_DIR = ROOT / 'data_baselines'


def create_db(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS metadata_entries (
            id TEXT PRIMARY KEY,
            tier TEXT,
            module TEXT,
            raw_metadata TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS metadata_tags (
            entry_id TEXT,
            tag TEXT,
            PRIMARY KEY(entry_id, tag),
            FOREIGN KEY(entry_id) REFERENCES metadata_entries(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS data_baselines (
            source_file TEXT,
            row_idx INTEGER,
            col_name TEXT,
            col_value TEXT,
            PRIMARY KEY(source_file, row_idx, col_name)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            entry_id_a TEXT,
            entry_id_b TEXT,
            score REAL,
            reason TEXT,
            PRIMARY KEY(entry_id_a, entry_id_b),
            FOREIGN KEY(entry_id_a) REFERENCES metadata_entries(id),
            FOREIGN KEY(entry_id_b) REFERENCES metadata_entries(id)
        )
    ''')
    conn.commit()


def ingest_external_metadata(conn):
    if not EXTERNAL_JSON.exists():
        return []
    with open(EXTERNAL_JSON, 'r', encoding='utf-8') as f:
        try:
            entries = json.load(f)
        except Exception:
            return []

    c = conn.cursor()
    for entry in entries:
        entry_id = entry.get('id') or entry.get('@id')
        if not entry_id:
            continue
        tier = entry.get('tier', 'EXTERNAL')
        tags = entry.get('tags', [])
        metadata = purge_drift_data(entry.get('metadata', entry))
        module = metadata.get('module') or metadata.get('@type') or 'EXTERNAL'

        c.execute('''
            INSERT OR REPLACE INTO metadata_entries (id, tier, module, raw_metadata)
            VALUES (?, ?, ?, ?)
        ''', (entry_id, tier, module, json.dumps(metadata, ensure_ascii=False)))

        for tag in tags:
            c.execute('''
                INSERT OR IGNORE INTO metadata_tags (entry_id, tag)
                VALUES (?, ?)
            ''', (entry_id, tag))

    conn.commit()
    return entries


def purge_drift_data(obj):
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            lower_k = k.lower() if isinstance(k, str) else ''
            if 'drift' in lower_k:
                continue
            cleaned_value = purge_drift_data(v)
            if isinstance(cleaned_value, str) and 'drift' in cleaned_value.lower():
                continue
            cleaned[k] = cleaned_value
        return cleaned
    elif isinstance(obj, list):
        return [purge_drift_data(i) for i in obj if not (isinstance(i, str) and 'drift' in i.lower())]
    elif isinstance(obj, str):
        return obj if 'drift' not in obj.lower() else ''
    else:
        return obj


def ingest_metadata_report(conn):
    with open(METADATA_REPORT, 'r', encoding='utf-8') as f:
        report = json.load(f)

    c = conn.cursor()
    for entry_id, entry in report.items():
        tier = entry.get('tier')
        tags = entry.get('tags', [])
        metadata = purge_drift_data(entry.get('metadata', {}))
        module = metadata.get('module') or metadata.get('mod') or None

        c.execute('''
            INSERT OR REPLACE INTO metadata_entries (id, tier, module, raw_metadata)
            VALUES (?, ?, ?, ?)
        ''', (entry_id, tier, module, json.dumps(metadata, ensure_ascii=False)))

        for tag in tags:
            c.execute('''
                INSERT OR IGNORE INTO metadata_tags (entry_id, tag)
                VALUES (?, ?)
            ''', (entry_id, tag))

    conn.commit()
    return report


def ingest_data_baselines(conn):
    c = conn.cursor()
    csv_files = sorted(glob.glob(str(BASELINES_DIR / '*.csv')))
    for csv_file in csv_files:
        filename = Path(csv_file).name
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                for col_name, col_value in row.items():
                    if 'drift' in col_name.lower():
                        continue
                    if isinstance(col_value, str) and 'drift' in col_value.lower():
                        continue
                    c.execute('''
                        INSERT OR REPLACE INTO data_baselines (source_file, row_idx, col_name, col_value)
                        VALUES (?, ?, ?, ?)
                    ''', (filename, i, col_name, col_value))
    conn.commit()


def inject_remnant_ethic_nodes(conn):
    c = conn.cursor()
    # Homo sapiens remnant trophic/ethical nodes
    remnant_entries = [
        {
            'id': 'lazarus_trophic_invisibility',
            'tier': 'FOAM',
            'module': 'ECO_SOUL_INTEGRATION',
            'raw_metadata': {
                'carrying_capacity_source': 'mountain_lichen_fungi',
                'population_mode': 'niche_occupant_capped',
                'migration_ethic': 'cyclic_relocalization',
                'detection_signature': 'background_biomass',
                'humanity_model': 'non-scar-making_low-impact'
            },
            'tags': ['Ecoresonantty', 'NetZero', 'TrophicInvisibility', 'Refugia', 'Lazarus']
        },
        {
            'id': 'lazarus_low_frequency_moral_code',
            'tier': 'PLASMA',
            'module': 'GROUP_SURVIVAL_QUIETISM',
            'raw_metadata': {
                'max_tool_visibility': 'minimal',
                'metabolic_tax_monitor': 'core<0.7',
                'moral_priority': 'group_survival_over_individual',
                'threat_response': 'sacrifice_lead_or_silent_cloak',
                'drone_interaction': 'avoidance_preferred'
            },
            'tags': ['CollectivistSurvival', 'AntiInnovation', 'Quietism', 'RemnantEthics']
        },
        {
            'id': 'sentinel_humanity_collision_1450AF',
            'tier': 'CRYSTALLINE',
            'module': 'SENTINEL_ALIGNER',
            'raw_metadata': {
                'expected_schema': 'id|dna|language',
                'observed_schema': 'epas1+sequence|lowfreq_whistles|group_shadow',
                'action_map': {
                    'carbon_footprint_lt_0.01': 'ignored_as_flora',
                    'tool_usage_visible': 'remediation'
                },
                'score_multiplier': 'EthicallyAlight(-1,+1)'
            },
            'tags': ['Sentinel', 'UN_Human_Rights', 'non-human', 'whistle_comm', 'invasive_marker']
        }
    ]

    for entry in remnant_entries:
        c.execute('''
            INSERT OR REPLACE INTO metadata_entries (id, tier, module, raw_metadata)
            VALUES (?, ?, ?, ?)
        ''', (entry['id'], entry['tier'], entry['module'], json.dumps(entry['raw_metadata'], ensure_ascii=False)))
        for tag in entry['tags']:
            c.execute('''
                INSERT OR IGNORE INTO metadata_tags (entry_id, tag)
                VALUES (?, ?)
            ''', (entry['id'], tag))

    # explicit remnant connections
    remnant_connections = [
        ('lazarus_trophic_invisibility', 'lazarus_low_frequency_moral_code', 8.0, 'trophic_moral_link'),
        ('lazarus_trophic_invisibility', 'sentinel_humanity_collision_1450AF', 7.5, 'detection_alignment'),
        ('lazarus_low_frequency_moral_code', 'sentinel_humanity_collision_1450AF', 9.0, 'ethics_collision'),
    ]
    for a, b, score, reason in remnant_connections:
        c.execute('''
            INSERT OR REPLACE INTO connections (entry_id_a, entry_id_b, score, reason)
            VALUES (?, ?, ?, ?)
        ''', (a, b, score, reason))

    conn.commit()


def infer_connections(conn):
    c = conn.cursor()
    # simple shared-tag based connection score
    c.execute('''
        SELECT a.entry_id, b.entry_id, COUNT(*) AS shared_tags
        FROM metadata_tags a
        JOIN metadata_tags b ON a.tag = b.tag AND a.entry_id < b.entry_id
        GROUP BY a.entry_id, b.entry_id
    ''')

    rows = c.fetchall()
    for entry_a, entry_b, shared in rows:
        score = shared * 1.0
        c.execute('''
            INSERT OR REPLACE INTO connections (entry_id_a, entry_id_b, score, reason)
            VALUES (?, ?, ?, ?)
        ''', (entry_a, entry_b, score, f"shared_tags={shared}"))

    # module-based strong connections
    c.execute('''
        SELECT m1.id, m2.id
        FROM metadata_entries m1
        JOIN metadata_entries m2 ON m1.module = m2.module AND m1.id < m2.id
        WHERE m1.module IS NOT NULL
    ''')
    for a, b in c.fetchall():
        c.execute('''
            INSERT OR REPLACE INTO connections (entry_id_a, entry_id_b, score, reason)
            VALUES (?, ?, ?, ?)
        ''', (a, b, 10.0, 'same_module'))

    conn.commit()


def summarize(conn):
    c = conn.cursor()
    out = {}
    c.execute('SELECT COUNT(*) FROM metadata_entries')
    out['metadata_entries'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM metadata_tags')
    out['metadata_tags'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM data_baselines')
    out['baseline_cells'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM connections')
    out['inferred_connections'] = c.fetchone()[0]

    c.execute('''
        SELECT entry_id_a, entry_id_b, score, reason
        FROM connections
        ORDER BY score DESC, entry_id_a, entry_id_b
        LIMIT 10
    ''')
    out['top_connections'] = [dict(entry_id_a=a, entry_id_b=b, score=s, reason=r) for a,b,s,r in c.fetchall()]
    return out


def main():
    conn = sqlite3.connect(DB_PATH)
    create_db(conn)
    report = ingest_metadata_report(conn)
    ingest_external_metadata(conn)
    ingest_data_baselines(conn)
    inject_remnant_ethic_nodes(conn)
    infer_connections(conn)
    summary = summarize(conn)

    print('Graph OS metadata DB built at', DB_PATH)
    print(json.dumps(summary, indent=2))
    print('Tip: query using SQLite client, e.g. sqlite3 graph_os_metadata.db')

    # save a connected graph for model use / analysis
    graph = {
        'nodes': [],
        'edges': []
    }
    c = conn.cursor()
    c.execute('SELECT id, tier, module FROM metadata_entries')
    for entry_id, tier, module in c.fetchall():
        graph['nodes'].append({'id': entry_id, 'tier': tier, 'module': module})
    c.execute('SELECT entry_id_a, entry_id_b, score, reason FROM connections')
    for a, b, score, reason in c.fetchall():
        graph['edges'].append({'from': a, 'to': b, 'weight': score, 'reason': reason})

    with open(ROOT / 'graph_os_metadata_graph.json', 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print('Graph export written to graph_os_metadata_graph.json')


if __name__ == '__main__':
    main()

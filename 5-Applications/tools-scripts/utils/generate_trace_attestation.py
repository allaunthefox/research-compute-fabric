#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent))
from rfc3161_stamp import stamp as rfc3161_stamp


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_preview(path: Path, max_lines: int = 10) -> List[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines[:max_lines]


def line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def sqlite_query(conn: sqlite3.Connection, query: str) -> List[Dict[str, Any]]:
    rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def build_attestation(db_path: Path, clusters_csv: Path, timeline_json: Path, template_csv: Path, session_files: List[Path] | None = None) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        counts = {
            "observables": sqlite_query(conn, "SELECT COUNT(*) AS value FROM observables")[0]["value"],
            "events": sqlite_query(conn, "SELECT COUNT(*) AS value FROM events")[0]["value"],
            "relationships": sqlite_query(conn, "SELECT COUNT(*) AS value FROM relationships")[0]["value"],
        }
        events = sqlite_query(
            conn,
            "SELECT id AS event_id, source, observed_at, notes FROM events ORDER BY id",
        )
        observables = sqlite_query(
            conn,
            "SELECT id, observable_type, value, normalized_value FROM observables ORDER BY id",
        )
        relationships = sqlite_query(
            conn,
            """
            SELECT r.id,
                   r.event_id,
                   os.observable_type AS source_type,
                   os.value AS source_value,
                   r.relation_type,
                   ot.observable_type AS target_type,
                   ot.value AS target_value,
                   r.confidence
            FROM relationships r
            JOIN observables os ON os.id = r.source_observable_id
            JOIN observables ot ON ot.id = r.target_observable_id
            ORDER BY r.id
            """,
        )
    finally:
        conn.close()

    timeline = read_json(timeline_json)
    sessions_artifacts = {}
    for sf in (session_files or []):
        sessions_artifacts[sf.name] = {
            "path": str(sf),
            "sha256": sha256_file(sf),
            "size_bytes": sf.stat().st_size,
        }

    attestation = {
        "attested_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generator": "5-Applications/scripts/generate_trace_attestation.py",
        "workspace_root": str(PROJECT_ROOT),
        "artifacts": {
            "db": {
                "path": str(db_path),
                "sha256": sha256_file(db_path),
            },
            "clusters_csv": {
                "path": str(clusters_csv),
                "sha256": sha256_file(clusters_csv),
                "line_count": line_count(clusters_csv),
                "preview": csv_preview(clusters_csv),
            },
            "timeline_json": {
                "path": str(timeline_json),
                "sha256": sha256_file(timeline_json),
                "event_count": len(timeline),
            },
            "repo_list_template": {
                "path": str(template_csv),
                "sha256": sha256_file(template_csv),
                "line_count": line_count(template_csv),
                "preview": csv_preview(template_csv),
            },
            **({"sessions": sessions_artifacts} if sessions_artifacts else {}),
        },
        "database_snapshot": {
            "counts": counts,
            "events": events,
            "observables": observables,
            "relationships": relationships,
        },
    }
    return attestation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate machine-checkable attestation for trace outputs.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "out" / "demo_trace.sqlite3"), help="Path to trace SQLite DB.")
    parser.add_argument("--clusters", default=str(PROJECT_ROOT / "out" / "clusters.csv"), help="Path to cluster CSV.")
    parser.add_argument("--timeline", default=str(PROJECT_ROOT / "out" / "timeline.json"), help="Path to timeline JSON.")
    parser.add_argument("--template", default=str(PROJECT_ROOT / "data_baselines" / "suspicious_repo_list_template.csv"), help="Path to repo list CSV template.")
    parser.add_argument("--out", default=str(PROJECT_ROOT / "out" / "trace_attestation.json"), help="Output JSON path.")
    parser.add_argument("--session", action="append", default=[], metavar="FILE", help="Session transcript file(s) to include as hashed artifacts. Repeatable.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    clusters_path = Path(args.clusters)
    timeline_path = Path(args.timeline)
    template_path = Path(args.template)
    out_path = Path(args.out)

    missing = [
        str(path)
        for path in (db_path, clusters_path, timeline_path, template_path)
        if not path.exists()
    ]
    if missing:
        print(json.dumps({"error": "missing_input_files", "paths": missing}, indent=2))
        return 2

    attestation = build_attestation(db_path, clusters_path, timeline_path, template_path, [Path(s) for s in args.session])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(attestation, indent=2) + "\n", encoding="utf-8")
    out_sha256 = sha256_file(out_path)
    try:
        ts_info = rfc3161_stamp(out_path)
    except Exception as exc:
        ts_info = {"error": str(exc)}

    session_stamps = {}
    for sf in [Path(s) for s in args.session]:
        try:
            session_stamps[sf.name] = rfc3161_stamp(sf)
        except Exception as exc:
            session_stamps[sf.name] = {"error": str(exc)}

    print(json.dumps({"wrote": str(out_path), "sha256": out_sha256, "rfc3161": ts_info, "session_stamps": session_stamps}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

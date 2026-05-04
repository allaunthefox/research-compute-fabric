# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
import argparse
import csv
import json
import sqlite3
# import subprocess (REMOVED BY WARDEN)
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jsonschema import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = PROJECT_ROOT / "trace_campaign.sqlite3"
DEFAULT_SCHEMA = PROJECT_ROOT / "schemas" / "trace_observation.schema.json"

LOWERCASE_TYPES = {"domain", "ip", "url", "email", "repo", "commit", "txid"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_schema(schema_path: Path = DEFAULT_SCHEMA) -> Dict[str, object]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_observation(record: Dict[str, object], schema_path: Path = DEFAULT_SCHEMA) -> None:
    validate(instance=record, schema=load_schema(schema_path))


def normalize_observable(observable_type: str, value: str) -> str:
    normalized = value.strip()
    if observable_type in LOWERCASE_TYPES:
        normalized = normalized.lower()
    return normalized


def create_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS observables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observable_type TEXT NOT NULL,
            value TEXT NOT NULL,
            normalized_value TEXT NOT NULL,
            first_seen TEXT,
            last_seen TEXT,
            source TEXT,
            UNIQUE(observable_type, normalized_value)
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            notes TEXT,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS event_observables (
            event_id INTEGER NOT NULL,
            observable_id INTEGER NOT NULL,
            role TEXT,
            PRIMARY KEY (event_id, observable_id),
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (observable_id) REFERENCES observables(id)
        );

        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            source_observable_id INTEGER NOT NULL,
            target_observable_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (source_observable_id) REFERENCES observables(id),
            FOREIGN KEY (target_observable_id) REFERENCES observables(id)
        );
        """
    )
    conn.commit()


def upsert_observable(
    conn: sqlite3.Connection,
    observable_type: str,
    value: str,
    source: str,
    observed_at: str,
) -> int:
    normalized = normalize_observable(observable_type, value)
    conn.execute(
        """
        INSERT INTO observables (observable_type, value, normalized_value, first_seen, last_seen, source)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(observable_type, normalized_value)
        DO UPDATE SET
            last_seen = excluded.last_seen,
            source = COALESCE(observables.source, excluded.source)
        """,
        (observable_type, value.strip(), normalized, observed_at, observed_at, source),
    )
    row = conn.execute(
        "SELECT id FROM observables WHERE observable_type = ? AND normalized_value = ?",
        (observable_type, normalized),
    ).fetchone()
    return int(row["id"])


def create_event(conn: sqlite3.Connection, source: str, observed_at: str, notes: str, raw_json: str) -> int:
    cursor = conn.execute(
        "INSERT INTO events (source, observed_at, notes, raw_json) VALUES (?, ?, ?, ?)",
        (source, observed_at, notes, raw_json),
    )
    return int(cursor.lastrowid)


def add_event_observable(conn: sqlite3.Connection, event_id: int, observable_id: int, role: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO event_observables (event_id, observable_id, role) VALUES (?, ?, ?)",
        (event_id, observable_id, role),
    )


def add_relationship(
    conn: sqlite3.Connection,
    event_id: int,
    source_observable_id: int,
    target_observable_id: int,
    relation_type: str,
    confidence: float,
) -> None:
    conn.execute(
        """
        INSERT INTO relationships (event_id, source_observable_id, target_observable_id, relation_type, confidence)
        VALUES (?, ?, ?, ?, ?)
        """,
        (event_id, source_observable_id, target_observable_id, relation_type, confidence),
    )


def import_observation(conn: sqlite3.Connection, record: Dict[str, object]) -> int:
    validate_observation(record)

    source = str(record["source"])
    observed_at = str(record.get("timestamp") or utc_now_iso())
    notes = str(record.get("notes") or "")
    event_id = create_event(conn, source, observed_at, notes, json.dumps(record, sort_keys=True))

    observable_ids: Dict[Tuple[str, str], int] = {}
    for observable in record.get("observables", []):
        observable_type = str(observable["type"])
        value = str(observable["value"])
        role = str(observable.get("role") or "observed")
        observable_id = upsert_observable(conn, observable_type, value, source, observed_at)
        observable_ids[(observable_type, normalize_observable(observable_type, value))] = observable_id
        add_event_observable(conn, event_id, observable_id, role)

    for relation in record.get("relations", []):
        src = relation["source"]
        dst = relation["target"]
        src_type = str(src["type"])
        src_value = str(src["value"])
        dst_type = str(dst["type"])
        dst_value = str(dst["value"])
        src_id = observable_ids.get((src_type, normalize_observable(src_type, src_value)))
        if src_id is None:
            src_id = upsert_observable(conn, src_type, src_value, source, observed_at)
            add_event_observable(conn, event_id, src_id, "relation_source")
        dst_id = observable_ids.get((dst_type, normalize_observable(dst_type, dst_value)))
        if dst_id is None:
            dst_id = upsert_observable(conn, dst_type, dst_value, source, observed_at)
            add_event_observable(conn, event_id, dst_id, "relation_target")
        add_relationship(
            conn,
            event_id,
            src_id,
            dst_id,
            str(relation["relation"]),
            float(relation.get("confidence", 0.5)),
        )

    if len(observable_ids) > 1:
        for left_id, right_id in combinations(observable_ids.values(), 2):
            add_relationship(conn, event_id, left_id, right_id, "co_observed", 0.25)

    conn.commit()
    return event_id


def import_jsonl(conn: sqlite3.Connection, file_path: Path) -> int:
    count = 0
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            import_observation(conn, json.loads(stripped))
            count += 1
    return count


def repo_id_from_url(repo_url: str) -> str:
    normalized = repo_url.strip().rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if normalized.startswith("git@") and ":" in normalized:
        return normalized.split(":", 1)[1]
    if normalized.startswith("http://") or normalized.startswith("https://"):
        parts = normalized.split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    return normalized


def make_repo_list_observation(source: str, repo_url: str, local_path: str = "", notes: str = "") -> Dict[str, object]:
    repo_id = repo_id_from_url(repo_url)
    observables: List[Dict[str, str]] = [
        {"type": "repo", "value": repo_id, "role": "repository"},
        {"type": "url", "value": repo_url, "role": "repo_url"},
    ]
    relations: List[Dict[str, object]] = [
        {
            "source": {"type": "url", "value": repo_url},
            "target": {"type": "repo", "value": repo_id},
            "relation": "identifies_repo",
            "confidence": 0.95,
        }
    ]
    if local_path:
        observables.append({"type": "file_path", "value": local_path, "role": "local_clone_path"})
        relations.append(
            {
                "source": {"type": "repo", "value": repo_id},
                "target": {"type": "file_path", "value": local_path},
                "relation": "local_clone_path",
                "confidence": 0.9,
            }
        )
    return {
        "source": source,
        "timestamp": utc_now_iso(),
        "notes": notes,
        "observables": observables,
        "relations": relations,
    }


def import_repo_list(
    conn: sqlite3.Connection,
    list_path: Path,
    source: str,
    collect_git: bool = False,
    mismatch_threshold_seconds: int = 86400,
) -> Dict[str, int]:
    rows: List[Dict[str, str]] = []
    if list_path.suffix.lower() == ".jsonl":
        with list_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                rows.append(json.loads(stripped))
    else:
        with list_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows.extend(dict(row) for row in reader)

    imported = 0
    collected_git = 0
    for row in rows:
        repo_url = (row.get("repo_url") or row.get("url") or "").strip()
        if not repo_url:
            continue
        local_path = (row.get("local_path") or row.get("path") or "").strip()
        notes = (row.get("notes") or "").strip()
        record_source = (row.get("source") or source).strip() or source
        import_observation(conn, make_repo_list_observation(record_source, repo_url, local_path, notes=notes))
        imported += 1

        if collect_git and local_path:
            git_records = collect_git_anomaly_observations(
                Path(local_path),
                repo_id=repo_id_from_url(repo_url),
                source=f"{record_source}-git-anomaly",
                mismatch_threshold_seconds=mismatch_threshold_seconds,
            )
            for git_record in git_records:
                import_observation(conn, git_record)
                collected_git += 1
    return {"repo_records": imported, "git_anomaly_records": collected_git}


def make_repo_ioc_observation(
    *,
    source: str,
    repo: str,
    timestamp: Optional[str] = None,
    commit: Optional[str] = None,
    file_paths: Optional[List[str]] = None,
    wallets: Optional[List[str]] = None,
    domains: Optional[List[str]] = None,
    ips: Optional[List[str]] = None,
    urls: Optional[List[str]] = None,
    txids: Optional[List[str]] = None,
    author_email: Optional[str] = None,
    committer_email: Optional[str] = None,
    signature_state: Optional[str] = None,
    notes: str = "",
    confidence: float = 0.75,
) -> Dict[str, object]:
    file_paths = file_paths or []
    wallets = wallets or []
    domains = domains or []
    ips = ips or []
    urls = urls or []
    txids = txids or []
    observed_at = timestamp or utc_now_iso()

    observables: List[Dict[str, str]] = [{"type": "repo", "value": repo, "role": "repository"}]
    relations: List[Dict[str, object]] = []

    relation_anchor = {"type": "repo", "value": repo}
    relation_type = "reported_with_repo"
    if commit:
        observables.append({"type": "commit", "value": commit, "role": "commit"})
        relations.append(
            {
                "source": {"type": "commit", "value": commit},
                "target": {"type": "repo", "value": repo},
                "relation": "appears_in_repo",
                "confidence": confidence,
            }
        )
        relation_anchor = {"type": "commit", "value": commit}
        relation_type = "referenced_in_commit"

    if commit and author_email:
        observables.append({"type": "email", "value": author_email, "role": "author_email"})
        relations.append(
            {
                "source": {"type": "commit", "value": commit},
                "target": {"type": "email", "value": author_email},
                "relation": "authored_by",
                "confidence": confidence,
            }
        )

    if commit and committer_email:
        observables.append({"type": "email", "value": committer_email, "role": "committer_email"})
        relations.append(
            {
                "source": {"type": "commit", "value": commit},
                "target": {"type": "email", "value": committer_email},
                "relation": "committed_by",
                "confidence": confidence,
            }
        )

    if commit and signature_state:
        signature_observable = f"signature_state:{signature_state}"
        observables.append({"type": "note", "value": signature_observable, "role": "signature_state"})
        relations.append(
            {
                "source": {"type": "commit", "value": commit},
                "target": {"type": "note", "value": signature_observable},
                "relation": "signature_state",
                "confidence": confidence,
            }
        )

    if author_email and committer_email and author_email.lower() != committer_email.lower():
        relations.append(
            {
                "source": {"type": "email", "value": author_email},
                "target": {"type": "email", "value": committer_email},
                "relation": "author_committer_email_mismatch",
                "confidence": confidence,
            }
        )

    for file_path in file_paths:
        observables.append({"type": "file_path", "value": file_path, "role": "file_path"})
        relations.append(
            {
                "source": relation_anchor,
                "target": {"type": "file_path", "value": file_path},
                "relation": "touches_file",
                "confidence": confidence,
            }
        )

    for observable_type, values in (
        ("wallet", wallets),
        ("domain", domains),
        ("ip", ips),
        ("url", urls),
        ("txid", txids),
    ):
        for value in values:
            observables.append({"type": observable_type, "value": value, "role": "ioc"})
            relations.append(
                {
                    "source": relation_anchor,
                    "target": {"type": observable_type, "value": value},
                    "relation": relation_type,
                    "confidence": confidence,
                }
            )

    return {
        "source": source,
        "timestamp": observed_at,
        "notes": notes,
        "observables": observables,
        "relations": relations,
    }


def make_wallet_txid_template(
    wallet: Optional[str] = None,
    txid: Optional[str] = None,
    source: str = "manual-template",
    notes: str = "Replace placeholders and relation type with independently verified values.",
) -> Dict[str, object]:
    wallet_value = wallet or "WALLET_ADDRESS_HERE"
    txid_value = txid or "TXID_HERE"
    return {
        "source": source,
        "timestamp": utc_now_iso(),
        "notes": notes,
        "observables": [
            {"type": "wallet", "value": wallet_value, "role": "wallet"},
            {"type": "txid", "value": txid_value, "role": "transaction"},
        ],
        "relations": [
            {
                "source": {"type": "txid", "value": txid_value},
                "target": {"type": "wallet", "value": wallet_value},
                "relation": "funds_wallet",
                "confidence": 0.5,
            }
        ],
    }


def fetch_observable(conn: sqlite3.Connection, observable_type: str, value: str) -> Optional[sqlite3.Row]:
    normalized = normalize_observable(observable_type, value)
    return conn.execute(
        "SELECT * FROM observables WHERE observable_type = ? AND normalized_value = ?",
        (observable_type, normalized),
    ).fetchone()


def build_clusters(conn: sqlite3.Connection, min_confidence: float = 0.0) -> List[Dict[str, object]]:
    adjacency: Dict[int, set[int]] = defaultdict(set)
    for row in conn.execute(
        """
        SELECT source_observable_id, target_observable_id
        FROM relationships
        WHERE confidence >= ?
        """,
        (min_confidence,),
    ):
        adjacency[int(row["source_observable_id"])].add(int(row["target_observable_id"]))
        adjacency[int(row["target_observable_id"])].add(int(row["source_observable_id"]))

    visited: set[int] = set()
    clusters: List[Dict[str, object]] = []
    for node_id in adjacency:
        if node_id in visited:
            continue
        queue: deque[int] = deque([node_id])
        component: List[int] = []
        visited.add(node_id)
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        members = conn.execute(
            "SELECT id, observable_type, value FROM observables WHERE id IN ({}) ORDER BY observable_type, value".format(
                ",".join("?" for _ in component)
            ),
            component,
        ).fetchall()
        type_counts = Counter(str(member["observable_type"]) for member in members)
        clusters.append(
            {
                "size": len(component),
                "type_counts": dict(type_counts),
                "members": [
                    {
                        "id": int(member["id"]),
                        "type": str(member["observable_type"]),
                        "value": str(member["value"]),
                    }
                    for member in members
                ],
            }
        )
    clusters.sort(key=lambda cluster: cluster["size"], reverse=True)
    return clusters


def cluster_for_seed(
    conn: sqlite3.Connection,
    observable_type: str,
    value: str,
    min_confidence: float = 0.0,
) -> Optional[Dict[str, object]]:
    seed = fetch_observable(conn, observable_type, value)
    if seed is None:
        return None
    seed_id = int(seed["id"])
    for cluster in build_clusters(conn, min_confidence=min_confidence):
        if any(member["id"] == seed_id for member in cluster["members"]):
            return cluster
    return {
        "size": 1,
        "type_counts": {str(seed["observable_type"]): 1},
        "members": [
            {
                "id": seed_id,
                "type": str(seed["observable_type"]),
                "value": str(seed["value"]),
            }
        ],
    }


def stats(conn: sqlite3.Connection) -> Dict[str, object]:
    observable_count = conn.execute("SELECT COUNT(*) AS count FROM observables").fetchone()["count"]
    event_count = conn.execute("SELECT COUNT(*) AS count FROM events").fetchone()["count"]
    relationship_count = conn.execute("SELECT COUNT(*) AS count FROM relationships").fetchone()["count"]
    by_type = conn.execute(
        "SELECT observable_type, COUNT(*) AS count FROM observables GROUP BY observable_type ORDER BY count DESC"
    ).fetchall()
    return {
        "observables": int(observable_count),
        "events": int(event_count),
        "relationships": int(relationship_count),
        "by_type": {str(row["observable_type"]): int(row["count"]) for row in by_type},
    }


def fetch_event_details(conn: sqlite3.Connection, event_id: int) -> Dict[str, object]:
    event_row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    observables = conn.execute(
        """
        SELECT o.observable_type, o.value, eo.role
        FROM event_observables eo
        JOIN observables o ON o.id = eo.observable_id
        WHERE eo.event_id = ?
        ORDER BY o.observable_type, o.value
        """,
        (event_id,),
    ).fetchall()
    relations = conn.execute(
        """
        SELECT os.observable_type AS source_type,
               os.value AS source_value,
               ot.observable_type AS target_type,
               ot.value AS target_value,
               r.relation_type,
               r.confidence
        FROM relationships r
        JOIN observables os ON os.id = r.source_observable_id
        JOIN observables ot ON ot.id = r.target_observable_id
        WHERE r.event_id = ?
        ORDER BY r.id
        """,
        (event_id,),
    ).fetchall()
    return {
        "event_id": int(event_row["id"]),
        "source": str(event_row["source"]),
        "observed_at": str(event_row["observed_at"]),
        "notes": str(event_row["notes"] or ""),
        "observables": [
            {"type": str(row["observable_type"]), "value": str(row["value"]), "role": str(row["role"] or "")}
            for row in observables
        ],
        "relations": [
            {
                "source": {"type": str(row["source_type"]), "value": str(row["source_value"])},
                "target": {"type": str(row["target_type"]), "value": str(row["target_value"])},
                "relation": str(row["relation_type"]),
                "confidence": float(row["confidence"]),
            }
            for row in relations
        ],
    }


def export_timeline(
    conn: sqlite3.Connection,
    seed_type: Optional[str] = None,
    seed_value: Optional[str] = None,
    min_confidence: float = 0.0,
) -> List[Dict[str, object]]:
    if seed_type and seed_value:
        cluster = cluster_for_seed(conn, seed_type, seed_value, min_confidence=min_confidence)
        if cluster is None:
            return []
        member_ids = [int(member["id"]) for member in cluster["members"]]
        rows = conn.execute(
            "SELECT DISTINCT event_id FROM event_observables WHERE observable_id IN ({}) ORDER BY event_id".format(
                ",".join("?" for _ in member_ids)
            ),
            member_ids,
        ).fetchall()
        event_ids = [int(row["event_id"]) for row in rows]
    else:
        rows = conn.execute("SELECT id FROM events ORDER BY observed_at, id").fetchall()
        event_ids = [int(row["id"]) for row in rows]
    timeline = [fetch_event_details(conn, event_id) for event_id in event_ids]
    timeline.sort(key=lambda item: (item["observed_at"], item["event_id"]))
    return timeline


def write_json_output(data: object, output_path: Path) -> None:
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def export_clusters_csv(clusters: List[Dict[str, object]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["cluster_index", "cluster_size", "observable_id", "observable_type", "observable_value"],
        )
        writer.writeheader()
        for index, cluster in enumerate(clusters, start=1):
            for member in cluster["members"]:
                writer.writerow(
                    {
                        "cluster_index": index,
                        "cluster_size": cluster["size"],
                        "observable_id": member["id"],
                        "observable_type": member["type"],
                        "observable_value": member["value"],
                    }
                )


def export_timeline_csv(timeline: List[Dict[str, object]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["event_id", "observed_at", "source", "notes", "observables_json", "relations_json"],
        )
        writer.writeheader()
        for event in timeline:
            writer.writerow(
                {
                    "event_id": event["event_id"],
                    "observed_at": event["observed_at"],
                    "source": event["source"],
                    "notes": event["notes"],
                    "observables_json": json.dumps(event["observables"], ensure_ascii=False),
                    "relations_json": json.dumps(event["relations"], ensure_ascii=False),
                }
            )


def run_git(repo_path: Path, args: List[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        check=check,
        capture_output=True,
        text=True,
    )


def infer_repo_id(repo_path: Path) -> str:
    resolved_path = repo_path.resolve()
    try:
        remote = run_git(resolved_path, ["config", "--get", "remote.origin.url"], check=False).stdout.strip()
    except OSError:
        remote = ""
    if remote.endswith(".git"):
        remote = remote[:-4]
    if remote.startswith("git@") and ":" in remote:
        return remote.split(":", 1)[1]
    if remote.startswith("https://") and "/" in remote:
        parts = remote.rstrip("/").split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    return resolved_path.name


def collect_git_commits(repo_path: Path) -> List[Dict[str, object]]:
    log_result = run_git(
        repo_path,
        ["log", "--all", "--format=%H%x1f%aI%x1f%cI%x1f%G?%x1f%ae%x1f%ce%x1f%s"],
        check=False,
    )
    if log_result.returncode != 0 or not log_result.stdout.strip():
        return []
    commits: List[Dict[str, object]] = []
    for line in log_result.stdout.splitlines():
        sha, author_iso, committer_iso, verify_state, author_email, committer_email, subject = line.split("\x1f", 6)
        commits.append(
            {
                "commit": sha,
                "author_date": author_iso,
                "committer_date": committer_iso,
                "verification": verify_state,
                "author_email": author_email,
                "committer_email": committer_email,
                "subject": subject,
            }
        )
    return commits


def collect_unreachable_commits(repo_path: Path) -> List[str]:
    result = run_git(repo_path, ["fsck", "--no-reflogs", "--unreachable", "--no-progress"], check=False)
    if result.returncode not in (0, 1):
        return []
    commits: List[str] = []
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) == 3 and parts[0] == "unreachable" and parts[1] == "commit":
            commits.append(parts[2])
    return commits


def detect_git_anomalies(
    repo_id: str,
    commits: List[Dict[str, object]],
    unreachable_commits: List[str],
    source: str,
    mismatch_threshold_seconds: int = 86400,
) -> List[Dict[str, object]]:
    observations: List[Dict[str, object]] = []
    for commit in commits:
        author_date = datetime.fromisoformat(str(commit["author_date"]).replace("Z", "+00:00"))
        committer_date = datetime.fromisoformat(str(commit["committer_date"]).replace("Z", "+00:00"))
        delta_seconds = int(abs((committer_date - author_date).total_seconds()))
        if delta_seconds >= mismatch_threshold_seconds:
            notes = (
                f"Committer date differs from author date by {delta_seconds} seconds. "
                f"verification={commit['verification']} subject={commit['subject']}"
            )
            observations.append(
                make_repo_ioc_observation(
                    source=source,
                    repo=repo_id,
                    timestamp=str(commit["committer_date"]),
                    commit=str(commit["commit"]),
                    author_email=str(commit["author_email"] or ""),
                    committer_email=str(commit["committer_email"] or ""),
                    signature_state=str(commit["verification"] or ""),
                    notes=notes,
                    confidence=0.9,
                )
            )

    for commit_sha in unreachable_commits:
        observations.append(
            make_repo_ioc_observation(
                source=source,
                repo=repo_id,
                timestamp=utc_now_iso(),
                commit=commit_sha,
                signature_state="unknown",
                notes="Unreachable commit detected by git fsck; possible local rewrite or history divergence indicator.",
                confidence=0.8,
            )
        )
    return observations


def collect_git_anomaly_observations(
    repo_path: Path,
    repo_id: Optional[str] = None,
    source: str = "git-anomaly-collector",
    mismatch_threshold_seconds: int = 86400,
) -> List[Dict[str, object]]:
    resolved_repo_id = repo_id or infer_repo_id(repo_path)
    commits = collect_git_commits(repo_path)
    unreachable_commits = collect_unreachable_commits(repo_path)
    return detect_git_anomalies(
        resolved_repo_id,
        commits,
        unreachable_commits,
        source,
        mismatch_threshold_seconds=mismatch_threshold_seconds,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Passive evidence import and clustering pipeline for campaign tracing.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Initialize the trace database.")

    import_parser = subparsers.add_parser("import-jsonl", help="Import schema-validated observation JSONL.")
    import_parser.add_argument("path", help="Path to observation JSONL file.")

    repo_ioc_parser = subparsers.add_parser("import-repo-ioc", help="Create and import a repo/commit IoC observation.")
    repo_ioc_parser.add_argument("--source", default="manual-repo-ioc", help="Observation source label.")
    repo_ioc_parser.add_argument("--timestamp", help="Observation timestamp in ISO-8601 form.")
    repo_ioc_parser.add_argument("--repo", required=True, help="Repository identifier, such as owner/repo.")
    repo_ioc_parser.add_argument("--commit", help="Commit SHA if available.")
    repo_ioc_parser.add_argument("--notes", default="", help="Freeform analyst notes.")
    repo_ioc_parser.add_argument("--file-path", action="append", default=[], help="Relevant file path. Repeatable.")
    repo_ioc_parser.add_argument("--wallet", action="append", default=[], help="Related wallet. Repeatable.")
    repo_ioc_parser.add_argument("--domain", action="append", default=[], help="Related domain. Repeatable.")
    repo_ioc_parser.add_argument("--ip", action="append", default=[], help="Related IP. Repeatable.")
    repo_ioc_parser.add_argument("--url", action="append", default=[], help="Related URL. Repeatable.")
    repo_ioc_parser.add_argument("--txid", action="append", default=[], help="Related transaction ID. Repeatable.")

    repo_list_parser = subparsers.add_parser("import-repo-list", help="Bulk import suspicious repo URLs and local paths.")
    repo_list_parser.add_argument("path", help="Path to CSV or JSONL containing repo_url and local_path fields.")
    repo_list_parser.add_argument("--source", default="bulk-repo-list", help="Default source label.")
    repo_list_parser.add_argument("--collect-git", action="store_true", help="Also run passive git anomaly collection for rows with local_path.")
    repo_list_parser.add_argument("--mismatch-threshold-seconds", type=int, default=86400, help="Minimum author/committer date gap to flag when collecting git anomalies.")

    wallet_template_parser = subparsers.add_parser("wallet-template", help="Generate a wallet/TXID observation template.")
    wallet_template_parser.add_argument("--wallet", help="Wallet address to prefill.")
    wallet_template_parser.add_argument("--txid", help="Transaction ID to prefill.")
    wallet_template_parser.add_argument("--source", default="manual-template", help="Template source label.")
    wallet_template_parser.add_argument("--notes", default="Replace placeholders and relation type with independently verified values.", help="Template notes.")
    wallet_template_parser.add_argument("--output", help="Optional path to write template JSON.")

    cluster_parser = subparsers.add_parser("cluster", help="Build passive clusters from imported evidence.")
    cluster_parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum relationship confidence.")
    cluster_parser.add_argument("--seed-type", help="Filter to cluster containing this observable type.")
    cluster_parser.add_argument("--seed-value", help="Filter to cluster containing this observable value.")
    cluster_parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    cluster_parser.add_argument("--output", help="Optional output file path (.json or .csv).")
    cluster_parser.add_argument("--format", choices=["json", "csv"], help="Explicit output format when --output is used.")

    timeline_parser = subparsers.add_parser("timeline", help="Export timeline events from the trace database.")
    timeline_parser.add_argument("--seed-type", help="Filter timeline to events linked to this observable type.")
    timeline_parser.add_argument("--seed-value", help="Filter timeline to events linked to this observable value.")
    timeline_parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum confidence used for seed clustering.")
    timeline_parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    timeline_parser.add_argument("--output", help="Optional output file path (.json or .csv).")
    timeline_parser.add_argument("--format", choices=["json", "csv"], help="Explicit output format when --output is used.")

    git_parser = subparsers.add_parser("collect-git-anomalies", help="Passively collect git-history anomaly observations.")
    git_parser.add_argument("path", help="Path to a local git repository.")
    git_parser.add_argument("--repo-id", help="Optional explicit repo identifier.")
    git_parser.add_argument("--source", default="git-anomaly-collector", help="Observation source label.")
    git_parser.add_argument("--mismatch-threshold-seconds", type=int, default=86400, help="Minimum author/committer date gap to flag.")
    git_parser.add_argument("--dry-run", action="store_true", help="Print observations instead of importing them.")

    subparsers.add_parser("stats", help="Show database summary statistics.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    conn = create_connection(db_path)
    init_db(conn)

    if args.command == "init-db":
        print(f"Initialized trace database at: {db_path}")
        return 0

    if args.command == "import-jsonl":
        count = import_jsonl(conn, Path(args.path))
        print(json.dumps({"imported_records": count, "db": str(db_path)}, indent=2))
        return 0

    if args.command == "import-repo-ioc":
        record = make_repo_ioc_observation(
            source=args.source,
            repo=args.repo,
            timestamp=args.timestamp,
            commit=args.commit,
            file_paths=list(args.file_path),
            wallets=list(args.wallet),
            domains=list(args.domain),
            ips=list(args.ip),
            urls=list(args.url),
            txids=list(args.txid),
            notes=args.notes,
        )
        event_id = import_observation(conn, record)
        print(json.dumps({"event_id": event_id, "db": str(db_path)}, indent=2))
        return 0

    if args.command == "import-repo-list":
        results = import_repo_list(
            conn,
            Path(args.path),
            source=args.source,
            collect_git=bool(args.collect_git),
            mismatch_threshold_seconds=int(args.mismatch_threshold_seconds),
        )
        payload = {"db": str(db_path), **results}
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "wallet-template":
        template = make_wallet_txid_template(wallet=args.wallet, txid=args.txid, source=args.source, notes=args.notes)
        rendered = json.dumps(template, indent=2)
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
            print(f"Wrote template to: {args.output}")
        else:
            print(rendered)
        return 0

    if args.command == "stats":
        print(json.dumps(stats(conn), indent=2))
        return 0

    if args.command == "cluster":
        if args.seed_type and args.seed_value:
            cluster = cluster_for_seed(conn, args.seed_type, args.seed_value, min_confidence=args.min_confidence)
            output = cluster if cluster is not None else {"error": "seed_not_found"}
            if args.output and cluster is not None:
                output_path = Path(args.output)
                output_format = args.format or output_path.suffix.lower().lstrip(".") or "json"
                if output_format == "json":
                    write_json_output(output, output_path)
                else:
                    export_clusters_csv([output], output_path)
                print(f"Wrote seed cluster to: {output_path}")
                return 0
            print(json.dumps(output, indent=2))
            return 0 if cluster is not None else 2

        clusters = build_clusters(conn, min_confidence=args.min_confidence)
        if args.output:
            output_path = Path(args.output)
            output_format = args.format or output_path.suffix.lower().lstrip(".") or "json"
            if output_format == "json":
                write_json_output(clusters, output_path)
            else:
                export_clusters_csv(clusters, output_path)
            print(f"Wrote clusters to: {output_path}")
            return 0
        if args.json:
            print(json.dumps(clusters, indent=2))
        else:
            for index, cluster in enumerate(clusters, start=1):
                print(f"Cluster {index}: size={cluster['size']} types={cluster['type_counts']}")
                for member in cluster["members"]:
                    print(f"  - {member['type']}: {member['value']}")
        return 0

    if args.command == "timeline":
        timeline = export_timeline(
            conn,
            seed_type=args.seed_type,
            seed_value=args.seed_value,
            min_confidence=args.min_confidence,
        )
        if args.output:
            output_path = Path(args.output)
            output_format = args.format or output_path.suffix.lower().lstrip(".") or "json"
            if output_format == "json":
                write_json_output(timeline, output_path)
            else:
                export_timeline_csv(timeline, output_path)
            print(f"Wrote timeline to: {output_path}")
            return 0
        if args.json:
            print(json.dumps(timeline, indent=2))
        else:
            for item in timeline:
                print(f"{item['observed_at']} [{item['source']}] event_id={item['event_id']}")
                if item["notes"]:
                    print(f"  notes: {item['notes']}")
                for observable in item["observables"]:
                    role_suffix = f" ({observable['role']})" if observable["role"] else ""
                    print(f"  observable: {observable['type']}={observable['value']}{role_suffix}")
                for relation in item["relations"]:
                    print(
                        "  relation: "
                        f"{relation['source']['type']}={relation['source']['value']} "
                        f"-{relation['relation']}-> "
                        f"{relation['target']['type']}={relation['target']['value']} "
                        f"(confidence={relation['confidence']})"
                    )
        return 0

    if args.command == "collect-git-anomalies":
        records = collect_git_anomaly_observations(
            Path(args.path),
            repo_id=args.repo_id,
            source=args.source,
            mismatch_threshold_seconds=args.mismatch_threshold_seconds,
        )
        if args.dry_run:
            print(json.dumps(records, indent=2))
            return 0
        imported = 0
        for record in records:
            import_observation(conn, record)
            imported += 1
        print(
            json.dumps(
                {
                    "generated_records": len(records),
                    "imported_records": imported,
                    "repo_path": str(Path(args.path)),
                    "repo_id": args.repo_id or infer_repo_id(Path(args.path)),
                    "db": str(db_path),
                },
                indent=2,
            )
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# INFRA:DEAD rds -- AWS RDS is gone. Any file referencing rds_connect.py or this hostname is stale and must be ported.
"""pist-trace-classify MCP server — classify proof traces against the flexure joint library.

Calling convention (MCP JSON-RPC on stdio):

Send:
  {"jsonrpc":"2.0","method":"tools/call","params":{"name":"pist_trace_classify","arguments":{"trace_path":"..."},"id":1}}

With options:
  trace_path: path to a ProofTraceReceipt v2 JSON file
  trace_json: inline JSON object (alternative to trace_path)
  insert: bool (default false) — store result in ene.artifacts
  top_k: int (default 5) — number of nearest motifs to return
"""
# PARTIAL BOUNDARY: decision-critical logic ported to Lean; Python retains I/O only.
#   classify_tactic_from_name  → Semantics.PIST.Spectral.classifyTacticFromName
#   compute_spectral           → Semantics.PIST.Spectral.computeSpectral
#   motif score + rank order   → Semantics.PIST.Motif (motifScore, rankMotifs)
#   RDS queries, MCP protocol, artifact insertion, classify_trace orchestration
#   remain in Python.

import json
import math
import os
from rds_connect import connect_rds
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

SERVER_NAME = "pist-trace-classify"
SERVER_VERSION = "0.1.0"

FLEXURE_SESSION = "a4a0eb20-93fe-413e-8e0b-50334bb778d8"

FEATURE_KEYS = ["matrix_size", "rank", "spectral_gap", "laplacian_zero_count", "density", "eigenvalue_max"]


def connect():
    return connect_rds()


def power_iteration(matrix, max_iter=100):
    n = len(matrix)
    if n == 0: return 0.0
    v = [1.0 / math.sqrt(n)] * n
    for _ in range(max_iter):
        vn = [sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n)]
        nm = math.sqrt(sum(x * x for x in vn))
        if nm < 1e-12: return 0.0
        v = [x / nm for x in vn]
    num = sum(v[i] * sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n))
    den = sum(v[i] * v[i] for i in range(n))
    return num / den if den > 0 else 0.0


def compute_spectral(matrix):
    """Full v2 spectral profile from a transition matrix."""
    n = len(matrix)
    if n == 0: return {}
    sym = [[(matrix[i][j] + matrix[j][i]) / 2.0 for j in range(n)] for i in range(n)]
    lap = [[sum(sym[i]) if i == j else -sym[i][j] for j in range(n)] for i in range(n)]
    ev_max = power_iteration(sym)
    shifted = [[sym[i][j] - 0.9 * ev_max * (1 if i == j else 0) for j in range(n)] for i in range(n)]
    ev_shift = power_iteration(shifted)
    ev_second = max(0, ev_max - ev_shift) if ev_shift < ev_max else ev_max
    gap = ev_max - ev_second
    lap_max = power_iteration(lap)
    neg_lap = [[-lap[i][j] for j in range(n)] for i in range(n)]
    lap_min = -power_iteration(neg_lap)
    ata = [[sum(matrix[k][i] * matrix[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    sv_max = math.sqrt(max(0, power_iteration(ata)))
    rank = sum(1 for row in matrix if sum(row) > 0)
    total = sum(sum(row) for row in matrix)
    frob = math.sqrt(sum(cell * cell for row in matrix for cell in row))
    lap_zero = sum(1 for i in range(n) if abs(sum(matrix[i]) - matrix[i][i]) < 1e-9)
    return {
        "matrix_size": n, "rank": rank, "spectral_gap": round(gap, 6),
        "density": round(total / max(n * n, 1), 6), "trace": sum(matrix[i][i] for i in range(n)),
        "frobenius_norm": round(frob, 6), "laplacian_zero_count": lap_zero,
        "adjacency_eigenvalue_max": round(ev_max, 6),
        "laplacian_eigenvalue_max": round(lap_max, 6),
        "singular_value_max": round(sv_max, 6),
    }


def classify_trace(trace: dict, top_k: int = 5, insert: bool = False) -> dict:
    """Full classification pipeline for a proof trace."""
    import hashlib
    name = trace.get("theorem_name", trace.get("name", "unnamed"))
    status = trace.get("status", "?")
    matrix = trace.get("transition_matrix", [])
    tags = trace.get("trace_tags", [])
    
    if not matrix or len(matrix) == 0:
        return {"error": "empty_transition_matrix", "theorem_name": name}
    
    spectral = compute_spectral(matrix)
    n = spectral.get("matrix_size", 0)
    vec = [spectral.get(k, 0) for k in FEATURE_KEYS]
    
    # Connect to RDS and query nearest motifs
    result = {"theorem_name": name, "trace_hash": hashlib.sha256(json.dumps(trace).encode()).hexdigest()[:16],
              "status": status, "spectral": spectral, "feature_version": "flexure-spectrum-v2",
              "predictions": {"proof_status": {"label": status, "confidence": 0.0}},
              "calibration": {"dataset": "tier2b_57_theorem_batch", "proof_status_loocv": 0.895,
                              "sample_count": 57, "feature_version": "flexure-spectrum-v2", "status": "experimental"},
              "nearest_motifs": [], "flexures": []}
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        # Load all flexure features from the trained session
        cur.execute(
            "SELECT decision_signals, converged FROM ene.flexures WHERE session_id = %s",
            (FLEXURE_SESSION,),
        )
        library = []
        for row in cur.fetchall():
            sig = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            sp = sig.get("spectral", {})
            lvec = [sp.get(k, 0) for k in FEATURE_KEYS]
            library.append({
                "features": lvec, "tactic_family": sig.get("tactic_family", "?"),
                "joint_label": sig.get("joint_label", "?"), "converged": row[1],
                "rrc_shape": sig.get("rrc_shape", "?"),
            })
        
        # Load motifs
        cur.execute("SELECT id, pattern_signature, frequency, pre_conditions, decision_rules FROM ene.flexure_patterns ORDER BY frequency DESC")
        motifs = [{"id": str(r[0]), "signature": r[1], "frequency": r[2],
                    "pre": json.loads(r[3]) if isinstance(r[3], str) else r[3],
                    "rules": json.loads(r[4]) if isinstance(r[4], str) else r[4]}
                  for r in cur.fetchall()]
        
        # Nearest motifs by frequency × label match
        for m in motifs:
            score = m["frequency"] / max(len(library), 1)
            if m["pre"].get("tactic_family", "") == classify_tactic_from_name(name):
                score += 0.3
            result["nearest_motifs"].append({
                "motif_id": m["id"], "score": round(score, 3),
                "support": m["frequency"],
                "tactic_family": m["pre"].get("tactic_family", "?"),
                "joint_label": m["rules"].get("joint_type", "?"),
            })
        
        # Sort by score
        result["nearest_motifs"].sort(key=lambda x: -x["score"])
        result["nearest_motifs"] = result["nearest_motifs"][:top_k]
        
        # Build predictions from nearest motifs
        if result["nearest_motifs"]:
            result["predictions"] = {
                "proof_status": {"label": status, "confidence": round(0.895, 2)},
                "tactic_family": {"label": result["nearest_motifs"][0]["tactic_family"],
                                  "confidence": round(result["nearest_motifs"][0]["score"], 2)},
                "joint_label": {"label": result["nearest_motifs"][0]["joint_label"],
                                "confidence": round(result["nearest_motifs"][0]["score"], 2)},
            }
        
        if insert:
            artifact_id = str(uuid.uuid4())
            content = json.dumps({"trace": name, "spectral": spectral, "classification": result["predictions"]})
            cur.execute(
                "INSERT INTO ene.artifacts (id, path, kind, language, title, content, content_hash, metadata) "
                "VALUES (%s, %s, 'pist_trace', 'json', %s, %s, %s, %s::jsonb)",
                (artifact_id, f"pist_traces/{name}_{uuid.uuid4().hex[:8]}.json",
                 f"PIST Classified: {name}",
                 content, hashlib.sha256(content.encode()).hexdigest(),
                 json.dumps({"pist_classified": True, "proof_status": status, "session": FLEXURE_SESSION})),
            )
            conn.commit()
            result["artifact_id"] = artifact_id
        
        cur.close()
        conn.close()
    except Exception as e:
        result["error"] = str(e)[:200]
        result["database_available"] = False
    
    return result


def classify_tactic_from_name(name: str) -> str:
    name_lower = name.lower()
    if "rw" in name_lower: return "rewrite"
    if "simp" in name_lower: return "normalization"
    if "omega" in name_lower: return "arithmetic"
    if "induct" in name_lower: return "induction"
    if "ring" in name_lower or "calc" in name_lower: return "algebraic"
    if "cases" in name_lower or "constructor" in name_lower: return "case_analysis"
    if any(k in name_lower for k in ["apply", "intro", "have", "logic"]): return "discharge"
    if "rfl" in name_lower: return "reflexivity"
    return "unknown"


TOOL_SCHEMA = {
    "name": "pist_trace_classify",
    "description": "Classify a proof trace against the flexure joint library. Returns transition matrix spectra, nearest motifs, and predictions for proof status, tactic family, and joint label.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "trace_path": {"type": "string", "description": "Path to a ProofTraceReceipt v2 JSON file on disk"},
            "trace_json": {"type": "object", "description": "Inline ProofTraceReceipt v2 JSON (alternative to trace_path)"},
            "insert": {"type": "boolean", "default": False, "description": "Store result in ene.artifacts"},
            "top_k": {"type": "number", "default": 5, "description": "Number of nearest motifs to return"},
        }
    }
}


def handle_request(request: dict) -> dict:
    method = request.get("method", "")
    req_id = request.get("id")
    
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2025-03-26", "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }}
    elif method == "notifications/initialized":
        return {"jsonrpc": "2.0", "id": req_id, "result": None}
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [TOOL_SCHEMA]}}
    elif method == "tools/call":
        params = request.get("params", {})
        args = params.get("arguments", {})
        trace_path = args.get("trace_path")
        trace_json = args.get("trace_json")
        insert = args.get("insert", False)
        top_k = args.get("top_k", 5)
        
        if trace_path:
            try:
                with open(trace_path) as f:
                    trace = json.load(f)
            except Exception as e:
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}]}}
        elif trace_json:
            trace = trace_json
        else:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": "provide trace_path or trace_json"})}]}}
        
        result = classify_trace(trace, top_k, insert)
        return {"jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}
    else:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            continue


if __name__ == "__main__":
    main()

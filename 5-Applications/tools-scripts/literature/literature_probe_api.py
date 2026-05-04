#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Local HTTP wrapper for the literature probe.

This exposes the question-focused probe as a small FastAPI service so local
LLM stacks can call it over HTTP instead of shelling out.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scripts.literature_probe import DEFAULT_OUT_DIR, run_probe, write_outputs


APP_TITLE = "Literature Probe API"
DEFAULT_BIND = os.getenv("LITERATURE_PROBE_API_BIND", "::1")
DEFAULT_PORT = int(os.getenv("LITERATURE_PROBE_API_PORT", "8011"))
DEFAULT_ALLOWED_ORIGINS = os.getenv("LITERATURE_PROBE_API_ALLOW_ORIGINS", "*")

app = FastAPI(title=APP_TITLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in DEFAULT_ALLOWED_ORIGINS.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProbeRequest(BaseModel):
    question: str = Field(..., min_length=1)
    extra_queries: List[str] = Field(default_factory=list)
    per_source: int = Field(default=8, ge=1, le=50)
    write_outputs: bool = True
    out_dir: Optional[str] = None
    include_full_result: bool = True


def build_response(result: Dict[str, Any], json_path: Optional[Path], markdown_path: Optional[Path], include_full_result: bool) -> Dict[str, Any]:
    papers = result.get("papers", [])
    return {
        "status": "ok",
        "question": result["question"],
        "wall_type": result["wall_type"],
        "semantic_scholar_status": result.get("source_stats", {}).get("semantic_scholar", {}).get("status", "unknown"),
        "source_stats": result.get("source_stats", {}),
        "source_contributions_top12": result.get("source_contributions_top12", {}),
        "recurring_terms": result.get("recurring_terms", []),
        "nearby_fields": result.get("nearby_fields", []),
        "top_papers": papers[:12],
        "json_path": str(json_path) if json_path else None,
        "markdown_path": str(markdown_path) if markdown_path else None,
        "result": result if include_full_result else None,
    }


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": APP_TITLE,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_url": "/health",
        "probe_url": "/probe",
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": APP_TITLE,
        "default_out_dir": str(DEFAULT_OUT_DIR),
        "default_bind": DEFAULT_BIND,
        "default_port": DEFAULT_PORT,
        "allow_origins": [origin.strip() for origin in DEFAULT_ALLOWED_ORIGINS.split(",") if origin.strip()],
    }


@app.post("/probe")
def probe(request: ProbeRequest) -> Dict[str, Any]:
    result = run_probe(request.question, request.extra_queries, request.per_source)

    json_path: Optional[Path] = None
    markdown_path: Optional[Path] = None
    if request.write_outputs:
        out_dir = Path(request.out_dir) if request.out_dir else Path(DEFAULT_OUT_DIR)
        json_path, markdown_path = write_outputs(result, out_dir)

    return build_response(result, json_path, markdown_path, request.include_full_result)

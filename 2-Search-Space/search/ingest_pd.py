#!/usr/bin/env python3
"""
Public Domain Ingestion Orchestrator
Target: /mnt/gdrive/Research_Archive/
Orchestrates high-volume ingestion from Openverse, IA, and Europeana.
"""

import os
import requests
import json
from pathlib import Path

# --- Configuration ---
GDRIVE_PATH = Path("/home/allaun/Documents/Research Stack/data/ingestion")
GDRIVE_PATH.mkdir(parents=True, exist_ok=True)

# Placeholder for API credentials (user can fill later)
CREDS = {
    "openverse": os.getenv("OPENVERSE_API_KEY", ""),
    "ia": os.getenv("INTERNET_ARCHIVE_S3_KEY", ""),
    "europeana": os.getenv("EUROPEANA_API_KEY", "")
}

def pull_openverse(query, limit=100):
  """Pull metadata and links for open domain works."""
  print(f"[INGEST] Searching Openverse for: {query}")
  url = "https://api.openverse.engineering/v1/images/"
  params = {"q": query, "license_type": "publicdomain", "page_size": limit}
  headers = {"Authorization": f"Token {CREDS['openverse']}"} if CREDS['openverse'] else {}
  
  res = requests.get(url, params=params, headers=headers)
  if res.status_code == 200:
    data = res.json()
    out_file = GDRIVE_PATH / f"openverse_{query.replace(' ', '_')}.json"
    with open(out_file, "w") as f:
      json.dump(data, f, indent=2)
    print(f"[SUCCESS] Saved {len(data['results'])} records to {out_file}")
  else:
    print(f"[ERROR] Openverse failed: {res.status_code}")

def pull_ia_metadata(query, limit=50):
  """Pull metadata from Internet Archive based on query."""
  print(f"[INGEST] Searching Internet Archive for: {query}")
  url = "https://archive.org/advancedsearch.php"
  params = {
    "q": f"{query} AND (licenseurl:*publicdomain* OR mediaprotocol:publicdomain)",
    "output": "json",
    "rows": limit,
    "page": 1
  }
  res = requests.get(url, params=params)
  if res.status_code == 200:
    data = res.json()
    out_file = GDRIVE_PATH / f"ia_{query.replace(' ', '_')}.json"
    with open(out_file, "w") as f:
      json.dump(data, f, indent=2)
    print(f"[SUCCESS] Saved IA records to {out_file}")
  else:
    print(f"[ERROR] IA failed: {res.status_code}")

if __name__ == "__main__":
  # Initial seeds for the Informatic Manifold
  seeds = [
    "theoretical physics",
    "neuromorphic computing",
    "pure mathematics",
    "maritime navigation",
    "sovereignty"
  ]
  
  for s in seeds:
    pull_openverse(s)
    pull_ia_metadata(s)

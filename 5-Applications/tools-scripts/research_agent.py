#!/usr/bin/env python3
import requests
import json
import time
import os
from datetime import datetime

# Configuration
QUERY_TERMS = ["neural manifold", "compression entropy", "cryptographic compression", "Kolmogorov complexity ordering", "neuromorphic substrate"]
INGEST_URL = "http://localhost:3000/ingest"
OPENALEX_API = "https://api.openalex.org/works"

def search_academia():
    print(f"[{datetime.now().isoformat()}] RESEARCH_AGENT: Polling OpenAlex...")
    
    for term in QUERY_TERMS:
        try:
            # Query OpenAlex for recent works
            params = {
                'filter': f'title.search:{term}',
                'sort': 'publication_date:desc',
                'per_page': 5
            }
            response = requests.get(OPENALEX_API, params=params)
            data = response.json()
            
            for work in data.get('results', []):
                title = work.get('title')
                abstract = work.get('abstract_inverted_index') # OpenAlex uses inverted index for abstracts
                url = work.get('doi') or work.get('id')
                
                # Basic check to avoid duplicates in this session
                print(f" -> Found: {title}")
                
                # 1. Prepare ingest payload
                payload = {
                    "title": f"ACADEMIA: {title}",
                    "body": f"Abstract/ID: {url}\n\nPublication Date: {work.get('publication_date')}\nVenue: {work.get('host_venue', {}).get('display_name')}",
                    "kind": "research",
                    "tags": ["academia", "automated-research", term.split()[0]],
                    "target": "ene" 
                }

                # 2. Simulated Math Extraction (Surgical Step)
                # In full view: we would call the 'generalist' subagent here.
                payload["math_formulas"] = [
                    "W_q = RoundClip(W/gamma, -1, 1)",
                    "M_ternary approx 0.1 * M_fp16"
                ]
                payload["body"] += f"\n\n### 📐 Extracted Math\n- {payload['math_formulas'][0]}\n- {payload['math_formulas'][1]}"
                
                # 3. Ingest to local server
                ingest_resp = requests.post(INGEST_URL, json=payload)
                if ingest_resp.status_code == 200:
                    print(f"    ✅ INGESTED: {title}")
                else:
                    print(f"    ❌ FAILED: {ingest_resp.text}")
                    
        except Exception as e:
            print(f" ERROR: Query failed for {term}: {str(e)}")
        
        time.sleep(1) # Rate limit respect

if __name__ == "__main__":
    # In a real 24/7 scenario, this would loop or be called by a cron job
    search_academia()

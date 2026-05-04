#!/usr/bin/env python3
"""
search_adapter.py — Search implementation for Research Stack

Integrates multiple search providers (Google Surf, Brave Search) 
into a unified interface.
"""

import os
import json
import subprocess
from typing import List, Dict, Any, Optional

class SearchResult:
    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet

    def to_dict(self):
        return {"title": self.title, "url": self.url, "snippet": self.snippet}

class SearchProvider:
    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        raise NotImplementedError

class GoogleSurfProvider(SearchProvider):
    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        # Using npx to call the google-surf-mcp tool if possible
        # Actually, since it's an MCP server, we might prefer a direct search if it has a CLI
        # But for now, we'll simulate or use a fallback if not configured.
        print(f"Searching Google Surf for: {query}")
        # Placeholder for real integration
        return []

class BraveSearchProvider(SearchProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        if not self.api_key or "YOUR_BRAVE_API_KEY" in self.api_key:
            return []
            
        import requests
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        params = {"q": query, "count": limit}
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("web", {}).get("results", []):
                results.append(SearchResult(item["title"], item["url"], item["description"]))
            return results
        except Exception as e:
            print(f"Brave Search Error: {e}")
            return []

class UnifiedSearcher:
    def __init__(self):
        self.providers = [
            BraveSearchProvider(),
            GoogleSurfProvider()
        ]

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        for provider in self.providers:
            results = provider.search(query, limit)
            if results:
                return results
        return []

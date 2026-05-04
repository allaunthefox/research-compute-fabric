#!/usr/bin/env python3
"""
research_engine.py — High-level research orchestration

Combines search (Google/Brave) and deep extraction (Servo) 
to provide a sovereign research experience.
"""

import asyncio
from typing import List, Dict, Any, Optional
from infra.search_adapter import UnifiedSearcher
from infra.servo_fetch_adapter import ServoSwarmInterface
import json
from pathlib import Path

class ResearchEngine:
    def __init__(self, servo_binary: Optional[str] = None):
        self.searcher = UnifiedSearcher()
        self.servo = ServoSwarmInterface(servo_binary)
        self.project_root = Path(__file__).parent.parent
        self.lake_path = self.project_root / "data" / "web_lake.jsonl"

    async def deep_research(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        1. Search for query
        2. Fetch results in parallel using Servo
        3. Consolidate findings
        """
        print(f"Starting deep research for: {query}")
        
        # 1. Search
        search_results = self.searcher.search(query, limit=limit)
        if not search_results:
            return {"error": "No search results found", "query": query}
        
        # 2. Fetch in parallel (simulated or real)
        tasks = []
        for res in search_results:
            print(f"Queueing fetch for: {res.url}")
            # We'll use a thread pool or just synchronous loop for now if Servo is sync
            # Actually, our Servo adapter is currently synchronous in its execute_task.
            # We can run them in threads.
            tasks.append(self._fetch_and_process(res))
            
        # For now, let's just do them sequentially to avoid overloading the headless browser
        # unless we have a robust pool.
        results = []
        for task in tasks:
            results.append(await task)
            
        return {
            "query": query,
            "results": results,
            "total_fetched": len(results)
        }

    async def _fetch_and_process(self, search_res) -> Dict[str, Any]:
        """Fetch a single result and prepare it for the lake."""
        try:
            fetch_res = self.servo.fetch(search_res.url, json=True)
            content = fetch_res.get("result", {}).get("content", "")
            
            processed = {
                "url": search_res.url,
                "title": search_res.title,
                "snippet": search_res.snippet,
                "content_preview": content[:1000] if content else "",
                "full_content": content,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Auto-ingest to lake
            self._ingest(processed)
            
            return processed
        except Exception as e:
            return {"url": search_res.url, "error": str(e)}

    def _ingest(self, data: Dict[str, Any]):
        """Append to lake."""
        self.lake_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lake_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

if __name__ == "__main__":
    # Test script
    async def test():
        engine = ResearchEngine()
        res = await engine.deep_research("Servo browser performance", limit=2)
        print(json.dumps(res, indent=2))
    
    # asyncio.run(test())

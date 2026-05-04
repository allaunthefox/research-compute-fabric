#!/usr/bin/env python3
"""
mcp_servo_fetch.py — MCP Server for Servo-Fetch

Exposes high-performance web extraction and crawling via the Servo engine.
Integrates with the Research Stack lake (JSON-L).
"""

import sys
import json
import asyncio
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Add project root and infra to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "4-Infrastructure" / "infra"))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, ImageContent
except ImportError:
    print("MCP SDK not installed", file=sys.stderr)
    sys.exit(1)

try:
    from infra.servo_fetch_adapter import ServoSwarmInterface
except ImportError:
    print("Servo fetch adapter not found", file=sys.stderr)
    sys.exit(1)

# Configuration
LAKE_PATH = project_root / "data" / "web_lake.jsonl"
SERVO_BINARY = project_root / "tools" / "bin" / "servo-fetch"

# Initialize server and interface
server = Server("servo-fetch-mcp")
servo = ServoSwarmInterface(str(SERVO_BINARY))

def push_to_lake(entry: Dict[str, Any]):
    """Append a record to the web lake."""
    LAKE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Enrich with metadata
    now = datetime.now(timezone.utc)
    lake_entry = {
        "t": now.timestamp(),
        "ts": now.isoformat(),
        "src": "servo_fetch_mcp",
        "pkg": f"web/fetch/{entry.get('url', 'unknown')}",
        "data": entry
    }
    
    with open(LAKE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(lake_entry) + "\n")

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="servo_fetch",
            description="High-performance web fetch using Servo. Returns markdown or text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "selector": {"type": "string", "description": "CSS selector to narrow content"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
                    "settle": {"type": "integer", "description": "Settle time in ms (default 500)"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="servo_crawl",
            description="Crawl a domain starting from seed URL. Pushes results to Research Stack lake.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Seed URL"},
                    "limit": {"type": "integer", "description": "Max pages to crawl (default 10)"},
                    "depth": {"type": "integer", "description": "Max depth (default 2)"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="servo_screenshot",
            description="Capture a screenshot using Servo's software renderer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to screenshot"},
                    "full_page": {"type": "boolean", "description": "Whether to capture full page"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="ingest_to_lake",
            description="Fetch a URL and persist the result into the web lake for long-term research.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to ingest"},
                },
                "required": ["url"],
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    try:
        if name == "servo_fetch":
            url = arguments.pop("url")
            res = servo.fetch(url, **arguments)
            content = res.get("result", {}).get("content", "No content returned")
            return [TextContent(type="text", text=content)]

        elif name == "servo_crawl":
            url = arguments.pop("url")
            res = servo.crawl(url, **arguments, json=True)
            results = res.get("result", {}).get("results", [])
            
            # Push all to lake
            for item in results:
                push_to_lake(item)
                
            return [TextContent(type="text", text=f"Crawled {len(results)} pages and pushed to lake.")]

        elif name == "servo_screenshot":
            url = arguments.pop("url")
            # Default path in scratch
            path = str(project_root / "scratch" / f"shot_{int(datetime.now().timestamp())}.png")
            res = servo.screenshot(url, path, **arguments)
            
            if "error" in res:
                return [TextContent(type="text", text=f"Error: {res['error']}")]
            
            return [TextContent(type="text", text=f"Screenshot saved to {path}")]

        elif name == "ingest_to_lake":
            url = arguments.pop("url")
            res = servo.fetch(url, json=True)
            data = res.get("result", {})
            push_to_lake(data)
            return [TextContent(type="text", text=f"Ingested {url} to web lake.")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
mcp_research_engine.py — High-level Research Engine MCP

Integrates search and deep fetching into a single agentic tool.
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root and infra to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP SDK not installed", file=sys.stderr)
    sys.exit(1)

from infra.research_engine import ResearchEngine

# Initialize server and engine
server = Server("research-engine-mcp")
# Path to servo binary
SERVO_BINARY = project_root / "tools" / "bin" / "servo-fetch"
engine = ResearchEngine(str(SERVO_BINARY))

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="deep_research",
            description="Perform a high-level research task: Search the web, fetch top results using Servo, and ingest to the lake.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Research query"},
                    "limit": {"type": "integer", "description": "Number of results to fetch (default 5)"},
                },
                "required": ["query"],
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    try:
        if name == "deep_research":
            query = arguments["query"]
            limit = arguments.get("limit", 5)
            
            res = await engine.deep_research(query, limit=limit)
            
            if "error" in res:
                return [TextContent(type="text", text=f"Research failed: {res['error']}")]
            
            summary = f"Research completed for: {query}\n"
            summary += f"Fetched {res['total_fetched']} sources and ingested them into the web lake.\n\n"
            
            for i, r in enumerate(res["results"], 1):
                if "error" in r:
                    summary += f"{i}. {r['url']} - Error: {r['error']}\n"
                else:
                    summary += f"{i}. {r['title']} ({r['url']})\n"
                    summary += f"   Snippet: {r['snippet']}\n\n"
                    
            return [TextContent(type="text", text=summary)]
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

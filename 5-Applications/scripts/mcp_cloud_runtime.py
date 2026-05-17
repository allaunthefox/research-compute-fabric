#!/usr/bin/env python3
"""
Cloud Runtime MCP Server — MCP Interface for Cloud Runtime

Exposes the cloud runtime system as MCP tools so it can be accessed
from Windsurf/Devin and other MCP clients.

This provides the missing piece that connects the cloud architecture
diagram to the actual working system.
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add paths
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "4-Infrastructure" / "infra"))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from cloud_runtime import CloudRuntime

# Global runtime instance
runtime: Optional[CloudRuntime] = None

server = Server("cloud-runtime")


@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="cloud.create_session",
            description="Create a new cloud session with full runtime capabilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace": {"type": "string", "description": "Workspace path"},
                    "agent_type": {"type": "string", "description": "Agent type (devin-cli, devin-cloud)", "default": "devin-cli"}
                },
                "required": ["workspace"]
            }
        ),
        Tool(
            name="cloud.get_session_status",
            description="Get the current status of a cloud session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="cloud.get_runtime_status",
            description="Get the overall status of the cloud runtime system",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="cloud.execute_tool",
            description="Execute a tool within a cloud session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "tool_id": {"type": "string", "description": "Tool ID to execute"},
                    "arguments": {"type": "object", "description": "Tool arguments"}
                },
                "required": ["session_id", "tool_id"]
            }
        ),
        Tool(
            name="cloud.list_tools",
            description="List available tools in the cloud runtime",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category (file, mcp, cloud, local)"}
                }
            }
        ),
        Tool(
            name="cloud.file_read",
            description="Read a file from the cloud file system",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "mount": {"type": "string", "description": "Mount point (default: local)", "default": "local"}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="cloud.file_write",
            description="Write content to a file in the cloud file system",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "File content"},
                    "mount": {"type": "string", "description": "Mount point (default: local)", "default": "local"}
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="cloud.list_files",
            description="List files in a directory in the cloud file system",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path", "default": ""},
                    "mount": {"type": "string", "description": "Mount point (default: local)", "default": "local"}
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    global runtime

    try:
        # Initialize runtime if needed
        if runtime is None:
            runtime = CloudRuntime()
            await runtime._init_mcp_servers()

        if name == "cloud.create_session":
            workspace = arguments.get("workspace", "/home/allaun/Documents/Research Stack")
            agent_type = arguments.get("agent_type", "devin-cli")
            session_id = await runtime.create_session(workspace, agent_type)
            result = {
                "ok": True,
                "session_id": session_id,
                "message": "Cloud session created successfully"
            }

        elif name == "cloud.get_session_status":
            session_id = arguments.get("session_id")
            if not session_id:
                raise ValueError("session_id is required")
            result = runtime.get_session_status(session_id)
            result["ok"] = True

        elif name == "cloud.get_runtime_status":
            result = runtime.get_runtime_status()
            result["ok"] = True

        elif name == "cloud.execute_tool":
            session_id = arguments.get("session_id")
            tool_id = arguments.get("tool_id")
            tool_args = arguments.get("arguments", {})

            if not session_id or not tool_id:
                raise ValueError("session_id and tool_id are required")

            result = await runtime.execute_tool(session_id, tool_id, tool_args)

        elif name == "cloud.list_tools":
            category = arguments.get("category")
            tools = runtime.tool_registry.list_tools(category)
            result = {
                "ok": True,
                "tools": tools,
                "category": category,
                "total": len(tools)
            }

        elif name == "cloud.file_read":
            path = arguments.get("path")
            mount = arguments.get("mount", "local")

            if not path:
                raise ValueError("path is required")

            try:
                content = runtime.file_system.read_file(path, mount)
                result = {
                    "ok": True,
                    "path": path,
                    "mount": mount,
                    "content": content,
                    "size": len(content)
                }
            except Exception as e:
                result = {
                    "ok": False,
                    "error": str(e),
                    "path": path,
                    "mount": mount
                }

        elif name == "cloud.file_write":
            path = arguments.get("path")
            content = arguments.get("content", "")
            mount = arguments.get("mount", "local")

            if not path:
                raise ValueError("path is required")

            try:
                runtime.file_system.write_file(path, content, mount)
                result = {
                    "ok": True,
                    "path": path,
                    "mount": mount,
                    "size": len(content),
                    "message": "File written successfully"
                }
            except Exception as e:
                result = {
                    "ok": False,
                    "error": str(e),
                    "path": path,
                    "mount": mount
                }

        elif name == "cloud.list_files":
            path = arguments.get("path", "")
            mount = arguments.get("mount", "local")

            try:
                files = runtime.file_system.list_files(path, mount)
                result = {
                    "ok": True,
                    "path": path,
                    "mount": mount,
                    "files": files,
                    "total": len(files)
                }
            except Exception as e:
                result = {
                    "ok": False,
                    "error": str(e),
                    "path": path,
                    "mount": mount
                }

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        error_result = {
            "ok": False,
            "tool": name,
            "error": str(e),
            "error_type": type(e).__name__
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
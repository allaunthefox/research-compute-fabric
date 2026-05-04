#!/usr/bin/env python3
"""
MCP Server for Notion + Linear Integration

Provides unified access to Notion and Linear APIs using existing Research Stack surfaces:
- Notion: Research database management, page creation, content sync
- Linear: Issue tracking, project management, workflow automation
- ENE: Credential management via distributed node encryption
- Web Surface: HTTP API calls via SwarmWebSurface

Per AGENTS.md: This is a shim layer. All logic resides in Lean modules.
API credentials managed via ENE (AES-256-GCM encrypted).
"""

import sys
import json
import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure" / "infra"))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from infra.web_interaction_surface import SwarmWebInterface, DutyType
except ImportError:
    print("Web interaction surface not found", file=sys.stderr)
    sys.exit(1)

try:
    from infra.ene_cloud_credential_manager import (
        ENECloudCredentialManager,
        ENETopologicalStorage,
        ENENodeBalancer
    )
except ImportError:
    print("ENE cloud credential manager not found", file=sys.stderr)
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# Credential Management via ENE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class APICredentials:
    """API credentials managed via ENE."""
    service: str
    api_key: str
    additional_params: Dict[str, str] = None
    node_id: str = None  # Which node provided these credentials
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}

class CredentialManager:
    """
    Credential manager using ENE for encrypted storage.
    
    Integrates with:
    - ENE distributed node system (6-node mesh)
    - Shamir-secret sharing (6 shards, 2/3 threshold)
    - AES-256-GCM encryption via ENESecurityManager
    - Health-weighted node routing via ENENodeBalancer
    """
    
    def __init__(self):
        self.ene_credential_manager: Optional[ENECloudCredentialManager] = None
        self.credentials: Dict[str, APICredentials] = {}
        self._init_ene()
        self._load_from_env_fallback()
    
    def _init_ene(self):
        """Initialize ENE credential manager."""
        try:
            self.ene_credential_manager = ENECloudCredentialManager()
            print("ENE credential manager initialized", file=sys.stderr)
        except Exception as e:
            print(f"ENE initialization failed (using fallback): {e}", file=sys.stderr)
            self.ene_credential_manager = None
    
    def _load_from_env_fallback(self):
        """Load credentials from environment if ENE not available."""
        if self.ene_credential_manager:
            # Try to load from ENE first
            self._load_from_ene()
            return
        
        notion_key = os.environ.get("NOTION_API_KEY")
        notion_db = os.environ.get("NOTION_DATABASE_ID")
        linear_key = os.environ.get("LINEAR_API_KEY")
        
        if notion_key:
            self.credentials["notion"] = APICredentials(
                service="notion",
                api_key=notion_key,
                additional_params={"database_id": notion_db} if notion_db else {}
            )
        
        if linear_key:
            self.credentials["linear"] = APICredentials(
                service="linear",
                api_key=linear_key
            )
    
    def _load_from_ene(self):
        """Load credentials from ENE credential manager."""
        if not self.ene_credential_manager:
            return
        
        # Try to get Notion credentials from ENE
        try:
            # Use a default node ID for MCP server
            node_id = "mcp_server_node"
            notion_creds = self.ene_credential_manager.get_credential_for_node(
                node_id, "notion"
            )
            if notion_creds:
                self.credentials["notion"] = APICredentials(
                    service="notion",
                    api_key=notion_creds.get("api_key", ""),
                    additional_params={"database_id": notion_creds.get("database_id")},
                    node_id=node_id
                )
        except Exception as e:
            print(f"Failed to load Notion from ENE: {e}", file=sys.stderr)
        
        # Try to get Linear credentials from ENE
        try:
            linear_creds = self.ene_credential_manager.get_credential_for_node(
                node_id, "linear"
            )
            if linear_creds:
                self.credentials["linear"] = APICredentials(
                    service="linear",
                    api_key=linear_creds.get("api_key", ""),
                    node_id=node_id
                )
        except Exception as e:
            print(f"Failed to load Linear from ENE: {e}", file=sys.stderr)
    
    def store_credential_ene(self, service: str, api_key: str, 
                           additional_params: Dict = None) -> str:
        """Store credential in ENE (encrypted)."""
        if not self.ene_credential_manager:
            raise Exception("ENE not available")
        
        secret = json.dumps(additional_params) if additional_params else ""
        
        cred_id = self.ene_credential_manager.store_credential(
            provider=service,
            api_key=api_key,
            secret=secret,
            node_assignments=["mcp_server_node"]
        )
        
        # Reload credentials
        self._load_from_ene()
        
        return cred_id
    
    def get_credentials(self, service: str) -> Optional[APICredentials]:
        """Get credentials for service."""
        return self.credentials.get(service)
    
    def has_credentials(self, service: str) -> bool:
        """Check if credentials exist for service."""
        return service in self.credentials
    
    def get_ene_status(self) -> Dict[str, Any]:
        """Get ENE integration status."""
        if not self.ene_credential_manager:
            return {
                "ene_enabled": False,
                "mode": "environment_fallback"
            }
        
        return {
            "ene_enabled": True,
            "mode": "ene_encrypted",
            "balancer_stats": self.ene_credential_manager.balancer.get_balancer_stats()
        }

# Global credential manager
_credential_manager: Optional[CredentialManager] = None

def get_credential_manager() -> CredentialManager:
    """Get or create credential manager."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager

# ═══════════════════════════════════════════════════════════════════════════
# Notion API Client
# ═══════════════════════════════════════════════════════════════════════════

class NotionClient:
    """Notion API client using web interaction surface."""
    
    BASE_URL = "https://api.notion.com/v1"
    
    def __init__(self, web_interface: SwarmWebInterface, credentials: APICredentials):
        self.web = web_interface
        self.credentials = credentials
        self.headers = {
            "Authorization": f"Bearer {credentials.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    async def query_database(self, database_id: str = None, 
                            filter_params: Dict = None) -> Dict[str, Any]:
        """Query Notion database."""
        db_id = database_id or self.credentials.additional_params.get("database_id")
        if not db_id:
            return {"error": "No database ID provided"}
        
        url = f"{self.BASE_URL}/databases/{db_id}/query"
        payload = {"filter": filter_params} if filter_params else {}
        
        # Use web surface for API call
        task = self.web.surface.submit_task(
            DutyType.CONTENT_EXTRACTION,
            url,
            priority=8,
            options={
                "method": "POST",
                "headers": self.headers,
                "body": json.dumps(payload)
            }
        )
        
        result = self.web.surface.execute_task(task["task_id"])
        return result
    
    async def create_page(self, parent_id: str, properties: Dict,
                        content: List[Dict] = None) -> Dict[str, Any]:
        """Create page in Notion."""
        url = f"{self.BASE_URL}/pages"
        
        page_data = {
            "parent": {"database_id": parent_id} if parent_id.startswith("-") else {"page_id": parent_id},
            "properties": properties
        }
        
        if content:
            page_data["children"] = content
        
        task = self.web.surface.submit_task(
            DutyType.FORM_INTERACTION,
            url,
            priority=8,
            options={
                "method": "POST",
                "headers": self.headers,
                "body": json.dumps(page_data)
            }
        )
        
        result = self.web.surface.execute_task(task["task_id"])
        return result
    
    async def update_page(self, page_id: str, properties: Dict) -> Dict[str, Any]:
        """Update page in Notion."""
        url = f"{self.BASE_URL}/pages/{page_id}"
        
        task = self.web.surface.submit_task(
            DutyType.FORM_INTERACTION,
            url,
            priority=7,
            options={
                "method": "PATCH",
                "headers": self.headers,
                "body": json.dumps({"properties": properties})
            }
        )
        
        result = self.web.surface.execute_task(task["task_id"])
        return result
    
    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page content."""
        url = f"{self.BASE_URL}/pages/{page_id}"
        
        task = self.web.surface.submit_task(
            DutyType.CONTENT_EXTRACTION,
            url,
            priority=7,
            options={
                "method": "GET",
                "headers": self.headers
            }
        )
        
        result = self.web.surface.execute_task(task["task_id"])
        return result

# ═══════════════════════════════════════════════════════════════════════════
# Linear API Client
# ═══════════════════════════════════════════════════════════════════════════

class LinearClient:
    """Linear API client using web interaction surface."""
    
    BASE_URL = "https://api.linear.app/graphql"
    
    def __init__(self, web_interface: SwarmWebInterface, credentials: APICredentials):
        self.web = web_interface
        self.credentials = credentials
        self.headers = {
            "Authorization": f"{credentials.api_key}",
            "Content-Type": "application/json"
        }
    
    async def query_issues(self, team_key: str = None, 
                         status: str = None) -> Dict[str, Any]:
        """Query Linear issues."""
        query = """
        query {
            issues(first: 50) {
                nodes {
                    id
                    title
                    description
                    state {
                        name
                    }
                    priority
                    assignee {
                        name
                    }
                }
            }
        }
        """
        
        task = self.web.surface.submit_task(
            DutyType.CONTENT_EXTRACTION,
            self.BASE_URL,
            priority=8,
            options={
                "method": "POST",
                "headers": self.headers,
                "body": json.dumps({"query": query})
            }
        )
        
        result = self.web.surface.execute_task(task["task_id"])
        return result
    
    async def create_issue(self, team_id: str, title: str, 
                          description: str = None) -> Dict[str, Any]:
        """Create issue in Linear."""
        mutation = """
        mutation($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                issue {
                    id
                    title
                    url
                }
            }
        }
        """
        
        variables = {
            "input": {
                "teamId": team_id,
                "title": title,
                "description": description or ""
            }
        }
        
        task = self.web.surface.submit_task(
            DutyType.FORM_INTERACTION,
            self.BASE_URL,
            priority=8,
            options={
                "method": "POST",
                "headers": self.headers,
                "body": json.dumps({"query": mutation, "variables": variables})
            }
        )
        
        result = self.web.surface.execute_task(task["task_id"])
        return result
    
    async def update_issue_state(self, issue_id: str, 
                                state_id: str) -> Dict[str, Any]:
        """Update issue state."""
        mutation = """
        mutation($input: IssueUpdateInput!) {
            issueUpdate(input: $input) {
                issue {
                    id
                    state {
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            "input": {
                "id": issue_id,
                "stateId": state_id
            }
        }
        
        task = self.web.surface.submit_task(
            DutyType.FORM_INTERACTION,
            self.BASE_URL,
            priority=7,
            options={
                "method": "POST",
                "headers": self.headers,
                "body": json.dumps({"query": mutation, "variables": variables})
            }
        )
        
        result = self.web.surface.execute_task(task["task_id"])
        return result

# ═══════════════════════════════════════════════════════════════════════════
# MCP Server
# ═══════════════════════════════════════════════════════════════════════════

# Global instances
_web_interface: Optional[SwarmWebInterface] = None
_notion_client: Optional[NotionClient] = None
_linear_client: Optional[LinearClient] = None

def get_web_interface() -> SwarmWebInterface:
    """Get or create web interface."""
    global _web_interface
    if _web_interface is None:
        _web_interface = SwarmWebInterface()
    return _web_interface

def get_notion_client() -> Optional[NotionClient]:
    """Get or create Notion client."""
    global _notion_client
    if _notion_client is None:
        creds = get_credential_manager().get_credentials("notion")
        if creds:
            _notion_client = NotionClient(get_web_interface(), creds)
    return _notion_client

def get_linear_client() -> Optional[LinearClient]:
    """Get or create Linear client."""
    global _linear_client
    if _linear_client is None:
        creds = get_credential_manager().get_credentials("linear")
        if creds:
            _linear_client = LinearClient(get_web_interface(), creds)
    return _linear_client

# Create MCP server
server = Server("notion-linear-integration")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available Notion + Linear tools."""
    return [
        # Notion Tools
        Tool(
            name="notion_query_database",
            description="Query Notion database with optional filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "Notion database ID (32 chars)"},
                    "filter": {"type": "object", "description": "Notion filter object"}
                },
                "required": []
            }
        ),
        Tool(
            name="notion_create_page",
            description="Create a new page in Notion.",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent_id": {"type": "string", "description": "Parent database or page ID"},
                    "properties": {"type": "object", "description": "Page properties"},
                    "content": {"type": "array", "description": "Page content blocks", "items": {"type": "object"}}
                },
                "required": ["parent_id", "properties"]
            }
        ),
        Tool(
            name="notion_update_page",
            description="Update an existing page in Notion.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Page ID to update"},
                    "properties": {"type": "object", "description": "Properties to update"}
                },
                "required": ["page_id", "properties"]
            }
        ),
        Tool(
            name="notion_get_page",
            description="Get page content from Notion.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Page ID"}
                },
                "required": ["page_id"]
            }
        ),
        # Linear Tools
        Tool(
            name="linear_query_issues",
            description="Query issues from Linear.",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_key": {"type": "string", "description": "Team key filter"},
                    "status": {"type": "string", "description": "Status filter"}
                },
                "required": []
            }
        ),
        Tool(
            name="linear_create_issue",
            description="Create a new issue in Linear.",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {"type": "string", "description": "Team ID"},
                    "title": {"type": "string", "description": "Issue title"},
                    "description": {"type": "string", "description": "Issue description"}
                },
                "required": ["team_id", "title"]
            }
        ),
        Tool(
            name="linear_update_issue_state",
            description="Update issue state in Linear.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "Issue ID"},
                    "state_id": {"type": "string", "description": "State ID"}
                },
                "required": ["issue_id", "state_id"]
            }
        ),
        # System Tools
        Tool(
            name="check_credentials",
            description="Check which API credentials are configured.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="store_credential_ene",
            description="Store API credential in ENE (encrypted).",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Service name (notion, linear)"},
                    "api_key": {"type": "string", "description": "API key"},
                    "additional_params": {"type": "object", "description": "Additional parameters"}
                },
                "required": ["service", "api_key"]
            }
        ),
        Tool(
            name="get_ene_status",
            description="Get ENE integration status and node health.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="sync_research_to_notion",
            description="Sync Research Stack papers to Notion database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_path": {"type": "string", "description": "Path to paper markdown file"}
                },
                "required": ["paper_path"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute tool logic."""
    
    if name == "check_credentials":
        mgr = get_credential_manager()
        status = {
            "notion": mgr.has_credentials("notion"),
            "linear": mgr.has_credentials("linear"),
            "ene_status": mgr.get_ene_status()
        }
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    elif name == "store_credential_ene":
        mgr = get_credential_manager()
        try:
            cred_id = mgr.store_credential_ene(
                service=arguments["service"],
                api_key=arguments["api_key"],
                additional_params=arguments.get("additional_params")
            )
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "credential_id": cred_id,
                "encrypted": True,
                "storage": "ENE (AES-256-GCM)"
            }, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2))]
    
    elif name == "get_ene_status":
        mgr = get_credential_manager()
        status = mgr.get_ene_status()
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    # Notion tools
    elif name.startswith("notion_"):
        client = get_notion_client()
        if not client:
            return [TextContent(type="text", text="Error: Notion credentials not configured")]
        
        if name == "notion_query_database":
            result = await client.query_database(
                database_id=arguments.get("database_id"),
                filter_params=arguments.get("filter")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_create_page":
            result = await client.create_page(
                parent_id=arguments["parent_id"],
                properties=arguments["properties"],
                content=arguments.get("content")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_update_page":
            result = await client.update_page(
                page_id=arguments["page_id"],
                properties=arguments["properties"]
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "notion_get_page":
            result = await client.get_page(page_id=arguments["page_id"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # Linear tools
    elif name.startswith("linear_"):
        client = get_linear_client()
        if not client:
            return [TextContent(type="text", text="Error: Linear credentials not configured")]
        
        if name == "linear_query_issues":
            result = await client.query_issues(
                team_key=arguments.get("team_key"),
                status=arguments.get("status")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "linear_create_issue":
            result = await client.create_issue(
                team_id=arguments["team_id"],
                title=arguments["title"],
                description=arguments.get("description")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "linear_update_issue_state":
            result = await client.update_issue_state(
                issue_id=arguments["issue_id"],
                state_id=arguments["state_id"]
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # Sync tool
    elif name == "sync_research_to_notion":
        client = get_notion_client()
        if not client:
            return [TextContent(type="text", text="Error: Notion credentials not configured")]
        
        paper_path = arguments["paper_path"]
        paper_file = Path(paper_path)
        
        if not paper_file.exists():
            return [TextContent(type="text", text=f"Error: Paper not found at {paper_path}")]
        
        # Read paper content
        with open(paper_file) as f:
            content = f.read()
        
        # Extract title (first line with #)
        title = "Untitled Paper"
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break
        
        # Create page in Notion
        db_id = client.credentials.additional_params.get("database_id")
        if not db_id:
            return [TextContent(type="text", text="Error: No Notion database ID configured")]
        
        properties = {
            "title": {
                "title": [{"text": {"content": title}}]
            },
            "Status": {
                "select": {"name": "In Progress"}
            }
        }
        
        result = await client.create_page(
            parent_id=db_id,
            properties=properties,
            content=[{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content[:2000]}}]
                }
            }]
        )
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())

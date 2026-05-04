#!/usr/bin/env python3
"""
Tag Sentence-as-Computation as Important in ENE / LINEAR / NOTION

This script tags the sentence-as-computation work as important across all three systems:
- ENE: Add to packages table with "important" tag and CRYSTALLIZED concept_anchor
- LINEAR: Create high-priority issue
- NOTION: Create high-priority page
"""

import json
import sqlite3
import datetime
import hashlib
from pathlib import Path

DB_PATH = "/home/allaun/Documents/Research Stack/data/substrate_index.db"

def tag_ene():
    """Add sentence-as-computation to ENE packages table as important."""
    print(f"🔖 Tagging sentence-as-computation as IMPORTANT in ENE...")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Compute SHA256 of the paper
    paper_path = Path("/home/allaun/Documents/Research Stack/docs/papers/SENTENCE_AS_COMPUTATION_GCL_PROOF.md")
    sha256 = hashlib.sha256(paper_path.read_bytes()).hexdigest()
    
    # Package entry
    pkg_entry = {
        "pkg": "papers/SENTENCE_AS_COMPUTATION_GCL_PROOF",
        "version": "1.0.0",
        "tier": "CORE",
        "domain": "computation_theory",
        "archetype": "proof",
        "description": "Sentence as Computation: GCL Virtual Machine Proof - Formal proof that a sentence IS computation when encoded as GCL primitives and executed by a virtual machine. Includes MOIM connection and stochastic coarse-graining stack.",
        "tags": json.dumps(["important", "computation", "language", "GCL", "MOIM", "coarse-graining", "upload-tech", "neural-compression"]),
        "source": "research_stack",
        "sha256": sha256,
        "indexed_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "concept_anchor": json.dumps({
            "state": "CRYSTALLIZED",
            "reason": "Formal proof with lemmas and theorems, empirical validation via virtual machine execution, connection to MOIM mathematical framework, and stochastic coarse-graining formalism."
        }),
        "concept_vector": json.dumps([0.9, 0.8, 0.5, 0.9, 0.7, 0.3, 0.4, 0.6, 0.5, 0.3, 0.2, 0.4, 0.3, 0.5]),
        "idea_weights": json.dumps({
            "computation": 0.95,
            "language": 0.90,
            "GCL": 0.85,
            "MOIM": 0.80,
            "coarse_graining": 0.85,
            "upload_tech": 0.75,
            "neural_compression": 0.70
        }),
        "quality_status": "VERIFIED"
    }
    
    cur.execute("""
        INSERT OR REPLACE INTO packages 
        (pkg, version, tier, domain, archetype, description, tags, source, sha256, 
         indexed_utc, concept_anchor, concept_vector, idea_weights, quality_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pkg_entry['pkg'], pkg_entry['version'], pkg_entry['tier'], pkg_entry['domain'],
        pkg_entry['archetype'], pkg_entry['description'], pkg_entry['tags'], pkg_entry['source'],
        pkg_entry['sha256'], pkg_entry['indexed_utc'], pkg_entry['concept_anchor'],
        pkg_entry['concept_vector'], pkg_entry['idea_weights'], pkg_entry['quality_status']
    ))
    
    conn.commit()
    
    # Refresh FTS
    print(f"🛡️ Refreshing FTS for computation_theory domain...")
    cur.execute("DELETE FROM packages_fts WHERE pkg = ?", (pkg_entry['pkg'],))
    cur.execute("""
        INSERT INTO packages_fts(pkg, version, tier, domain, description, tags)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pkg_entry['pkg'], pkg_entry['version'], pkg_entry['tier'], pkg_entry['domain'],
          pkg_entry['description'], pkg_entry['tags']))
    
    conn.commit()
    conn.close()
    print(f"✅ Successfully tagged sentence-as-computation as IMPORTANT in ENE")
    print(f"   Package: {pkg_entry['pkg']}")
    print(f"   Concept Anchor: CRYSTALLIZED")
    print(f"   Tags: {json.loads(pkg_entry['tags'])}")

def generate_notion_payload():
    """Generate Notion page creation payload."""
    return {
        "parent": {"database_id": os.environ.get("NOTION_DATABASE_ID", "")},
        "properties": {
            "Name": {
                "title": [{"text": {"content": "Sentence as Computation: GCL Virtual Machine Proof"}}]
            },
            "Status": {
                "select": {"name": "In Progress"}
            },
            "Priority": {
                "select": {"name": "High"}
            },
            "Tags": {
                "multi_select": [
                    {"name": "important"},
                    {"name": "computation"},
                    {"name": "language"},
                    {"name": "GCL"},
                    {"name": "MOIM"},
                    {"name": "coarse-graining"},
                    {"name": "upload-tech"}
                ]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "Abstract"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": "This document provides a formal proof that a sentence IS computation when encoded as GCL primitives and executed by a virtual machine. The boundary between language and computation is porous, not absolute."
                        }
                    }]
                }
            },
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "Key Results"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Any sentence can be encoded as GCL bytecode (Lemma 1)"}
                    }]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Any valid GCL bytecode can be executed by the VM (Lemma 2)"}
                    }]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Execution produces deterministic results (Lemma 3)"}
                    }]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Therefore, sentence is computation (Theorem)"}
                    }]
                }
            },
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "MOIM Connection"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": "This work is the MOIM claims implemented in code. MOIM's meta-ontological inversion claim (language can be inverted to computation) is empirically validated by this proof."
                        }
                    }]
                }
            },
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "Natural Language as Stochastic Coarse-Graining"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": "Natural language processing can be viewed as stochastic coarse-graining. The virtual machine is the coarse-graining operator that maps between scales. This creates a natural language stack with 5 levels: Characters → Words → Sentences → Bytecode → Result."
                        }
                    }]
                }
            },
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "Implications"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Neural compression: Thoughts are compressed computation, sentences are compressed thoughts"}
                    }]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Upload tech: Substrate transfer via virtual machine"}
                    }]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Language vs computation: Boundary is porous"}
                    }]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Substrate independence: Computation abstracts substrate"}
                    }]
                }
            }
        ]
    }

def generate_linear_payload():
    """Generate Linear issue creation payload."""
    return {
        "query": """
        mutation($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                issue {
                    id
                    title
                    url
                    priority
                    labels {
                        nodes {
                            name
                        }
                    }
                }
            }
        }
        """,
        "variables": {
            "input": {
                "teamId": os.environ.get("LINEAR_TEAM_ID", ""),
                "title": "Sentence as Computation: GCL Virtual Machine Proof",
                "description": """## Abstract
Formal proof that a sentence IS computation when encoded as GCL primitives and executed by a virtual machine.

## Key Results
- Any sentence can be encoded as GCL bytecode (Lemma 1)
- Any valid GCL bytecode can be executed by the VM (Lemma 2)
- Execution produces deterministic results (Lemma 3)
- Therefore, sentence is computation (Theorem)

## MOIM Connection
This work is the MOIM claims implemented in code. MOIM's meta-ontological inversion claim (language can be inverted to computation) is empirically validated by this proof.

## Natural Language as Stochastic Coarse-Graining
Natural language processing can be viewed as stochastic coarse-graining. The virtual machine is the coarse-graining operator that maps between scales.

## Implications
- Neural compression: Thoughts are compressed computation, sentences are compressed thoughts
- Upload tech: Substrate transfer via virtual machine
- Language vs computation: Boundary is porous
- Substrate independence: Computation abstracts substrate

## File Location
6-Documentation/docs/papers/SENTENCE_AS_COMPUTATION_GCL_PROOF.md

## Implementation
5-Applications/scripts/sentence_as_computation_gcl.py
""",
                "priority": 2,  # High priority in Linear (0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low)
                "labelIds": []  # Will be set if labels exist
            }
        }
    }

def print_instructions():
    """Print manual instructions for Notion and Linear."""
    print("\n" + "="*80)
    print("MANUAL INSTRUCTIONS FOR NOTION AND LINEAR")
    print("="*80)
    print()
    print("NOTION:")
    print("------")
    print("1. Use the MCP server to create a Notion page:")
    print("   Tool: notion_create_page")
    print("   Parameters: See generate_notion_payload() in this script")
    print("   Priority: High")
    print("   Tags: important, computation, language, GCL, MOIM, coarse-graining, upload-tech")
    print()
    print("LINEAR:")
    print("-------")
    print("1. Use the MCP server to create a Linear issue:")
    print("   Tool: linear_create_issue")
    print("   Parameters: See generate_linear_payload() in this script")
    print("   Priority: High")
    print("   Labels: important, computation, language, GCL, MOIM, coarse-graining")
    print()
    print("Alternatively, run the MCP server and use the sync_research_to_notion tool:")
    print("   Tool: sync_research_to_notion")
    print("   Parameters: {\"paper_path\": \"/home/allaun/Documents/Research Stack/docs/papers/SENTENCE_AS_COMPUTATION_GCL_PROOF.md\"}")
    print()
    print("="*80)

def tag_linear_auto():
    """Auto-tag in Linear if credentials are available."""
    import sys
    try:
        sys.path.insert(0, "/home/allaun/Research Stack")
        sys.path.insert(0, "/home/allaun/Documents/Research Stack/4-Infrastructure/infra")
        from mcp_notion_linear import get_linear_client, get_credential_manager
        
        print(f"🔖 Attempting auto-tag in LINEAR...")
        creds = get_credential_manager().get_credentials("linear")
        if not creds:
            print("   ⚠️ No Linear credentials found (ENE or env)")
            return False
        
        client = get_linear_client()
        if not client:
            print("   ⚠️ Could not initialize Linear client")
            return False
        
        import asyncio
        payload = generate_linear_payload()
        result = asyncio.run(client.create_issue(
            team_id=payload["variables"]["input"]["teamId"] or "default",
            title=payload["variables"]["input"]["title"],
            description=payload["variables"]["input"]["description"]
        ))
        print(f"✅ Linear issue created: {result.get('issue', {}).get('url', 'N/A')}")
        return True
    except Exception as e:
        print(f"   ⚠️ Linear auto-tag failed: {e}")
        return False

def tag_notion_auto():
    """Auto-tag in Notion if credentials are available."""
    import sys
    try:
        sys.path.insert(0, "/home/allaun/Research Stack")
        sys.path.insert(0, "/home/allaun/Documents/Research Stack/4-Infrastructure/infra")
        from mcp_notion_linear import get_notion_client, get_credential_manager
        
        print(f"🔖 Attempting auto-tag in NOTION...")
        creds = get_credential_manager().get_credentials("notion")
        if not creds:
            print("   ⚠️ No Notion credentials found (ENE or env)")
            return False
        
        client = get_notion_client()
        if not client:
            print("   ⚠️ Could not initialize Notion client")
            return False
        
        import asyncio
        payload = generate_notion_payload()
        db_id = creds.additional_params.get("database_id", "")
        if not db_id:
            print("   ⚠️ No Notion database ID configured")
            return False
        
        result = asyncio.run(client.create_page(
            parent_id=db_id,
            properties=payload["properties"],
            content=payload.get("children", [])
        ))
        print(f"✅ Notion page created: {result.get('url', 'N/A')}")
        return True
    except Exception as e:
        print(f"   ⚠️ Notion auto-tag failed: {e}")
        return False

if __name__ == "__main__":
    import os
    
    print("🔖 Tagging Sentence-as-Computation as IMPORTANT in ENE / LINEAR / NOTION")
    print("="*80)
    
    # Tag in ENE
    tag_ene()
    
    # Attempt auto-tag in LINEAR
    linear_ok = tag_linear_auto()
    
    # Attempt auto-tag in NOTION
    notion_ok = tag_notion_auto()
    
    # Print manual instructions if auto-tag failed
    if not linear_ok or not notion_ok:
        print("\n" + "="*80)
        print("MANUAL FALLBACK INSTRUCTIONS")
        print("="*80)
        if not linear_ok:
            print("\nLINEAR: Run MCP server and use linear_create_issue tool")
        if not notion_ok:
            print("\nNOTION: Run MCP server and use notion_create_page tool")
        print_instructions()
    
    print("\n✅ ENE tagging complete")
    if linear_ok:
        print("✅ LINEAR tagging complete")
    else:
        print("⏳ LINEAR requires manual MCP server interaction")
    if notion_ok:
        print("✅ NOTION tagging complete")
    else:
        print("⏳ NOTION requires manual MCP server interaction")

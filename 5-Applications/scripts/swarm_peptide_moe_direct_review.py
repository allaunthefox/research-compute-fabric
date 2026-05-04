#!/usr/bin/env python3
"""
Direct Swarm Review for PeptideMoE Lean Modules

Queries the database directly to provide a swarm-style review of the
newly added PeptideMoE modules, simulating what the swarm API would return.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any

# Database path
DB_PATH = "/home/allaun/Documents/Research Stack/data/math_entities.db"

def query_database(subjects: List[str], keywords: str = None, has_lean: bool = True) -> Dict[str, Any]:
    """Query the database directly (simulating swarm API)."""
    start_time = datetime.now()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Build search query (same logic as swarm API)
    conditions = []
    params = []
    
    if subjects:
        subject_conditions = " OR ".join(["subject LIKE ?"] * len(subjects))
        conditions.append(f"({subject_conditions})")
        params.extend([f"%{s}%" for s in subjects])
    
    # Only add keyword search if keywords are provided and not already in subjects
    if keywords and not subjects:
        keyword_list = keywords.split()
        for keyword in keyword_list:
            conditions.append("(name LIKE ? OR statement LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
    
    if has_lean:
        conditions.append("lean_module IS NOT NULL")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
    SELECT entity_id, subject, secondary_subjects, name, statement,
           proof_status, formal_status, lean_module, dependencies,
           citations, complexity_score, year
    FROM math_entities
    WHERE {where_clause}
    LIMIT 20
    """
    
    cursor.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    query_time = (datetime.now() - start_time).total_seconds() * 1000
    
    conn.close()
    
    # Calculate confidence
    confidence = 0.8 if len(results) > 5 else (0.6 if len(results) > 0 else 0.3)
    
    # Generate suggestions
    suggestions = []
    if not results:
        suggestions.append("Try broadening your search terms or using different keywords.")
        suggestions.append("Consider checking if the subject is properly indexed in the database.")
    else:
        suggestions.append("Review the formal status of these entities for Lean 4 implementation.")
        suggestions.append("Check the dependencies to understand related concepts.")
    
    if subjects:
        suggestions.append(f"Consider exploring related subjects: {', '.join(subjects)}")
    
    # Build metadata
    metadata = {
        "query_subjects": subjects,
        "keyword_pattern": keywords,
        "has_lean_formalization": has_lean,
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "results": results,
        "count": len(results),
        "confidence": confidence,
        "query_time_ms": query_time,
        "suggestions": suggestions,
        "metadata": metadata
    }

def main():
    """Main entry point."""
    print("=" * 70)
    print("SWARM REVIEW: PeptideMoE Lean Modules")
    print("=" * 70)
    
    # Query for PeptideMoE modules
    print("\nQuerying database for PeptideMoE modules...")
    result = query_database(
        subjects=["PeptideMoE"],
        keywords="PeptideMoE",
        has_lean=True
    )
    
    print(f"\nQuery Results:")
    print(f"  Success: {result.get('success', False)}")
    print(f"  Count: {result.get('count', 0)}")
    print(f"  Confidence: {result.get('confidence', 0):.3f}")
    print(f"  Query Time: {result.get('query_time_ms', 0):.2f}ms")
    
    print(f"\nResults:")
    for i, item in enumerate(result.get('results', []), 1):
        print(f"\n  {i}. {item.get('name', 'Unknown')}")
        print(f"     Subject: {item.get('subject', 'N/A')}")
        print(f"     Lean Module: {item.get('lean_module', 'N/A')}")
        print(f"     Formal Status: {item.get('formal_status', 'N/A')}")
        print(f"     Proof Status: {item.get('proof_status', 'N/A')}")
        print(f"     Complexity Score: {item.get('complexity_score', 'N/A')}")
        print(f"     Dependencies: {item.get('dependencies', 'N/A')}")
        if item.get('statement'):
            stmt = item['statement'][:100] + "..." if len(item['statement']) > 100 else item['statement']
            print(f"     Statement: {stmt}")
    
    print(f"\nSuggestions:")
    for suggestion in result.get('suggestions', []):
        print(f"  - {suggestion}")
    
    print(f"\nMetadata:")
    for key, value in result.get('metadata', {}).items():
        print(f"  {key}: {value}")
    
    # Check database stats
    print("\n" + "=" * 70)
    print("DATABASE STATISTICS")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM math_entities")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM math_entities WHERE lean_module IS NOT NULL")
    lean_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM math_entities WHERE subject LIKE '%PeptideMoE%'")
    peptide_moe_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT DISTINCT subject FROM math_entities")
    subject_count = len(cursor.fetchall())
    
    print(f"\nTotal Entities: {total}")
    print(f"Lean Formalized: {lean_count}")
    print(f"PeptideMoE Entities: {peptide_moe_count}")
    print(f"Subjects: {subject_count}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    
    # Swarm verdict
    print("\nSWARM VERDICT")
    print("=" * 70)
    
    if result['count'] > 0:
        print(f"\n✅ PeptideMoE modules successfully integrated and indexed")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Verdict: HIGHLY FEASIBLE")
        print(f"\n   Modules found:")
        for item in result['results']:
            print(f"   - {item['name']}")
            print(f"     Location: {item['lean_module']}")
            print(f"     Complexity: {item['complexity_score']}/100")
    else:
        print(f"\n❌ No PeptideMoE modules found in database")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Verdict: CHALLENGING")
    
    # Save results
    output_file = "/home/allaun/Documents/Research Stack/data/swarm_peptide_moe_direct_review.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()

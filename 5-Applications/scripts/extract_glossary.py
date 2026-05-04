#!/usr/bin/env python3
"""Extract glossary terms from GCL documentation."""

import re
import json
from pathlib import Path
from collections import defaultdict

GCL_DIR = Path("/home/allaun/Documents/Research Stack/0-Core-Formalism/otom/docs/gcl")

# Definition patterns
PATTERNS = [
    # **Term** is a/an/the ...
    re.compile(r'\*\*([^*]+)\*\*\s+is\s+(a|an|the)\s+([^\n]+)', re.IGNORECASE),
    # A **Term** is ...
    re.compile(r'(?:^|\n)(?:A|An|The)\s+\*\*([^*]+)\*\*\s+is\s+([^\n]+)', re.IGNORECASE),
    # Term := ...
    re.compile(r'\*\*([^*]+)\*\*\s*[:=]\s*([^\n]+)'),
    # ## Term
    # ...is...
    re.compile(r'#{2,4}\s+([A-Za-z][A-Za-z0-9_ ]+)\s*\n+([A-Za-z].*?is\s+[^\n]+)', re.DOTALL),
    # Canonical definition / Formal definition blocks
    re.compile(r'(?:canonical|formal)\s+definition\s*\n+\*\*([^*]+)\*\*\s*[:=]?\s*([^\n]+)', re.IGNORECASE),
    # "A **Term** is defined as..."
    re.compile(r'\*\*([^*]+)\*\*\s+(?:is\s+)?defined\s+as\s+([^\n]+)', re.IGNORECASE),
]

TERM_RE = re.compile(r'\*\*([^*]+)\*\*')

def extract_terms(filepath):
    """Extract (term, definition, source) tuples from a file."""
    results = []
    text = filepath.read_text(encoding='utf-8')
    
    for pattern in PATTERNS:
        for m in pattern.finditer(text):
            term = m.group(1).strip()
            definition = m.group(2 if len(m.groups()) >= 2 else 1).strip()
            # Clean up definition
            definition = re.sub(r'\*\*', '', definition)
            definition = definition[:200] + '...' if len(definition) > 200 else definition
            results.append({
                "term": term,
                "definition": definition,
                "source": filepath.name,
            })
    
    return results

def main():
    all_entries = []
    for filepath in sorted(GCL_DIR.glob("*.md")):
        entries = extract_terms(filepath)
        all_entries.extend(entries)
    
    # Deduplicate by term (keep shortest definition)
    by_term = defaultdict(list)
    for e in all_entries:
        by_term[e["term"]].append(e)
    
    glossary = []
    for term, entries in sorted(by_term.items()):
        # Pick the clearest definition (shortest non-trivial)
        best = min(entries, key=lambda e: len(e["definition"]) if len(e["definition"]) > 20 else 999)
        glossary.append({
            "term": term,
            "definition": best["definition"],
            "sources": list(set(e["source"] for e in entries)),
            "variants": len(entries),
        })
    
    # Output as markdown
    out_path = Path("/home/allaun/Documents/Research Stack/6-Documentation/docs/gcl/GLOSSARY.md")
    with open(out_path, "w") as f:
        f.write("# GCL Glossary\n\n")
        f.write("**Generated from:** `0-Core-Formalism/otom/docs/gcl/`\n\n")
        f.write(f"**Total terms:** {len(glossary)}\n\n")
        f.write("---\n\n")
        
        for entry in glossary:
            f.write(f"## {entry['term']}\n\n")
            f.write(f"{entry['definition']}\n\n")
            if len(entry["sources"]) > 1:
                f.write(f"*Sources: {', '.join(entry['sources'])}*\n\n")
            else:
                f.write(f"*Source: {entry['sources'][0]}*\n\n")
    
    # Also output JSON
    json_path = Path("/home/allaun/Documents/Research Stack/6-Documentation/docs/gcl/GLOSSARY.json")
    with open(json_path, "w") as f:
        json.dump({"terms": glossary}, f, indent=2)
    
    print(f"Wrote {len(glossary)} terms to:")
    print(f"  Markdown: {out_path}")
    print(f"  JSON:     {json_path}")

if __name__ == "__main__":
    main()

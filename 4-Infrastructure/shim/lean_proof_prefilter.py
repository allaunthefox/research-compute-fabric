#!/usr/bin/env python3
"""
Lean Proof Pre-Filter (copy-if pattern for compilation)

Inspired by vectorized copy_if (VPCOMPRESSD):
- Memory-destination compress = 144 microcode uops (processes everything)
- Register-destination compress + filter = 10-40x faster (skips zeros)

Applied to Lean compilation:
- `simp` processes ALL terms, even those in normal form (zero deltas)
- `native_decide` explores ALL branches, even trivially-false ones
- Pre-filter: identify which proof obligations are trivial vs non-trivial
- Skip trivial ones, concentrate solver on residuals

Usage:
  python3 lean_proof_prefilter.py <lean_file>
  python3 lean_proof_prefilter.py --scan <lean_dir>

Output: JSON with trivial/non-trivial classification per theorem.
"""

from __future__ import annotations
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


def extract_theorems(content: str) -> List[Dict]:
    """Extract theorem/lemma/def blocks from Lean source."""
    theorems = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        # Match theorem/lemma/def declarations
        m = re.match(
            r'^(theorem|lemma|def|instance|abbrev)\s+(\w+)',
            line
        )
        if m:
            kind = m.group(1)
            name = m.group(2)
            
            # Collect the full block (until next theorem or end of namespace)
            block_lines = [line]
            depth = line.count(':=') + line.count('by')
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if re.match(r'^(theorem|lemma|def|instance|abbrev|end |namespace )', next_line):
                    break
                block_lines.append(next_line)
                depth += next_line.count(':=') + next_line.count('by')
                i += 1
            
            block = '\n'.join(block_lines)
            theorems.append({
                'kind': kind,
                'name': name,
                'line': i - len(block_lines) + 1,
                'block': block,
                'depth': depth,
            })
        else:
            i += 1
    
    return theorems


def classify_theorem(thm: Dict) -> Dict:
    """Classify a theorem as trivial or non-trivial (copy-if predicate).
    
    Trivial = "zero delta" = already in normal form, solver can skip.
    Non-trivial = "non-zero delta" = needs solver attention.
    """
    block = thm['block']
    name = thm['name']
    
    # Trivial patterns (zero deltas — solver should skip)
    trivial_patterns = [
        # Pure rfl
        (r':=.*rfl$', 'rfl'),
        # Pure decide
        (r':=.*decide$', 'decide'),
        # Pure trivial
        (r':=.*trivial$', 'trivial'),
        # Type alias
        (r':=.*\w+$', 'alias'),
        # Simple constructor
        (r':=.*⟨.*⟩$', 'constructor'),
        # sorry with TODO (documented = acceptable)
        (r'sorry.*TODO', 'sorry_documented'),
        # #eval witness (not a proof, just a check)
        (r'#eval', 'eval_witness'),
    ]
    
    for pattern, category in trivial_patterns:
        if re.search(pattern, block, re.MULTILINE):
            return {
                **thm,
                'classification': 'trivial',
                'category': category,
                'reason': f'Matches trivial pattern: {category}',
            }
    
    # Non-trivial patterns (non-zero deltas — solver must process)
    nontrivial_indicators = [
        ('sorry', 'sorry_undocumented'),
        ('native_decide', 'native_decide'),
        ('omega', 'omega'),
        ('simp', 'simp'),
        ('norm_num', 'norm_num'),
        ('ring', 'ring'),
        ('linarith', 'linarith'),
        ('nlinarith', 'nlinarith'),
        ('apply?', 'apply_search'),
        ('exact?', 'exact_search'),
        ('aesop', 'aesop'),
        ('tauto', 'tauto'),
        ('decide', 'decide_tactic'),
    ]
    
    tactics_found = []
    for indicator, category in nontrivial_indicators:
        if indicator in block:
            tactics_found.append(category)
    
    if tactics_found:
        return {
            **thm,
            'classification': 'non_trivial',
            'category': ','.join(tactics_found),
            'reason': f'Uses tactics: {", ".join(tactics_found)}',
        }
    
    # Default: assume non-trivial (conservative)
    return {
        **thm,
        'classification': 'non_trivial',
        'category': 'unknown',
        'reason': 'No trivial pattern matched',
    }


def analyze_file(path: str) -> Dict:
    """Analyze a Lean file and classify all theorems."""
    content = Path(path).read_text()
    theorems = extract_theorems(content)
    
    classified = [classify_theorem(t) for t in theorems]
    
    trivial = [t for t in classified if t['classification'] == 'trivial']
    non_trivial = [t for t in classified if t['classification'] == 'non_trivial']
    
    return {
        'file': path,
        'total': len(classified),
        'trivial': len(trivial),
        'non_trivial': len(non_trivial),
        'skip_ratio': len(trivial) / max(len(classified), 1),
        'theorems': classified,
    }


def lean_build_prefilter(lean_dir: str) -> Dict:
    """Pre-filter Lean build: identify which modules need full compilation.
    
    Modules with only trivial theorems can use fast-path (skip simp/decide).
    Modules with non-trivial theorems need full solver.
    
    This is the copy-if pattern: filter out zero-delta modules, then
    concentrate the solver on the non-zero residuals.
    """
    results = []
    lean_path = Path(lean_dir)
    
    for lean_file in sorted(lean_path.rglob('*.lean')):
        if '.lake' in str(lean_file):
            continue
        try:
            analysis = analyze_file(str(lean_file))
            results.append(analysis)
        except Exception as e:
            results.append({
                'file': str(lean_file),
                'error': str(e),
            })
    
    # Aggregate stats
    total_thms = sum(r.get('total', 0) for r in results)
    total_trivial = sum(r.get('trivial', 0) for r in results)
    total_nontrivial = sum(r.get('non_trivial', 0) for r in results)
    
    # Sort by non-trivial count (highest first = most solver work needed)
    results.sort(key=lambda r: r.get('non_trivial', 0), reverse=True)
    
    return {
        'summary': {
            'files': len(results),
            'total_theorems': total_thms,
            'trivial': total_trivial,
            'non_trivial': total_nontrivial,
            'skip_ratio': total_trivial / max(total_thms, 1),
            'estimated_speedup': f"{total_thms / max(total_nontrivial, 1):.1f}x",
        },
        'top_10_heaviest': [
            {
                'file': r['file'],
                'non_trivial': r.get('non_trivial', 0),
                'trivial': r.get('trivial', 0),
                'skip_ratio': r.get('skip_ratio', 0),
            }
            for r in results[:10]
        ],
        'files': results,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: lean_proof_prefilter.py <lean_file>")
        print("       lean_proof_prefilter.py --scan <lean_dir>")
        sys.exit(1)
    
    if sys.argv[1] == '--scan':
        lean_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
        result = lean_build_prefilter(lean_dir)
        print(json.dumps(result['summary'], indent=2))
        print("\nTop 10 heaviest modules:")
        for r in result['top_10_heaviest']:
            print(f"  {r['file']}: {r['non_trivial']} non-trivial, {r['trivial']} trivial ({r['skip_ratio']:.0%} skip)")
    else:
        result = analyze_file(sys.argv[1])
        print(json.dumps({
            'file': result['file'],
            'total': result['total'],
            'trivial': result['trivial'],
            'non_trivial': result['non_trivial'],
            'skip_ratio': f"{result['skip_ratio']:.0%}",
        }, indent=2))
        print("\nNon-trivial theorems:")
        for t in result['theorems']:
            if t['classification'] == 'non_trivial':
                print(f"  L{t['line']}: {t['name']} ({t['category']})")


if __name__ == '__main__':
    main()

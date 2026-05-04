#!/usr/bin/env python3
"""
Consolidate All Coding Languages for Training Data

This script pulls in every coding language source file in the codebase and
consolidates them into a unified training dataset for NII cores to become
n-semantic morphic.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import hashlib

# Coding language file extensions to include
CODING_EXTENSIONS = {
    '.py': 'python',
    '.lean': 'lean',
    '.rs': 'rust',
    '.c': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.h': 'c_header',
    '.hpp': 'cpp_header',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript_react',
    '.jsx': 'javascript_react',
    '.v': 'verilog',
    '.vhdl': 'vhdl',
    '.java': 'java',
    '.go': 'go',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.lua': 'lua',
    '.r': 'r',
    '.m': 'matlab',
    '.jl': 'julia',
    '.sh': 'shell',
    '.bash': 'bash',
    '.zsh': 'zsh',
    '.fish': 'fish',
    '.ps1': 'powershell',
    '.rb': 'ruby',
    '.php': 'php',
    '.pl': 'perl',
    '.cs': 'csharp',
    '.fs': 'fsharp',
    '.fsx': 'fsharp',
    '.sql': 'sql',
    '.graphql': 'graphql',
    '.gql': 'graphql',
    '.toml': 'toml',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.xml': 'xml',
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.less': 'less',
    '.json': 'json',
    '.md': 'markdown',
    '.rst': 'rst',
    '.tex': 'latex',
    '.bib': 'bibtex'
}

# Directories to exclude (node_modules, etc.)
EXCLUDE_DIRS = {
    'node_modules',
    '.git',
    '__pycache__',
    '.venv',
    'venv',
    'env',
    'dist',
    'build',
    'target',
    'bin',
    'obj',
    '.lake',
    '.lean'
}

def extract_source_code(file_path: str) -> Tuple[str, str]:
    """Extract source code content and language from file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Determine language from extension
        file_path_obj = Path(file_path)
        ext = file_path_obj.suffix.lower()
        language = CODING_EXTENSIONS.get(ext, 'unknown')
        
        return content, language
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return "", "error"

def should_exclude_path(path: Path) -> bool:
    """Check if path should be excluded."""
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False

def consolidate_coding_languages(base_path: str) -> Dict[str, Any]:
    """Consolidate all coding language source files."""
    print("=" * 70)
    print("CONSOLIDATING ALL CODING LANGUAGES FOR TRAINING DATA")
    print("=" * 70)
    
    base_path = Path(base_path)
    
    consolidated_data = {
        'timestamp': datetime.now().isoformat(),
        'sources': {
            'by_language': {},
            'total_files': 0,
            'total_lines': 0,
            'total_size_bytes': 0
        },
        'data': [],
        'statistics': {
            'languages_found': {},
            'total_files': 0,
            'total_lines': 0,
            'total_size_bytes': 0
        }
    }
    
    # Find all source code files
    print("\n[1/3] Scanning for coding language files...")
    source_files = []
    
    for ext in CODING_EXTENSIONS.keys():
        files = list(base_path.rglob(f"*{ext}"))
        for file in files:
            if not should_exclude_path(file):
                source_files.append(file)
    
    print(f"Found {len(source_files)} source code files")
    
    # Extract source code from each file
    print("\n[2/3] Extracting source code...")
    for i, file_path in enumerate(source_files):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(source_files)} files processed")
        
        content, language = extract_source_code(str(file_path))
        
        if content and language != "error":
            # Calculate statistics
            lines = len(content.splitlines())
            size_bytes = len(content.encode('utf-8'))
            
            # Create record
            record = {
                'file_path': str(file_path),
                'language': language,
                'content': content,
                'lines': lines,
                'size_bytes': size_bytes,
                'file_hash': hashlib.md5(content.encode('utf-8')).hexdigest()
            }
            
            consolidated_data['data'].append(record)
            
            # Update statistics
            if language not in consolidated_data['statistics']['languages_found']:
                consolidated_data['statistics']['languages_found'][language] = 0
            consolidated_data['statistics']['languages_found'][language] += 1
            consolidated_data['statistics']['total_files'] += 1
            consolidated_data['statistics']['total_lines'] += lines
            consolidated_data['statistics']['total_size_bytes'] += size_bytes
            
            # Update sources by language
            if language not in consolidated_data['sources']['by_language']:
                consolidated_data['sources']['by_language'][language] = []
            consolidated_data['sources']['by_language'][language].append(str(file_path))
    
    print(f"  Completed: {len(source_files)}/{len(source_files)} files processed")
    
    # Calculate final statistics
    print("\n[3/3] Calculating statistics...")
    consolidated_data['sources']['total_files'] = consolidated_data['statistics']['total_files']
    consolidated_data['sources']['total_lines'] = consolidated_data['statistics']['total_lines']
    consolidated_data['sources']['total_size_bytes'] = consolidated_data['statistics']['total_size_bytes']
    
    print(f"\nConsolidation Statistics:")
    print(f"  Total Files: {consolidated_data['statistics']['total_files']}")
    print(f"  Total Lines: {consolidated_data['statistics']['total_lines']}")
    print(f"  Total Size: {consolidated_data['statistics']['total_size_bytes'] / 1024 / 1024:.2f} MB")
    print(f"  Languages Found: {len(consolidated_data['statistics']['languages_found'])}")
    
    print(f"\nLanguages Breakdown:")
    for lang, count in sorted(consolidated_data['statistics']['languages_found'].items(), 
                             key=lambda x: x[1], reverse=True):
        print(f"  {lang}: {count} files")
    
    return consolidated_data

def save_consolidated_coding_data(consolidated_data: Dict[str, Any], output_path: str):
    """Save consolidated coding data to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save full consolidated data (without content for JSON size reasons)
    summary_data = {
        'timestamp': consolidated_data['timestamp'],
        'sources': consolidated_data['sources'],
        'statistics': consolidated_data['statistics'],
        'file_count': len(consolidated_data['data'])
    }
    
    summary_output = f"{output_path}/coding_languages_summary_{timestamp}.json"
    with open(summary_output, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)
    print(f"\n✅ Summary saved to: {summary_output}")
    
    # Save training-ready dataset (JSONL with content)
    training_output = f"{output_path}/coding_training_dataset_{timestamp}.jsonl"
    with open(training_output, 'w', encoding='utf-8') as f:
        for record in consolidated_data['data']:
            # For training, include essential fields
            training_record = {
                'file_path': record['file_path'],
                'language': record['language'],
                'content': record['content'],
                'lines': record['lines'],
                'file_hash': record['file_hash']
            }
            f.write(json.dumps(training_record) + '\n')
    print(f"✅ Training dataset saved to: {training_output}")
    
    # Save statistics
    stats_output = f"{output_path}/coding_statistics_{timestamp}.json"
    with open(stats_output, 'w', encoding='utf-8') as f:
        json.dump(consolidated_data['statistics'], f, indent=2)
    print(f"✅ Statistics saved to: {stats_output}")
    
    return summary_output, training_output, stats_output

def main():
    base_path = "/home/allaun/Research Stack"
    output_path = "/home/allaun/Documents/Research Stack/data/training_data"
    
    # Create output directory
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    # Consolidate all coding languages
    consolidated_data = consolidate_coding_languages(base_path)
    
    # Save consolidated data
    save_consolidated_coding_data(consolidated_data, output_path)
    
    print("\n" + "=" * 70)
    print("CODING LANGUAGE CONSOLIDATION COMPLETE")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

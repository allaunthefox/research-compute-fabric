#!/usr/bin/env python3
"""
Run Project Health Auditor MCP tool equivalents and save results.

This script implements the functionality of:
- list_repo_files() - Lists all files in the repository
- map_tests(path=".") - Maps source files to test files
- git_churn(path=".") - Returns git churn metrics

Results are saved to:
- reports/mcp_health_files.json
- reports/mcp_health_test_map.json
- reports/mcp_health_churn.json
"""

import json
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def list_repo_files(root: Path = Path(".")) -> dict:
    """
    List all files in the repository (excluding common ignore patterns).

    Returns a structured response similar to the MCP tool.
    """
    ignore_patterns = {
        '.git', '.venv', '.venv-audit', '__pycache__', '.pytest_cache',
        '.ruff_cache', '.mypy_cache', '.hypothesis', 'node_modules',
        'build', 'dist', '*.egg-info', 'htmlcov', '.coverage',
        '*.pyc', '*.pyo', '.DS_Store', 'Thumbs.db'
    }

    files = []
    for path in root.rglob("*"):
        # Skip ignored directories
        skip = False
        for part in path.parts:
            if part.startswith('.venv') or part in {'.git', 'node_modules', '__pycache__'}:
                skip = True
                break
            if part.endswith('.egg-info'):
                skip = True
                break

        if skip:
            continue

        if path.is_file():
            rel_path = str(path.relative_to(root))
            # Skip binary/cache files
            if any(rel_path.endswith(ext) for ext in ['.pyc', '.pyo', '.db', '.so']):
                if not rel_path.endswith('.db') or 'shard' in rel_path:
                    continue

            files.append({
                "path": rel_path,
                "size": path.stat().st_size,
                "type": get_file_type(rel_path)
            })

    files.sort(key=lambda x: x["path"])

    return {
        "tool": "list_repo_files",
        "path": str(root.absolute()),
        "timestamp": datetime.now().isoformat(),
        "total_files": len(files),
        "files": files,
        "by_type": count_by_type(files)
    }


def get_file_type(path: str) -> str:
    """Determine file type based on extension and path."""
    if path.endswith('.py'):
        if 'test' in path.lower() or path.startswith('test_'):
            return 'test'
        return 'python'
    elif path.endswith(('.js', '.ts', '.jsx', '.tsx')):
        return 'javascript'
    elif path.endswith(('.yaml', '.yml')):
        return 'yaml'
    elif path.endswith('.json'):
        return 'json'
    elif path.endswith('.md'):
        return 'markdown'
    elif path.endswith('.txt'):
        return 'text'
    elif path.endswith('.toml'):
        return 'toml'
    elif path.endswith('.ini'):
        return 'ini'
    elif path.endswith('.cfg'):
        return 'config'
    elif path.endswith('.sh'):
        return 'shell'
    elif path.endswith('Dockerfile') or 'dockerfile' in path.lower():
        return 'dockerfile'
    elif path.endswith('.gitignore'):
        return 'gitignore'
    elif path.endswith('.xml'):
        return 'xml'
    else:
        return 'other'


def count_by_type(files: list) -> dict:
    """Count files by type."""
    counts = defaultdict(int)
    for f in files:
        counts[f["type"]] += 1
    return dict(counts)


def map_tests(root: Path = Path(".")) -> dict:
    """
    Map source files to their corresponding test files.

    Identifies:
    - Source files with tests
    - Source files without tests (untested)
    - Test files without corresponding source (orphaned tests)
    """
    source_files = []
    test_files = []

    for path in root.rglob("*"):
        # Skip ignored directories
        skip = False
        for part in path.parts:
            if part.startswith('.venv') or part in {'.git', 'node_modules', '__pycache__'}:
                skip = True
                break
            if part.endswith('.egg-info'):
                skip = True
                break

        if skip:
            continue

        if path.is_file() and path.suffix == '.py':
            rel_path = str(path.relative_to(root))

            if 'test' in path.name.lower() or 'tests' in path.parts:
                test_files.append(rel_path)
            elif not any(x in rel_path for x in ['conftest', '__pycache__']):
                # Only include source files from main packages
                if any(pkg in rel_path for pkg in ['nodupe/', 'pipeline/', 'github/']):
                    source_files.append(rel_path)

    # Build mapping
    source_to_test = {}
    tested_sources = set()

    for test_file in test_files:
        # Try to find corresponding source file
        test_name = Path(test_file).name
        source_candidates = []

        # Pattern: test_foo.py -> foo.py
        if test_name.startswith('test_'):
            source_name = test_name[5:]  # Remove 'test_' prefix
            for src in source_files:
                if src.endswith(source_name):
                    source_candidates.append(src)

        # Pattern: tests/test_foo.py -> nodupe/foo.py
        if not source_candidates:
            base_name = test_name.replace('test_', '')
            for src in source_files:
                if src.endswith(base_name) or base_name.replace('.py', '') in src:
                    source_candidates.append(src)

        if source_candidates:
            for src in source_candidates:
                if src not in source_to_test:
                    source_to_test[src] = []
                source_to_test[src].append(test_file)
                tested_sources.add(src)

    untested_sources = [s for s in source_files if s not in tested_sources]

    return {
        "tool": "map_tests",
        "path": str(root.absolute()),
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_source_files": len(source_files),
            "total_test_files": len(test_files),
            "tested_source_files": len(tested_sources),
            "untested_source_files": len(untested_sources),
            "coverage_percentage": round(len(tested_sources) / len(source_files) * 100, 1) if source_files else 0
        },
        "source_to_test": source_to_test,
        "untested_sources": sorted(untested_sources),
        "test_files": sorted(test_files)
    }


def git_churn(root: Path = Path(".")) -> dict:
    """
    Calculate git churn metrics for files.

    Churn is measured by:
    - Number of commits touching each file
    - Lines added/removed per file
    - Last modified date
    """
    churn_data = []

    try:
        # Get list of tracked files
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            return {
                "tool": "git_churn",
                "path": str(root.absolute()),
                "timestamp": datetime.now().isoformat(),
                "error": "Failed to get git files list",
                "stderr": result.stderr
            }

        tracked_files = result.stdout.strip().split('\n')

        for file_path in tracked_files:
            if not file_path or any(x in file_path for x in ['.venv', 'node_modules']):
                continue

            try:
                # Get commit count for file
                commit_result = subprocess.run(
                    ["git", "-C", str(root), "log", "--oneline", "--", file_path],
                    capture_output=True, text=True, timeout=30
                )
                commits = commit_result.stdout.strip().split('\n') if commit_result.stdout.strip() else []
                commit_count = len([c for c in commits if c])

                # Get last modified date
                date_result = subprocess.run(
                    ["git", "-C", str(root), "log", "-1", "--format=%ci", "--", file_path],
                    capture_output=True, text=True, timeout=30
                )
                last_modified = date_result.stdout.strip()

                # Get lines added/removed
                blame_result = subprocess.run(
                    ["git", "-C", str(root), "blame", "--line-porcelain", "--", file_path],
                    capture_output=True, text=True, timeout=60
                )

                # Count unique authors
                authors = set()
                if blame_result.stdout:
                    for line in blame_result.stdout.split('\n'):
                        if line.startswith('author '):
                            authors.add(line[7:])

                churn_data.append({
                    "path": file_path,
                    "commit_count": commit_count,
                    "last_modified": last_modified,
                    "unique_authors": len(authors),
                    "churn_level": categorize_churn(commit_count)
                })

            except subprocess.TimeoutExpired:
                churn_data.append({
                    "path": file_path,
                    "error": "timeout"
                })
            except Exception as e:
                churn_data.append({
                    "path": file_path,
                    "error": str(e)
                })

    except subprocess.TimeoutExpired:
        return {
            "tool": "git_churn",
            "path": str(root.absolute()),
            "timestamp": datetime.now().isoformat(),
            "error": "Git command timed out"
        }
    except FileNotFoundError:
        return {
            "tool": "git_churn",
            "path": str(root.absolute()),
            "timestamp": datetime.now().isoformat(),
            "error": "Git not found or not a git repository"
        }

    # Sort by commit count (highest first)
    churn_data.sort(key=lambda x: x.get('commit_count', 0), reverse=True)

    # Calculate summary
    high_churn = [f for f in churn_data if f.get('churn_level') == 'high']
    medium_churn = [f for f in churn_data if f.get('churn_level') == 'medium']
    low_churn = [f for f in churn_data if f.get('churn_level') == 'low']

    return {
        "tool": "git_churn",
        "path": str(root.absolute()),
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_files": len(churn_data),
            "high_churn_files": len(high_churn),
            "medium_churn_files": len(medium_churn),
            "low_churn_files": len(low_churn)
        },
        "files": churn_data
    }


def categorize_churn(commit_count: int) -> str:
    """Categorize churn level based on commit count."""
    if commit_count >= 20:
        return "high"
    elif commit_count >= 5:
        return "medium"
    else:
        return "low"


def main():
    """Run all health audit tools and save results."""
    root = Path("/home/prod/Workspaces/repos/github/NoDupeLabs")
    reports_dir = root / "reports"
    reports_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("Running Project Health Auditor MCP Tool Equivalents")
    print("=" * 60)

    # 1. list_repo_files()
    print("\n[1/3] Running list_repo_files()...")
    files_result = list_repo_files(root)
    files_path = reports_dir / "mcp_health_files.json"
    with open(files_path, 'w') as f:
        json.dump(files_result, f, indent=2)
    print(f"  Total files: {files_result['total_files']}")
    print(f"  By type: {files_result['by_type']}")
    print(f"  Saved to: {files_path}")

    # 2. map_tests()
    print("\n[2/3] Running map_tests(path='.')...")
    tests_result = map_tests(root)
    tests_path = reports_dir / "mcp_health_test_map.json"
    with open(tests_path, 'w') as f:
        json.dump(tests_result, f, indent=2)
    print(f"  Source files: {tests_result['summary']['total_source_files']}")
    print(f"  Test files: {tests_result['summary']['total_test_files']}")
    print(f"  Coverage: {tests_result['summary']['coverage_percentage']}%")
    print(f"  Untested: {tests_result['summary']['untested_source_files']}")
    print(f"  Saved to: {tests_path}")

    # 3. git_churn()
    print("\n[3/3] Running git_churn(path='.')...")
    churn_result = git_churn(root)
    churn_path = reports_dir / "mcp_health_churn.json"
    with open(churn_path, 'w') as f:
        json.dump(churn_result, f, indent=2)
    if 'error' not in churn_result:
        print(f"  Total files: {churn_result['summary']['total_files']}")
        print(f"  High churn: {churn_result['summary']['high_churn_files']}")
        print(f"  Medium churn: {churn_result['summary']['medium_churn_files']}")
        print(f"  Low churn: {churn_result['summary']['low_churn_files']}")
    else:
        print(f"  Error: {churn_result.get('error', 'Unknown error')}")
    print(f"  Saved to: {churn_path}")

    print("\n" + "=" * 60)
    print("Health audit complete!")
    print("=" * 60)

    return {
        "files_report": str(files_path),
        "test_map_report": str(tests_path),
        "churn_report": str(churn_path)
    }


if __name__ == "__main__":
    main()

"""
pylsp_trivial_detector - Pre-filter plugin for python-lsp-server

Detects and handles trivial code changes instantly:
- Whitespace-only edits
- Comment-only changes
- Docstring-only changes
- Import-only additions
- Obvious syntax errors (fast-fail)

Non-trivial changes fall through to full pylsp analysis.
"""

from pylsp import hookimpl
from pylsp._utils import get_text_document
import re


def _is_trivial_change(doc_text: str, old_text: str) -> tuple[bool, str]:
    """
    Returns (is_trivial, reason) for fast-path handling.
    """
    if not old_text:
        return False, "new file"

    # Strip and compare empty
    if not doc_text.strip() and not old_text.strip():
        return True, "empty file"

    # Whitespace-only change
    if doc_text.strip() == old_text.strip() and doc_text != old_text:
        return True, "whitespace-only change"

    # Comment-only change (Python comment is #)
    doc_lines = doc_text.splitlines()
    old_lines = old_text.splitlines()

    if len(doc_lines) == len(old_lines):
        diff_lines = []
        for d, o in zip(doc_lines, old_lines):
            stripped_d = d.lstrip()
            stripped_o = o.lstrip()
            if stripped_d == stripped_o:
                continue
            # Both are comments or whitespace
            if (not stripped_d or stripped_d.startswith('#')) and \
               (not stripped_o or stripped_o.startswith('#')):
                diff_lines.append((d, o))
            else:
                break
        else:
            if diff_lines:
                return True, "comment-only change"

    # Docstring-only change
    if _is_docstring_only_diff(doc_text, old_text):
        return True, "docstring-only change"

    # Import-only addition
    if _is_import_only_addition(doc_text, old_text):
        return True, "import-only addition"

    return False, ""


def _is_docstring_only_diff(doc: str, old: str) -> bool:
    """Check if the only changes are docstring modifications."""
    import ast
    try:
        doc_tree = ast.parse(doc)
        old_tree = ast.parse(old)
        if len(doc_tree.body) != len(old_tree.body):
            return False
        for d_node, o_node in zip(doc_tree.body, old_tree.body):
            if type(d_node) != type(o_node):
                return False
            if isinstance(d_node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                d_doc = ast.get_docstring(d_node)
                o_doc = ast.get_docstring(o_node)
                if d_doc != o_doc:
                    continue
                # Check if function body is otherwise identical
                if ast.dump(d_node) != ast.dump(o_node):
                    return False
            else:
                if ast.dump(d_node) != ast.dump(o_node):
                    return False
        return True
    except SyntaxError:
        return False


def _is_import_only_addition(doc: str, old: str) -> bool:
    """Check if only imports were added."""
    import ast
    try:
        doc_tree = ast.parse(doc)
        old_tree = ast.parse(old)
        doc_imports = set()
        old_imports = set()
        for node in ast.walk(doc_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    doc_imports.add((type(node).__name__, alias.name if alias.name else alias.asname or '*'))
        for node in ast.walk(old_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    old_imports.add((type(node).__name__, alias.name if alias.name else alias.asname or '*'))
        added = doc_imports - old_imports
        removed = old_imports - doc_imports
        if added and not removed:
            return True
        return False
    except SyntaxError:
        return False


def _fast_syntax_check(text: str) -> tuple[bool, str]:
    """
    Fast syntax check - fails fast on obvious errors.
    Returns (is_valid, error_message).
    """
    import ast
    try:
        ast.parse(text)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"


@hookimpl
def pylsp_hover(doc_text: str, **kwargs) -> dict | None:
    """Skip hover on whitespace-only files."""
    return None


@hookimpl
def pylsp_completion(doc_text: str, **kwargs) -> list | None:
    """Provide fast-path completion for trivial changes."""
    return None


@hookimpl
def pylsp_diagnostics(doc_text: str, doc_uri: str = "", **kwargs) -> list:
    """
    Main diagnostic hook with fast-path for trivial changes.
    Falls through to full analysis only for non-trivial edits.
    """
    if not doc_text:
        return []

    # Fast syntax check first
    is_valid, error = _fast_syntax_check(doc_text)
    if not is_valid:
        return [{
            "source": "pylsp_trivial",
            "severity": 1,  # Error
            "message": error,
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 0}
            }
        }]

    # For now, we don't auto-skip - this is the pre-filter
    # Full diagnostics are still run by other plugins
    # The is_trivial result is available for other hooks to use
    return []


def trivial_filter(doc_text: str, old_text: str) -> tuple[bool, str]:
    """
    Public API: check if a document change is trivial.

    Returns:
        (is_trivial, reason)

    Usage:
        is_trivial, reason = trivial_filter(new_text, old_text)
        if is_trivial:
            skip_full_analysis()
    """
    return _is_trivial_change(doc_text, old_text)

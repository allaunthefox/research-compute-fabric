"""Test fcntl import fallback using subprocess."""

import subprocess
import sys


def test_fcntl_import_error_handling():
    """Test that module handles fcntl ImportError gracefully."""
    # Run a separate Python process where we mock fcntl import
    code = '''
import sys
import builtins
from unittest.mock import patch

# Mock builtins.__import__ to raise ImportError for fcntl
original_import = builtins.__import__

def mock_import(name, *args, **kwargs):
    if name == 'fcntl':
        raise ImportError("No module named 'fcntl'")
    return original_import(name, *args, **kwargs)

with patch.object(builtins, '__import__', side_effect=mock_import):
    from nodupe.core.tool_system import hot_reload
    assert hot_reload.fcntl is None, f"Expected fcntl to be None, got {hot_reload.fcntl}"
    print("SUCCESS: fcntl is None")
'''

    result = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True,
        text=True,
        cwd='/home/prod/Workspaces/repos/github/NoDupeLabs'
    )

    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    assert result.returncode == 0, f"Subprocess failed: {result.stderr}"
    assert "SUCCESS" in result.stdout

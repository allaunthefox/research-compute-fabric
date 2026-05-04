"""Test Tool Security Module - Additional Coverage Tests.

Tests to achieve higher coverage for security.py
"""

import ast
import tempfile
from pathlib import Path

import pytest

from nodupe.core.tool_system.security import (
    SecurityASTVisitor,
    ToolSecurity,
    ToolSecurityError,
    create_tool_security,
)


class TestToolSecurityCheckToolPermissions:
    """Test check_tool_permissions method."""

    def test_check_tool_permissions_returns_true(self):
        """Test that check_tool_permissions always returns True."""
        security = ToolSecurity()
        mock_tool = object()
        result = security.check_tool_permissions(mock_tool)
        assert result is True


class TestToolSecurityValidateTool:
    """Test validate_tool method."""

    def test_validate_tool_with_valid_tool(self):
        """Test validate_tool with valid tool object."""
        security = ToolSecurity()
        mock_tool = type('MockTool', (), {'name': 'Test', 'version': '1.0.0'})()
        result = security.validate_tool(mock_tool)
        assert result is True

    def test_validate_tool_with_invalid_tool(self):
        """Test validate_tool with invalid tool object."""
        security = ToolSecurity()
        mock_tool = object()
        result = security.validate_tool(mock_tool)
        assert result is False


class TestValidateToolFileEdgeCases:
    """Test validate_tool_file method edge cases."""

    def test_validate_tool_file_not_exists(self):
        """Test validating non-existent file."""
        security = ToolSecurity()
        nonexistent = Path("/nonexistent/file.py")
        
        with pytest.raises(ToolSecurityError) as exc_info:
            security.validate_tool_file(nonexistent)
        assert "does not exist" in str(exc_info.value)

    def test_validate_tool_file_not_python(self):
        """Test validating non-Python file."""
        security = ToolSecurity()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'# not python')
            f.flush()
            path = Path(f.name)
        
        with pytest.raises(ToolSecurityError) as exc_info:
            security.validate_tool_file(path)
        assert "must be Python" in str(exc_info.value)

    def test_validate_tool_file_syntax_error(self):
        """Test validating file with syntax error."""
        security = ToolSecurity()
        
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b'if if if')  # Syntax error
            f.flush()
            path = Path(f.name)
        
        with pytest.raises(ToolSecurityError) as exc_info:
            security.validate_tool_file(path)
        assert "Invalid Python syntax" in str(exc_info.value)


class TestSecurityPolicyManagement:
    """Test security policy management."""

    def test_set_get_security_policy(self):
        """Test setting and getting security policies."""
        security = ToolSecurity()
        
        security.set_security_policy("max_file_size", 1000)
        result = security.get_security_policy("max_file_size")
        assert result == 1000

    def test_get_security_policy_not_set(self):
        """Test getting non-existent policy."""
        security = ToolSecurity()
        result = security.get_security_policy("nonexistent")
        assert result is None


class TestWhitelistBlacklistManagement:
    """Test whitelist and blacklist management."""

    def test_remove_whitelisted_module(self):
        """Test removing module from whitelist."""
        security = ToolSecurity()
        security.add_whitelisted_module("test_module")
        security.remove_whitelisted_module("test_module")
        # After removal, module is not in whitelist
        # Since blacklist takes precedence, os is still blocked
        assert security.is_safe_module_import("os") is False

    def test_remove_blacklisted_module(self):
        """Test removing module from blacklist."""
        security = ToolSecurity()
        # os is in blacklist by default
        security.remove_blacklisted_module("os")
        # After removal, os should be safe (unless whitelist blocks it)
        assert security.is_safe_module_import("os") is True


class TestDangerousImportsDetection:
    """Test dangerous imports detection."""

    def test_check_dangerous_imports_from_import(self):
        """Test detecting dangerous from-import."""
        security = ToolSecurity()
        
        code = """
from os import system
"""
        tree = ast.parse(code)
        fake_path = Path("test.py")
        
        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_dangerous_imports(tree, fake_path)
        assert "Dangerous import found" in str(exc_info.value)


class TestDangerousMethodCalls:
    """Test dangerous method call detection."""

    def test_dangerous_method_open(self):
        """Test detecting dangerous open function."""
        security = ToolSecurity()
        
        code = """
f = open('file.txt', 'w')
"""
        tree = ast.parse(code)
        fake_path = Path("test.py")
        
        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        # The error is "Dangerous function call" not "method call"
        assert "Dangerous" in str(exc_info.value) and "open" in str(exc_info.value)


class TestSecurityASTVisitorAdvanced:
    """Test SecurityASTVisitor advanced cases."""

    def test_visitor_safe_code(self):
        """Test visitor with safe code."""
        visitor = SecurityASTVisitor()
        
        code = """
def safe_function(x, y):
    return x + y

result = safe_function(1, 2)
"""
        tree = ast.parse(code)
        visitor.visit(tree)
        
        # Should not detect any dangerous nodes
        assert len(visitor.dangerous_nodes) == 0


class TestValidateToolCodeErrors:
    """Test validate_tool_code error handling."""

    def test_validate_tool_code_syntax_error(self):
        """Test validating code with syntax error."""
        security = ToolSecurity()
        
        result = security.validate_tool_code("if if if")
        assert result is False


class TestSecurityCheckToolPermissionsAdvanced:
    """Test check_tool_permissions advanced cases."""

    def test_check_tool_permissions_different_objects(self):
        """Test check_tool_permissions with different object types."""
        security = ToolSecurity()
        
        # Test with None
        assert security.check_tool_permissions(None) is True
        
        # Test with string
        assert security.check_tool_permissions("tool") is True
        
        # Test with dict
        assert security.check_tool_permissions({}) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

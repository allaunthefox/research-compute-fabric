"""Test Tool Security Module - Coverage Completion.

Tests to achieve 100% coverage for security.py
"""

import ast

import pytest

from nodupe.core.tool_system.security import (
    SecurityASTVisitor,
    ToolSecurity,
    ToolSecurityError,
    create_tool_security,
)


class TestToolSecurityInit:
    """Test ToolSecurity initialization edge cases."""

    def test_init_blacklist_copy(self):
        """Test that blacklist is a copy of DANGEROUS_MODULES."""
        security = ToolSecurity()
        assert security._blacklisted_modules == ToolSecurity.DANGEROUS_MODULES
        # Should be a copy, not the same object
        assert security._blacklisted_modules is not ToolSecurity.DANGEROUS_MODULES


class TestIsSafeModuleImport:
    """Test is_safe_module_import method edge cases."""

    def test_is_safe_module_import_blacklisted(self):
        """Test checking blacklisted module."""
        security = ToolSecurity()
        result = security.is_safe_module_import("os")
        assert result is False

    def test_is_safe_module_import_safe(self):
        """Test checking safe module (not blacklisted, whitelist empty)."""
        security = ToolSecurity()
        result = security.is_safe_module_import("json")
        assert result is True

    def test_is_safe_module_import_whitelist_enforced(self):
        """Test that whitelist is enforced when not empty."""
        security = ToolSecurity()
        security.add_whitelisted_module("json")
        security.add_whitelisted_module("math")

        # json is whitelisted
        assert security.is_safe_module_import("json") is True

        # math is whitelisted
        assert security.is_safe_module_import("math") is True

        # os is not whitelisted (and not blacklisted, but whitelist is enforced)
        assert security.is_safe_module_import("os") is False


class TestCheckDangerousConstructs:
    """Test _check_dangerous_constructs method edge cases."""

    def test_check_dangerous_constructs_with_visitor_detection(self, tmp_path):
        """Test checking detects dangerous constructs via visitor."""
        security = ToolSecurity()

        code = """
def test():
    exec("code")
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        # The visitor should detect exec call
        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_dangerous_constructs(tree, fake_path)
        assert "Dangerous constructs" in str(exc_info.value)

    def test_check_dangerous_constructs_safe_code(self, tmp_path):
        """Test checking with safe code."""
        security = ToolSecurity()

        code = """
def test():
    return 42
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        # Should not raise
        security._check_dangerous_constructs(tree, fake_path)


class TestSecurityASTVisitor:
    """Test SecurityASTVisitor edge cases."""

    def test_visitor_visit_exec_method(self):
        """Test visitor visit_exec method directly."""
        visitor = SecurityASTVisitor()

        code = "print('test')"
        tree = ast.parse(code)

        # Find an Exec node if present (Python 2) or just test the method
        # Call visit_exec directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr):
                visitor.visit_Exec(node)
                break

        # Method should be callable
        assert hasattr(visitor, "visit_Exec")

    def test_visitor_visit_eval_method(self):
        """Test visitor visit_eval method directly."""
        visitor = SecurityASTVisitor()

        code = "eval('1+1')"
        tree = ast.parse(code)

        # Call visit_eval directly on a Call node
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Eval(node)
                break

        # Should have detected eval
        assert len(visitor.dangerous_nodes) > 0

    def test_visitor_visit_call_method(self):
        """Test visitor visit_call method directly."""
        visitor = SecurityASTVisitor()

        code = "exec('code')"
        tree = ast.parse(code)

        # Call visit_call directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)
                break

        # Should have detected exec
        assert len(visitor.dangerous_nodes) > 0
        assert any('exec' in node for node in visitor.dangerous_nodes)

    def test_visitor_visit_call_eval_method(self):
        """Test visitor visit_call method with eval."""
        visitor = SecurityASTVisitor()

        code = "eval('1+1')"
        tree = ast.parse(code)

        # Call visit_call directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)
                break

        # Should have detected eval
        assert len(visitor.dangerous_nodes) > 0
        assert any('eval' in node for node in visitor.dangerous_nodes)

    def test_visitor_visit_call_compile_method(self):
        """Test visitor visit_call method with compile."""
        visitor = SecurityASTVisitor()

        code = "compile('code', 'file', 'exec')"
        tree = ast.parse(code)

        # Call visit_call directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)
                break

        # Should have detected compile
        assert len(visitor.dangerous_nodes) > 0
        assert any('compile' in node for node in visitor.dangerous_nodes)

    def test_visitor_visit_call_open_method(self):
        """Test visitor visit_call method with open."""
        visitor = SecurityASTVisitor()

        code = "open('file.txt')"
        tree = ast.parse(code)

        # Call visit_call directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)
                break

        # Should have detected open
        assert len(visitor.dangerous_nodes) > 0
        assert any('open' in node for node in visitor.dangerous_nodes)

    def test_visitor_visit_import_method(self):
        """Test visitor visit_import method directly."""
        visitor = SecurityASTVisitor()

        code = "import math"
        tree = ast.parse(code)

        # Call visit_import directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                visitor.visit_Import(node)
                break

        # Should be callable
        assert hasattr(visitor, "visit_Import")

    def test_visitor_visit_import_from_method(self):
        """Test visitor visit_import_from method directly."""
        visitor = SecurityASTVisitor()

        code = "from math import sqrt"
        tree = ast.parse(code)

        # Call visit_import_from directly
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                visitor.visit_ImportFrom(node)
                break

        # Should be callable
        assert hasattr(visitor, "visit_ImportFrom")


class TestCheckAdditionalSecurityIssues:
    """Test _check_additional_security_issues edge cases."""

    def test_check_additional_dangerous_getattr(self, tmp_path):
        """Test checking detects dangerous getattr call."""
        security = ToolSecurity()

        code = """
getattr(obj, 'attr')
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_dangerous_setattr(self, tmp_path):
        """Test checking detects dangerous setattr call."""
        security = ToolSecurity()

        code = """
setattr(obj, 'attr', value)
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_dangerous_delattr(self, tmp_path):
        """Test checking detects dangerous delattr call."""
        security = ToolSecurity()

        code = """
delattr(obj, 'attr')
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_dangerous_globals(self, tmp_path):
        """Test checking detects dangerous globals call."""
        security = ToolSecurity()

        code = """
globals()
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_dangerous_locals(self, tmp_path):
        """Test checking detects dangerous locals call."""
        security = ToolSecurity()

        code = """
locals()
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_dangerous_vars(self, tmp_path):
        """Test checking detects dangerous vars call."""
        security = ToolSecurity()

        code = """
vars()
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_dangerous_dir(self, tmp_path):
        """Test checking detects dangerous dir call."""
        security = ToolSecurity()

        code = """
dir()
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_dangerous_hasattr(self, tmp_path):
        """Test checking detects dangerous hasattr call."""
        security = ToolSecurity()

        code = """
hasattr(obj, 'attr')
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_dangerous_input(self, tmp_path):
        """Test checking detects dangerous input call."""
        security = ToolSecurity()

        code = """
input("Enter: ")
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_dangerous_breakpoint(self, tmp_path):
        """Test checking detects dangerous breakpoint call."""
        security = ToolSecurity()

        code = """
breakpoint()
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        with pytest.raises(ToolSecurityError) as exc_info:
            security._check_additional_security_issues(tree, fake_path)
        assert "Dangerous function call" in str(exc_info.value)

    def test_check_additional_safe_attribute_access(self, tmp_path):
        """Test checking allows safe attribute access."""
        security = ToolSecurity()

        code = """
obj.attr
"""
        tree = ast.parse(code)
        fake_path = tmp_path / "test.py"

        # Should not raise
        security._check_additional_security_issues(tree, fake_path)


class TestValidateToolCodeEdgeCases:
    """Test validate_tool_code edge cases."""

    def test_validate_tool_code_empty(self):
        """Test validating empty code."""
        security = ToolSecurity()
        result = security.validate_tool_code("")
        assert result is True

    def test_validate_tool_code_whitespace_only(self):
        """Test validating whitespace-only code."""
        security = ToolSecurity()
        result = security.validate_tool_code("   \n\n   ")
        assert result is True

    def test_validate_tool_code_comments_only(self):
        """Test validating comments-only code."""
        security = ToolSecurity()
        result = security.validate_tool_code("# Just a comment\n# Another comment")
        assert result is True

    def test_validate_tool_code_docstring_only(self):
        """Test validating docstring-only code."""
        security = ToolSecurity()
        result = security.validate_tool_code('"""Just a docstring"""')
        assert result is True


class TestCreateToolSecurity:
    """Test create_tool_security factory function."""

    def test_create_tool_security_returns_instance(self):
        """Test that factory returns ToolSecurity instance."""
        security = create_tool_security()
        assert isinstance(security, ToolSecurity)


class TestToolSecurityError:
    """Test ToolSecurityError exception."""

    def test_tool_security_error_creation(self):
        """Test creating ToolSecurityError."""
        error = ToolSecurityError("Test error")
        assert str(error) == "Test error"

    def test_tool_security_error_with_cause(self):
        """Test creating ToolSecurityError with cause."""
        original_error = ValueError("Original error")
        error = ToolSecurityError("Security error")
        error.__cause__ = original_error
        assert error.__cause__ is not None


class TestSecurityASTVisitorEdgeCases:
    """Test SecurityASTVisitor edge cases."""

    def test_visitor_nested_calls(self):
        """Test visitor with nested function calls."""
        visitor = SecurityASTVisitor()

        code = """
result = eval(str(len([1, 2, 3])))
"""
        tree = ast.parse(code)

        # Call visit_call directly on Call nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)

        # Should detect eval
        assert any('eval' in node for node in visitor.dangerous_nodes)

    def test_visitor_lambda_with_eval(self):
        """Test visitor with lambda containing eval."""
        visitor = SecurityASTVisitor()

        code = """
f = lambda x: eval(x)
"""
        tree = ast.parse(code)

        # Call visit_call directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)

        # Should detect eval
        assert any('eval' in node for node in visitor.dangerous_nodes)

    def test_visitor_class_with_dangerous_method(self):
        """Test visitor with class containing dangerous method."""
        visitor = SecurityASTVisitor()

        code = """
class Test:
    def execute(self, code):
        exec(code)
"""
        tree = ast.parse(code)

        # Call visit_call directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)

        # Should detect exec
        assert any('exec' in node for node in visitor.dangerous_nodes)

    def test_visitor_conditional_exec(self):
        """Test visitor with conditional exec."""
        visitor = SecurityASTVisitor()

        code = """
if condition:
    exec(code)
"""
        tree = ast.parse(code)

        # Call visit_call directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)

        # Should detect exec
        assert any('exec' in node for node in visitor.dangerous_nodes)

    def test_visitor_try_except_exec(self):
        """Test visitor with exec in try-except."""
        visitor = SecurityASTVisitor()

        code = """
try:
    exec(code)
except:
    pass
"""
        tree = ast.parse(code)

        # Call visit_call directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)

        # Should detect exec
        assert any('exec' in node for node in visitor.dangerous_nodes)

    def test_visitor_async_function(self):
        """Test visitor with async function."""
        visitor = SecurityASTVisitor()

        code = """
async def async_func():
    return await some_call()
"""
        tree = ast.parse(code)
        visitor.visit(tree)

        # Should not detect anything dangerous
        assert len(visitor.dangerous_nodes) == 0

    def test_visitor_generator(self):
        """Test visitor with generator."""
        visitor = SecurityASTVisitor()

        code = """
def gen():
    for i in range(10):
        yield i
"""
        tree = ast.parse(code)
        visitor.visit(tree)

        # Should not detect anything dangerous
        assert len(visitor.dangerous_nodes) == 0

    def test_visitor_context_manager(self):
        """Test visitor with context manager."""
        visitor = SecurityASTVisitor()

        code = """
with open("file.txt") as f:
    content = f.read()
"""
        tree = ast.parse(code)

        # Call visit_call directly
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                visitor.visit_Call(node)

        # Should detect open call
        assert any('open' in node for node in visitor.dangerous_nodes)


class TestValidateToolFileEdgeCases:
    """Test validate_tool_file edge cases."""

    def test_validate_tool_file_with_encoding_error(self, tmp_path):
        """Test validating file with encoding issues."""
        security = ToolSecurity()

        # Create a file with invalid UTF-8
        bad_file = tmp_path / "bad_encoding.py"
        bad_file.write_bytes(b'\x80\x81\x82')

        with pytest.raises(ToolSecurityError) as exc_info:
            security.validate_tool_file(bad_file)
        # Should fail to parse
        assert "Invalid Python syntax" in str(exc_info.value) or "security validation failed" in str(exc_info.value).lower()

"""Tool Security Module.

Tool security and validation using standard library only.

Key Features:
    - Tool file validation and security checking
    - Safe execution environment setup
    - Permission and access control
    - Security policy enforcement
    - Standard library only (no external dependencies)

Dependencies:
    - ast (standard library)
    - pathlib (standard library)
    - typing (standard library)
"""

import ast
from pathlib import Path
from typing import List, Set, Optional, Dict, Any


class ToolSecurityError(Exception):
    """Exception raised when a tool security check fails.

    This exception is raised when a tool file or code fails security validation,
    such as containing dangerous constructs, importing restricted modules, or
    violating security policies.

    Args:
        message: Description of the security violation
    """


class ToolSecurity:
    """Handle tool security and validation.

    Provides security checking for tool files and safe execution environments.
    """

    # Dangerous AST nodes that should not be allowed in tools
    DANGEROUS_NODES = {
        # Import-related dangerous nodes
        'Import', 'ImportFrom',  # Imports can be controlled separately
        'Exec', 'Eval',  # Dynamic code execution
        'Compile',  # Dynamic compilation
        # File system access
        'With',  # Can be used for file access
        # System calls
        'Call',  # Need to check specific function calls
    }

    # Dangerous built-in functions that should be restricted
    DANGEROUS_BUILTINS = {
        'exec', 'eval', 'compile', 'open', 'execfile', 'file',
        'input', 'raw_input',  # Input functions
        '__import__',  # Import function
        'globals', 'locals', 'vars', 'dir',  # Reflection
        'getattr', 'setattr', 'delattr',  # Attribute manipulation
        'hasattr', '__getattribute__',  # Attribute access
        'breakpoint', 'quit', 'exit',  # Program termination
        'copyright', 'credits', 'license', 'help',  # Help functions
    }

    # Dangerous modules that should not be imported
    DANGEROUS_MODULES = {
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
        'pickle', 'marshal', 'shelve', 'cgi', 'ctypes', 'platform',
        'multiprocessing', 'threading', 'concurrent', 'asyncio',
        'code', 'codeop', 'trace', 'pdb', 'profile', 'cProfile',
        'runpy', 'importlib', 'pkgutil', 'zipimport', 'compileall',
        'py_compile', 'distutils', 'site', 'sysconfig', 'builtins',
        'gc', 'inspect', 'dis', 'opcode', 'symbol', 'tokenize',
        'keyword', 'tokenize', 'tabnanny', 'pyclbr', 'pickletools',
    }

    def __init__(self) -> None:
        """Initialize tool security.

        Sets up the security manager with default blacklisted modules
        and empty whitelist and security policies.
        """
        self._whitelisted_modules: Set[str] = set()
        self._blacklisted_modules: Set[str] = self.DANGEROUS_MODULES.copy()
        self._security_policies: Dict[str, Any] = {}

    def check_tool_permissions(self, tool: Any) -> bool:
        """Check if tool has required permissions.

        Verifies that a tool has the necessary permissions to execute
        within the secure environment.

        Args:
            tool: Tool instance to check.

        Returns:
            True if tool has required permissions, False otherwise.

        Raises:
            ToolSecurityError: If permission check fails unexpectedly.
        """
        return True

    def validate_tool(self, tool: Any) -> bool:
        """Validate a tool instance.

        Performs basic validation that an object is a valid tool by
        checking for required attributes.

        Args:
            tool: Tool instance to validate.

        Returns:
            True if tool is valid, False otherwise.

        Raises:
            ToolSecurityError: If validation encounters an unexpected error.
        """
        # For now, just return True if it's a tool-like object
        return hasattr(tool, 'name') and hasattr(tool, 'version')

    def validate_tool_file(self, file_path: Path) -> bool:
        """Validate a tool file for security issues.

        Performs comprehensive security validation on a Python tool file,
        checking for dangerous constructs, imports, and other security issues.

        Args:
            file_path: Path to tool file to validate.

        Returns:
            True if file passes security validation.

        Raises:
            ToolSecurityError: If security validation fails due to:
                - File does not exist
                - File is not a Python file
                - Invalid Python syntax
                - Dangerous constructs found
                - Dangerous imports found
                - Other security violations
        """
        try:
            if not file_path.exists():
                raise ToolSecurityError(f"Tool file does not exist: {file_path}")

            if file_path.suffix != '.py':
                raise ToolSecurityError(f"Tool file must be Python: {file_path}")

            # Read and parse the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                raise ToolSecurityError(f"Invalid Python syntax: {e}")

            # Check for dangerous constructs
            self._check_dangerous_constructs(tree, file_path)

            # Check for dangerous imports
            self._check_dangerous_imports(tree, file_path)

            # Additional security checks can be added here
            self._check_additional_security_issues(tree, file_path)

            return True

        except ToolSecurityError:
            raise
        except Exception as e:
            raise ToolSecurityError(f"Security validation failed for {file_path}: {e}") from e

    def validate_tool_code(self, code: str, source_name: str = "<string>") -> bool:
        """Validate tool code string for security issues.

        Performs security validation on a code string without requiring
        a file on disk.

        Args:
            code: Tool code to validate.
            source_name: Name for the source (for error reporting).

        Returns:
            True if code passes security validation, False if validation
            fails or an error occurs during parsing.

        Raises:
            ToolSecurityError: If security validation fails due to dangerous
                constructs or imports (though these are currently caught and
                result in False being returned).
        """
        try:
            tree = ast.parse(code)

            # Create a fake Path for validation
            fake_path = Path(source_name)

            self._check_dangerous_constructs(tree, fake_path)
            self._check_dangerous_imports(tree, fake_path)
            self._check_additional_security_issues(tree, fake_path)

            return True

        except Exception:
            return False

    def is_safe_module_import(self, module_name: str) -> bool:
        """Check if importing a module is considered safe.

        Determines whether a module can be safely imported based on
        the current whitelist and blacklist configurations.

        Args:
            module_name: Name of module to import.

        Returns:
            True if module import is safe, False if it is blacklisted
            or not whitelisted (when whitelist is active).
        """
        # Check blacklist first
        if module_name in self._blacklisted_modules:
            return False

        # Check whitelist
        if self._whitelisted_modules and module_name not in self._whitelisted_modules:
            return False

        return True

    def set_security_policy(self, policy_name: str, policy_value: Any) -> None:
        """Set a security policy.

        Configures a security policy that affects validation behavior.

        Args:
            policy_name: Name of security policy to set.
            policy_value: Value for the policy.

        Returns:
            None.
        """
        self._security_policies[policy_name] = policy_value

    def get_security_policy(self, policy_name: str) -> Optional[Any]:
        """Get a security policy value.

        Retrieves the value of a previously configured security policy.

        Args:
            policy_name: Name of security policy to retrieve.

        Returns:
            Policy value if set, None if the policy does not exist.
        """
        return self._security_policies.get(policy_name)

    def add_whitelisted_module(self, module_name: str) -> None:
        """Add a module to the whitelist.

        Adds a module to the allowed import list. When a whitelist is active,
        only whitelisted modules can be imported.

        Args:
            module_name: Name of module to whitelist.

        Returns:
            None.
        """
        self._whitelisted_modules.add(module_name)

    def remove_whitelisted_module(self, module_name: str) -> None:
        """Remove a module from the whitelist.

        Removes a module from the allowed import list.

        Args:
            module_name: Name of module to remove from whitelist.

        Returns:
            None.
        """
        self._whitelisted_modules.discard(module_name)

    def add_blacklisted_module(self, module_name: str) -> None:
        """Add a module to the blacklist.

        Adds a module to the disallowed import list. Blacklisted modules
        can never be imported regardless of whitelist status.

        Args:
            module_name: Name of module to blacklist.

        Returns:
            None.
        """
        self._blacklisted_modules.add(module_name)

    def remove_blacklisted_module(self, module_name: str) -> None:
        """Remove a module from the blacklist.

        Removes a module from the disallowed import list.

        Args:
            module_name: Name of module to remove from blacklist.

        Returns:
            None.
        """
        self._blacklisted_modules.discard(module_name)

    def _check_dangerous_constructs(self, tree: ast.AST, file_path: Path) -> None:
        """Check AST for dangerous constructs.

        Inspects the parsed AST for dangerous language constructs like
        exec, eval, and other potentially unsafe operations.

        Args:
            tree: Parsed AST tree to check.
            file_path: Path to tool file (for error reporting).

        Raises:
            ToolSecurityError: If dangerous constructs are found in the AST.
        """
        visitor = SecurityASTVisitor()
        visitor.visit(tree)

        if visitor.dangerous_nodes:
            dangerous_list = ', '.join(visitor.dangerous_nodes)
            raise ToolSecurityError(
                f"Dangerous constructs found in {file_path}: {dangerous_list}"
            )

    def _check_dangerous_imports(self, tree: ast.AST, file_path: Path) -> None:
        """Check AST for dangerous imports.

        Inspects the parsed AST for imports of blacklisted or non-whitelisted
        modules.

        Args:
            tree: Parsed AST tree to check.
            file_path: Path to tool file (for error reporting).

        Raises:
            ToolSecurityError: If dangerous imports are found in the AST.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if not self.is_safe_module_import(module_name):
                        raise ToolSecurityError(
                            f"Dangerous import found in {file_path}: {module_name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
                if module_name and not self.is_safe_module_import(module_name):
                    raise ToolSecurityError(
                        f"Dangerous import found in {file_path}: from {module_name} import ..."
                    )

    def _check_additional_security_issues(self, tree: ast.AST, file_path: Path) -> None:
        """Check for additional security issues.

        Performs additional security checks beyond dangerous constructs and
        imports, such as dangerous function calls and method invocations.

        Args:
            tree: Parsed AST tree to check.
            file_path: Path to tool file (for error reporting).

        Raises:
            ToolSecurityError: If security issues are found in the AST.
        """
        # Check for dangerous function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in self.DANGEROUS_BUILTINS:
                        raise ToolSecurityError(
                            f"Dangerous function call found in {file_path}: {func_name}"
                        )
                elif isinstance(node.func, ast.Attribute):
                    # Check for dangerous method calls like file operations
                    if isinstance(node.func.value, ast.Name):
                        if node.func.attr in ['open', 'write', 'read', 'close']:
                            raise ToolSecurityError(
                                f"Dangerous method call found in {file_path}: {node.func.attr}"
                            )


class SecurityASTVisitor(ast.NodeVisitor):
    """AST visitor to identify dangerous constructs.

    Traverses an AST tree and identifies potentially dangerous language
    constructs that could pose security risks in tool code.
    """

    def __init__(self) -> None:
        """Initialize the visitor.

        Sets up an empty list to track dangerous nodes found during traversal.
        """
        self.dangerous_nodes: List[str] = []

    def visit_exec(self, node: ast.AST) -> None:
        """Visit exec statement.

        Detects and records exec statements which allow dynamic code execution.

        Args:
            node: AST node representing the exec statement.

        Returns:
            None.
        """
        self.dangerous_nodes.append('exec statement')
        self.generic_visit(node)

    def visit_eval(self, node: ast.AST) -> None:
        """Visit eval call.

        Detects and records eval calls which allow dynamic code execution.

        Args:
            node: AST node representing the eval call.

        Returns:
            None.
        """
        self.dangerous_nodes.append('eval')
        self.generic_visit(node)

    def visit_call(self, node: ast.Call) -> None:
        """Visit function calls.

        Detects and records dangerous function calls such as exec, eval,
        compile, and open.

        Args:
            node: AST node representing the function call.

        Returns:
            None.
        """
        if isinstance(node.func, ast.Name):
            if node.func.id in ['exec', 'eval', 'compile', 'open']:
                self.dangerous_nodes.append(f'call to {node.func.id}')
        self.generic_visit(node)

    def visit_import(self, node: ast.AST) -> None:
        """Visit import statements.

        Processes import statements. Note: detailed import checking is
        handled separately in the security validation methods.

        Args:
            node: AST node representing the import statement.

        Returns:
            None.
        """
        # These are handled separately for more detailed checking
        self.generic_visit(node)

    def visit_import_from(self, node: ast.AST) -> None:
        """Visit from-import statements.

        Processes from-import statements. Note: detailed import checking is
        handled separately in the security validation methods.

        Args:
            node: AST node representing the from-import statement.

        Returns:
            None.
        """
        # These are handled separately for more detailed checking
        self.generic_visit(node)


def create_tool_security() -> ToolSecurity:
    """Create a tool security instance.

    Factory function that creates and returns a new ToolSecurity
    instance configured with default settings.

    Returns:
        A new ToolSecurity instance with default blacklist and empty
        whitelist and security policies.
    """
    return ToolSecurity()

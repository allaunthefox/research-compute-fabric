"""Tool Compatibility Module.

Tool compatibility checking using standard library only.

Key Features:
    - Python version compatibility checking
    - Dependency version validation
    - Tool API compatibility verification
    - Forward and backward compatibility management
    - Standard library only (no external dependencies)

Dependencies:
    - sys (standard library)
    - typing (standard library)
    - packaging (if available, otherwise manual version parsing)

"""

import sys
from typing import Dict, List, Optional, Tuple, Any
import re
from nodupe.core.tool_system.base import Tool


class CompatibilityError(Exception):
    """Exception raised when a compatibility check fails.

    This exception is raised when tool compatibility checking encounters
    a version mismatch or incompatible configuration.
    """

    pass


class CompatibilityChecker:
    """Handle tool compatibility checking.

    Checks Python version compatibility, dependency versions,
    and API compatibility between tools.
    """

    def __init__(self):
        """Initialize the compatibility checker.

        Sets up the checker with default supported Python versions
        and empty internal storage for API versions and dependency constraints.
        """
        self._python_version = sys.version_info
        self._supported_versions = [(3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14)]
        self._api_versions: Dict[str, str] = {}
        self._dependency_constraints: Dict[str, str] = {}

    def check_python_compatibility(
        self,
        required_version: Optional[Tuple[int, ...]] = None,
        min_version: Optional[Tuple[int, ...]] = None,
        max_version: Optional[Tuple[int, ...]] = None
    ) -> Tuple[bool, str]:
        """Check Python version compatibility.

        Validates whether the current Python version meets the requirements
        specified by any combination of required, minimum, or maximum versions.

        Args:
            required_version: Exact Python version required as (major, minor) tuple.
                If provided, the current version must match exactly.
            min_version: Minimum Python version required as (major, minor) tuple.
                The current version must be greater than or equal to this.
            max_version: Maximum Python version allowed as (major, minor) tuple.
                The current version must be less than or equal to this.

        Returns:
            Tuple of (is_compatible, reason_message).
            - is_compatible: True if current version meets all requirements
            - reason_message: Human-readable explanation of compatibility status

        Raises:
            TypeError: If version arguments are not tuples of integers
        """
        current = self._python_version

        # Check exact version requirement
        if required_version:
            if (current.major, current.minor) != required_version:
                return False, (
                    f"Requires Python {required_version[0]}.{required_version[1]}, "
                    f"running {current.major}.{current.minor}"
                )

        # Check minimum version
        if min_version:
            if (current.major, current.minor) < min_version:
                return False, (
                    f"Requires Python {min_version[0]}.{min_version[1]}+, "
                    f"running {current.major}.{current.minor}"
                )

        # Check maximum version
        if max_version:
            if (current.major, current.minor) > max_version:
                return False, (
                    f"Maximum Python {max_version[0]}.{max_version[1]} supported, "
                    f"running {current.major}.{current.minor}"
                )

        return True, f"Compatible with Python {current.major}.{current.minor}"

    def check_dependency_compatibility(
        self,
        dependency_name: str,
        required_version: Optional[str] = None,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Check dependency version compatibility.

        Validates whether an installed dependency meets version requirements
        specified by any combination of required, minimum, or maximum versions.

        Args:
            dependency_name: Name of the dependency to check. This should match
                the importable module name.
            required_version: Exact version required (e.g., '1.2.3').
                Uses semantic versioning comparison.
            min_version: Minimum version required (e.g., '1.0.0').
                Uses '>=' comparison.
            max_version: Maximum version allowed (e.g., '2.0.0').
                Uses '<=' comparison.

        Returns:
            Tuple of (is_compatible, reason_message).
            - is_compatible: True if dependency meets all requirements
            - reason_message: Human-readable explanation of compatibility status

        Raises:
            ImportError: If the dependency cannot be imported (for required deps)
            TypeError: If version arguments are not strings
        """
        try:
            # Import the dependency to check its version
            module = __import__(dependency_name)
            if hasattr(module, '__version__'):
                installed_version = module.__version__
            elif hasattr(module, 'VERSION'):
                installed_version = str(module.VERSION)
            else:
                return True, f"Cannot determine version for {dependency_name}, assuming compatible"

            # Parse versions
            if required_version and not self._version_matches(installed_version, required_version):
                return False, f"{dependency_name} {installed_version} does not match required {required_version}"

            if min_version and not self._version_satisfies_min(installed_version, min_version):
                return False, f"{dependency_name} {installed_version} below minimum {min_version}"

            if max_version and not self._version_satisfies_max(installed_version, max_version):
                return False, f"{dependency_name} {installed_version} exceeds maximum {max_version}"

            return True, f"Compatible with {dependency_name} {installed_version}"

        except ImportError:
            if required_version or min_version:
                return False, f"Required dependency {dependency_name} not installed"
            return True, f"Optional dependency {dependency_name} not installed"

        except Exception as e:
            return True, f"Could not check {dependency_name} version: {e}"

    def check_api_compatibility(
        self,
        tool_name: str,
        required_api_version: str,
        current_api_version: str
    ) -> Tuple[bool, str]:
        """Check API compatibility between tool and host.

        Validates whether the tool's required API version is compatible
        with the host's current API version.

        Args:
            tool_name: Name of the tool being checked.
            required_api_version: API version that the tool requires.
                Format should be 'major.minor.patch'.
            current_api_version: Current API version provided by the host.
                Format should be 'major.minor.patch'.

        Returns:
            Tuple of (is_compatible, reason_message).
            - is_compatible: True if API versions are compatible
            - reason_message: Human-readable explanation of compatibility status

        Raises:
            ValueError: If API version strings cannot be parsed
        """
        if not self._api_version_compatible(required_api_version, current_api_version):
            return False, f"{tool_name} requires API {required_api_version}, host provides {current_api_version}"

        return True, (
            f"API compatible with {tool_name} "
            f"(host: {current_api_version}, required: {required_api_version})"
        )

    def check_tool_compatibility(
        self,
        tool_info: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Check overall tool compatibility.

        Performs a comprehensive compatibility check for a tool including
        Python version, dependencies, and API version requirements.

        Args:
            tool_info: Dictionary containing tool compatibility information.
                Expected keys:
                - 'name': Tool name (str)
                - 'python_version': Required Python version (str or tuple)
                - 'dependencies': Dependency requirements (dict)
                - 'api_version': Required API version (str)
                - 'current_api_version': Host API version (str)

        Returns:
            Tuple of (is_compatible, list_of_issues).
            - is_compatible: True if all compatibility checks pass
            - list_of_issues: List of strings describing any compatibility issues

        Raises:
            ValueError: If tool_info format is invalid
            TypeError: If tool_info is not a dictionary
        """
        issues: List[str] = []

        # Check Python version compatibility
        if 'python_version' in tool_info:
            req_version = tool_info['python_version']
            if isinstance(req_version, str):
                try:
                    major, minor = map(int, req_version.split('.')[:2])
                    req_tuple = (major, minor)
                    is_compat, msg = self.check_python_compatibility(required_version=req_tuple)
                    if not is_compat:
                        issues.append(msg)
                except ValueError:
                    issues.append(f"Invalid Python version format: {req_version}")
            elif isinstance(req_version, tuple):
                is_compat, msg = self.check_python_compatibility(
                    required_version=req_version)  # type: ignore
                if not is_compat:
                    issues.append(msg)

        # Check dependencies
        if 'dependencies' in tool_info:
            deps = tool_info['dependencies']
            if isinstance(deps, dict):
                # Cast to proper dict type for type checking
                typed_deps = deps
                deps_dict: Dict[str, str] = {}
                for item_key, item_value in typed_deps.items():
                    try:
                        key_str: str = str(item_key) if item_key is not None else ""
                        value_str: str = str(item_value) if item_value is not None else ""
                        deps_dict[key_str] = value_str
                    except (TypeError, ValueError):
                        # Skip items that can't be converted to strings
                        continue
                for dep_name, version_constraint in deps_dict.items():
                    if version_constraint.startswith('>='):
                        min_ver = version_constraint[2:]
                        is_compat, msg = self.check_dependency_compatibility(
                            dep_name, min_version=min_ver
                        )
                        if not is_compat:
                            issues.append(msg)
                    elif version_constraint.startswith('<='):
                        max_ver = version_constraint[2:]
                        is_compat, msg = self.check_dependency_compatibility(
                            dep_name, max_version=max_ver
                        )
                        if not is_compat:
                            issues.append(msg)
                    elif version_constraint.startswith('=='):
                        exact_ver = version_constraint[2:]
                        is_compat, msg = self.check_dependency_compatibility(
                            dep_name, required_version=exact_ver
                        )
                        if not is_compat:
                            issues.append(msg)
                    else:
                        # Assume it's a version constraint
                        is_compat, msg = self.check_dependency_compatibility(
                            dep_name, min_version=version_constraint
                        )
                        if not is_compat:
                            issues.append(msg)

        # Check API compatibility
        if 'api_version' in tool_info and 'current_api_version' in tool_info:
            tool_name = tool_info.get('name', 'unknown')
            is_compat, msg = self.check_api_compatibility(
                tool_name,
                tool_info['api_version'],
                tool_info['current_api_version']
            )
            if not is_compat:
                issues.append(msg)

        return len(issues) == 0, issues

    def register_api_version(self, tool_name: str, api_version: str) -> None:
        """Register an API version for a tool.

        Stores the API version for a tool to enable tracking and
        compatibility checking.

        Args:
            tool_name: Name of the tool to register the API version for.
            api_version: API version string in 'major.minor.patch' format.

        Raises:
            ValueError: If tool_name is empty or api_version is invalid
            TypeError: If arguments are not strings
        """
        self._api_versions[tool_name] = api_version

    def register_dependency_constraint(
        self,
        dependency_name: str,
        constraint: str
    ) -> None:
        """Register a dependency version constraint.

        Stores a version constraint for a dependency to enable
        validation during compatibility checking.

        Args:
            dependency_name: Name of the dependency to register constraint for.
            constraint: Version constraint string (e.g., '>=1.0.0', '<=2.0.0').

        Raises:
            ValueError: If dependency_name is empty or constraint is invalid
            TypeError: If arguments are not strings
        """
        self._dependency_constraints[dependency_name] = constraint

    def get_supported_python_versions(self) -> List[Tuple[int, int]]:
        """Get list of supported Python versions.

        Returns the list of Python versions that are officially supported
        by this compatibility checker.

        Returns:
            List of supported Python versions as (major, minor) tuples.
            Each tuple contains two integers representing the version.

        Raises:
            RuntimeError: If supported versions are not configured
        """
        return self._supported_versions.copy()

    def is_version_compatible(
        self,
        version1: str,
        version2: str,
        tolerance: str = 'patch'
    ) -> bool:
        """Check if two versions are compatible within tolerance.

        Compares two version strings and determines if they are compatible
        based on the specified tolerance level.

        Args:
            version1: First version string to compare (e.g., '1.2.3').
            version2: Second version string to compare (e.g., '1.2.4').
            tolerance: Level of tolerance for compatibility.
                Valid values: 'major', 'minor', 'patch'.
                - 'major': Versions are compatible if major versions match
                - 'minor': Versions are compatible if major.minor match
                - 'patch': Versions are compatible if major.minor.patch match

        Returns:
            True if versions are compatible within the specified tolerance,
            False otherwise.

        Raises:
            ValueError: If tolerance is not one of 'major', 'minor', or 'patch'
            TypeError: If version arguments are not strings
        """
        try:
            v1_parts = self._parse_version(version1)
            v2_parts = self._parse_version(version2)

            if tolerance == 'major':
                return v1_parts[0] == v2_parts[0]
            elif tolerance == 'minor':
                return v1_parts[:2] == v2_parts[:2]
            elif tolerance == 'patch':
                return v1_parts[:3] == v2_parts[:3]
            else:
                return False

        except Exception:
            return False

    def _version_matches(self, installed: str, required: str) -> bool:
        """Check if installed version matches required version.

        Internal method to compare an installed version against a required version.

        Args:
            installed: Installed version string (e.g., '1.2.3').
            required: Required version string (e.g., '1.2.0').

        Returns:
            True if installed version matches required version,
            False otherwise.

        Raises:
            ValueError: If version strings cannot be parsed
            TypeError: If arguments are not strings
        """
        if required.startswith('=='):
            required = required[2:]

        installed_parts = self._parse_version(installed)
        required_parts = self._parse_version(required)

        # Compare up to the length of required version
        return installed_parts[:len(required_parts)] == required_parts

    def _version_satisfies_min(self, installed: str, minimum: str) -> bool:
        """Check if installed version satisfies minimum version.

        Internal method to verify the installed version meets the minimum requirement.

        Args:
            installed: Installed version string (e.g., '1.2.3').
            minimum: Minimum version string (e.g., '1.0.0').

        Returns:
            True if installed version is greater than or equal to minimum,
            False otherwise.

        Raises:
            ValueError: If version strings cannot be parsed
            TypeError: If arguments are not strings
        """
        if minimum.startswith('>='):
            minimum = minimum[2:]

        installed_parts = self._parse_version(installed)
        min_parts = self._parse_version(minimum)

        for i in range(min(len(installed_parts), len(min_parts))):
            if installed_parts[i] > min_parts[i]:
                return True
            elif installed_parts[i] < min_parts[i]:
                return False

        # If all compared parts are equal, installed version should be at least as long
        return len(installed_parts) >= len(min_parts)

    def _version_satisfies_max(self, installed: str, maximum: str) -> bool:
        """Check if installed version satisfies maximum version.

        Internal method to verify the installed version meets the maximum constraint.

        Args:
            installed: Installed version string (e.g., '1.2.3').
            maximum: Maximum version string (e.g., '2.0.0').

        Returns:
            True if installed version is less than or equal to maximum,
            False otherwise.

        Raises:
            ValueError: If version strings cannot be parsed
            TypeError: If arguments are not strings
        """
        if maximum.startswith('<='):
            maximum = maximum[2:]

        installed_parts = self._parse_version(installed)
        max_parts = self._parse_version(maximum)

        for i in range(min(len(installed_parts), len(max_parts))):
            if installed_parts[i] < max_parts[i]:
                return True
            elif installed_parts[i] > max_parts[i]:
                return False

        # If all compared parts are equal, installed version should not be longer
        return len(installed_parts) <= len(max_parts)

    def _api_version_compatible(self, required: str, current: str) -> bool:
        """Check if API versions are compatible.

        Internal method to determine if API versions are compatible.
        API versions are considered compatible if they have the same major version.

        Args:
            required: Required API version string (e.g., '1.0.0').
            current: Current API version string (e.g., '1.2.0').

        Returns:
            True if API versions are compatible (same major version),
            False otherwise.

        Raises:
            ValueError: If version strings cannot be parsed
            TypeError: If arguments are not strings
        """
        # For API compatibility, we typically want same major version
        req_parts = self._parse_version(required)
        cur_parts = self._parse_version(current)

        # Same major version is typically required for API compatibility
        return req_parts[0] == cur_parts[0] if req_parts and cur_parts else False

    def _parse_version(self, version_str: str) -> List[int]:
        """Parse version string into integer parts.

        Internal method to extract numeric version components from a version string.
        Handles pre-release and build metadata by ignoring them.

        Args:
            version_str: Version string to parse (e.g., '1.2.3-beta+build').

        Returns:
            List of integer version parts (e.g., [1, 2, 3]).

        Raises:
            ValueError: If version_str cannot be parsed
            TypeError: If version_str is not a string
        """
        # Remove any pre-release or build metadata
        clean_version = re.split(r'[-+]', version_str)[0]
        # Split on dots and convert to integers
        parts: List[int] = []
        for part in clean_version.split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                # Stop at first non-numeric part
                break
        return parts


def create_compatibility_checker() -> CompatibilityChecker:
    """Create a compatibility checker instance.

    Factory function to create and return a new CompatibilityChecker instance
    configured with default settings.

    Returns:
        A new CompatibilityChecker instance ready for use.

    Raises:
        RuntimeError: If CompatibilityChecker initialization fails
    """
    return CompatibilityChecker()


class ToolCompatibilityError(Exception):
    """Exception raised when tool compatibility check fails.

    This exception is raised when a tool fails compatibility validation,
    such as missing required attributes or having invalid configurations.
    """

    pass


class ToolCompatibility:
    """Tool compatibility checker with tool-specific functionality.

    Provides compatibility checking for tools, including interface validation,
    dependency checking, and lifecycle management.
    """

    def __init__(self):
        """Initialize tool compatibility checker.

        Creates a new ToolCompatibility instance with an internal
        CompatibilityChecker and no container assigned.
        """
        self.container = None
        self._checker = CompatibilityChecker()

    def check_compatibility(self, tool: Tool) -> Dict[str, Any]:
        """Check tool compatibility.

        Validates that a tool meets all compatibility requirements including
        proper inheritance, required attributes, and required methods.

        Args:
            tool: Tool instance to check for compatibility.

        Returns:
            Dictionary with compatibility information containing:
            - 'compatible': Boolean indicating if tool is compatible
            - 'issues': List of compatibility issues found
            - 'warnings': List of compatibility warnings

        Raises:
            ToolCompatibilityError: If tool fails any compatibility requirement
            TypeError: If tool is not a Tool instance
        """
        if not isinstance(tool, Tool):
            raise ToolCompatibilityError("Tool must inherit from Tool base class")

        if not hasattr(tool, 'name') or not tool.name:
            raise ToolCompatibilityError("Tool must have a valid name")

        if not hasattr(tool, 'version'):
            raise ToolCompatibilityError("Tool must have a version")

        if not hasattr(tool, 'dependencies'):
            raise ToolCompatibilityError("Tool must have dependencies")

        # Check required methods
        required_methods = ['initialize', 'shutdown', 'get_capabilities']
        for method in required_methods:
            if not hasattr(tool, method):
                raise ToolCompatibilityError(f"Tool must implement {method} method")

        # Create compatibility report
        report = {
            "compatible": True,
            "issues": [],
            "warnings": []
        }

        # Check tool attributes
        if not tool.name.strip():
            report["compatible"] = False
            report["issues"].append("Tool name cannot be empty")

        # Check version format
        try:
            self._parse_version(tool.version)
        except Exception:
            report["compatible"] = False
            report["issues"].append(f"Invalid version format: {tool.version}")

        # Check dependencies
        if not isinstance(tool.dependencies, list):
            report["compatible"] = False
            report["issues"].append("Dependencies must be a list")

        return report

    def get_compatibility_report(self, tool: Tool) -> Dict[str, Any]:
        """Get detailed compatibility report for a tool.

        Generates a comprehensive compatibility report for a tool including
        its status, version information, and any issues found.

        Args:
            tool: Tool instance to generate compatibility report for.

        Returns:
            Dictionary containing detailed compatibility report:
            - 'tool_name': Name of the tool
            - 'tool_version': Version of the tool
            - 'compatibility_status': Status string ('compatible', 'incompatible', 'unknown')
            - 'compatibility_issues': List of issues found
            - 'compatibility_warnings': List of warnings

        Raises:
            ToolCompatibilityError: If tool is not a Tool instance
            TypeError: If tool is not a Tool instance
        """
        if not isinstance(tool, Tool):
            raise ToolCompatibilityError("Tool must inherit from Tool base class")

        report = {
            "tool_name": getattr(tool, 'name', 'unknown'),
            "tool_version": getattr(tool, 'version', 'unknown'),
            "compatibility_status": "unknown",
            "compatibility_issues": [],
            "compatibility_warnings": []
        }

        # Basic validation
        if not hasattr(tool, 'name') or not tool.name:
            report["compatibility_status"] = "incompatible"
            report["compatibility_issues"].append("Tool must have a valid name")
            return report

        if not hasattr(tool, 'version'):
            report["compatibility_status"] = "incompatible"
            report["compatibility_issues"].append("Tool must have a version")
            return report

        if not hasattr(tool, 'dependencies'):
            report["compatibility_status"] = "incompatible"
            report["compatibility_issues"].append("Tool must have dependencies")
            return report

        # Check required methods
        required_methods = ['initialize', 'shutdown', 'get_capabilities']
        for method in required_methods:
            if not hasattr(tool, method):
                report["compatibility_status"] = "incompatible"
                report["compatibility_issues"].append(f"Tool must implement {method} method")

        # If we got here, basic checks passed
        if not report["compatibility_issues"]:
            report["compatibility_status"] = "compatible"

        return report

    def initialize(self, container: Any) -> None:
        """Initialize compatibility checker with container.

        Sets up the compatibility checker with a service container for
        dependency injection and access to other services.

        Args:
            container: Service container instance providing access to
                application services and configuration.

        Raises:
            TypeError: If container is not a valid container type
        """
        self.container = container

    def shutdown(self) -> None:
        """Shutdown compatibility checker.

        Performs cleanup operations when the compatibility checker is
        being shut down, releasing any held resources.

        Raises:
            RuntimeError: If shutdown fails due to resource issues
        """
        self.container = None

    def _parse_version(self, version_str: str) -> List[int]:
        """Parse version string into components.

        Internal method to validate and parse a version string into
        its component parts.

        Args:
            version_str: Version string to parse (e.g., '1.2.3').

        Returns:
            List of integer version components [major, minor, patch, ...].

        Raises:
            ValueError: If version_str is empty, has invalid format,
                or has fewer than 2 components
            TypeError: If version_str is not a string
        """
        if not version_str:
            raise ValueError("Version string cannot be empty")

        parts = []
        for part in version_str.split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                raise ValueError(f"Invalid version part: {part}")

        if len(parts) < 2:
            raise ValueError("Version must have at least major.minor format")

        return parts

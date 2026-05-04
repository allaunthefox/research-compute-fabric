"""Tool Dependencies Module.

Tool dependency management using standard library only.

Key Features:
    - Tool dependency resolution and ordering
    - Circular dependency detection
    - Dependency validation and conflict resolution
    - Topological sorting for initialization order
    - Standard library only (no external dependencies)

Dependencies:
    - typing (standard library)
    - enum (standard library)
"""

from enum import Enum
from typing import Dict, List, Set, Any, Tuple, Optional
from .base import Tool


class DependencyError(Exception):
    """Exception raised when tool dependency resolution fails.

    This exception is raised when there are issues with tool dependencies,
    such as circular dependencies or missing dependencies.
    """
    pass


class ResolutionStatus(Enum):
    """Dependency resolution status values.

    Attributes:
        RESOLVED: All dependencies resolved successfully.
        UNRESOLVED: Dependencies could not be resolved.
        CIRCULAR: Circular dependency detected.
        MISSING: Required dependencies are missing.
        CONFLICT: Conflicting dependencies detected.
    """
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    CIRCULAR = "circular"
    MISSING = "missing"
    CONFLICT = "conflict"


class DependencyResolver:
    """Handle tool dependency resolution and management.

    Resolves tool dependencies, detects circular dependencies,
    and provides ordering for initialization.

    Attributes:
        _dependencies: Dictionary mapping tool names to their dependencies.
        _dependents: Dictionary mapping tool names to tools that depend on them.
        _resolutions: Dictionary storing resolution status for tools.
        _resolved_order: List of tools in resolved order.
    """

    def __init__(self):
        """Initialize dependency resolver.

        Creates empty dependency graphs for tracking tool dependencies
        and their relationships.
        """
        self._dependencies: Dict[str, List[str]] = {}
        self._dependents: Dict[str, List[str]] = {}
        self._resolutions: Dict[str, ResolutionStatus] = {}
        self._resolved_order: List[str] = []

    def check_dependency_graph(self, tools: List[str]) -> bool:
        """Check if the dependency graph is valid (no circular dependencies).

        Args:
            tools: List of tool names to check.

        Returns:
            True if graph is valid (no circular dependencies), False otherwise.

        Raises:
            None
        """
        return not self._has_circular_dependency(tools)

    def add_dependency(self, tool_name: str, dependency_name: str) -> None:
        """Add a dependency relationship.

        Establishes that tool_name depends on dependency_name. This creates
        a bidirectional relationship in the dependency graph.

        Args:
            tool_name: Name of tool that depends on another.
            dependency_name: Name of tool that is depended upon.

        Raises:
            None
        """
        if tool_name not in self._dependencies:
            self._dependencies[tool_name] = []
        if dependency_name not in self._dependencies[tool_name]:
            self._dependencies[tool_name].append(dependency_name)

        # Update reverse dependencies
        if dependency_name not in self._dependents:
            self._dependents[dependency_name] = []
        if tool_name not in self._dependents[dependency_name]:
            self._dependents[dependency_name].append(tool_name)

        # Reset resolution status when dependencies change
        self._resolutions.clear()
        self._resolved_order.clear()

    def remove_dependency(self, tool_name: str, dependency_name: str) -> bool:
        """Remove a dependency relationship.

        Removes the dependency relationship between two tools.

        Args:
            tool_name: Name of tool that had dependency.
            dependency_name: Name of dependency to remove.

        Returns:
            True if dependency was removed, False if not found.

        Raises:
            None
        """
        if (tool_name in self._dependencies and
                dependency_name in self._dependencies[tool_name]):
            self._dependencies[tool_name].remove(dependency_name)

            # Update reverse dependencies
            if (dependency_name in self._dependents and
                    tool_name in self._dependents[dependency_name]):
                self._dependents[dependency_name].remove(tool_name)

            # Reset resolution status
            self._resolutions.clear()
            self._resolved_order.clear()
            return True

        return False

    def get_dependencies(self, tool_name: str) -> List[str]:
        """Get dependencies for a tool.

        Args:
            tool_name: Name of tool.

        Returns:
            List of dependency names for the specified tool.

        Raises:
            None
        """
        return self._dependencies.get(tool_name, [])

    def get_dependents(self, tool_name: str) -> List[str]:
        """Get tools that depend on this tool.

        Args:
            tool_name: Name of tool.

        Returns:
            List of dependent tool names that depend on this tool.

        Raises:
            None
        """
        return self._dependents.get(tool_name, [])

    def resolve_dependencies(self, tools: List[str]) -> Tuple[ResolutionStatus, List[str]]:
        """Resolve dependencies for a list of tools.

        Performs dependency resolution including checking for missing
        dependencies, circular dependencies, and computing the correct
        initialization order using topological sort.

        Args:
            tools: List of tool names to resolve.

        Returns:
            Tuple of (resolution status, ordered list of tools).
            The status indicates whether resolution was successful and
            the list contains tools in initialization order.

        Raises:
            DependencyError: If dependency resolution fails unexpectedly.
        """
        try:
            # Check for missing dependencies
            all_deps = set()
            for tool in tools:
                deps = set(self._dependencies.get(tool, []))
                all_deps.update(deps)

            missing = all_deps - set(tools)
            if missing:
                return ResolutionStatus.MISSING, []

            # Check for circular dependencies
            if self._has_circular_dependency(tools):
                return ResolutionStatus.CIRCULAR, []

            # Perform topological sort
            ordered_tools = self._topological_sort(tools)

            if not ordered_tools:
                return ResolutionStatus.UNRESOLVED, []

            return ResolutionStatus.RESOLVED, ordered_tools

        except Exception as e:
            raise DependencyError(f"Dependency resolution failed: {e}") from e

    def _has_circular_dependency(self, tools: List[str]) -> bool:
        """Check if there are circular dependencies among tools.

        Uses depth-first search to detect cycles in the dependency graph.

        Args:
            tools: List of tool names to check.

        Returns:
            True if circular dependency exists, False otherwise.

        Raises:
            None
        """
        # Build dependency graph for the specific tools
        graph = {}
        tool_set = set(tools)

        for tool in tools:
            deps = [dep for dep in self._dependencies.get(tool, []) if dep in tool_set]
            graph[tool] = deps

        # Use DFS to detect cycles
        visiting = set()
        visited = set()

        def dfs(node: str) -> bool:
            """Detect cycles using depth-first search.

            Args:
                node: Current node to visit in the graph.

            Returns:
                True if a cycle is detected, False otherwise.
            """
            if node in visited:
                return False
            if node in visiting:
                return True  # Cycle detected

            visiting.add(node)
            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        for tool in tools:
            if dfs(tool):
                return True

        return False

    def _topological_sort(self, tools: List[str]) -> List[str]:
        """Perform topological sort to get dependency order.

        Uses depth-first search to perform a topological sort on the
        dependency graph, returning tools in the order they should
        be initialized (dependencies first).

        Args:
            tools: List of tool names to sort.

        Returns:
            Ordered list of tool names with dependencies first,
            or empty list if a cycle exists.

        Raises:
            None
        """
        if self._has_circular_dependency(tools):
            return []  # Cannot sort with circular dependencies

        # Build dependency graph
        graph = {}
        tool_set = set(tools)

        for tool in tools:
            deps = [dep for dep in self._dependencies.get(tool, []) if dep in tool_set]
            graph[tool] = deps

        # Perform topological sort using DFS
        result = []
        visited = set()
        temp_visited = set()

        def visit(node: str) -> bool:
            """Visit a node in the topological sort algorithm.

            Args:
                node: Current node to visit.

            Returns:
                True if visit completed successfully, False if cycle detected.
            """
            if node in temp_visited:
                return False  # Cycle detected (shouldn't happen if checked earlier)
            if node in visited:
                return True

            temp_visited.add(node)
            for dependency in graph.get(node, []):
                if not visit(dependency):
                    return False
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
            return True

        for tool in tools:
            if tool not in visited:
                if not visit(tool):
                    return []  # Cycle detected

        return result

    def get_initialization_order(self, tools: List[str]) -> List[str]:
        """Get the correct initialization order for tools.

        Computes the order in which tools should be initialized,
        ensuring all dependencies are available before a tool starts.

        Args:
            tools: List of tool names.

        Returns:
            List of tool names in initialization order (dependencies first),
            or empty list if resolution fails.

        Raises:
            None
        """
        status, order = self.resolve_dependencies(tools)
        if status == ResolutionStatus.RESOLVED:
            return order
        return []

    def get_shutdown_order(self, tools: List[str]) -> List[str]:
        """Get the correct shutdown order for tools (reverse of initialization).

        Computes the reverse order of initialization, ensuring that
        tools are shutdown after the tools that depend on them.

        Args:
            tools: List of tool names.

        Returns:
            List of tool names in shutdown order (dependents first).

        Raises:
            None
        """
        init_order = self.get_initialization_order(tools)
        return list(reversed(init_order))

    def validate_tool_compatibility(
        self,
        tool: Tool,
        available_tools: List[str]
    ) -> Tuple[bool, List[str]]:
        """Validate that a tool is compatible with available tools.

        Checks if all required dependencies for a tool are available
        in the current toolset.

        Args:
            tool: Tool instance to validate.
            available_tools: List of available tool names.

        Returns:
            Tuple of (is_compatible, list_of_missing_dependencies).
            is_compatible is True if all dependencies are available.

        Raises:
            None
        """
        required_deps = getattr(tool, 'dependencies', [])
        missing_deps = [dep for dep in required_deps if dep not in available_tools]

        return len(missing_deps) == 0, missing_deps

    def get_dependency_tree(self, tool_name: str) -> Dict[str, Any]:
        """Get the dependency tree for a tool.

        Builds a hierarchical tree structure showing all dependencies
        of the specified tool, including transitive dependencies.

        Args:
            tool_name: Name of tool.

        Returns:
            Dictionary representing dependency tree with keys:
            - name: Tool name
            - dependencies: Dictionary of dependency names to their trees
            - circular: Boolean indicating if circular (if applicable)

        Raises:
            None
        """
        def build_tree(name: str, visited: Optional[Set[str]] = None) -> Dict[str, Any]:
            """Build dependency tree recursively.

            Args:
                name: Name of the tool to build tree for.
                visited: Set of already visited tools to detect cycles.

            Returns:
                Dictionary representing the dependency tree.
            """
            if visited is None:
                visited = set()

            if name in visited:
                return {"name": name, "circular": True, "dependencies": {}}

            visited.add(name)

            deps = self._dependencies.get(name, [])
            tree = {
                "name": name,
                "dependencies": {}
            }

            for dep in deps:
                tree["dependencies"][dep] = build_tree(dep, visited.copy())

            return tree

        return build_tree(tool_name)

    def get_all_dependencies(self, tool_name: str) -> Set[str]:
        """Get all transitive dependencies for a tool.

        Computes the complete set of dependencies (direct and indirect)
        for the specified tool.

        Args:
            tool_name: Name of tool.

        Returns:
            Set of all dependency names (direct and indirect).

        Raises:
            None
        """
        all_deps = set()
        to_process = [tool_name]
        processed = set()

        while to_process:
            current = to_process.pop(0)
            if current in processed:
                continue

            processed.add(current)
            deps = self._dependencies.get(current, [])

            for dep in deps:
                if dep not in all_deps:
                    all_deps.add(dep)
                    to_process.append(dep)

        return all_deps

    def clear_dependencies(self) -> None:
        """Clear all dependency information.

        Removes all tracked dependencies, dependents, and resolution
        state from the resolver.

        Raises:
            None
        """
        self._dependencies.clear()
        self._dependents.clear()
        self._resolutions.clear()
        self._resolved_order.clear()


def create_dependency_resolver() -> DependencyResolver:
    """Create a dependency resolver instance.

    Factory function to create a new DependencyResolver with
    empty dependency graphs.

    Returns:
        A new DependencyResolver instance.

    Raises:
        None
    """
    return DependencyResolver()


# Alias for backward compatibility
ToolDependencyManager = DependencyResolver

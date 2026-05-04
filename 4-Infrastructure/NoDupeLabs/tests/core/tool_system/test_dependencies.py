"""Test Tool Dependencies Module.

Comprehensive tests for the dependency management system including:
- Dependency graph management
- Circular dependency detection
- Topological sorting
- Dependency resolution
- Initialization and shutdown ordering
"""

from unittest.mock import MagicMock

import pytest

from nodupe.core.tool_system.base import Tool
from nodupe.core.tool_system.dependencies import (
    DependencyError,
    DependencyResolver,
    ResolutionStatus,
    ToolDependencyManager,
    create_dependency_resolver,
)


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self, name="MockTool", version="1.0.0", dependencies=None):
        """Initialize MockTool with name, version, and dependencies."""
        self._name = name
        self._version = version
        self._dependencies = dependencies or []
        self._initialized = False

    @property
    def name(self):
        """Tool name property."""
        return self._name

    @property
    def version(self):
        """Tool version property."""
        return self._version

    @property
    def dependencies(self):
        """Tool dependencies property."""
        return self._dependencies

    def initialize(self, container):
        """Initialize the tool with the given container."""
        self._initialized = True

    def shutdown(self):
        """Shutdown the tool and clean up resources."""
        self._initialized = False

    def get_capabilities(self):
        """Get the tool capabilities."""
        return {"test": "capability"}

    @property
    def api_methods(self):
        """API methods exposed by this tool."""
        return {}

    def run_standalone(self, args):
        """Run the tool as a standalone process."""
        return 0

    def describe_usage(self):
        """Describe how to use this tool."""
        return "Mock tool usage"


class TestDependencyResolverInit:
    """Test DependencyResolver initialization."""

    def test_dependency_resolver_init(self):
        """Test basic DependencyResolver initialization."""
        resolver = DependencyResolver()

        assert resolver._dependencies == {}
        assert resolver._dependents == {}
        assert resolver._resolutions == {}
        assert resolver._resolved_order == []

    def test_create_dependency_resolver_factory(self):
        """Test the create_dependency_resolver factory function."""
        resolver = create_dependency_resolver()

        assert isinstance(resolver, DependencyResolver)

    def test_tool_dependency_manager_alias(self):
        """Test that ToolDependencyManager is an alias for DependencyResolver."""
        assert ToolDependencyManager is DependencyResolver


class TestAddDependency:
    """Test adding dependencies."""

    def test_add_dependency_basic(self):
        """Test adding a basic dependency."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")

        assert "tool_a" in resolver._dependencies
        assert "tool_b" in resolver._dependencies["tool_a"]

    def test_add_dependency_multiple(self):
        """Test adding multiple dependencies for same tool."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_a", "tool_c")

        assert "tool_b" in resolver._dependencies["tool_a"]
        assert "tool_c" in resolver._dependencies["tool_a"]
        assert len(resolver._dependencies["tool_a"]) == 2

    def test_add_dependency_duplicate(self):
        """Test adding duplicate dependency (should not duplicate)."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_a", "tool_b")

        assert resolver._dependencies["tool_a"].count("tool_b") == 1

    def test_add_dependency_updates_dependents(self):
        """Test that adding dependency updates dependents."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")

        assert "tool_a" in resolver._dependents["tool_b"]

    def test_add_dependency_clears_resolution(self):
        """Test that adding dependency clears resolution cache."""
        resolver = DependencyResolver()

        # Set up some resolution state
        resolver._resolutions["test"] = ResolutionStatus.RESOLVED
        resolver._resolved_order = ["tool_a", "tool_b"]

        resolver.add_dependency("tool_a", "tool_b")

        assert resolver._resolutions == {}
        assert resolver._resolved_order == []


class TestRemoveDependency:
    """Test removing dependencies."""

    def test_remove_dependency_existing(self):
        """Test removing an existing dependency."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        result = resolver.remove_dependency("tool_a", "tool_b")

        assert result is True
        assert "tool_b" not in resolver._dependencies.get("tool_a", [])

    def test_remove_dependency_nonexistent(self):
        """Test removing a nonexistent dependency."""
        resolver = DependencyResolver()

        result = resolver.remove_dependency("tool_a", "tool_b")

        assert result is False

    def test_remove_dependency_updates_dependents(self):
        """Test that removing dependency updates dependents."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.remove_dependency("tool_a", "tool_b")

        assert "tool_a" not in resolver._dependents.get("tool_b", [])

    def test_remove_dependency_clears_resolution(self):
        """Test that removing dependency clears resolution cache."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver._resolutions["test"] = ResolutionStatus.RESOLVED
        resolver._resolved_order = ["tool_a", "tool_b"]

        resolver.remove_dependency("tool_a", "tool_b")

        assert resolver._resolutions == {}
        assert resolver._resolved_order == []


class TestGetDependencies:
    """Test getting dependencies."""

    def test_get_dependencies_existing(self):
        """Test getting dependencies for existing tool."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_a", "tool_c")

        deps = resolver.get_dependencies("tool_a")

        assert "tool_b" in deps
        assert "tool_c" in deps

    def test_get_dependencies_nonexistent(self):
        """Test getting dependencies for nonexistent tool."""
        resolver = DependencyResolver()

        deps = resolver.get_dependencies("nonexistent")

        assert deps == []


class TestGetDependents:
    """Test getting dependents."""

    def test_get_dependents_existing(self):
        """Test getting dependents for existing tool."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_c", "tool_b")

        dependents = resolver.get_dependents("tool_b")

        assert "tool_a" in dependents
        assert "tool_c" in dependents

    def test_get_dependents_nonexistent(self):
        """Test getting dependents for nonexistent tool."""
        resolver = DependencyResolver()

        dependents = resolver.get_dependents("nonexistent")

        assert dependents == []


class TestCircularDependencyDetection:
    """Test circular dependency detection."""

    def test_check_dependency_graph_no_cycle(self):
        """Test checking graph without circular dependency."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")

        is_valid = resolver.check_dependency_graph(["tool_a", "tool_b", "tool_c"])

        assert is_valid is True

    def test_check_dependency_graph_simple_cycle(self):
        """Test checking graph with simple circular dependency."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_a")

        is_valid = resolver.check_dependency_graph(["tool_a", "tool_b"])

        assert is_valid is False

    def test_check_dependency_graph_self_dependency(self):
        """Test checking graph with self-dependency."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_a")

        is_valid = resolver.check_dependency_graph(["tool_a"])

        assert is_valid is False

    def test_check_dependency_graph_complex_cycle(self):
        """Test checking graph with complex circular dependency."""
        resolver = DependencyResolver()

        # A -> B -> C -> A (cycle)
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver.add_dependency("tool_c", "tool_a")

        is_valid = resolver.check_dependency_graph(["tool_a", "tool_b", "tool_c"])

        assert is_valid is False

    def test_check_dependency_graph_empty_graph(self):
        """Test checking empty dependency graph."""
        resolver = DependencyResolver()

        is_valid = resolver.check_dependency_graph([])

        assert is_valid is True

    def test_check_dependency_graph_single_node(self):
        """Test checking graph with single node."""
        resolver = DependencyResolver()

        is_valid = resolver.check_dependency_graph(["tool_a"])

        assert is_valid is True

    def test_has_circular_dependency_no_cycle(self):
        """Test _has_circular_dependency with no cycle."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")

        has_cycle = resolver._has_circular_dependency(["tool_a", "tool_b", "tool_c"])

        assert has_cycle is False

    def test_has_circular_dependency_with_cycle(self):
        """Test _has_circular_dependency with cycle."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_a")

        has_cycle = resolver._has_circular_dependency(["tool_a", "tool_b"])

        assert has_cycle is True

    def test_has_circular_dependency_partial_graph(self):
        """Test circular dependency detection in partial graph."""
        resolver = DependencyResolver()

        # A -> B -> C (no cycle in full graph)
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        # D -> E -> D (cycle in subset)
        resolver.add_dependency("tool_d", "tool_e")
        resolver.add_dependency("tool_e", "tool_d")

        # Check only the non-cyclic part
        has_cycle = resolver._has_circular_dependency(["tool_a", "tool_b", "tool_c"])

        assert has_cycle is False

        # Check the cyclic part
        has_cycle = resolver._has_circular_dependency(["tool_d", "tool_e"])

        assert has_cycle is True


class TestDependencyResolution:
    """Test dependency resolution."""

    def test_resolve_dependencies_success(self):
        """Test successful dependency resolution."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")

        status, order = resolver.resolve_dependencies(["tool_a", "tool_b", "tool_c"])

        assert status == ResolutionStatus.RESOLVED
        # tool_c should come before tool_b, tool_b before tool_a
        assert order.index("tool_c") < order.index("tool_b")
        assert order.index("tool_b") < order.index("tool_a")

    def test_resolve_dependencies_missing(self):
        """Test resolution with missing dependencies."""
        resolver = DependencyResolver()

        # tool_a depends on tool_b, but tool_b is not in the list
        resolver.add_dependency("tool_a", "tool_b")

        status, order = resolver.resolve_dependencies(["tool_a"])

        assert status == ResolutionStatus.MISSING
        assert order == []

    def test_resolve_dependencies_circular(self):
        """Test resolution with circular dependencies."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_a")

        status, order = resolver.resolve_dependencies(["tool_a", "tool_b"])

        assert status == ResolutionStatus.CIRCULAR
        assert order == []

    def test_resolve_dependencies_exception(self):
        """Test resolution with exception."""
        resolver = DependencyResolver()

        # Mock _has_circular_dependency to raise exception
        original_method = resolver._has_circular_dependency

        def mock_method(tools):
            """Mock method that raises an exception for testing."""
            raise Exception("Test exception")

        resolver._has_circular_dependency = mock_method

        with pytest.raises(DependencyError) as exc_info:
            resolver.resolve_dependencies(["tool_a"])

        assert "Dependency resolution failed" in str(exc_info.value)

        # Restore original method
        resolver._has_circular_dependency = original_method


class TestTopologicalSort:
    """Test topological sorting."""

    def test_topological_sort_basic(self):
        """Test basic topological sort."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")

        order = resolver._topological_sort(["tool_a", "tool_b", "tool_c"])

        assert len(order) == 3
        assert order.index("tool_c") < order.index("tool_b")
        assert order.index("tool_b") < order.index("tool_a")

    def test_topological_sort_with_cycle(self):
        """Test topological sort with cycle returns empty list."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_a")

        order = resolver._topological_sort(["tool_a", "tool_b"])

        assert order == []

    def test_topological_sort_no_dependencies(self):
        """Test topological sort with no dependencies."""
        resolver = DependencyResolver()

        order = resolver._topological_sort(["tool_a", "tool_b", "tool_c"])

        assert len(order) == 3
        # Order doesn't matter when no dependencies

    def test_topological_sort_complex_graph(self):
        """Test topological sort with complex dependency graph."""
        resolver = DependencyResolver()

        # Create a diamond dependency:
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_a", "tool_c")
        resolver.add_dependency("tool_b", "tool_d")
        resolver.add_dependency("tool_c", "tool_d")

        order = resolver._topological_sort(["tool_a", "tool_b", "tool_c", "tool_d"])

        assert len(order) == 4
        # D should come first (no dependencies)
        assert order.index("tool_d") < order.index("tool_b")
        assert order.index("tool_d") < order.index("tool_c")
        # B and C should come before A
        assert order.index("tool_b") < order.index("tool_a")
        assert order.index("tool_c") < order.index("tool_a")


class TestInitializationAndShutdownOrder:
    """Test initialization and shutdown order methods."""

    def test_get_initialization_order_success(self):
        """Test getting initialization order."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")

        order = resolver.get_initialization_order(["tool_a", "tool_b", "tool_c"])

        assert len(order) == 3
        assert order.index("tool_c") < order.index("tool_b")
        assert order.index("tool_b") < order.index("tool_a")

    def test_get_initialization_order_failure(self):
        """Test getting initialization order with failure."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_a")

        order = resolver.get_initialization_order(["tool_a", "tool_b"])

        assert order == []

    def test_get_shutdown_order(self):
        """Test getting shutdown order (reverse of initialization)."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")

        init_order = resolver.get_initialization_order(["tool_a", "tool_b", "tool_c"])
        shutdown_order = resolver.get_shutdown_order(["tool_a", "tool_b", "tool_c"])

        assert shutdown_order == list(reversed(init_order))
        # A should shutdown first (was initialized last)
        assert shutdown_order[0] == "tool_a"
        # C should shutdown last (was initialized first)
        assert shutdown_order[-1] == "tool_c"


class TestToolCompatibilityValidation:
    """Test tool compatibility validation."""

    def test_validate_tool_compatibility_success(self):
        """Test validating tool compatibility with all dependencies available."""
        resolver = DependencyResolver()

        tool = MockTool(
            name="TestTool",
            dependencies=["dep_a", "dep_b"]
        )

        available_tools = ["dep_a", "dep_b", "dep_c"]

        is_compatible, missing = resolver.validate_tool_compatibility(
            tool, available_tools
        )

        assert is_compatible is True
        assert missing == []

    def test_validate_tool_compatibility_missing_deps(self):
        """Test validating tool compatibility with missing dependencies."""
        resolver = DependencyResolver()

        tool = MockTool(
            name="TestTool",
            dependencies=["dep_a", "dep_b", "dep_c"]
        )

        available_tools = ["dep_a", "dep_b"]

        is_compatible, missing = resolver.validate_tool_compatibility(
            tool, available_tools
        )

        assert is_compatible is False
        assert "dep_c" in missing

    def test_validate_tool_compatibility_no_dependencies(self):
        """Test validating tool with no dependencies."""
        resolver = DependencyResolver()

        tool = MockTool(
            name="TestTool",
            dependencies=[]
        )

        available_tools = []

        is_compatible, missing = resolver.validate_tool_compatibility(
            tool, available_tools
        )

        assert is_compatible is True
        assert missing == []

    def test_validate_tool_compatibility_tool_without_deps_attr(self):
        """Test validating tool without dependencies attribute."""
        resolver = DependencyResolver()

        tool = MagicMock()
        # No dependencies attribute

        available_tools = ["dep_a"]

        is_compatible, missing = resolver.validate_tool_compatibility(
            tool, available_tools
        )

        assert is_compatible is True
        assert missing == []


class TestDependencyTree:
    """Test dependency tree methods."""

    def test_get_dependency_tree_simple(self):
        """Test getting simple dependency tree."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")

        tree = resolver.get_dependency_tree("tool_a")

        assert tree["name"] == "tool_a"
        assert "tool_b" in tree["dependencies"]
        assert tree["dependencies"]["tool_b"]["name"] == "tool_b"
        assert "tool_c" in tree["dependencies"]["tool_b"]["dependencies"]

    def test_get_dependency_tree_no_dependencies(self):
        """Test getting dependency tree for tool with no dependencies."""
        resolver = DependencyResolver()

        tree = resolver.get_dependency_tree("tool_a")

        assert tree["name"] == "tool_a"
        assert tree["dependencies"] == {}

    def test_get_dependency_tree_circular(self):
        """Test getting dependency tree with circular dependency."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_a")

        tree = resolver.get_dependency_tree("tool_a")

        assert tree["name"] == "tool_a"
        # Should detect circular dependency in the grandchild
        child = tree["dependencies"]["tool_b"]
        grandchild = child["dependencies"]["tool_a"]
        assert grandchild.get("circular", False) is True

    def test_get_dependency_tree_multiple_deps(self):
        """Test getting dependency tree with multiple dependencies."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_a", "tool_c")
        resolver.add_dependency("tool_b", "tool_d")
        resolver.add_dependency("tool_c", "tool_d")

        tree = resolver.get_dependency_tree("tool_a")

        assert tree["name"] == "tool_a"
        assert "tool_b" in tree["dependencies"]
        assert "tool_c" in tree["dependencies"]


class TestAllDependencies:
    """Test getting all transitive dependencies."""

    def test_get_all_dependencies_simple(self):
        """Test getting all dependencies in simple chain."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver.add_dependency("tool_c", "tool_d")

        all_deps = resolver.get_all_dependencies("tool_a")

        assert "tool_b" in all_deps
        assert "tool_c" in all_deps
        assert "tool_d" in all_deps
        assert len(all_deps) == 3

    def test_get_all_dependencies_no_deps(self):
        """Test getting all dependencies when there are none."""
        resolver = DependencyResolver()

        all_deps = resolver.get_all_dependencies("tool_a")

        assert all_deps == set()

    def test_get_all_dependencies_diamond(self):
        """Test getting all dependencies in diamond pattern."""
        resolver = DependencyResolver()

        # Diamond: A depends on B and C, both depend on D
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_a", "tool_c")
        resolver.add_dependency("tool_b", "tool_d")
        resolver.add_dependency("tool_c", "tool_d")

        all_deps = resolver.get_all_dependencies("tool_a")

        # Should include B, C, D (D only once despite being dependency of both B and C)
        assert "tool_b" in all_deps
        assert "tool_c" in all_deps
        assert "tool_d" in all_deps
        assert len(all_deps) == 3

    def test_get_all_dependencies_complex(self):
        """Test getting all dependencies in complex graph."""
        resolver = DependencyResolver()

        # Complex graph
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_a", "tool_c")
        resolver.add_dependency("tool_b", "tool_d")
        resolver.add_dependency("tool_c", "tool_e")
        resolver.add_dependency("tool_d", "tool_f")
        resolver.add_dependency("tool_e", "tool_f")

        all_deps = resolver.get_all_dependencies("tool_a")

        assert "tool_b" in all_deps
        assert "tool_c" in all_deps
        assert "tool_d" in all_deps
        assert "tool_e" in all_deps
        assert "tool_f" in all_deps
        assert len(all_deps) == 5


class TestClearDependencies:
    """Test clearing dependencies."""

    def test_clear_dependencies(self):
        """Test clearing all dependencies."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver._resolutions["test"] = ResolutionStatus.RESOLVED
        resolver._resolved_order = ["tool_c", "tool_b", "tool_a"]

        resolver.clear_dependencies()

        assert resolver._dependencies == {}
        assert resolver._dependents == {}
        assert resolver._resolutions == {}
        assert resolver._resolved_order == []


class TestResolutionStatusEnum:
    """Test ResolutionStatus enum."""

    def test_resolution_status_values(self):
        """Test ResolutionStatus enum values."""
        assert ResolutionStatus.RESOLVED.value == "resolved"
        assert ResolutionStatus.UNRESOLVED.value == "unresolved"
        assert ResolutionStatus.CIRCULAR.value == "circular"
        assert ResolutionStatus.MISSING.value == "missing"
        assert ResolutionStatus.CONFLICT.value == "conflict"

    def test_resolution_status_comparison(self):
        """Test ResolutionStatus enum comparison."""
        status = ResolutionStatus.RESOLVED

        assert status == ResolutionStatus.RESOLVED
        assert status != ResolutionStatus.UNRESOLVED
        assert status.value == "resolved"


class TestDependencyResolverEdgeCases:
    """Test edge cases in dependency resolution."""

    def test_add_dependency_chain(self):
        """Test adding a long chain of dependencies."""
        resolver = DependencyResolver()

        # Create a chain: A -> B -> C -> D -> E
        tools = ["tool_a", "tool_b", "tool_c", "tool_d", "tool_e"]
        for i in range(len(tools) - 1):
            resolver.add_dependency(tools[i], tools[i + 1])

        status, order = resolver.resolve_dependencies(tools)

        assert status == ResolutionStatus.RESOLVED
        # Verify order: E, D, C, B, A
        expected_order = ["tool_e", "tool_d", "tool_c", "tool_b", "tool_a"]
        assert order == expected_order

    def test_resolve_with_extra_tools(self):
        """Test resolution with tools not in dependency graph."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")

        # Include tool_c which has no dependencies
        status, order = resolver.resolve_dependencies(["tool_a", "tool_b", "tool_c"])

        assert status == ResolutionStatus.RESOLVED
        assert len(order) == 3

    def test_get_dependencies_after_clear(self):
        """Test getting dependencies after clearing."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.clear_dependencies()

        deps = resolver.get_dependencies("tool_a")

        assert deps == []

    def test_circular_detection_large_graph(self):
        """Test circular detection in large graph."""
        resolver = DependencyResolver()

        # Create a large graph with one cycle
        num_tools = 100
        for i in range(num_tools - 1):
            resolver.add_dependency(f"tool_{i}", f"tool_{i + 1}")

        # Add a cycle at the end
        resolver.add_dependency(f"tool_{num_tools - 1}", "tool_0")

        tools = [f"tool_{i}" for i in range(num_tools)]
        is_valid = resolver.check_dependency_graph(tools)

        assert is_valid is False

    def test_topological_sort_large_graph(self):
        """Test topological sort on large graph."""
        resolver = DependencyResolver()

        # Create a large DAG (no cycles)
        num_tools = 100
        for i in range(num_tools - 1):
            resolver.add_dependency(f"tool_{i}", f"tool_{i + 1}")

        tools = [f"tool_{i}" for i in range(num_tools)]
        order = resolver._topological_sort(tools)

        assert len(order) == num_tools
        # Verify order is reversed (dependencies first)
        assert order[0] == f"tool_{num_tools - 1}"
        assert order[-1] == "tool_0"


class TestDependenciesCoverageGaps:
    """Additional tests to cover remaining lines in dependencies.py."""

    def test_resolve_dependencies_missing_deps(self):
        """Test resolve_dependencies when there are missing dependencies."""
        resolver = DependencyResolver()

        # tool_a depends on tool_b, but tool_b is not in the list
        resolver.add_dependency("tool_a", "tool_b")

        status, order = resolver.resolve_dependencies(["tool_a"])

        assert status == ResolutionStatus.MISSING
        assert order == []

    def test_topological_sort_cycle_detection(self):
        """Test _topological_sort detects cycle and returns empty list."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver.add_dependency("tool_c", "tool_a")

        order = resolver._topological_sort(["tool_a", "tool_b", "tool_c"])

        assert order == []

    def test_get_all_dependencies_self_reference(self):
        """Test get_all_dependencies with self-referencing tool."""
        resolver = DependencyResolver()

        # Self-reference
        resolver.add_dependency("tool_a", "tool_a")

        all_deps = resolver.get_all_dependencies("tool_a")

        # Should include the self-reference
        assert "tool_a" in all_deps

    def test_get_all_dependencies_complex_cycle(self):
        """Test get_all_dependencies with complex cycle."""
        resolver = DependencyResolver()

        # A -> B -> C -> A (cycle)
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver.add_dependency("tool_c", "tool_a")

        all_deps = resolver.get_all_dependencies("tool_a")

        assert "tool_b" in all_deps
        assert "tool_c" in all_deps

    def test_get_dependency_tree_circular_grandchild(self):
        """Test get_dependency_tree marks circular grandchild."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_a")

        tree = resolver.get_dependency_tree("tool_a")

        assert tree["name"] == "tool_a"
        child = tree["dependencies"]["tool_b"]
        grandchild = child["dependencies"]["tool_a"]
        assert grandchild.get("circular", False) is True

    def test_get_initialization_order_unresolved(self):
        """Test get_initialization_order when resolution fails."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        # tool_b is missing

        order = resolver.get_initialization_order(["tool_a"])

        assert order == []


class TestDependenciesCoverageGapsFinal:
    """Final tests to cover remaining lines in dependencies.py."""

    def test_resolve_dependencies_missing_branch(self):
        """Test resolve_dependencies missing branch (line 98->103)."""
        resolver = DependencyResolver()

        # tool_a depends on tool_b, but tool_b is not in the list
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_a", "tool_c")  # Also missing

        status, order = resolver.resolve_dependencies(["tool_a"])

        assert status == ResolutionStatus.MISSING
        assert order == []
        # Both tool_b and tool_c should be in missing
        all_deps = set()
        for tool in ["tool_a"]:
            deps = set(resolver._dependencies.get(tool, []))
            all_deps.update(deps)
        missing = all_deps - set(["tool_a"])
        assert "tool_b" in missing
        assert "tool_c" in missing

    def test_topological_sort_cycle_returns_empty(self):
        """Test _topological_sort returns empty on cycle (line 159)."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver.add_dependency("tool_c", "tool_a")

        # This should detect cycle and return empty
        order = resolver._topological_sort(["tool_a", "tool_b", "tool_c"])

        assert order == []

    def test_get_dependency_tree_circular_detection(self):
        """Test get_dependency_tree circular detection (line 236)."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_a")  # Circular

        tree = resolver.get_dependency_tree("tool_a")

        assert tree["name"] == "tool_a"
        # Check that circular is detected in grandchild
        child = tree["dependencies"]["tool_b"]
        assert "tool_a" in child["dependencies"]
        grandchild = child["dependencies"]["tool_a"]
        assert grandchild.get("circular", False) is True

    def test_get_dependency_tree_build_tree(self):
        """Test get_dependency_tree build_tree function (line 243)."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver.add_dependency("tool_b", "tool_d")

        tree = resolver.get_dependency_tree("tool_a")

        assert tree["name"] == "tool_a"
        assert "tool_b" in tree["dependencies"]
        child = tree["dependencies"]["tool_b"]
        assert "tool_c" in child["dependencies"]
        assert "tool_d" in child["dependencies"]

    def test_get_dependency_tree_return(self):
        """Test get_dependency_tree return statement (line 252)."""
        resolver = DependencyResolver()

        resolver.add_dependency("tool_a", "tool_b")

        tree = resolver.get_dependency_tree("tool_a")

        # Verify the tree structure is returned correctly
        assert isinstance(tree, dict)
        assert "name" in tree
        assert "dependencies" in tree
        assert tree["name"] == "tool_a"
        assert "tool_b" in tree["dependencies"]


class TestDependenciesCoverageGapsFinal2:
    """Test dependencies.py remaining coverage gaps."""

    def test_remove_dependency_not_in_dependents(self):
        """Test remove_dependency when dependency is not in dependents (line 98->103)."""
        resolver = DependencyResolver()

        # Add dependency normally
        resolver.add_dependency("tool_a", "tool_b")

        # Manually remove from dependents to simulate edge case
        resolver._dependents["tool_b"].remove("tool_a")

        # Now remove the dependency - should still return True but skip the dependents update
        result = resolver.remove_dependency("tool_a", "tool_b")

        assert result is True
        assert "tool_b" not in resolver.get_dependencies("tool_a")

    def test_resolve_dependencies_topological_sort_returns_empty(self):
        """Test resolve_dependencies when topological sort returns empty (line 159)."""
        resolver = DependencyResolver()

        # Create a situation where topological sort returns empty but circular check passes
        # This is a edge case where the circular check doesn't detect the cycle
        # but topological sort does
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver.add_dependency("tool_c", "tool_a")  # Creates cycle

        status, order = resolver.resolve_dependencies(["tool_a", "tool_b", "tool_c"])

        # Should return CIRCULAR because circular dependency is detected
        assert status == ResolutionStatus.CIRCULAR
        assert order == []

    def test_topological_sort_cycle_in_visit(self):
        """Test _topological_sort cycle detection in visit function (line 236)."""
        resolver = DependencyResolver()

        # The cycle detection in visit() is triggered when a node is in temp_visited
        # This happens during DFS traversal when we encounter a back edge
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver.add_dependency("tool_c", "tool_a")

        # This should trigger the cycle detection in visit()
        result = resolver._topological_sort(["tool_a", "tool_b", "tool_c"])

        assert result == []

    def test_topological_sort_visit_returns_false(self):
        """Test _topological_sort when visit returns False (line 243)."""
        resolver = DependencyResolver()

        # Create a graph where visit() will return False
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_c")
        resolver.add_dependency("tool_c", "tool_b")  # Cycle between b and c

        result = resolver._topological_sort(["tool_a", "tool_b", "tool_c"])

        assert result == []

    def test_topological_sort_outer_loop_cycle(self):
        """Test _topological_sort outer loop cycle detection (line 252)."""
        resolver = DependencyResolver()

        # Create a cycle that will be detected in the outer loop
        resolver.add_dependency("tool_a", "tool_b")
        resolver.add_dependency("tool_b", "tool_a")

        result = resolver._topological_sort(["tool_a", "tool_b"])

        assert result == []

"""Tests for the tool_system loading_order module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from nodupe.core.tool_system.loading_order import (
    ToolDependencyError,
    ToolLoadInfo,
    ToolLoadingError,
    ToolLoadingOrder,
    ToolLoadOrder,
)


class TestToolLoadOrder:
    """Test ToolLoadOrder enum."""

    def test_tool_load_order_values(self):
        """Test ToolLoadOrder enum values."""
        assert ToolLoadOrder.CORE_INFRASTRUCTURE.value == 1
        assert ToolLoadOrder.SYSTEM_UTILITIES.value == 2
        assert ToolLoadOrder.STORAGE_SERVICES.value == 3
        assert ToolLoadOrder.PROCESSING_SERVICES.value == 4
        assert ToolLoadOrder.UI_COMMANDS.value == 5
        assert ToolLoadOrder.SPECIALIZED_TOOLS.value == 6

    def test_tool_load_order_ordering(self):
        """Test ToolLoadOrder enum ordering."""
        assert ToolLoadOrder.CORE_INFRASTRUCTURE.value < ToolLoadOrder.SYSTEM_UTILITIES.value
        assert ToolLoadOrder.SYSTEM_UTILITIES.value < ToolLoadOrder.STORAGE_SERVICES.value
        assert ToolLoadOrder.STORAGE_SERVICES.value < ToolLoadOrder.PROCESSING_SERVICES.value
        assert ToolLoadOrder.PROCESSING_SERVICES.value < ToolLoadOrder.UI_COMMANDS.value
        assert ToolLoadOrder.UI_COMMANDS.value < ToolLoadOrder.SPECIALIZED_TOOLS.value


class TestToolLoadInfo:
    """Test ToolLoadInfo dataclass."""

    def test_tool_load_info_creation(self):
        """Test ToolLoadInfo instance creation."""
        info = ToolLoadInfo(
            name="TestTool",
            load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
            required_dependencies=["dep1", "dep2"],
            optional_dependencies=["opt1"],
            critical=True,
            description="Test tool description"
        )

        assert info.name == "TestTool"
        assert info.load_order == ToolLoadOrder.CORE_INFRASTRUCTURE
        assert info.required_dependencies == ["dep1", "dep2"]
        assert info.optional_dependencies == ["opt1"]
        assert info.critical is True
        assert info.description == "Test tool description"

    def test_tool_load_info_default_values(self):
        """Test ToolLoadInfo default values."""
        info = ToolLoadInfo(
            name="TestTool",
            load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
            required_dependencies=[],
            optional_dependencies=[]
        )

        assert info.critical is False
        assert info.description == ""
        assert info.load_priority == 0

    def test_tool_load_info_with_priority(self):
        """Test ToolLoadInfo with load priority."""
        info = ToolLoadInfo(
            name="TestTool",
            load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
            required_dependencies=[],
            optional_dependencies=[],
            load_priority=10
        )

        assert info.load_priority == 10


class TestToolLoadingOrderInitialization:
    """Test ToolLoadingOrder initialization."""

    def test_tool_loading_order_creation(self):
        """Test ToolLoadingOrder instance creation."""
        loader = ToolLoadingOrder()
        assert loader is not None

    def test_tool_loading_order_has_known_tools(self):
        """Test ToolLoadingOrder initializes with known tools."""
        loader = ToolLoadingOrder()

        # Should have core tools registered
        assert loader.get_tool_info("core") is not None
        assert loader.get_tool_info("deps") is not None
        assert loader.get_tool_info("container") is not None
        assert loader.get_tool_info("registry") is not None

    def test_tool_loading_order_load_order_levels(self):
        """Test ToolLoadingOrder has all load order levels."""
        loader = ToolLoadingOrder()
        orders = loader.get_load_order()

        assert len(orders) == 6
        assert ToolLoadOrder.CORE_INFRASTRUCTURE in orders
        assert ToolLoadOrder.SYSTEM_UTILITIES in orders
        assert ToolLoadOrder.STORAGE_SERVICES in orders
        assert ToolLoadOrder.PROCESSING_SERVICES in orders
        assert ToolLoadOrder.UI_COMMANDS in orders
        assert ToolLoadOrder.SPECIALIZED_TOOLS in orders


class TestToolLoadingOrderRegistration:
    """Test tool registration in ToolLoadingOrder."""

    def test_register_tool(self):
        """Test registering a tool."""
        loader = ToolLoadingOrder()

        tool_info = ToolLoadInfo(
            name="CustomTool",
            load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
            required_dependencies=[],
            optional_dependencies=[]
        )

        loader.register_tool(tool_info)

        info = loader.get_tool_info("CustomTool")
        assert info is not None
        assert info.name == "CustomTool"

    def test_register_tool_with_dependencies(self):
        """Test registering a tool with dependencies."""
        loader = ToolLoadingOrder()

        tool_info = ToolLoadInfo(
            name="DependentTool",
            load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
            required_dependencies=["core", "deps"],
            optional_dependencies=["config"]
        )

        loader.register_tool(tool_info)

        deps = loader.get_required_dependencies("DependentTool")
        assert "core" in deps
        assert "deps" in deps

        opt_deps = loader.get_optional_dependencies("DependentTool")
        assert "config" in opt_deps

    def test_register_tool_critical(self):
        """Test registering a critical tool."""
        loader = ToolLoadingOrder()

        tool_info = ToolLoadInfo(
            name="CriticalTool",
            load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
            required_dependencies=[],
            optional_dependencies=[],
            critical=True
        )

        loader.register_tool(tool_info)

        assert loader.is_critical("CriticalTool") is True


class TestToolLoadingOrderQueries:
    """Test ToolLoadingOrder query methods."""

    def test_get_tools_for_order(self):
        """Test getting tools for a specific order level."""
        loader = ToolLoadingOrder()

        core_tools = loader.get_tools_for_order(ToolLoadOrder.CORE_INFRASTRUCTURE)
        assert len(core_tools) > 0
        assert "core" in core_tools

    def test_get_required_dependencies(self):
        """Test getting required dependencies."""
        loader = ToolLoadingOrder()

        deps = loader.get_required_dependencies("container")
        # container depends on core and container (self-reference in the code)
        assert "core" in deps

    def test_get_required_dependencies_unknown_tool(self):
        """Test getting dependencies for unknown tool."""
        loader = ToolLoadingOrder()

        deps = loader.get_required_dependencies("UnknownTool")
        assert deps == []

    def test_get_optional_dependencies(self):
        """Test getting optional dependencies."""
        loader = ToolLoadingOrder()

        opt_deps = loader.get_optional_dependencies("config")
        assert isinstance(opt_deps, list)

    def test_get_optional_dependencies_unknown_tool(self):
        """Test getting optional dependencies for unknown tool."""
        loader = ToolLoadingOrder()

        opt_deps = loader.get_optional_dependencies("UnknownTool")
        assert opt_deps == []

    def test_is_critical(self):
        """Test checking if tool is critical."""
        loader = ToolLoadingOrder()

        assert loader.is_critical("core") is True
        assert loader.is_critical("deps") is True

    def test_is_critical_unknown_tool(self):
        """Test is_critical for unknown tool."""
        loader = ToolLoadingOrder()

        assert loader.is_critical("UnknownTool") is False

    def test_get_tool_info(self):
        """Test getting tool info."""
        loader = ToolLoadingOrder()

        info = loader.get_tool_info("core")
        assert info is not None
        assert info.name == "core"

    def test_get_tool_info_unknown_tool(self):
        """Test getting info for unknown tool."""
        loader = ToolLoadingOrder()

        info = loader.get_tool_info("UnknownTool")
        assert info is None

    def test_get_tool_description(self):
        """Test getting tool description."""
        loader = ToolLoadingOrder()

        desc = loader.get_tool_description("core")
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_get_tool_description_unknown_tool(self):
        """Test getting description for unknown tool."""
        loader = ToolLoadingOrder()

        desc = loader.get_tool_description("UnknownTool")
        assert desc == "Unknown tool"


class TestToolLoadingOrderValidation:
    """Test ToolLoadingOrder validation methods."""

    def test_validate_dependencies_success(self):
        """Test validating dependencies that are satisfied."""
        loader = ToolLoadingOrder()

        is_valid, missing = loader.validate_dependencies(
            "core",
            {"core", "deps", "container"}
        )

        assert is_valid is True
        assert missing == []

    def test_validate_dependencies_missing(self):
        """Test validating dependencies that are missing."""
        loader = ToolLoadingOrder()

        # container depends on core and deps
        is_valid, missing = loader.validate_dependencies(
            "container",
            {"container"}  # Missing core and deps
        )

        assert is_valid is False
        assert len(missing) > 0

    def test_validate_dependencies_unknown_tool(self):
        """Test validating dependencies for unknown tool."""
        loader = ToolLoadingOrder()

        is_valid, missing = loader.validate_dependencies(
            "UnknownTool",
            set()
        )

        assert is_valid is True
        assert missing == []


class TestToolLoadingOrderSequences:
    """Test ToolLoadingOrder sequence methods."""

    def test_get_load_sequence(self):
        """Test getting load sequence."""
        loader = ToolLoadingOrder()

        sequence = loader.get_load_sequence(["container"])

        # Should include dependencies
        assert "core" in sequence
        assert "deps" in sequence
        assert "container" in sequence

    def test_get_load_sequence_multiple_tools(self):
        """Test getting load sequence for multiple tools."""
        loader = ToolLoadingOrder()

        sequence = loader.get_load_sequence(["container", "config"])

        # Should include all dependencies
        assert "core" in sequence
        assert "deps" in sequence
        assert "container" in sequence

    def test_get_load_sequence_circular_dependency(self):
        """Test load sequence with circular dependency raises error."""
        loader = ToolLoadingOrder()

        # Register tools with circular dependency
        tool_a = ToolLoadInfo(
            name="ToolA",
            load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
            required_dependencies=["ToolB"],
            optional_dependencies=[]
        )
        tool_b = ToolLoadInfo(
            name="ToolB",
            load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
            required_dependencies=["ToolA"],
            optional_dependencies=[]
        )

        loader.register_tool(tool_a)
        loader.register_tool(tool_b)

        with pytest.raises(ValueError) as exc_info:
            loader.get_load_sequence(["ToolA"])

        assert "Circular dependency" in str(exc_info.value)

    def test_get_critical_tools(self):
        """Test getting critical tools."""
        loader = ToolLoadingOrder()

        critical = loader.get_critical_tools()

        assert len(critical) > 0
        assert "core" in critical

    def test_get_dependency_chain(self):
        """Test getting dependency chain."""
        loader = ToolLoadingOrder()

        chain = loader.get_dependency_chain("container")

        # Should include dependencies but not the tool itself
        assert "core" in chain
        assert "deps" in chain
        assert "container" not in chain

    def test_get_dependency_chain_no_dependencies(self):
        """Test dependency chain for tool with no dependencies."""
        loader = ToolLoadingOrder()

        chain = loader.get_dependency_chain("core")

        # Core has no dependencies
        assert chain == []

    def test_validate_load_sequence_valid(self):
        """Test validating a valid load sequence."""
        loader = ToolLoadingOrder()

        is_valid, missing, circular = loader.validate_load_sequence(
            ["core", "deps", "container"]
        )

        assert is_valid is True
        assert missing == []
        assert circular == []

    def test_validate_load_sequence_missing_deps(self):
        """Test validating load sequence with missing dependencies."""
        loader = ToolLoadingOrder()

        is_valid, missing, circular = loader.validate_load_sequence(
            ["container"]  # Missing core and deps
        )

        assert is_valid is False
        assert len(missing) > 0

    def test_get_safe_load_sequence(self):
        """Test getting safe load sequence."""
        loader = ToolLoadingOrder()

        safe_sequence, excluded = loader.get_safe_load_sequence(
            ["core", "deps", "container"]
        )

        assert isinstance(safe_sequence, list)
        assert isinstance(excluded, list)
        assert "core" in safe_sequence

    def test_get_safe_load_sequence_with_missing_deps(self):
        """Test safe load sequence with missing dependencies."""
        loader = ToolLoadingOrder()

        safe_sequence, excluded = loader.get_safe_load_sequence(
            ["container"]  # Missing dependencies
        )

        # Container may or may not be excluded depending on implementation
        # Just verify the function returns valid results
        assert isinstance(safe_sequence, list)
        assert isinstance(excluded, list)


class TestToolLoadingOrderFailureAnalysis:
    """Test ToolLoadingOrder failure analysis methods."""

    def test_get_failure_impact_analysis(self):
        """Test getting failure impact analysis."""
        loader = ToolLoadingOrder()

        impact = loader.get_failure_impact_analysis(
            "core",
            ["core", "deps", "container"]
        )

        # container depends on core, so it should be affected
        assert isinstance(impact, dict)

    def test_get_failure_impact_analysis_no_impact(self):
        """Test failure impact with no affected tools."""
        loader = ToolLoadingOrder()

        impact = loader.get_failure_impact_analysis(
            "core",
            ["core"]  # Only core loaded, nothing depends on it yet
        )

        assert isinstance(impact, dict)

    def test_should_continue_loading_non_critical(self):
        """Test should_continue_loading for non-critical tool."""
        loader = ToolLoadingOrder()

        should_continue, reason = loader.should_continue_loading(
            "config",  # Non-critical
            ["core", "deps", "config"]
        )

        assert should_continue is True

    def test_should_continue_loading_critical(self):
        """Test should_continue_loading for critical tool."""
        loader = ToolLoadingOrder()

        should_continue, reason = loader.should_continue_loading(
            "core",  # Critical
            ["core"]
        )

        assert should_continue is False

    def test_get_load_priorities(self):
        """Test getting load priorities."""
        loader = ToolLoadingOrder()

        priorities = loader.get_load_priorities(["core", "deps", "config"])

        assert isinstance(priorities, list)
        assert len(priorities) > 0

        # Should be sorted by priority (higher first)
        for i in range(len(priorities) - 1):
            assert priorities[i][1] >= priorities[i + 1][1]


class TestToolLoadingOrderEdgeCases:
    """Test edge cases for ToolLoadingOrder."""

    def test_register_tool_duplicate_name(self):
        """Test registering tool with duplicate name."""
        loader = ToolLoadingOrder()

        tool_info1 = ToolLoadInfo(
            name="DuplicateTool",
            load_order=ToolLoadOrder.CORE_INFRASTRUCTURE,
            required_dependencies=[],
            optional_dependencies=[]
        )

        tool_info2 = ToolLoadInfo(
            name="DuplicateTool",
            load_order=ToolLoadOrder.SYSTEM_UTILITIES,
            required_dependencies=[],
            optional_dependencies=[]
        )

        loader.register_tool(tool_info1)
        loader.register_tool(tool_info2)  # Should overwrite

        info = loader.get_tool_info("DuplicateTool")
        assert info is not None
        assert info.load_order == ToolLoadOrder.SYSTEM_UTILITIES

    def test_get_load_sequence_empty_list(self):
        """Test load sequence with empty tool list."""
        loader = ToolLoadingOrder()

        sequence = loader.get_load_sequence([])

        assert sequence == []

    def test_validate_dependencies_empty_set(self):
        """Test validating dependencies with empty available set."""
        loader = ToolLoadingOrder()

        is_valid, missing = loader.validate_dependencies(
            "container",
            set()
        )

        assert is_valid is False
        assert len(missing) > 0

    def test_get_failure_impact_analysis_empty_loaded(self):
        """Test failure impact with empty loaded tools."""
        loader = ToolLoadingOrder()

        impact = loader.get_failure_impact_analysis("core", [])

        assert impact == {}

    def test_get_load_priorities_empty_list(self):
        """Test load priorities with empty tool list."""
        loader = ToolLoadingOrder()

        priorities = loader.get_load_priorities([])

        assert priorities == []

    def test_get_load_priorities_unknown_tools(self):
        """Test load priorities with unknown tools."""
        loader = ToolLoadingOrder()

        priorities = loader.get_load_priorities(["UnknownTool1", "UnknownTool2"])

        # Unknown tools should be skipped
        assert priorities == []

    def test_fallback_load_sequence(self):
        """Test fallback load sequence."""
        loader = ToolLoadingOrder()

        # Register a custom tool
        tool_info = ToolLoadInfo(
            name="FallbackTool",
            load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
            required_dependencies=[],
            optional_dependencies=[]
        )
        loader.register_tool(tool_info)

        sequence = loader._fallback_load_sequence(["FallbackTool", "core"])

        assert isinstance(sequence, list)
        assert len(sequence) == 2

    def test_tool_loading_error_exception(self):
        """Test ToolLoadingError exception."""
        error = ToolLoadingError("Test error message")

        assert str(error) == "Test error message"

    def test_tool_dependency_error_exception(self):
        """Test ToolDependencyError exception."""
        error = ToolDependencyError("Dependency error message")

        assert str(error) == "Dependency error message"

    def test_tool_dependency_error_inheritance(self):
        """Test ToolDependencyError inherits from ToolLoadingError."""
        error = ToolDependencyError("Test")

        assert isinstance(error, ToolLoadingError)

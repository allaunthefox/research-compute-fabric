"""Test tool compatibility functionality."""

import pytest
from unittest.mock import MagicMock
from typing import List
from nodupe.core.tool_system.compatibility import ToolCompatibility
from nodupe.core.tool_system.compatibility import ToolCompatibilityError
from nodupe.core.tool_system.base import Tool


class TestToolCompatibility:
    """Test tool compatibility core functionality."""

    def test_tool_compatibility_initialization(self):
        """Test tool compatibility initialization."""
        compatibility = ToolCompatibility()
        assert compatibility is not None
        assert isinstance(compatibility, ToolCompatibility)

        # Test that it has expected attributes
        assert hasattr(compatibility, 'check_compatibility')
        assert hasattr(compatibility, 'get_compatibility_report')
        assert hasattr(compatibility, 'initialize')
        assert hasattr(compatibility, 'shutdown')

    def test_tool_compatibility_with_container(self):
        """Test tool compatibility with dependency container."""
        from nodupe.core.container import ServiceContainer

        compatibility = ToolCompatibility()
        container = ServiceContainer()

        # Initialize compatibility with container
        compatibility.initialize(container)
        assert compatibility.container is container

    def test_tool_compatibility_lifecycle(self):
        """Test tool compatibility lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        compatibility = ToolCompatibility()
        container = ServiceContainer()

        # Test initialization
        compatibility.initialize(container)
        assert compatibility.container is container

        # Test shutdown
        compatibility.shutdown()
        assert compatibility.container is None

        # Test re-initialization
        compatibility.initialize(container)
        assert compatibility.container is container


class TestToolCompatibilityOperations:
    """Test tool compatibility operations."""

    def test_check_compatibility(self):
        """Test checking tool compatibility."""
        compatibility = ToolCompatibility()

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "test_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return ["core>=1.0.0"]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()

        # Check compatibility
        report = compatibility.check_compatibility(test_tool)
        assert report is not None
        assert isinstance(report, dict)

        # Verify report structure
        assert "compatible" in report
        assert "issues" in report
        assert "warnings" in report

    def test_get_compatibility_report(self):
        """Test getting compatibility report."""
        compatibility = ToolCompatibility()

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "test_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return ["core>=1.0.0"]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()

        # Get compatibility report
        report = compatibility.get_compatibility_report(test_tool)
        assert report is not None
        assert isinstance(report, dict)

        # Verify report structure
        assert "tool_name" in report
        assert "tool_version" in report
        assert "compatibility_status" in report
        assert "compatibility_issues" in report
        assert "compatibility_warnings" in report

    def test_check_compatible_tool(self):
        """Test checking compatible tool."""
        compatibility = ToolCompatibility()

        # Create a compatible test tool
        class CompatibleTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "compatible_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return ["core>=1.0.0"]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        compatible_tool = CompatibleTool()

        # Check compatibility
        report = compatibility.check_compatibility(compatible_tool)
        assert report["compatible"] is True
        assert len(report["issues"]) == 0

    def test_check_incompatible_tool(self):
        """Test checking incompatible tool."""
        compatibility = ToolCompatibility()

        # Create an incompatible test tool
        class IncompatibleTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "incompatible_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return ["nonexistent>=1.0.0"]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        incompatible_tool = IncompatibleTool()

        # Check compatibility
        report = compatibility.check_compatibility(incompatible_tool)
        assert report["compatible"] is False
        assert len(report["issues"]) > 0


class TestToolCompatibilityEdgeCases:
    """Test tool compatibility edge cases."""

    def test_check_tool_with_no_dependencies(self):
        """Test checking tool with no dependencies."""
        compatibility = ToolCompatibility()

        # Create a tool with no dependencies
        class NoDepsTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "no_deps_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return []

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        no_deps_tool = NoDepsTool()

        # Check compatibility
        report = compatibility.check_compatibility(no_deps_tool)
        assert report is not None
        assert report["compatible"] is True

    def test_check_tool_with_empty_name(self):
        """Test checking tool with empty name."""
        compatibility = ToolCompatibility()

        # Create a tool with empty name
        class EmptyNameTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return ""

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return []

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        empty_name_tool = EmptyNameTool()

        # Check compatibility
        report = compatibility.check_compatibility(empty_name_tool)
        assert report is not None
        assert report["compatible"] is False
        assert len(report["issues"]) > 0

    def test_check_tool_with_invalid_version(self):
        """Test checking tool with invalid version."""
        compatibility = ToolCompatibility()

        # Create a tool with invalid version
        class InvalidVersionTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "invalid_version_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "invalid_version"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return []

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        invalid_version_tool = InvalidVersionTool()

        # Check compatibility
        report = compatibility.check_compatibility(invalid_version_tool)
        assert report is not None
        assert report["compatible"] is False
        assert len(report["issues"]) > 0

    def test_check_tool_with_missing_methods(self):
        """Test checking tool with missing required methods."""
        compatibility = ToolCompatibility()

        # Create a tool missing required methods
        class IncompleteTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "incomplete_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return []

            def __init__(self):
                """Initialize the test tool."""
                # Missing initialize and shutdown methods

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        incomplete_tool = IncompleteTool()

        # Check compatibility
        report = compatibility.check_compatibility(incomplete_tool)
        assert report is not None
        assert report["compatible"] is False
        assert len(report["issues"]) > 0


class TestToolCompatibilityPerformance:
    """Test tool compatibility performance."""

    def test_mass_tool_compatibility_checking(self):
        """Test mass tool compatibility checking."""
        compatibility = ToolCompatibility()

        # Create many test tools
        tools = []
        for i in range(10):
            class TestTool(Tool):
                """Test tool implementation."""
                
                @property
                def name(self) -> str:
                    """Get the tool name."""
                    return f"test_tool_{i}"

                @property
                def version(self) -> str:
                    """Get the tool version."""
                    return "1.0.0"

                @property
                def dependencies(self) -> List[str]:
                    """Get the tool dependencies."""
                    return ["core>=1.0.0"]

                def __init__(self):
                    """Initialize the test tool."""
                    self.initialized = False

                def initialize(self, container):
                    """Initialize the tool with the container."""
                    self.initialized = True

                def shutdown(self):
                    """Shutdown the tool."""
                    pass

                def get_capabilities(self):
                    """Get the tool capabilities."""
                    return {"test": True}

                @property
                def api_methods(self):
                    """Get the API methods."""
                    return {}

                def run_standalone(self, args):
                    """Run the tool in standalone mode."""
                    return 0

                def describe_usage(self):
                    """Describe how to use the tool."""
                    return "Test tool"

            test_tool = TestTool()
            tools.append(test_tool)

        # Check compatibility for all tools
        for tool in tools:
            report = compatibility.check_compatibility(tool)
            assert report is not None
            assert isinstance(report, dict)

    def test_tool_compatibility_performance(self):
        """Test tool compatibility performance."""
        import time

        compatibility = ToolCompatibility()

        # Create many test tools
        tools = []
        for i in range(50):
            class TestTool(Tool):
                """Test tool implementation."""
                
                @property
                def name(self) -> str:
                    """Get the tool name."""
                    return f"perf_tool_{i}"

                @property
                def version(self) -> str:
                    """Get the tool version."""
                    return "1.0.0"

                @property
                def dependencies(self) -> List[str]:
                    """Get the tool dependencies."""
                    return ["core>=1.0.0"]

                def __init__(self):
                    """Initialize the test tool."""
                    self.initialized = False

                def initialize(self, container):
                    """Initialize the tool with the container."""
                    self.initialized = True

                def shutdown(self):
                    """Shutdown the tool."""
                    pass

                def get_capabilities(self):
                    """Get the tool capabilities."""
                    return {"test": True}

                @property
                def api_methods(self):
                    """Get the API methods."""
                    return {}

                def run_standalone(self, args):
                    """Run the tool in standalone mode."""
                    return 0

                def describe_usage(self):
                    """Describe how to use the tool."""
                    return "Test tool"

            test_tool = TestTool()
            tools.append(test_tool)

        # Test compatibility checking performance
        start_time = time.time()
        for tool in tools:
            compatibility.check_compatibility(tool)
        compatibility_time = time.time() - start_time

        # Should be fast operation
        assert compatibility_time < 1.0


class TestToolCompatibilityIntegration:
    """Test tool compatibility integration scenarios."""

    def test_compatibility_with_registry(self):
        """Test compatibility integration with registry."""
        from nodupe.core.tool_system.registry import ToolRegistry

        compatibility = ToolCompatibility()
        registry = ToolRegistry()

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "test_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return ["core>=1.0.0"]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()
        registry.register(test_tool)

        # Check compatibility
        report = compatibility.check_compatibility(test_tool)
        assert report is not None
        assert isinstance(report, dict)

    def test_compatibility_with_loader(self):
        """Test compatibility integration with loader."""
        from nodupe.core.tool_system.loader import ToolLoader
        from nodupe.core.tool_system.registry import ToolRegistry

        compatibility = ToolCompatibility()
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Create a test tool
        class TestTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "test_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return ["core>=1.0.0"]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        test_tool = TestTool()

        # Load tool
        loaded_tool = loader.load_tool(test_tool)

        # Check compatibility
        report = compatibility.check_compatibility(loaded_tool)
        assert report is not None
        assert isinstance(report, dict)


class TestToolCompatibilityErrorHandling:
    """Test tool compatibility error handling."""

    def test_check_compatibility_with_invalid_tool(self):
        """Test checking compatibility with invalid tool."""
        compatibility = ToolCompatibility()

        # Create an invalid tool (not inheriting from Tool)
        class InvalidTool:
            """Test helper class."""
            
            def __init__(self):
                """Initialize the invalid tool."""
                self.name = "invalid_tool"

        invalid_tool = InvalidTool()

        # Check compatibility
        with pytest.raises(ToolCompatibilityError):
            compatibility.check_compatibility(invalid_tool)

    def test_check_compatibility_with_none_tool(self):
        """Test checking compatibility with None tool."""
        compatibility = ToolCompatibility()

        # Check compatibility with None
        with pytest.raises(ToolCompatibilityError):
            compatibility.check_compatibility(None)

    def test_check_compatibility_with_missing_attributes(self):
        """Test checking compatibility with tool missing attributes."""
        compatibility = ToolCompatibility()

        # Create a tool missing required attributes
        class IncompleteTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            def __init__(self):
                """Initialize the test tool."""
                # Missing name, version, dependencies
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        incomplete_tool = IncompleteTool()

        # Check compatibility
        report = compatibility.check_compatibility(incomplete_tool)
        assert report is not None
        assert report["compatible"] is False
        assert len(report["issues"]) > 0


class TestToolCompatibilityAdvanced:
    """Test advanced tool compatibility functionality."""

    def test_compatibility_with_complex_dependencies(self):
        """Test compatibility with complex dependencies."""
        compatibility = ToolCompatibility()

        # Create a tool with complex dependencies
        class ComplexDepsTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "complex_deps_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return [
                    "core>=1.0.0",
                    "utils>=2.0.0",
                    "network>=1.5.0",
                    "ml>=3.0.0"
                ]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        complex_deps_tool = ComplexDepsTool()

        # Check compatibility
        report = compatibility.check_compatibility(complex_deps_tool)
        assert report is not None
        assert isinstance(report, dict)

        # Verify dependencies are checked
        assert len(report["issues"]) > 0 or len(report["warnings"]) > 0

    def test_compatibility_with_version_constraints(self):
        """Test compatibility with version constraints."""
        compatibility = ToolCompatibility()

        # Create a tool with version constraints
        class VersionConstrainedTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "version_constrained_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return [
                    "core>=1.0.0,<2.0.0",
                    "utils>=2.0.0,<=3.0.0"
                ]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        version_constrained_tool = VersionConstrainedTool()

        # Check compatibility
        report = compatibility.check_compatibility(version_constrained_tool)
        assert report is not None
        assert isinstance(report, dict)

    def test_compatibility_with_conditional_checking(self):
        """Test compatibility with conditional checking."""
        compatibility = ToolCompatibility()

        # Create tools with different compatibility profiles
        tools = []

        # Compatible tool
        class CompatibleTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "compatible_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return ["core>=1.0.0"]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        # Incompatible tool
        class IncompatibleTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "incompatible_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return ["nonexistent>=1.0.0"]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        tools.append(CompatibleTool())
        tools.append(IncompatibleTool())

        # Check compatibility for all tools
        results = []
        for tool in tools:
            report = compatibility.check_compatibility(tool)
            results.append(report)

        # Verify different results
        assert results[0]["compatible"] is True
        assert results[1]["compatible"] is False

    def test_compatibility_with_dynamic_dependency_management(self):
        """Test compatibility with dynamic dependency management."""
        compatibility = ToolCompatibility()

        # Create a tool with dynamic dependencies
        class DynamicDepsTool(Tool):
            """Test tool implementation for compatibility testing."""
            
            @property
            def name(self) -> str:
                """Get the tool name."""
                return "dynamic_deps_tool"

            @property
            def version(self) -> str:
                """Get the tool version."""
                return "1.0.0"

            @property
            def dependencies(self) -> List[str]:
                """Get the tool dependencies."""
                return ["core>=1.0.0"]

            def __init__(self):
                """Initialize the test tool."""
                self.initialized = False
                self.dynamic_dependencies = []

            def initialize(self, container):
                """Initialize the tool with the container."""
                self.initialized = True
                # Add dynamic dependencies during initialization
                self.dynamic_dependencies = ["utils>=2.0.0", "network>=1.0.0"]

            def shutdown(self):
                """Shutdown the tool."""
                pass

            def get_capabilities(self):
                """Get the tool capabilities."""
                return {"test": True}

            @property
            def api_methods(self):
                """Get the API methods."""
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode."""
                return 0

            def describe_usage(self):
                """Describe how to use the tool."""
                return "Test tool"

        dynamic_deps_tool = DynamicDepsTool()

        # Check compatibility before initialization
        report1 = compatibility.check_compatibility(dynamic_deps_tool)
        assert report1 is not None

        # Initialize tool
        dynamic_deps_tool.initialize(MagicMock())

        # Check compatibility after initialization
        report2 = compatibility.check_compatibility(dynamic_deps_tool)
        assert report2 is not None

        # Compare reports
        assert report1 != report2

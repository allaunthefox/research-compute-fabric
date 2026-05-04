"""Tests for tool loading order functionality.

This module tests the ToolLoadingOrder class which manages the order in which
tools are loaded, handles dependencies, and provides fallback sequences.
"""

import unittest
from unittest.mock import Mock, patch

from nodupe.core.tool_system.loading_order import ToolLoadInfo, ToolLoadingOrder
from nodupe.core.tool_system.loading_order import ToolLoadOrder as LoadOrder
from nodupe.core.tool_system.loading_order import get_tool_loading_order, reset_tool_loading_order


class TestLoadingOrder(unittest.TestCase):
    """Tests for ToolLoadingOrder class."""

    def setUp(self):
        """Set up test fixtures."""
        self.loader = ToolLoadingOrder()
        # Clear default tools for cleaner testing if needed, or just work with them
        # self.loader._tool_info.clear() 
        # But _initialize_known_tools is called in __init__, so we might want to test those first.

    def test_initialization_defaults(self):
        """Test that core tools are initialized with correct defaults.
        
        Verifies that the 'core' and 'config' tools exist and have the correct
        criticality settings.
        """
        # Verify core tools are present
        self.assertIsNotNone(self.loader.get_tool_info("core"))
        self.assertIsNotNone(self.loader.get_tool_info("config"))
        self.assertTrue(self.loader.is_critical("core"))
        self.assertFalse(self.loader.is_critical("config"))

    def test_register_tool(self):
        """Test registering a new tool with the loader.
        
        Verifies that:
        - Tool info can be registered
        - Tool appears in correct load order group
        - Reverse dependencies are tracked
        """
        info = ToolLoadInfo(
            name="custom_tool",
            load_order=LoadOrder.SPECIALIZED_TOOLS,
            required_dependencies=["core"],
            optional_dependencies=[],
            critical=False
        )
        self.loader.register_tool(info)
        self.assertIsNotNone(self.loader.get_tool_info("custom_tool"))
        self.assertIn("custom_tool", self.loader._load_order_groups[LoadOrder.SPECIALIZED_TOOLS])
        self.assertIn("custom_tool", self.loader._reverse_dependencies["core"])

    def test_dependency_chain_simple(self):
        """Test simple dependency chain resolution.
        
        Verifies that when A depends on B, the dependency chain returns [B].
        """
        # A depends on B
        info_b = ToolLoadInfo("B", LoadOrder.CORE_INFRASTRUCTURE, [], [])
        info_a = ToolLoadInfo("A", LoadOrder.SYSTEM_UTILITIES, ["B"], [])
        
        self.loader.register_tool(info_b)
        self.loader.register_tool(info_a)
        
        chain = self.loader.get_dependency_chain("A")
        self.assertEqual(chain, ["B"])

    def test_dependency_chain_circular(self):
        """Test circular dependency detection.
        
        Verifies that circular dependencies (A->B->A) raise ValueError.
        """
        # A depends on B, B depends on A
        info_a = ToolLoadInfo("CircA", LoadOrder.CORE_INFRASTRUCTURE, ["CircB"], [])
        info_b = ToolLoadInfo("CircB", LoadOrder.CORE_INFRASTRUCTURE, ["CircA"], [])
        
        self.loader.register_tool(info_a)
        self.loader.register_tool(info_b)
        
        # get_load_sequence should raise ValueError
        with self.assertRaises(ValueError):
            self.loader.get_load_sequence(["CircA", "CircB"])

    def test_get_load_sequence_complex(self):
        """Test complex load sequence with multiple dependencies.
        
        Verifies that C->B->A chain resolves to [A, B, C] order.
        """
        # C -> B -> A
        info_a = ToolLoadInfo("SeqA", LoadOrder.CORE_INFRASTRUCTURE, [], [])
        info_b = ToolLoadInfo("SeqB", LoadOrder.SYSTEM_UTILITIES, ["SeqA"], [])
        info_c = ToolLoadInfo("SeqC", LoadOrder.STORAGE_SERVICES, ["SeqB"], [])

        self.loader.register_tool(info_a)
        self.loader.register_tool(info_b)
        self.loader.register_tool(info_c)

        # Requesting just C should pull in B and A
        seq = self.loader.get_load_sequence(["SeqC"])
        # Order should be A, B, C (assuming correct topological sort)
        # Note: visited logic adds node AFTER dependencies
        expected_subset = ["SeqA", "SeqB", "SeqC"]
        filtered_seq = [x for x in seq if x in expected_subset]
        self.assertEqual(filtered_seq, expected_subset)

    def test_validate_dependencies(self):
        """Test dependency validation.
        
        Verifies that:
        - Missing required dependencies are detected
        - Present dependencies pass validation
        """
        info = ToolLoadInfo("ValA", LoadOrder.CORE_INFRASTRUCTURE, ["ValB"], [])
        self.loader.register_tool(info)
        
        # ValB missing
        is_valid, missing = self.loader.validate_dependencies("ValA", set())
        self.assertFalse(is_valid)
        self.assertIn("ValB", missing)
        
        # ValB present
        is_valid, missing = self.loader.validate_dependencies("ValA", {"ValB"})
        self.assertTrue(is_valid)

    def test_validate_load_sequence(self):
        """Test load sequence validation with missing dependencies.
        
        Verifies that validation detects missing dependencies in load sequence.
        """
        info = ToolLoadInfo("ValA", LoadOrder.CORE_INFRASTRUCTURE, ["MissingDep"], [])
        self.loader.register_tool(info)
        
        is_valid, missing, circular = self.loader.validate_load_sequence(["ValA"])
        self.assertFalse(is_valid)
        self.assertTrue(any("MissingDep" in m for m in missing))

    def test_get_safe_load_sequence_with_missing(self):
        """Test safe load sequence generation with missing dependencies.
        
        Verifies that tools with missing dependencies are excluded from safe sequence.
        """
        # A depends on Missing
        info_a = ToolLoadInfo("SafeA", LoadOrder.CORE_INFRASTRUCTURE, ["Missing"], [])
        self.loader.register_tool(info_a)
        
        safe, excluded = self.loader.get_safe_load_sequence(["SafeA"])
        self.assertNotIn("SafeA", safe)
        self.assertTrue(any("SafeA" in e for e in excluded))

    def test_failure_impact_analysis(self):
        """Test failure impact analysis for tool dependencies.
        
        Verifies that impact analysis correctly identifies all tools affected
        when a given tool fails.
        """
        # B depends on A
        info_a = ToolLoadInfo("ImpA", LoadOrder.CORE_INFRASTRUCTURE, [], [])
        info_b = ToolLoadInfo("ImpB", LoadOrder.SYSTEM_UTILITIES, ["ImpA"], [])
        
        self.loader.register_tool(info_a)
        self.loader.register_tool(info_b)
        
        impact = self.loader.get_failure_impact_analysis("ImpA", ["ImpA", "ImpB"])
        self.assertIn("ImpA", impact)
        self.assertIn("ImpB", impact["ImpA"])

    def test_should_continue_loading(self):
        """Test continue loading decision based on tool criticality.
        
        Verifies that:
        - Critical tool failures stop loading
        - Non-critical tool failures allow continuing
        """
        info_crit = ToolLoadInfo("Crit", LoadOrder.CORE_INFRASTRUCTURE, [], [], critical=True)
        info_non = ToolLoadInfo("NonCrit", LoadOrder.CORE_INFRASTRUCTURE, [], [], critical=False)
        
        self.loader.register_tool(info_crit)
        self.loader.register_tool(info_non)
        
        should_cont, reason = self.loader.should_continue_loading("Crit", [])
        self.assertFalse(should_cont)
        
        should_cont, reason = self.loader.should_continue_loading("NonCrit", [])
        self.assertTrue(should_cont)

    def test_get_load_priorities(self):
        """Test load priority calculation.
        
        Verifies that priorities are calculated correctly based on:
        - Load order (core tools have higher priority)
        - Criticality (+50 for critical tools)
        - Number of dependents
        """
        # A: Core (High), Critical (+50), No deps
        # B: Specialized (Low), Non-Critical, Depends on A (A gets bonus?)
        
        info_a = ToolLoadInfo("PrioA", LoadOrder.CORE_INFRASTRUCTURE, [], [], critical=True)
        info_b = ToolLoadInfo("PrioB", LoadOrder.SPECIALIZED_TOOLS, ["PrioA"], [], critical=False)
        
        self.loader.register_tool(info_a)
        self.loader.register_tool(info_b)
        
        priorities = self.loader.get_load_priorities(["PrioA", "PrioB"])
        # PrioA should be higher than PrioB
        # PrioA score: (6-1)*100 = 500 + 50 (crit) + 10 (1 reversedep) = 560
        # PrioB score: (6-6)*100 = 0 + 0 + 0 = 0
        
        self.assertEqual(priorities[0][0], "PrioA")
        self.assertEqual(priorities[1][0], "PrioB")

    def test_callbacks(self):
        """Test load callback registration and notification.
        
        Verifies that:
        - Callbacks are called when tool is loaded
        - Callback errors are handled gracefully
        """
        mock_cb = Mock()
        self.loader.register_load_callback("CallbackTool", mock_cb)
        self.loader.notify_tool_loaded("CallbackTool")
        mock_cb.assert_called_with("CallbackTool")
        
        # Test error handling in callback
        mock_cb_err = Mock(side_effect=Exception("Boom"))
        self.loader.register_load_callback("CallbackTool", mock_cb_err)
        # Should not raise
        self.loader.notify_tool_loaded("CallbackTool")

    def test_get_tool_statistics(self):
        """Test tool statistics retrieval.
        
        Verifies that statistics include total tools, tools by order, and critical tools.
        """
        stats = self.loader.get_tool_statistics()
        self.assertIn('total_tools', stats)
        self.assertIn('tools_by_order', stats)
        self.assertIn('critical_tools', stats)

    def test_singleton(self):
        """Test that get_tool_loading_order returns a singleton.
        
        Verifies that:
        - Multiple calls return the same instance
        - Reset creates a new instance
        """
        reset_tool_loading_order()
        l1 = get_tool_loading_order()
        l2 = get_tool_loading_order()
        self.assertIs(l1, l2)
        
        reset_tool_loading_order()
        l3 = get_tool_loading_order()
        self.assertIsNot(l1, l3)

    def test_helpers(self):
        """Test helper methods for tool information retrieval.
        
        Verifies that:
        - Required/optional dependencies are returned correctly
        - Tool descriptions work for known and unknown tools
        """
        self.assertEqual(self.loader.get_required_dependencies("core"), [])
        self.assertEqual(self.loader.get_optional_dependencies("core"), [])
        self.assertNotEqual(self.loader.get_tool_description("core"), "Unknown tool")
        self.assertEqual(self.loader.get_tool_description("invalid_tool"), "Unknown tool")
        
        self.assertEqual(self.loader.get_required_dependencies("unknown"), [])
        self.assertEqual(self.loader.get_optional_dependencies("unknown"), [])

    def test_fallback_sequence(self):
        """Test fallback sequence when circular dependencies occur.
        
        Verifies that when circular dependencies are detected, a fallback
        sequence is generated based on load order.
        """
        # Force a circular dependency error to trigger fallback in get_safe_load_sequence
        # Assuming we can mock get_load_sequence to raise ValueError
        with patch.object(self.loader, 'get_load_sequence', side_effect=ValueError("Circular")):
            # Register simplistic tools for fallback test
            info_a = ToolLoadInfo("FallA", LoadOrder.CORE_INFRASTRUCTURE, [], [])
            info_b = ToolLoadInfo("FallB", LoadOrder.SYSTEM_UTILITIES, [], [])
            self.loader.register_tool(info_a)
            self.loader.register_tool(info_b)
            
            safe, excluded = self.loader.get_safe_load_sequence(["FallB", "FallA"])
            # Fallback sorts by order: A (Core) then B (System)
            self.assertEqual(safe, ["FallA", "FallB"])

if __name__ == '__main__':
    unittest.main()

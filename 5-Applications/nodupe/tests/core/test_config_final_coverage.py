# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Final coverage tests for config.py - covering remaining gaps."""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from nodupe.core.config import ConfigManager


class TestConfigFinalCoverage(unittest.TestCase):
    """Tests to cover final gaps in config.py."""

    def test_get_config_value_exception_path(self):
        """Cover lines 107-108: get_config_value exception handling."""
        from nodupe.core.config import ConfigManager

        # Create a manager with a mock config that raises exception on get()
        manager = ConfigManager.__new__(ConfigManager)
        manager.config = {}

        # Mock the nested dict to raise exception
        mock_section = Mock()
        mock_section.get.side_effect = RuntimeError("Test error")

        # We need get_nodupe_config to return something that raises exception
        # The actual exception handler is in get_config_value
        manager.config = Mock()
        manager.config.get.side_effect = RuntimeError("Config error")

        # get_config_value should catch the exception and return default
        result = manager.get_config_value("section", "key", "default_value")
        self.assertEqual(result, "default_value")


class TestVersioningFullCoverage(unittest.TestCase):
    """Ensure versioning.py stays at 100%."""

    def test_versioning_100_percent(self):
        """Verify versioning.py coverage remains at 100%."""
        from nodupe.core.api.versioning import (
            APIVersion,
            VersionedFunction,
            get_api_version,
            is_api_deprecated,
            versioned,
        )

        # Test all public APIs
        api = APIVersion("v1")
        api.register_version("v2")
        api.set_current_version("v2")

        # Test deprecation
        api.deprecate_version("v1", "v2")
        self.assertTrue(api.is_version_deprecated("v1"))
        self.assertFalse(api.is_version_deprecated("v2"))
        msg = api.get_deprecation_message("v1")
        self.assertIn("v1", msg)
        self.assertIn("v2", msg)

        # Test versioned decorator
        @versioned("v1")
        def func_v1():
            """Version 1 function for testing."""
            return "v1"

        @versioned("v2", deprecated=True)
        def func_v2():
            """Version 2 function that is deprecated."""
            return "v2"

        # Test get_api_version
        self.assertEqual(get_api_version(func_v1), "v1")
        self.assertEqual(get_api_version(func_v2), "v2")
        self.assertIsNone(get_api_version(lambda: None))

        # Test is_api_deprecated
        self.assertFalse(is_api_deprecated(func_v1))
        self.assertTrue(is_api_deprecated(func_v2))
        self.assertFalse(is_api_deprecated(lambda: None))

        # Test VersionedFunction dataclass
        vf = VersionedFunction(func_v1, "v1")
        self.assertEqual(vf.version, "v1")
        self.assertFalse(vf.deprecated)

        vf2 = VersionedFunction(func_v2, "v2", deprecated=True, deprecation_message="Use v2")
        self.assertEqual(vf2.version, "v2")
        self.assertTrue(vf2.deprecated)
        self.assertEqual(vf2.deprecation_message, "Use v2")


if __name__ == '__main__':
    unittest.main()

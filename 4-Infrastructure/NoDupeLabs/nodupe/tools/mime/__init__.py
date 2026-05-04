# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Standard MIME Detection Tool for NoDupeLabs.

Provides MIME type detection capabilities as a tool.
"""

from .mime_tool import register_tool

__all__ = ['register_tool']

from typing import List, Dict, Any, Optional, Callable
from nodupe.core.tool_system.base import Tool
from .mime_logic import MIMEDetection


class StandardMIMETool(Tool):
    """Standard MIME detection tool using mimetypes."""

    @property
    def name(self) -> str:
        """Get tool name.
        
        Returns:
            Tool name identifier
        """
        return "standard_mime"

    @property
    def version(self) -> str:
        """Get tool version.
        
        Returns:
            Version string in semver format
        """
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        """Get tool dependencies.
        
        Returns:
            List of dependency names
        """
        return []

    @property
    def api_methods(self) -> Dict[str, Callable[..., Any]]:
        """Get API methods exposed by this tool.
        
        Returns:
            Dictionary mapping method names to callable functions
        """
        return {
            'detect_mime_type': self.detector.detect_mime_type,
            'is_text': self.detector.is_text,
            'is_image': self.detector.is_image,
            'is_archive': self.detector.is_archive
        }

    def __init__(self):
        """Initialize the tool."""
        self.detector = MIMEDetection()

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services."""
        container.register_service('mime_service', self.detector)

    def shutdown(self) -> None:
        """Shutdown the tool."""

    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities."""
        return {
            'features': ['magic_number_detection', 'extension_mapping', 'rfc6838_compliance']
        }


def register_tool():
    """Register the MIME tool."""
    return StandardMIMETool()

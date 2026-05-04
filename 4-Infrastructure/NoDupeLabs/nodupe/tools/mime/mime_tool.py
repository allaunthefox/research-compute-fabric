# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Standard MIME Detection Tool for NoDupeLabs.

Provides MIME type detection capabilities as a tool.
"""

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

    def run_standalone(self, args: List[str]) -> int:
        """Run the tool in standalone mode.
        
        Args:
            args: List of command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if not args or '--help' in args or '-h' in args:
            print(self.describe_usage())
            raise SystemExit(0)
        
        # Parse arguments
        file_path = None
        verbose = '--verbose' in args or '-v' in args
        
        for i, arg in enumerate(args):
            if arg in ('--file', '-f') and i + 1 < len(args):
                file_path = args[i + 1]
                break
            elif not arg.startswith('-') and file_path is None:
                file_path = arg
        
        if file_path is None:
            print(self.describe_usage())
            raise SystemExit(0)
        
        # Detect MIME type
        try:
            mime_type = self.detector.detect_mime_type(file_path)
            print(f"File: {file_path}")
            print(f"MIME Type: {mime_type}")
            
            if verbose:
                print(f"Is text: {self.detector.is_text(mime_type)}")
                print(f"Is image: {self.detector.is_image(mime_type)}")
                print(f"Is archive: {self.detector.is_archive(mime_type)}")
            
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def describe_usage(self) -> str:
        """Return human-readable usage description.
        
        Returns:
            Usage description string
        """
        return """Standard MIME Detection Tool

Detects MIME types using magic number detection and file extensions.

Usage:
    --file PATH     Path to file to analyze
    --verbose       Show detailed MIME type information

Examples:
    Detect MIME type of a file:
        python -m nodupe.tools.mime.mime_tool --file document.pdf
    
    Show detailed information:
        python -m nodupe.tools.mime.mime_tool --file image.png --verbose

Features:
    - Magic number detection (file content analysis)
    - Extension-based detection
    - RFC 6838 compliant MIME type identification
"""


def register_tool():
    """Register the MIME tool."""
    return StandardMIMETool()

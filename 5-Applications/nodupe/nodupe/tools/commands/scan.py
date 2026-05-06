# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Scan tool for NoDupeLabs.

This tool provides the scan functionality as a tool that can be
loaded by the core system. It demonstrates how to convert existing
modules to tools.

Key Features:
    - Directory scanning
    - File processing
    - Duplicate detection
    - Progress tracking
    - Tool integration
"""

from typing import Any, Dict
import argparse
import time
import os
from nodupe.core.tool_system.base import Tool
from nodupe.tools.scanner_engine.processor import FileProcessor
from nodupe.tools.scanner_engine.walker import FileWalker
from nodupe.tools.databases.files import FileRepository
from nodupe.tools.databases.connection import DatabaseConnection


class ScanTool(Tool):
    """Scan tool implementation.

    Provides directory scanning functionality for finding duplicate files.
    """

    name = "scan"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        """Initialize scan tool."""
        self.description = "Scan directories for duplicate files"

    def initialize(self, container: Any) -> None:
        """Initialize the tool.

        Args:
            container: Service container
        """
        pass

    def shutdown(self) -> None:
        """Shutdown the tool and cleanup resources."""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities.

        Returns:
            Dictionary of capability flags
        """
        return {'commands': ['scan']}

    @property
    def api_methods(self) -> Dict[str, Any]:
        """Get API methods exposed by this tool.

        Returns:
            Dictionary of API methods
        """
        return {}

    def describe_usage(self) -> str:
        """Return human-readable usage instructions.

        Returns:
            Usage description string
        """
        return "Scan directories to find and index files for duplicate detection"

    def run_standalone(self, args: Any) -> int:
        """Execute the tool in standalone mode.

        Args:
            args: Command line arguments

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        return self.execute_scan(args)

    def _on_scan_start(self, **kwargs: Any) -> None:
        """Handle scan start event.

        Args:
            **kwargs: Event data including path
        """
        print(f"[TOOL] Scan started: {kwargs.get('path', 'unknown')}")

    def _on_scan_complete(self, **kwargs: Any) -> None:
        """Handle scan complete event.

        Args:
            **kwargs: Event data including files_processed count
        """
        print(f"[TOOL] Scan completed: {kwargs.get('files_processed', 0)} files processed")

    def register_commands(self, subparsers: Any) -> None:
        """Register scan command with argument parser.

        Args:
            subparsers: Argument parser subparsers object
        """
        scan_parser = subparsers.add_parser('scan', help='Scan directories for duplicates')
        scan_parser.add_argument('paths', nargs='+', help='Directories to scan')
        scan_parser.add_argument('--min-size', type=int, default=0, help='Minimum file size')
        scan_parser.add_argument('--max-size', type=int, help='Maximum file size')
        scan_parser.add_argument('--extensions', nargs='+', help='File extensions to include')
        scan_parser.add_argument('--exclude', nargs='+', help='Directories to exclude')
        scan_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        scan_parser.set_defaults(func=self.execute_scan)

    def execute_scan(self, args: argparse.Namespace) -> int:
        """Execute scan command.

        Args:
            args: Command arguments including injected 'container'

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Validation
            if not args.paths:
                print("[ERROR] No paths provided. Please specify at least one directory to scan.")
                return 1

            # Check if paths exist
            valid_paths = []
            for path in args.paths:
                if not os.path.exists(path):
                    print(f"[ERROR] Path does not exist: {path}")
                    return 1
                valid_paths.append(path)

            print(f"[TOOL] Executing scan command: {valid_paths}")
            start_time = time.monotonic()

            # 1. Get services
            container = getattr(args, 'container', None)
            if not container:
                print("[ERROR] Dependency container not available")
                return 1

            db_connection = container.get_service('database')
            if not db_connection:
                print("[ERROR] Database service not available")
                print("[WARN] Attempting to connect to default database...")
                db_connection = DatabaseConnection.get_instance()

            # 2. Setup components
            file_repo = FileRepository(db_connection)

            # Setup filter
            def file_filter(info: Dict[str, Any]) -> bool:
                """Filter files based on criteria.

                Args:
                    info: File information dictionary

                Returns:
                    True if file passes filter, False otherwise
                """
                if args.min_size and info['size'] < args.min_size:
                    return False
                if args.max_size and info['size'] > args.max_size:
                    return False
                if args.extensions:
                    ext = info['extension'].lstrip('.')
                    if ext not in args.extensions:
                        return False
                return True

            # Setup progress callback
            def progress_callback(p: Dict[str, Any]) -> None:
                """Handle progress updates.

                Args:
                    p: Progress information dictionary
                """
                if args.verbose:
                    print(
                        f"\rScanning... {p['files_processed']} files ({p['files_per_second']:.1f} f/s)",
                        end="",
                        flush=True
                    )

            # 3. Process Execution
            walker = FileWalker()
            processor = FileProcessor(walker)

            all_processed_files = []

            for path in args.paths:
                print(f"[TOOL] Scanning directory: {path}")
                self._on_scan_start(path=path)

                # Process files
                results = processor.process_files(
                    root_path=path,
                    file_filter=file_filter,
                    on_progress=progress_callback
                )

                if results:
                    print(f"\n[TOOL] Found {len(results)} files in {path}")
                    all_processed_files.extend(results)

                    # 4. Save to Database
                    print("[TOOL] Saving to database...")
                    count = file_repo.batch_add_files(results)
                    print(f"[TOOL] Saved {count} records")
                else:
                    print(f"\n[TOOL] No files found in {path}")

            elapsed = time.monotonic() - start_time
            print(f"\n[TOOL] Scan complete in {elapsed:.2f}s")
            print(f"[TOOL] Total files processed: {len(all_processed_files)}")

            self._on_scan_complete(files_processed=len(all_processed_files))
            return 0

        except Exception as e:
            print(f"[TOOL ERROR] Scan failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1


# Create tool instance when module is loaded
scan_tool = ScanTool()


def register_tool():
    """Register tool with core system.

    Returns:
        Initialized ScanTool instance
    """
    return scan_tool


# Export tool interface
__all__ = ['scan_tool', 'register_tool']

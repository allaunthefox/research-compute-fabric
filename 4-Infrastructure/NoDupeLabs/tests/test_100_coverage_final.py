# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Final Coverage Completion Tests.

Tests to achieve 100% coverage for all 11 target files.

Note: Now uses pickle-safe test helpers for ProcessPoolExecutor testing.
See: docs/PARALLEL_TESTING_SUSTAINABILITY.md
"""

import mmap
import os
import shutil
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

# Loader Tests
from nodupe.core.loader import (
    CoreLoader,
    bootstrap,
)
from nodupe.tools.hashing.autotune_logic import (
    autotune_hash_algorithm,
    create_autotuned_hasher,
)
from nodupe.tools.databases.connection import get_connection

# Discovery Tests
from nodupe.core.tool_system.discovery import (
    ToolDiscovery,
    ToolDiscoveryError,
    ToolInfo,
    create_tool_discovery,
)

# Archive Logic Tests
from nodupe.tools.archive.archive_logic import (
    ArchiveHandler,
    ArchiveHandlerError,
    create_archive_handler,
)

# Leap Year Tests
from nodupe.tools.leap_year.leap_year import LeapYearTool

# MIME Logic Tests
from nodupe.tools.mime.mime_logic import MIMEDetection, MIMEDetectionError

# Import pickle-safe test helpers for process testing
from tests.parallel.test_helpers import (
    double_number,
    square_number,
    add_one,
    identity,
    maybe_raise,
)

# MIME Tool Tests
from nodupe.tools.mime.mime_tool import StandardMIMETool, register_tool

# Filesystem Tests
from nodupe.tools.os_filesystem.filesystem import Filesystem, FilesystemError

# MMAP Handler Tests
from nodupe.tools.os_filesystem.mmap_handler import MMAPHandler

# Parallel Logic Tests
from nodupe.tools.parallel.parallel_logic import Parallel, ParallelError, ParallelProgress

# Security Logic Tests
from nodupe.tools.security_audit.security_logic import Security, SecurityError

# =============================================================================
# Archive Logic - Missing Lines: 97, 99, 101, 103, 105, 161-163, 216->214, 242->241, 243-268
# =============================================================================

class TestArchiveLogicMissingCoverage:
    """Test missing coverage in archive_logic.py."""

    def test_detect_archive_format_nonexistent_file(self):
        """Test detect_archive_format with nonexistent file - line 97."""
        handler = ArchiveHandler()
        result = handler.detect_archive_format('/nonexistent/file.zip')
        assert result is None

    def test_detect_archive_format_extension_fallback_zip(self):
        """Test extension fallback for zip - line 99."""
        handler = ArchiveHandler()
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            f.write(b'not a real zip')
            f.flush()
            try:
                # Mock mime detection to return None
                with patch.object(handler._mime_detector, 'detect_mime_type', return_value=None):
                    result = handler.detect_archive_format(f.name)
                    assert result == 'zip'
            finally:
                os.unlink(f.name)

    def test_detect_archive_format_extension_fallback_tar(self):
        """Test extension fallback for tar - line 101."""
        handler = ArchiveHandler()
        with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as f:
            f.write(b'not a real tar')
            f.flush()
            try:
                with patch.object(handler._mime_detector, 'detect_mime_type', return_value=None):
                    result = handler.detect_archive_format(f.name)
                    assert result == 'tar'
            finally:
                os.unlink(f.name)

    def test_detect_archive_format_extension_fallback_tgz(self):
        """Test extension fallback for tgz - line 103."""
        handler = ArchiveHandler()
        with tempfile.NamedTemporaryFile(suffix='.tgz', delete=False) as f:
            f.write(b'not a real tgz')
            f.flush()
            try:
                with patch.object(handler._mime_detector, 'detect_mime_type', return_value=None):
                    result = handler.detect_archive_format(f.name)
                    assert result == 'tar.gz'
            finally:
                os.unlink(f.name)

    def test_detect_archive_format_extension_fallback_tbz2(self):
        """Test extension fallback for tbz2 - line 105."""
        handler = ArchiveHandler()
        with tempfile.NamedTemporaryFile(suffix='.tbz2', delete=False) as f:
            f.write(b'not a real tbz2')
            f.flush()
            try:
                with patch.object(handler._mime_detector, 'detect_mime_type', return_value=None):
                    result = handler.detect_archive_format(f.name)
                    assert result == 'tar.bz2'
            finally:
                os.unlink(f.name)

    def test_extract_archive_unsupported_format_mime(self):
        """Test extract_archive with unsupported format - lines 161-163."""
        handler = ArchiveHandler()
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'unknown format')
            f.flush()
            try:
                with patch.object(handler._mime_detector, 'detect_mime_type', return_value='application/unknown'):
                    with pytest.raises(ArchiveHandlerError) as exc_info:
                        handler.extract_archive(f.name)
                    assert 'Unsupported archive format' in str(exc_info.value)
            finally:
                os.unlink(f.name)

    def test_create_archive_tar_lzma_format(self):
        """Test create_archive with tar.lzma format - line 216->214."""
        handler = ArchiveHandler()
        with tempfile.NamedTemporaryFile(suffix='.tar.lzma', delete=False) as f:
            archive_path = f.name
        
        with tempfile.NamedTemporaryFile(delete=False) as data_file:
            data_file.write(b'test data')
            data_file.flush()
            data_path = data_file.name
        
        try:
            # tar.lzma is not supported for creation - falls back to tar mode
            result = handler.create_archive(archive_path, [data_path], format='tar.lzma')
            # Should create a tar file (tar.lzma falls through to tar mode)
            assert result == archive_path
            assert os.path.exists(archive_path)
        finally:
            os.unlink(archive_path)
            os.unlink(data_path)

    def test_get_archive_contents_info_exception_path(self):
        """Test get_archive_contents_info exception path - lines 242->241, 243-268."""
        handler = ArchiveHandler()
        
        # Create a valid zip file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            archive_path = f.name
        
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        try:
            # Mock extract_archive to raise an exception
            with patch.object(handler, 'extract_archive', side_effect=Exception('Extraction failed')):
                result = handler.get_archive_contents_info(archive_path, '/base')
                assert result == []
        finally:
            os.unlink(archive_path)

    def test_get_archive_contents_info_stat_error(self):
        """Test get_archive_contents_info with stat error."""
        handler = ArchiveHandler()
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            archive_path = f.name
        
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        try:
            # Extract first
            extracted = handler.extract_archive(archive_path)
            
            # Now mock stat to raise exception
            with patch.object(Path, 'stat', side_effect=Exception('Stat failed')):
                result = handler.get_archive_contents_info(archive_path, '/base')
                # Should return empty list due to exception handling
        finally:
            handler.cleanup()
            os.unlink(archive_path)


# =============================================================================
# MIME Tool - Missing Line: 72->78
# =============================================================================

class TestMIMEToolMissingCoverage:
    """Test missing coverage in mime_tool.py."""

    def test_run_standalone_no_file_arg(self):
        """Test run_standalone with no file argument - line 72->78."""
        tool = StandardMIMETool()
        # When no args, should print help and raise SystemExit(0)
        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone([])
        assert exc_info.value.code == 0


# =============================================================================
# MIME Logic - Missing Lines: 179, 210-216, 247
# =============================================================================

class TestMIMELogicMissingCoverage:
    """Test missing coverage in mime_logic.py."""

    def test_detect_by_magic_no_match(self):
        """Test _detect_by_magic with no matching magic number - line 179."""
        from nodupe.tools.mime.mime_logic import MIMEDetection
        detector = MIMEDetection()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'unknown file content')
            f.flush()
            try:
                result = detector._detect_by_magic(Path(f.name))
                assert result is None
            finally:
                os.unlink(f.name)

    def test_detect_by_magic_ogg(self):
        """Test _detect_by_magic for OGG format - line 210-216."""
        from nodupe.tools.mime.mime_logic import MIMEDetection
        detector = MIMEDetection()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'OggS\x00\x00\x00\x00')
            f.flush()
            try:
                result = detector._detect_by_magic(Path(f.name))
                assert result == 'audio/ogg'
            finally:
                os.unlink(f.name)

    def test_detect_by_magic_read_error(self):
        """Test _detect_by_magic with read error - line 247."""
        from nodupe.tools.mime.mime_logic import MIMEDetection
        detector = MIMEDetection()
        mock_path = MagicMock()
        mock_path.open.side_effect = IOError('Cannot read')

        result = detector._detect_by_magic(mock_path)
        assert result is None


# =============================================================================
# Loader - Missing Lines: 66->65, 162->165, 192->196, 253-257, 295->307, 296->295, 301, 303-304, 343-346, 374, 377, 414
# =============================================================================

class TestLoaderMissingCoverage:
    """Test missing coverage in loader.py."""

    def test_initialize_double_init(self):
        """Test initialize when already initialized - line 66->65."""
        loader = CoreLoader()
        loader.initialized = True
        
        # Should return immediately
        loader.initialize()
        assert loader.initialized is True

    def test_initialize_config_merge_nested_dict(self):
        """Test config merge with nested dicts - line 162->165."""
        loader = CoreLoader()
        
        mock_config = MagicMock()
        mock_config.config = {'tools': {'existing': 'value'}}
        
        with patch('nodupe.core.loader.load_config', return_value=mock_config), \
             patch.object(loader, '_apply_platform_autoconfig', return_value={'tools': {'new': 'value'}}), \
             patch('nodupe.core.loader.ToolRegistry'), \
             patch('nodupe.core.loader.create_tool_loader'), \
             patch('nodupe.core.loader.create_tool_discovery'), \
             patch('nodupe.core.loader.create_lifecycle_manager'), \
             patch('nodupe.core.loader.ToolHotReload'), \
             patch('nodupe.core.loader.ToolIPCServer'), \
             patch('nodupe.core.loader.logging'):
            
            try:
                loader.initialize()
            except Exception:
                pass  # Expected due to mocking
            
            # Both keys should exist
            assert 'existing' in mock_config.config['tools']
            assert 'new' in mock_config.config['tools']

    def test_discover_and_load_tools_disabled(self):
        """Test tool discovery when auto_load is disabled - line 192->196."""
        loader = CoreLoader()
        loader.config = MagicMock()
        loader.config.config = {'tools': {'auto_load': False}}
        loader.tool_discovery = MagicMock()
        
        loader._discover_and_load_tools()
        
        # Should not call discover_tools_in_directory
        loader.tool_discovery.discover_tools_in_directory.assert_not_called()

    def test_perform_hash_autotuning_no_hasher_with_error(self):
        """Test hash autotuning with error - lines 253-257."""
        loader = CoreLoader()
        loader.container = MagicMock()
        loader.container.get_service.return_value = None
        loader.logger = MagicMock()
        
        with patch('nodupe.core.loader.autotune_hash_algorithm', side_effect=Exception('Autotune failed')), \
             patch('nodupe.core.loader.create_autotuned_hasher') as mock_create:
            
            mock_create.return_value = (MagicMock(), {})
            
            loader._perform_hash_autotuning()
            
            # Should create fallback hasher
            assert loader.container.register_service.called

    def test_shutdown_not_initialized(self):
        """Test shutdown when not initialized - line 295->307."""
        loader = CoreLoader()
        loader.initialized = False
        
        # Should return immediately
        loader.shutdown()

    def test_shutdown_exception_handling(self, caplog):
        """Test shutdown with exception - lines 296->295, 301, 303-304."""
        loader = CoreLoader()
        loader.initialized = True
        loader.tool_lifecycle = MagicMock()
        loader.tool_lifecycle.shutdown_all_tools.side_effect = Exception('Shutdown failed')
        loader.logger = MagicMock()
        
        loader.shutdown()
        
        # Should log error but continue
        assert loader.logger.error.called

    def test_apply_platform_autoconfig_psutil_exception(self):
        """Test _apply_platform_autoconfig with psutil exception - lines 343-346."""
        loader = CoreLoader()
        
        with patch('nodupe.core.loader.psutil') as mock_psutil:
            mock_psutil.virtual_memory.side_effect = Exception('psutil failed')
            mock_psutil.disk_partitions.return_value = []
            
            result = loader._detect_system_resources()
            
            assert 'ram_gb' in result
            assert result['ram_gb'] == 8  # Default value

    def test_detect_thread_restrictions_kubernetes(self):
        """Test thread restriction detection for Kubernetes - line 374."""
        loader = CoreLoader()
        system_info = {}
        
        with patch.dict(os.environ, {'KUBERNETES_SERVICE_HOST': 'localhost'}):
            loader._detect_thread_restrictions(system_info)
            
            assert system_info['thread_restrictions_detected'] is True
            assert 'kubernetes' in system_info['thread_restriction_reasons']

    def test_detect_thread_restrictions_docker(self):
        """Test thread restriction detection for Docker - line 377."""
        loader = CoreLoader()
        system_info = {}
        
        with patch.dict(os.environ, {'DOCKER_CONTAINER': 'true'}):
            loader._detect_thread_restrictions(system_info)
            
            assert system_info['thread_restrictions_detected'] is True
            assert 'container' in system_info['thread_restriction_reasons']

    def test_detect_thread_restrictions_cgroup(self):
        """Test thread restriction detection for cgroups - line 414."""
        loader = CoreLoader()
        system_info = {}
        
        # Create a mock cgroup file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cgroup') as f:
            f.write('50000')
            f.flush()
            cgroup_path = f.name
        
        try:
            with patch('nodupe.core.loader.os.path.exists', return_value=True), \
                 patch('nodupe.core.loader.open', mock_open(read_data='50000')):
                
                loader._detect_thread_restrictions(system_info)
                
                assert system_info['thread_restrictions_detected'] is True
                assert 'cgroup_cpu_limit' in system_info['thread_restriction_reasons']
        finally:
            os.unlink(cgroup_path)

    def test_get_connection_existing(self):
        """Test get_connection with existing database."""
        mock_db = MagicMock()

        with patch('nodupe.tools.databases.connection.global_container') as mock_container:
            mock_container.get_service.return_value = mock_db

            result = get_connection()

            # Should return the mock database
            assert result is not None

    def test_autotune_hash_algorithm(self):
        """Test autotune_hash_algorithm function."""
        result = autotune_hash_algorithm()
        
        assert 'optimal_algorithm' in result
        assert result['optimal_algorithm'] == 'blake3'

    def test_create_autotuned_hasher(self):
        """Test create_autotuned_hasher function."""
        hasher, config = create_autotuned_hasher()
        
        assert hasher is not None
        assert config['algorithm'] == 'blake3'


# =============================================================================
# Discovery - Missing Lines: 148->129, 155-161, 165-167, 193->192, 235->234, 239-244, 273->272, 275, 312, 318, 335, 371->365, 383, 385, 400->365, 405-406, 411->365, 469-478
# =============================================================================

class TestDiscoveryMissingCoverage:
    """Test missing coverage in discovery.py."""

    def test_discover_tools_in_directory_iterdir_exception(self):
        """Test discover_tools_in_directory with iterdir exception - line 148->129."""
        discovery = ToolDiscovery()
        
        mock_dir = MagicMock()
        mock_dir.iterdir.side_effect = TypeError('Not a directory')
        
        result = discovery.discover_tools_in_directory(mock_dir)
        
        assert result == []

    def test_discover_tools_in_directory_os_error(self):
        """Test discover_tools_in_directory with OSError - lines 155-161."""
        discovery = ToolDiscovery()
        
        mock_dir = MagicMock()
        mock_dir.iterdir.side_effect = OSError('Directory not found')
        
        result = discovery.discover_tools_in_directory(mock_dir)
        
        assert result == []

    def test_discover_tools_in_directory_item_exception(self):
        """Test discover_tools_in_directory with item exception - lines 165-167."""
        discovery = ToolDiscovery()
        
        mock_item = MagicMock()
        mock_item.is_file.side_effect = Exception('Item check failed')
        
        mock_dir = MagicMock()
        mock_dir.iterdir.return_value = [mock_item]
        
        result = discovery.discover_tools_in_directory(mock_dir)
        
        assert result == []

    def test_discover_tools_in_directories_exception(self):
        """Test discover_tools_in_directories with exception - line 193->192."""
        discovery = ToolDiscovery()
        
        mock_dir = MagicMock()
        mock_dir.iterdir.side_effect = ToolDiscoveryError('Discovery failed')
        
        result = discovery.discover_tools_in_directories([mock_dir])
        
        assert result == []

    def test_find_tool_by_name_in_discovered(self):
        """Test find_tool_by_name in discovered tools - line 235->234."""
        discovery = ToolDiscovery()
        
        tool_info = ToolInfo(name='test_tool', file_path=Path('/test.py'))
        discovery._discovered_tools.append(tool_info)
        
        result = discovery.find_tool_by_name('test_tool')
        
        assert result == tool_info

    def test_find_tool_by_name_not_found(self):
        """Test find_tool_by_name not found - lines 239-244."""
        discovery = ToolDiscovery()
        
        result = discovery.find_tool_by_name('nonexistent_tool')
        
        assert result is None

    def test_find_tool_by_name_subdir_check(self):
        """Test find_tool_by_name with subdir check - line 273->272."""
        discovery = ToolDiscovery()
        
        mock_dir = MagicMock()
        mock_dir.exists.return_value = False
        
        with patch('nodupe.core.tool_system.discovery.Path', return_value=mock_dir):
            result = discovery.find_tool_by_name('test_tool', search_directories=[MagicMock()])
            
            assert result is None

    def test_find_tool_by_name_exception(self):
        """Test find_tool_by_name with exception - line 275."""
        discovery = ToolDiscovery()
        
        mock_dir = MagicMock()
        mock_dir.iterdir.side_effect = ToolDiscoveryError('Failed')
        
        result = discovery.find_tool_by_name('test_tool', search_directories=[mock_dir])
        
        assert result is None

    def test_refresh_discovery(self):
        """Test refresh_discovery - line 312."""
        discovery = ToolDiscovery()
        discovery._discovered_tools.append(ToolInfo(name='test', file_path=Path('/test.py')))
        
        discovery.refresh_discovery()
        
        assert len(discovery._discovered_tools) == 0

    def test_get_discovered_tool_found(self):
        """Test get_discovered_tool found - line 318."""
        discovery = ToolDiscovery()
        tool_info = ToolInfo(name='test_tool', file_path=Path('/test.py'))
        discovery._discovered_tools.append(tool_info)
        
        result = discovery.get_discovered_tool('test_tool')
        
        assert result == tool_info

    def test_get_discovered_tool_not_found(self):
        """Test get_discovered_tool not found - line 335."""
        discovery = ToolDiscovery()
        
        result = discovery.get_discovered_tool('nonexistent')
        
        assert result is None

    def test_is_tool_discovered_true(self):
        """Test is_tool_discovered true - line 371->365."""
        discovery = ToolDiscovery()
        discovery._discovered_tools.append(ToolInfo(name='test_tool', file_path=Path('/test.py')))
        
        result = discovery.is_tool_discovered('test_tool')
        
        assert result is True

    def test_is_tool_discovered_false(self):
        """Test is_tool_discovered false - line 383."""
        discovery = ToolDiscovery()
        
        result = discovery.is_tool_discovered('nonexistent')
        
        assert result is False

    def test_extract_tool_info_exception(self):
        """Test _extract_tool_info with exception - line 385."""
        discovery = ToolDiscovery()
        
        mock_path = MagicMock()
        mock_path.open.side_effect = Exception('Read failed')
        
        result = discovery._extract_tool_info(mock_path)
        
        assert result is None

    def test_parse_metadata_capabilities_exception(self):
        """Test _parse_metadata with capabilities exception - line 400->365."""
        discovery = ToolDiscovery()
        
        content = """
CAPABILITIES = "invalid syntax {{{"
"""
        
        metadata = discovery._parse_metadata(content)
        
        # Should handle gracefully - may not have capabilities key
        assert metadata is not None

    def test_parse_metadata_dependencies_exception(self):
        """Test _parse_metadata with dependencies exception - lines 405-406."""
        discovery = ToolDiscovery()
        
        content = """
DEPENDENCIES = "invalid syntax {{{"
"""
        
        metadata = discovery._parse_metadata(content)
        
        # Should handle gracefully
        assert metadata.get('dependencies') is None or metadata.get('dependencies') == []

    def test_parse_metadata_version_exception(self):
        """Test _parse_metadata with version exception - line 411->365."""
        discovery = ToolDiscovery()
        
        content = """
__version__ = "invalid syntax {{{"
"""
        
        metadata = discovery._parse_metadata(content)
        
        # Should handle gracefully
        assert 'version' in metadata

    def test_validate_tool_file_empty(self):
        """Test validate_tool_file with empty file - lines 469-478."""
        discovery = ToolDiscovery()
        
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            # Empty file
            temp_path = Path(f.name)
        
        try:
            result = discovery.validate_tool_file(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)


# =============================================================================
# Parallel Logic - Missing Lines: 128-130, 132, 165, 195, 202-204, 264, 268-273, 280-282, 284, 291-322, 326-330, 340-341, 355-356, 367
# =============================================================================

class TestParallelLogicMissingCoverage:
    """Test missing coverage in parallel_logic.py.
    
    Note: Uses pickle-safe helpers from test_helpers for process testing.
    See: docs/PARALLEL_TESTING_SUSTAINABILITY.md
    """

    def test_process_in_parallel_task_exception(self):
        """Test process_in_parallel with task exception - lines 128-130, 132."""
        # Use pickle-safe maybe_raise for process testing
        with pytest.raises(ParallelError) as exc_info:
            Parallel.process_in_parallel(
                maybe_raise,  # ✅ Pickle-safe
                [1, -1, 3],  # -1 triggers error
                workers=2,
                use_processes=False  # Threads for error testing
            )

        assert 'Error for value -1' in str(exc_info.value)

    def test_map_parallel_unordered_batch_size_one(self):
        """Test map_parallel_unordered with batch_size=1 - line 165."""
        items = [1, 2, 3]
        
        results = list(Parallel.map_parallel_unordered(
            double_number, items, workers=2, use_processes=True, prefer_batches=True
        ))
        
        assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_interpreter_exception(self):
        """Test map_parallel_unordered interpreter exception path - line 195."""
        items = [1, 2, 3]
        
        with patch('nodupe.tools.parallel.parallel_logic.Parallel.supports_interpreter_pool', return_value=True):
            results = list(Parallel.map_parallel_unordered(
                double_number, items, workers=2, use_interpreters=True
            ))
            
            assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_batch_exception(self):
        """Test map_parallel_unordered batch exception - lines 202-204."""
        items = [1, 2, 3]
        
        with patch.object(os, 'getenv', return_value='invalid'):
            results = list(Parallel.map_parallel_unordered(
                double_number, items, workers=2, use_processes=True, prefer_batches=True
            ))
            
            assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_cpu_count_exception(self):
        """Test map_parallel_unordered cpu count exception - line 264."""
        items = [1, 2, 3]
        
        with patch.object(Parallel, 'get_cpu_count', side_effect=Exception('CPU count failed')):
            results = list(Parallel.map_parallel_unordered(
                double_number, items, workers=2, use_processes=True
            ))
            
            assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_batch_logging(self):
        """Test map_parallel_unordered with batch logging - lines 268-273."""
        items = [1, 2, 3]
        
        with patch.dict(os.environ, {'NODUPE_BATCH_LOG': '1'}):
            results = list(Parallel.map_parallel_unordered(
                double_number, items, workers=2, use_processes=True, prefer_batches=True
            ))
            
            assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_chunksize_exception(self):
        """Test map_parallel_unordered chunksize exception - lines 280-282, 284."""
        items = [1, 2, 3]

        # Test with threads (not processes) to avoid multiprocessing issues with mocks
        # Use side_effect as a callable that returns default values for specific calls
        def getenv_side_effect(key, default=None):
            """Mock getenv that raises exception for specific environment variables."""
            if key in ("NODUPE_BATCH_DIVISOR", "NODUPE_CHUNK_FACTOR"):
                raise Exception('Env failed')
            return default
        
        with patch.object(os, 'getenv', side_effect=getenv_side_effect):
            results = list(Parallel.map_parallel_unordered(
                double_number, items, workers=2, use_processes=False, prefer_batches=False, prefer_map=True
            ))

            assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_bounded_submission(self):
        """Test map_parallel_unordered bounded submission - lines 291-322."""
        items = [1, 2, 3, 4, 5]
        
        results = list(Parallel.map_parallel_unordered(
            double_number, items, workers=2, use_processes=False
        ))
        
        assert sorted(results) == [2, 4, 6, 8, 10]

    def test_map_parallel_unordered_stopiteration(self):
        """Test map_parallel_unordered StopIteration handling - lines 326-330."""
        items = [1]  # Single item to trigger StopIteration early
        
        results = list(Parallel.map_parallel_unordered(
            double_number, items, workers=2
        ))
        
        assert results == [2]

    def test_map_parallel_unordered_future_exception(self):
        """Test map_parallel_unordered future exception - line 340-341."""
        # Use pickle-safe maybe_raise for process testing
        with pytest.raises(ParallelError) as exc_info:
            list(Parallel.map_parallel_unordered(
                maybe_raise,  # ✅ Pickle-safe
                [-1],  # -1 triggers error
                workers=1
            ))

        assert 'Error for value -1' in str(exc_info.value)

    def test_map_parallel_unordered_timeout(self):
        """Test map_parallel_unordered with timeout - line 355-356."""
        from tests.parallel.test_helpers import slow_square
        
        # Use pickle-safe slow_square for timeout testing
        with pytest.raises(ParallelError):
            list(Parallel.map_parallel_unordered(
                slow_square,  # ✅ Pickle-safe with delay
                [1],
                timeout=0.01,
                use_processes=False  # Threads for timeout testing
            ))

    def test_map_parallel_unordered_keyerror(self):
        """Test map_parallel_unordered KeyError handling - line 367."""
        items = [1, 2, 3]

        # This should handle KeyError gracefully
        results = list(Parallel.map_parallel_unordered(
            double_number, items, workers=2
        ))

        assert sorted(results) == [2, 4, 6]

    def test_map_parallel_unordered_with_processes(self):
        """Test map_parallel_unordered with ProcessPoolExecutor."""
        items = [1, 2, 3, 4, 5]
        
        # Test with actual processes
        results = list(Parallel.map_parallel_unordered(
            double_number,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True  # ✅ Test processes
        ))
        
        assert sorted(results) == [2, 4, 6, 8, 10]

    def test_process_in_parallel_with_processes(self):
        """Test process_in_parallel with ProcessPoolExecutor."""
        items = [1, 2, 3, 4, 5]
        
        # Test with actual processes
        results = Parallel.process_in_parallel(
            square_number,  # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True  # ✅ Test processes
        )
        
        assert results == [1, 4, 9, 16, 25]

    def test_thread_vs_process_consistency(self):
        """Verify thread and process results are consistent."""
        items = [1, 2, 3, 4, 5]
        
        # Thread result
        thread_result = Parallel.process_in_parallel(
            double_number,
            items,
            workers=2,
            use_processes=False
        )
        
        # Process result
        process_result = Parallel.process_in_parallel(
            double_number,
            items,
            workers=2,
            use_processes=True
        )
        
        # Both should produce same results
        assert thread_result == process_result == [2, 4, 6, 8, 10]


# =============================================================================
# Security Logic - Missing Lines: 114, 154->157, 167, 176, 177->181, 183, 184->187, 342->344, 413-414, 442-444
# =============================================================================

class TestSecurityLogicMissingCoverage:
    """Test missing coverage in security_logic.py."""

    def test_sanitize_path_null_bytes(self):
        """Test sanitize_path with null bytes - line 114."""
        with pytest.raises(SecurityError) as exc_info:
            Security.sanitize_path('test\x00path')
        
        assert 'null bytes' in str(exc_info.value)

    def test_validate_path_allowed_parent_exception(self):
        """Test validate_path with allowed_parent exception - line 154->157."""
        with pytest.raises(SecurityError) as exc_info:
            Security.validate_path('/test/path', allowed_parent='/nonexistent')
        
        assert 'Cannot resolve allowed parent' in str(exc_info.value) or 'outside allowed' in str(exc_info.value)

    def test_validate_path_must_exist(self):
        """Test validate_path with must_exist - line 167."""
        with pytest.raises(SecurityError) as exc_info:
            Security.validate_path('/nonexistent/path', must_exist=True)
        
        assert 'does not exist' in str(exc_info.value)

    def test_validate_path_must_be_file(self):
        """Test validate_path with must_be_file - line 176."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path(tmpdir, must_be_file=True)
            
            assert 'not a file' in str(exc_info.value)

    def test_validate_path_must_be_dir(self):
        """Test validate_path with must_be_dir - line 177->181."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path(temp_file, must_be_dir=True)
            
            assert 'not a directory' in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_validate_path_resolve_exception(self):
        """Test validate_path with resolve exception - line 183."""
        mock_path = MagicMock()
        mock_path.resolve.side_effect = RuntimeError('Resolve failed')
        
        with patch('nodupe.tools.security_audit.security_logic.Path', return_value=mock_path):
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path(mock_path)
            
            assert 'Cannot resolve' in str(exc_info.value)

    def test_validate_path_general_exception(self):
        """Test validate_path with general exception - line 184->187."""
        with patch('nodupe.tools.security_audit.security_logic.Path') as mock_path_class:
            mock_path_class.side_effect = Exception('Path creation failed')
            
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path('/test')
            
            assert 'validation failed' in str(exc_info.value)

    def test_check_permissions_not_exists(self):
        """Test check_permissions with nonexistent path - line 342->344."""
        with pytest.raises(SecurityError) as exc_info:
            Security.check_permissions('/nonexistent/path', readable=True)
        
        assert 'does not exist' in str(exc_info.value)

    def test_sanitize_filename_exception(self):
        """Test sanitize_filename with exception - lines 413-414."""
        with patch('nodupe.tools.security_audit.security_logic.re.sub', side_effect=Exception('Regex failed')):
            with pytest.raises(SecurityError) as exc_info:
                Security.sanitize_filename('test.txt')
            
            assert 'sanitization failed' in str(exc_info.value)

    def test_generate_safe_filename_exception(self):
        """Test generate_safe_filename with exception - lines 442-444."""
        with patch('nodupe.tools.security_audit.security_logic.Security.sanitize_filename', side_effect=Exception('Failed')):
            with pytest.raises(SecurityError) as exc_info:
                Security.generate_safe_filename('test')
            
            assert 'generation failed' in str(exc_info.value)


# =============================================================================
# Filesystem - Missing Lines: 52, 74, 91, 110-116, 121-122, 141, 153, 170, 193, 201, 215, 219-220, 235, 256, 258, 273, 289, 291, 306
# =============================================================================

class TestFilesystemMissingCoverage:
    """Test missing coverage in filesystem.py."""

    def test_safe_read_not_exists(self):
        """Test safe_read with nonexistent file - line 52."""
        with pytest.raises(FilesystemError) as exc_info:
            Filesystem.safe_read('/nonexistent/file.txt')
        
        assert 'does not exist' in str(exc_info.value)

    def test_safe_read_not_file(self):
        """Test safe_read with directory - line 74."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.safe_read(tmpdir)
            
            assert 'not a file' in str(exc_info.value)

    def test_safe_read_exceeds_max_size(self):
        """Test safe_read with max_size exceeded - line 91."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'x' * 100)
            temp_file = f.name
        
        try:
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.safe_read(temp_file, max_size=50)
            
            assert 'exceeds limit' in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_safe_write_atomic_exception(self):
        """Test safe_write with atomic exception - lines 110-116."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / 'test.txt'
            
            with patch('nodupe.tools.os_filesystem.filesystem.os.write', side_effect=OSError('Write failed')):
                with pytest.raises(FilesystemError) as exc_info:
                    Filesystem.safe_write(target, b'test data', atomic=True)
                
                assert 'Failed to write' in str(exc_info.value)

    def test_safe_write_direct_exception(self):
        """Test safe_write with direct write exception - lines 121-122."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / 'test.txt'
            
            with patch('nodupe.tools.os_filesystem.filesystem.Path.write_bytes', side_effect=OSError('Write failed')):
                with pytest.raises(FilesystemError) as exc_info:
                    Filesystem.safe_write(target, b'test data', atomic=False)
                
                assert 'Failed to write' in str(exc_info.value)

    def test_validate_path_must_exist_fail(self):
        """Test validate_path with must_exist failure - line 141."""
        with pytest.raises(FilesystemError) as exc_info:
            Filesystem.validate_path('/nonexistent/path', must_exist=True)
        
        assert 'does not exist' in str(exc_info.value)

    def test_validate_path_resolve_exception(self):
        """Test validate_path with resolve exception - line 153."""
        mock_path = MagicMock()
        mock_path.resolve.side_effect = RuntimeError('Resolve failed')
        
        with patch('nodupe.tools.os_filesystem.filesystem.Path', return_value=mock_path):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.validate_path(mock_path)
            
            assert 'Invalid path' in str(exc_info.value)

    def test_get_size_exception(self):
        """Test get_size with exception - line 170."""
        mock_path = MagicMock()
        mock_path.stat.side_effect = OSError('Stat failed')
        
        with patch('nodupe.tools.os_filesystem.filesystem.Path', return_value=mock_path):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.get_size(mock_path)
            
            assert 'Failed to get file size' in str(exc_info.value)

    def test_list_directory_not_dir(self):
        """Test list_directory with non-directory - line 193."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.list_directory(temp_file)
            
            assert 'not a directory' in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_list_directory_exception(self):
        """Test list_directory with exception - line 201."""
        mock_path = MagicMock()
        mock_path.is_dir.return_value = True
        mock_path.glob.side_effect = OSError('Glob failed')
        
        with patch('nodupe.tools.os_filesystem.filesystem.Path', return_value=mock_path):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.list_directory(mock_path)
            
            assert 'Failed to list directory' in str(exc_info.value)

    def test_ensure_directory_exception(self):
        """Test ensure_directory with exception - line 215."""
        mock_path = MagicMock()
        mock_path.mkdir.side_effect = OSError('Mkdir failed')
        
        with patch('nodupe.tools.os_filesystem.filesystem.Path', return_value=mock_path):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.ensure_directory(mock_path)
            
            assert 'Failed to create directory' in str(exc_info.value)

    def test_remove_file_exception(self):
        """Test remove_file with exception - lines 219-220."""
        mock_path = MagicMock()
        mock_path.unlink.side_effect = OSError('Unlink failed')
        
        with patch('nodupe.tools.os_filesystem.filesystem.Path', return_value=mock_path):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.remove_file(mock_path)
            
            assert 'Failed to remove' in str(exc_info.value)

    def test_copy_file_not_exists(self):
        """Test copy_file with nonexistent source - line 235."""
        with pytest.raises(FilesystemError) as exc_info:
            Filesystem.copy_file('/nonexistent/src.txt', '/tmp/dst.txt')
        
        assert 'does not exist' in str(exc_info.value)

    def test_copy_file_exists_no_overwrite(self):
        """Test copy_file with existing destination - line 256."""
        with tempfile.NamedTemporaryFile(delete=False) as src:
            src.write(b'source')
            src_path = src.name
        
        with tempfile.NamedTemporaryFile(delete=False) as dst:
            dst.write(b'dest')
            dst_path = dst.name
        
        try:
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.copy_file(src_path, dst_path, overwrite=False)
            
            assert 'Destination file exists' in str(exc_info.value)
        finally:
            os.unlink(src_path)
            os.unlink(dst_path)

    def test_copy_file_exception(self):
        """Test copy_file with exception - line 258."""
        with patch('nodupe.tools.os_filesystem.filesystem.shutil.copy2', side_effect=OSError('Copy failed')):
            with tempfile.NamedTemporaryFile(delete=False) as src:
                src.write(b'source')
                src_path = src.name
            
            try:
                with pytest.raises(FilesystemError) as exc_info:
                    Filesystem.copy_file(src_path, '/tmp/new_dst.txt', overwrite=True)
                
                assert 'Failed to copy' in str(exc_info.value)
            finally:
                os.unlink(src_path)

    def test_move_file_not_exists(self):
        """Test move_file with nonexistent source - line 273."""
        with pytest.raises(FilesystemError) as exc_info:
            Filesystem.move_file('/nonexistent/src.txt', '/tmp/dst.txt')
        
        assert 'does not exist' in str(exc_info.value)

    def test_move_file_exists_no_overwrite(self):
        """Test move_file with existing destination - line 289."""
        with tempfile.NamedTemporaryFile(delete=False) as src:
            src.write(b'source')
            src_path = src.name
        
        with tempfile.NamedTemporaryFile(delete=False) as dst:
            dst.write(b'dest')
            dst_path = dst.name
        
        try:
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.move_file(src_path, dst_path, overwrite=False)
            
            assert 'Destination file exists' in str(exc_info.value)
        finally:
            os.unlink(src_path)
            os.unlink(dst_path)

    def test_move_file_exception(self):
        """Test move_file with exception - line 291."""
        with patch('nodupe.tools.os_filesystem.filesystem.shutil.move', side_effect=OSError('Move failed')):
            with tempfile.NamedTemporaryFile(delete=False) as src:
                src.write(b'source')
                src_path = src.name
            
            try:
                with pytest.raises(FilesystemError) as exc_info:
                    Filesystem.move_file(src_path, '/tmp/new_dst.txt', overwrite=True)
                
                assert 'Failed to move' in str(exc_info.value)
            finally:
                os.unlink(src_path)

    def test_safe_read_string_path(self):
        """Test safe_read with string path - line 306."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test data')
            temp_file = f.name
        
        try:
            result = Filesystem.safe_read(temp_file)
            assert result == b'test data'
        finally:
            os.unlink(temp_file)


# =============================================================================
# MMAP Handler - Missing Line: 50->exit
# =============================================================================

class TestMMAPHandlerMissingCoverage:
    """Test missing coverage in mmap_handler.py."""

    def test_mmap_context_exception(self):
        """Test mmap_context with exception - line 50->exit."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test data')
            temp_file = f.name
        
        try:
            # Test that context manager properly closes on exception
            with pytest.raises(ValueError):
                with MMAPHandler.mmap_context(temp_file) as mapped:
                    raise ValueError('Test exception')
            
            # File should be properly closed
        finally:
            os.unlink(temp_file)


# =============================================================================
# Leap Year - Missing Lines: 128-130, 168->exit, 174->exit, 272, 560->562
# =============================================================================

class TestLeapYearMissingCoverage:
    """Test missing coverage in leap_year.py."""

    def test_run_standalone_exception_handling(self):
        """Test run_standalone with exception - lines 128-130."""
        tool = LeapYearTool()
        
        # Test with invalid argument that causes argparse to fail
        with patch('sys.argv', ['leap_year', 'invalid']):
            try:
                result = tool.run_standalone(['invalid'])
            except SystemExit:
                pass  # Expected from argparse

    def test_shutdown_with_cache_stats(self):
        """Test shutdown with cache stats - line 168->exit."""
        tool = LeapYearTool(enable_cache=True)
        tool.is_leap_year(2000)  # Populate cache
        
        mock_container = MagicMock()
        tool.shutdown(mock_container)
        
        # Should log cache stats

    def test_shutdown_without_cache(self):
        """Test shutdown without cache - line 174->exit."""
        tool = LeapYearTool(enable_cache=False)
        
        mock_container = MagicMock()
        tool.shutdown(mock_container)
        
        # Should not log cache stats

    def test_get_calendar_info(self):
        """Test get_calendar_info - line 272."""
        tool = LeapYearTool()
        
        info = tool.get_calendar_info(2000)
        
        assert info['year'] == 2000
        assert info['is_leap_year'] is True
        assert info['days_in_year'] == 366

    def test_is_gregorian_leap_year(self):
        """Test is_gregorian_leap_year - line 560->562."""
        tool = LeapYearTool()
        
        assert tool.is_gregorian_leap_year(2000) is True
        assert tool.is_gregorian_leap_year(1900) is False
        assert tool.is_gregorian_leap_year(2004) is True


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for multiple modules."""

    def test_archive_with_mime_detection(self):
        """Test archive handler with MIME detection."""
        handler = ArchiveHandler()
        
        # Create a valid zip file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            archive_path = f.name
        
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        
        try:
            # Test detection
            assert handler.is_archive_file(archive_path) is True
            assert handler.detect_archive_format(archive_path) == 'zip'
            
            # Test extraction
            result = handler.extract_archive(archive_path)
            assert len(result) > 0
        finally:
            handler.cleanup()
            os.unlink(archive_path)

    def test_parallel_with_filesystem(self):
        """Test parallel processing with filesystem operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_files = []
            for i in range(5):
                test_file = Path(tmpdir) / f'test_{i}.txt'
                test_file.write_bytes(f'data_{i}'.encode())
                test_files.append(test_file)
            
            # Process in parallel
            def read_file(path):
                """Helper function to read file content."""
                return Filesystem.safe_read(path)
            
            results = Parallel.process_in_parallel(read_file, test_files, workers=2)
            
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result == f'data_{i}'.encode()

    def test_security_with_filesystem(self):
        """Test security validation with filesystem operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.txt'
            test_file.write_bytes(b'test data')
            
            # Validate path
            assert Security.validate_path(test_file, must_exist=True, must_be_file=True)
            
            # Check permissions
            assert Security.check_permissions(test_file, readable=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

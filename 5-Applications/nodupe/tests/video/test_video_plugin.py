# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/video/video_plugin.py - VideoTool."""

from unittest.mock import MagicMock, patch

import pytest

# Import directly from the plugin file to avoid __init__.py import chain issues
from nodupe.tools.video import video_plugin

VideoTool = video_plugin.VideoTool
register_tool = video_plugin.register_tool


class TestVideoToolProperties:
    """Test VideoTool properties."""

    def test_name_property(self):
        """VideoTool.name returns correct value."""
        tool = VideoTool()
        assert tool.name == "video_tool"

    def test_version_property(self):
        """VideoTool.version returns correct value."""
        tool = VideoTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """VideoTool.dependencies returns empty list."""
        tool = VideoTool()
        assert tool.dependencies == []


class TestVideoToolInitialization:
    """Test VideoTool initialization."""

    def test_init_creates_manager(self):
        """VideoTool initializes with a manager."""
        tool = VideoTool()
        assert tool.manager is not None

    def test_api_methods_property(self):
        """VideoTool.api_methods returns correct methods."""
        tool = VideoTool()
        api_methods = tool.api_methods

        assert 'extract_frames' in api_methods
        assert 'get_metadata' in api_methods
        assert 'compute_phash' in api_methods

        # Verify they are bound to manager methods
        assert api_methods['extract_frames'] == tool.manager.extract_frames
        assert api_methods['get_metadata'] == tool.manager.get_video_metadata
        assert api_methods['compute_phash'] == tool.manager.compute_perceptual_hash

    def test_api_methods_are_callable(self):
        """VideoTool.api_methods returns callable methods."""
        tool = VideoTool()
        api_methods = tool.api_methods

        assert callable(api_methods['extract_frames'])
        assert callable(api_methods['get_metadata'])
        assert callable(api_methods['compute_phash'])


class TestVideoToolInitialize:
    """Test VideoTool.initialize() method."""

    def test_initialize_registers_service(self):
        """initialize() registers video_manager service."""
        tool = VideoTool()
        container = MagicMock()

        tool.initialize(container)

        container.register_service.assert_called_once_with('video_manager', tool.manager)

    def test_initialize_with_mock_container(self):
        """initialize() works with mock container."""
        tool = VideoTool()
        container = MagicMock()
        container.register_service = MagicMock()

        tool.initialize(container)

        assert container.register_service.called

    def test_initialize_preserves_manager(self):
        """initialize() preserves the manager reference."""
        tool = VideoTool()
        container = MagicMock()
        original_manager = tool.manager

        tool.initialize(container)

        assert tool.manager is original_manager


class TestVideoToolShutdown:
    """Test VideoTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = VideoTool()
        # Should not raise
        tool.shutdown()

    def test_shutdown_multiple_times(self):
        """shutdown() can be called multiple times without error."""
        tool = VideoTool()
        tool.shutdown()
        tool.shutdown()  # Should not raise

    def test_shutdown_before_initialize(self):
        """shutdown() works even if initialize was not called."""
        tool = VideoTool()
        tool.shutdown()  # Should not raise


class TestVideoToolGetCapabilities:
    """Test VideoTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary with expected keys."""
        tool = VideoTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'backends' in capabilities
        assert 'available' in capabilities

    def test_get_capabilities_backends(self):
        """get_capabilities() returns list for backends."""
        tool = VideoTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['backends'], list)

    def test_get_capabilities_available(self):
        """get_capabilities() returns boolean for available."""
        tool = VideoTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['available'], bool)

    def test_get_capabilities_with_mocked_manager(self):
        """get_capabilities() uses manager info correctly."""
        tool = VideoTool()
        mock_backend1 = MagicMock()
        mock_backend1.__class__.__name__ = 'MockBackend1'
        mock_backend2 = MagicMock()
        mock_backend2.__class__.__name__ = 'MockBackend2'
        tool.manager.backends = [mock_backend1, mock_backend2]

        capabilities = tool.get_capabilities()

        assert capabilities['backends'] == ['MockBackend1', 'MockBackend2']
        assert capabilities['available'] is True

    def test_get_capabilities_no_backends(self):
        """get_capabilities() handles no backends."""
        tool = VideoTool()
        tool.manager.backends = []

        capabilities = tool.get_capabilities()

        assert capabilities['backends'] == []
        assert capabilities['available'] is False


class TestRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_video_tool(self):
        """register_tool() returns a VideoTool instance."""
        tool = register_tool()
        assert isinstance(tool, VideoTool)

    def test_register_tool_creates_new_instance(self):
        """register_tool() creates a new instance each call."""
        tool1 = register_tool()
        tool2 = register_tool()
        assert tool1 is not tool2

    def test_register_tool_properties(self):
        """register_tool() returns tool with correct properties."""
        tool = register_tool()
        assert tool.name == "video_tool"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []


class TestVideoToolDescribeUsage:
    """Test VideoTool.describe_usage() method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = VideoTool()
        description = tool.describe_usage()

        assert isinstance(description, str)
        assert "video" in description.lower()

    def test_describe_usage_mentions_opencv(self):
        """describe_usage() mentions OpenCV support."""
        tool = VideoTool()
        description = tool.describe_usage()

        assert "opencv" in description.lower()

    def test_describe_usage_mentions_ffmpeg(self):
        """describe_usage() mentions FFmpeg support."""
        tool = VideoTool()
        description = tool.describe_usage()

        assert "ffmpeg" in description.lower()

    def test_describe_usage_mentions_frame_extraction(self):
        """describe_usage() mentions frame extraction."""
        tool = VideoTool()
        description = tool.describe_usage()

        assert "frame" in description.lower() or "extraction" in description.lower()

    def test_describe_usage_mentions_metadata(self):
        """describe_usage() mentions metadata analysis."""
        tool = VideoTool()
        description = tool.describe_usage()

        assert "metadata" in description.lower()

    def test_describe_usage_mentions_hashing(self):
        """describe_usage() mentions perceptual hashing."""
        tool = VideoTool()
        description = tool.describe_usage()

        assert "hash" in description.lower()


class TestVideoToolRunStandalone:
    """Test VideoTool.run_standalone() method."""

    def test_run_standalone_returns_zero(self, capsys):
        """run_standalone() returns 0 and prints output."""
        tool = VideoTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Video Tool: Self-test mode." in captured.out
        assert "Backends:" in captured.out
        assert "Available:" in captured.out

    def test_run_standalone_with_args(self, capsys):
        """run_standalone() handles args parameter."""
        tool = VideoTool()
        result = tool.run_standalone(['--verbose', '--test'])

        assert result == 0

    def test_run_standalone_empty_args(self, capsys):
        """run_standalone() works with empty args."""
        tool = VideoTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Video Tool: Self-test mode." in captured.out

    def test_run_standalone_with_various_args(self, capsys):
        """run_standalone() handles various argument formats."""
        tool = VideoTool()

        # Test with different argument formats
        for args in [['--help'], ['-v'], ['test', 'arg1', 'arg2'], []]:
            result = tool.run_standalone(args)
            assert result == 0


class TestVideoToolWithMockedManager:
    """Test VideoTool with mocked manager for complete coverage."""

    @patch('nodupe.tools.video.video_plugin.get_video_backend_manager')
    def test_with_mocked_opencv_backend(self, mock_get_manager):
        """Test with mocked OpenCV backend."""
        mock_manager = MagicMock()
        mock_backend = MagicMock()
        mock_backend.__class__.__name__ = 'OpenCVBackend'
        mock_manager.backends = [mock_backend]
        mock_get_manager.return_value = mock_manager

        tool = VideoTool()

        caps = tool.get_capabilities()
        assert caps['backends'] == ['OpenCVBackend']
        assert caps['available'] is True

    @patch('nodupe.tools.video.video_plugin.get_video_backend_manager')
    def test_with_mocked_ffmpeg_backend(self, mock_get_manager):
        """Test with mocked FFmpeg backend."""
        mock_manager = MagicMock()
        mock_backend = MagicMock()
        mock_backend.__class__.__name__ = 'FFmpegSubprocessBackend'
        mock_manager.backends = [mock_backend]
        mock_get_manager.return_value = mock_manager

        tool = VideoTool()

        caps = tool.get_capabilities()
        assert caps['backends'] == ['FFmpegSubprocessBackend']

    @patch('nodupe.tools.video.video_plugin.get_video_backend_manager')
    def test_with_multiple_backends(self, mock_get_manager):
        """Test with multiple backends."""
        mock_manager = MagicMock()
        mock_backend1 = MagicMock()
        mock_backend1.__class__.__name__ = 'OpenCVBackend'
        mock_backend2 = MagicMock()
        mock_backend2.__class__.__name__ = 'FFmpegSubprocessBackend'
        mock_manager.backends = [mock_backend1, mock_backend2]
        mock_get_manager.return_value = mock_manager

        tool = VideoTool()

        caps = tool.get_capabilities()
        assert 'OpenCVBackend' in caps['backends']
        assert 'FFmpegSubprocessBackend' in caps['backends']
        assert caps['available'] is True

    @patch('nodupe.tools.video.video_plugin.get_video_backend_manager')
    def test_api_methods_call_manager(self, mock_get_manager):
        """Test that api_methods correctly call manager methods."""
        mock_manager = MagicMock()
        mock_manager.backends = [MagicMock()]
        mock_manager.extract_frames.return_value = []
        mock_manager.get_video_metadata.return_value = {'width': 1920, 'height': 1080}
        mock_manager.compute_perceptual_hash.return_value = 'abc123'
        mock_get_manager.return_value = mock_manager

        tool = VideoTool()

        # Test extract_frames
        tool.api_methods['extract_frames']('video.mp4')
        mock_manager.extract_frames.assert_called_once()

        # Test get_metadata
        tool.api_methods['get_metadata']('video.mp4')
        mock_manager.get_video_metadata.assert_called_once()

        # Test compute_phash
        import numpy as np
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        tool.api_methods['compute_phash'](frame)
        mock_manager.compute_perceptual_hash.assert_called_once()


class TestVideoToolEdgeCases:
    """Test VideoTool edge cases."""

    @patch('nodupe.tools.video.video_plugin.get_video_backend_manager')
    def test_manager_raises_exception(self, mock_get_manager):
        """Test handling when manager raises exception."""
        mock_manager = MagicMock()
        mock_manager.backends = [MagicMock()]
        mock_manager.extract_frames.side_effect = Exception("Extraction error")
        mock_get_manager.return_value = mock_manager

        tool = VideoTool()

        with pytest.raises(Exception, match="Extraction error"):
            tool.manager.extract_frames('video.mp4')

    @patch('nodupe.tools.video.video_plugin.get_video_backend_manager')
    def test_manager_returns_empty_results(self, mock_get_manager):
        """Test handling when manager operations return empty results."""
        mock_manager = MagicMock()
        mock_manager.backends = [MagicMock()]
        mock_manager.extract_frames.return_value = []
        mock_manager.get_video_metadata.return_value = {}
        mock_manager.compute_perceptual_hash.return_value = ''
        mock_get_manager.return_value = mock_manager

        tool = VideoTool()

        assert tool.manager.extract_frames('video.mp4') == []
        assert tool.manager.get_video_metadata('video.mp4') == {}
        assert tool.manager.compute_perceptual_hash(None) == ''

    def test_tool_instantiation_multiple_times(self):
        """Test that multiple tool instances can be created."""
        tool1 = VideoTool()
        tool2 = VideoTool()

        assert tool1 is not tool2
        assert tool1.name == tool2.name
        assert tool1.version == tool2.version

    @patch('nodupe.tools.video.video_plugin.get_video_backend_manager')
    def test_manager_no_backends(self, mock_get_manager):
        """Test handling when manager has no backends."""
        mock_manager = MagicMock()
        mock_manager.backends = []
        mock_get_manager.return_value = mock_manager

        tool = VideoTool()

        caps = tool.get_capabilities()
        assert caps['backends'] == []
        assert caps['available'] is False

    @patch('nodupe.tools.video.video_plugin.get_video_backend_manager')
    def test_manager_backends_attribute_error(self, mock_get_manager):
        """Test handling when manager backends attribute is missing."""
        mock_manager = MagicMock()
        del mock_manager.backends
        mock_get_manager.return_value = mock_manager

        tool = VideoTool()

        with pytest.raises(AttributeError):
            tool.get_capabilities()

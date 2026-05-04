# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/video/__init__.py - Video Backend implementations."""

from unittest.mock import MagicMock, mock_open, patch

import numpy as np
import pytest

# Import the video backend classes
from nodupe.tools.video import (
    FFmpegSubprocessBackend,
    OpenCVBackend,
    VideoBackend,
    VideoBackendManager,
    get_video_backend_manager,
)


class TestVideoBackend:
    """Test abstract VideoBackend class."""

    def test_is_abstract(self):
        """VideoBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            VideoBackend()


class TestFFmpegSubprocessBackend:
    """Test FFmpegSubprocessBackend class."""

    def test_ffmpeg_backend_creation(self):
        """FFmpegSubprocessBackend can be created."""
        backend = FFmpegSubprocessBackend()
        assert backend is not None

    def test_ffmpeg_backend_priority(self):
        """FFmpegSubprocessBackend has priority 5."""
        backend = FFmpegSubprocessBackend()
        assert backend.get_priority() == 5

    def test_get_priority(self):
        """get_priority returns correct priority."""
        backend = FFmpegSubprocessBackend()
        assert backend.get_priority() == 5


class TestOpenCVBackend:
    """Test OpenCVBackend class."""

    def test_opencv_backend_creation(self):
        """OpenCVBackend can be created."""
        backend = OpenCVBackend()
        assert backend is not None

    def test_opencv_backend_priority(self):
        """OpenCVBackend has priority 4."""
        backend = OpenCVBackend()
        assert backend.get_priority() == 4


class TestVideoBackendManager:
    """Test VideoBackendManager class."""

    def test_manager_creation(self):
        """VideoBackendManager can be created."""
        manager = VideoBackendManager()
        assert manager is not None

    def test_manager_backends_list(self):
        """VideoBackendManager has backends list."""
        manager = VideoBackendManager()
        assert isinstance(manager.backends, list)

    def test_extract_frames_no_backends(self):
        """VideoBackendManager handles no backends."""
        manager = VideoBackendManager()
        # Even with no backends, should not crash
        frames = manager.extract_frames("nonexistent.mp4")
        assert frames == []

    def test_get_video_metadata_no_backends(self):
        """VideoBackendManager handles no backends for metadata."""
        manager = VideoBackendManager()
        metadata = manager.get_video_metadata("nonexistent.mp4")
        assert metadata == {}

    def test_compute_perceptual_hash_no_backends(self):
        """VideoBackendManager handles no backends for hashing."""
        manager = VideoBackendManager()
        # Create a dummy frame
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        phash = manager.compute_perceptual_hash(frame)
        # Should return empty string or fallback hash
        assert isinstance(phash, str)


class TestGetVideoBackendManager:
    """Test get_video_backend_manager function."""

    def test_get_manager_returns_manager(self):
        """get_video_backend_manager returns VideoBackendManager."""
        manager = get_video_backend_manager()
        assert isinstance(manager, VideoBackendManager)

    def test_get_manager_singleton(self):
        """get_video_backend_manager returns the same instance."""
        manager1 = get_video_backend_manager()
        manager2 = get_video_backend_manager()
        # Both should be the same instance
        assert manager1 is manager2

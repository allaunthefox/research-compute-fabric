# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/gpu/__init__.py - GPU Backend implementations."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Import the GPU backend classes
from nodupe.tools.gpu import (
    CPUFallbackBackend,
    CUDABackend,
    GPUBackend,
    MetalBackend,
    create_gpu_backend,
    get_gpu_backend,
)


class TestGPUBackend:
    """Test abstract GPUBackend class."""

    def test_is_abstract(self):
        """GPUBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            GPUBackend()


class TestCPUFallbackBackend:
    """Test CPUFallbackBackend class."""

    def test_cpu_backend_creation(self):
        """CPUFallbackBackend can be created."""
        backend = CPUFallbackBackend()
        assert backend is not None

    def test_is_available(self):
        """CPUFallbackBackend is always available."""
        backend = CPUFallbackBackend()
        assert backend.is_available() is True

    def test_get_device_info(self):
        """CPUFallbackBackend returns device info."""
        backend = CPUFallbackBackend()
        info = backend.get_device_info()
        assert isinstance(info, dict)
        assert info['type'] == 'cpu'

    def test_compute_embeddings_empty_list(self):
        """CPUFallbackBackend handles empty list."""
        backend = CPUFallbackBackend()
        embeddings = backend.compute_embeddings([])
        assert embeddings == []

    def test_compute_embeddings_lists(self):
        """CPUFallbackBackend generates embeddings for lists."""
        backend = CPUFallbackBackend()
        embeddings = backend.compute_embeddings([[1, 2, 3], [4, 5, 6]])
        assert len(embeddings) == 2

    def test_compute_embeddings_numpy_arrays(self):
        """CPUFallbackBackend generates embeddings for numpy arrays."""
        backend = CPUFallbackBackend()
        arr1 = np.array([1.0, 2.0, 3.0])
        arr2 = np.array([4.0, 5.0, 6.0])
        embeddings = backend.compute_embeddings([arr1, arr2])
        assert len(embeddings) == 2

    def test_compute_embeddings_other_types(self):
        """CPUFallbackBackend handles other types."""
        backend = CPUFallbackBackend()
        embeddings = backend.compute_embeddings([42, "string", None])
        assert len(embeddings) == 3

    def test_matrix_multiply_basic(self):
        """CPUFallbackBackend performs matrix multiplication."""
        backend = CPUFallbackBackend()
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        result = backend.matrix_multiply(a, b)
        # [[1*5+2*7, 1*6+2*8], [3*5+4*7, 3*6+4*8]] = [[19, 22], [43, 50]]
        assert result[0][0] == 19
        assert result[0][1] == 22
        assert result[1][0] == 43
        assert result[1][1] == 50

    def test_matrix_multiply_empty(self):
        """CPUFallbackBackend handles empty matrices."""
        backend = CPUFallbackBackend()
        result = backend.matrix_multiply([], [])
        # Empty input returns 0.0 or empty
        assert result == [] or result == 0.0

    def test_matrix_multiply_invalid(self):
        """CPUFallbackBackend handles invalid matrices."""
        backend = CPUFallbackBackend()
        result = backend.matrix_multiply([[1, 2]], [[3], [4]])  # Incompatible dimensions
        # Should return empty or handle gracefully
        assert isinstance(result, list)


class TestCUDABackend:
    """Test CUDABackend class."""

    def test_cuda_backend_creation(self):
        """CUDABackend can be created."""
        backend = CUDABackend()
        assert backend is not None

    def test_cuda_backend_with_device_id(self):
        """CUDABackend can be created with device_id."""
        backend = CUDABackend(device_id=1)
        assert backend.device_id == 1

    def test_cuda_backend_not_available(self):
        """CUDABackend is not available without CUDA."""
        backend = CUDABackend()
        # Falls back to CPU when CUDA is not available
        assert backend.is_available() is False

    def test_get_device_info_no_device(self):
        """CUDABackend returns empty dict when not available."""
        backend = CUDABackend()
        info = backend.get_device_info()
        assert info == {}


class TestMetalBackend:
    """Test MetalBackend class."""

    def test_metal_backend_creation(self):
        """MetalBackend can be created."""
        backend = MetalBackend()
        assert backend is not None

    def test_metal_backend_not_available(self):
        """MetalBackend is not available without Metal."""
        backend = MetalBackend()
        # Falls back to CPU when Metal is not available
        assert backend.is_available() is False

    def test_get_device_info_no_device(self):
        """MetalBackend returns empty dict when not available."""
        backend = MetalBackend()
        info = backend.get_device_info()
        assert info == {}


class TestCreateGpuBackend:
    """Test create_gpu_backend factory function."""

    def test_create_gpu_backend_auto(self):
        """create_gpu_backend with 'auto' returns CPUFallbackBackend."""
        backend = create_gpu_backend('auto')
        assert isinstance(backend, CPUFallbackBackend)

    def test_create_gpu_backend_cpu(self):
        """create_gpu_backend with 'cpu' returns CPUFallbackBackend."""
        backend = create_gpu_backend('cpu')
        assert isinstance(backend, CPUFallbackBackend)

    def test_create_gpu_backend_cuda(self):
        """create_gpu_backend with 'cuda' returns CUDABackend."""
        backend = create_gpu_backend('cuda')
        assert isinstance(backend, CUDABackend)

    def test_create_gpu_backend_metal(self):
        """create_gpu_backend with 'metal' returns MetalBackend."""
        backend = create_gpu_backend('metal')
        assert isinstance(backend, MetalBackend)

    def test_create_gpu_backend_unknown_type(self):
        """create_gpu_backend raises ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown GPU backend type"):
            create_gpu_backend('unknown')


class TestGetGpuBackend:
    """Test get_gpu_backend function."""

    def test_get_backend_returns_backend(self):
        """get_gpu_backend returns a GPUBackend."""
        backend = get_gpu_backend()
        assert isinstance(backend, GPUBackend)

    def test_get_backend_singleton(self):
        """get_gpu_backend returns the same instance."""
        backend1 = get_gpu_backend()
        backend2 = get_gpu_backend()
        assert backend1 is backend2

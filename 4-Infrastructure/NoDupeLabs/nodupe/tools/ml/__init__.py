"""NoDupeLabs ML Tools - Machine Learning Backends

This module provides ML backend implementations for embedding generation
and other machine learning tasks with graceful degradation.

Key Features:
    - Multiple backend support (CPU, ONNX)
    - Graceful fallback to CPU
    - Embedding generation
    - Extensible backend interface
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

# Lazy numpy import - only import when actually needed
_numpy = None


def _get_numpy():
    """Lazy numpy import."""
    global _numpy
    if _numpy is None:
        import numpy as np
        _numpy = np
    return _numpy


class MLBackend(ABC):
    """Abstract base class for ML backends.
    
    Defines the interface that all ML backend implementations must follow.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available.
        
        Returns:
            True if the backend can be used, False otherwise
        """

    @abstractmethod
    def generate_embeddings(self, data: List[Any]) -> List[List[float]]:
        """Generate embeddings for input data.
        
        Args:
            data: List of items to generate embeddings for
            
        Returns:
            List of embedding vectors
        """

    @abstractmethod
    def get_embedding_dimensions(self) -> int:
        """Get the dimensionality of embeddings produced by this backend.
        
        Returns:
            Embedding dimension size
        """


class CPUBackend(MLBackend):
    """CPU-based ML backend using pure NumPy (always available).
    
    Provides CPU-based implementations of ML operations as a fallback
    when other backends are not available.
    """

    def __init__(self):
        """Initialize CPU backend."""
        self.dimensions = 128  # Default embedding dimensions

    def is_available(self) -> bool:
        """This backend is always available.
        
        Returns:
            Always True
        """
        return True

    def generate_embeddings(self, data: List[Any]) -> List[List[float]]:
        """Generate simple embeddings using NumPy.

        This is a placeholder implementation that creates random embeddings.

        Args:
            data: List of items to generate embeddings for

        Returns:
            List of embedding vectors
        """
        try:
            np = _get_numpy()
            embeddings = []
            for item in data:
                # Simple hash-based embedding for demonstration
                if isinstance(item, str):
                    # Convert string to numerical representation
                    embedding = np.random.randn(self.dimensions).tolist()
                elif isinstance(item, (list, np.ndarray)):
                    # For array-like data, create embedding based on content
                    embedding = np.random.randn(self.dimensions).tolist()
                else:
                    # Fallback for other types
                    embedding = np.random.randn(self.dimensions).tolist()
                embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings with CPU backend: {e}")
            # Return empty embeddings on error
            return [[] for _ in data]

    def get_embedding_dimensions(self) -> int:
        """Get embedding dimensionality.
        
        Returns:
            Embedding dimension size
        """
        return self.dimensions


class ONNXBackend(MLBackend):
    """ONNX Runtime backend for ML inference.
    
    Provides ONNX-based ML inference when available.
    Falls back to CPU if ONNX is not available.
    """

    def __init__(self, model_path: Optional[str] = None):
        """Initialize ONNX backend.
        
        Args:
            model_path: Optional path to ONNX model file
        """
        self.dimensions = 128
        self.model_path = model_path
        self._available = False
        self._model = None

        try:
            # Try to import ONNX runtime
            import onnxruntime as ort

            # Try to load model if path provided
            if model_path:
                self._model = ort.InferenceSession(model_path)
                self._available = True
                logger.info(f"ONNX backend loaded model from {model_path}")
            else:
                logger.warning("ONNX backend: no model path provided")
        except ImportError:
            logger.warning("ONNX runtime not available, falling back to CPU backend")
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")

    def is_available(self) -> bool:
        """Check if ONNX backend is available.
        
        Returns:
            True if ONNX is available and model is loaded, False otherwise
        """
        return self._available

    def generate_embeddings(self, data: List[Any]) -> List[List[float]]:
        """Generate embeddings using ONNX model.

        Args:
            data: List of items to generate embeddings for

        Returns:
            List of embedding vectors
        """
        if not self.is_available():
            logger.warning("ONNX backend not available, using CPU fallback")
            cpu_backend = CPUBackend()
            return cpu_backend.generate_embeddings(data)

        try:
            np = _get_numpy()
            # Placeholder: actual implementation would use ONNX model
            embeddings = []
            for _ in data:
                # Convert data to format expected by ONNX model
                # This is a placeholder - actual implementation would preprocess data
                embedding = np.random.randn(self.dimensions).tolist()
                embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings with ONNX backend: {e}")
            # Fallback to CPU backend
            cpu_backend = CPUBackend()
            return cpu_backend.generate_embeddings(data)

    def get_embedding_dimensions(self) -> int:
        """Get embedding dimensionality.
        
        Returns:
            Embedding dimension size
        """
        return self.dimensions


def create_ml_backend(backend_type: str = "auto", **kwargs) -> MLBackend:
    """Create an ML backend instance with graceful degradation.

    Args:
        backend_type: Type of backend ('auto', 'cpu', 'onnx')
        **kwargs: Additional arguments for backend creation

    Returns:
        MLBackend instance
    """
    backend_type = backend_type.lower()

    if backend_type == "auto":
        # Try ONNX first, fallback to CPU
        try:
            onnx_backend = ONNXBackend(kwargs.get('model_path'))
            if onnx_backend.is_available():
                logger.info("Using ONNX backend")
                return onnx_backend
        except Exception:
            pass

        # Fallback to CPU
        logger.info("Using CPU backend (fallback)")
        return CPUBackend()

    elif backend_type == "onnx":
        return ONNXBackend(kwargs.get('model_path'))

    elif backend_type == "cpu":
        return CPUBackend()

    else:
        raise ValueError(f"Unknown backend type: {backend_type}")


# Module-level backend instance (lazy initialization)
ML_BACKEND: Optional[MLBackend] = None


def get_ml_backend() -> MLBackend:
    """Get the global ML backend instance.
    
    Returns:
        The singleton MLBackend instance
    """
    global ML_BACKEND
    if ML_BACKEND is None:
        ML_BACKEND = create_ml_backend()
    return ML_BACKEND


# Initialize backend on import
get_ml_backend()

__all__ = ['MLBackend', 'CPUBackend', 'ONNXBackend', 'create_ml_backend', 'get_ml_backend']

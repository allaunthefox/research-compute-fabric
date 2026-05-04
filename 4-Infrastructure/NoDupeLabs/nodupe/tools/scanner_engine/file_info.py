"""File Information Module.

Get basic file information using only standard library.

Key Features:
    - File metadata retrieval
    - File type detection
    - Symbolic link handling
"""

from pathlib import Path
from typing import Dict, Any


class FileInfo:
    """File information container.
    
    Provides access to file metadata and properties.
    """

    def __init__(self, file_path: Path):
        """Initialize FileInfo.
        
        Args:
            file_path: Path to the file
        """
        self.file_path = file_path

    def get_info(self) -> Dict[str, Any]:
        """Get file information.
        
        Returns:
            Dictionary containing file metadata
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File {self.file_path} does not exist")

        stat = self.file_path.stat()
        return {
            'path': str(self.file_path),
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'ctime': stat.st_ctime,
            'is_file': self.file_path.is_file(),
            'is_dir': self.file_path.is_dir(),
            'is_symlink': self.file_path.is_symlink()
        }

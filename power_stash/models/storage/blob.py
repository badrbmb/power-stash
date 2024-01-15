from pathlib import Path
from typing import Protocol


class StorageInterface(Protocol):
    """Generic interface for storing blob data."""

    def exists(self, *, path: Path) -> bool:
        """Check if file exists in store."""
        pass

    def is_valid(self, *, path: Path, min_size_bytes: float) -> bool:
        """Check if a file is valid."""

    def store(self, *, obj: any, destination_path: Path) -> Path:
        """Store an object."""
        pass

    def delete(self, *, path: Path) -> bool:
        """Delete a given record using path."""
        pass

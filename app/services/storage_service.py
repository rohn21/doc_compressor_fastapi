"""Local and adapter-ready storage service for original and compressed files."""

import io
import uuid
import zipfile
from pathlib import Path

from app.core.config import get_settings


class StorageService:
    """Handles persistence, retrieval, and packaging of files."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        settings = get_settings()
        self.base_dir = Path(base_dir or settings.LOCAL_STORAGE_DIR).resolve()
        self.raw_dir = self.base_dir / "raw"
        self.compressed_dir = self.base_dir / "compressed"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure necessary storage directories exist."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.compressed_dir.mkdir(parents=True, exist_ok=True)

    def save_file(
        self,
        content: bytes,
        filename: str,
        is_output: bool = False,
    ) -> tuple[str, str]:
        """Save binary content to storage.

        Returns (internal_file_reference, storage_path).
        """
        target_dir = self.compressed_dir if is_output else self.raw_dir
        ext = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        dest_path = target_dir / unique_name

        dest_path.write_bytes(content)
        # Internal reference is relative or string representation
        rel_ref = str(dest_path.relative_to(self.base_dir))
        return rel_ref, str(dest_path)

    def get_absolute_path(self, reference: str) -> Path:
        """Resolve a storage reference to an absolute filesystem path."""
        p = Path(reference)
        if p.is_absolute():
            return p
        return (self.base_dir / reference).resolve()

    def read_file(self, reference: str) -> bytes:
        """Read binary contents from a storage reference."""
        path = self.get_absolute_path(reference)
        if not path.is_file():
            raise FileNotFoundError(f"Stored file not found: {reference}")
        return path.read_bytes()

    def delete_file(self, reference: str) -> bool:
        """Delete stored file if present."""
        try:
            path = self.get_absolute_path(reference)
            if path.is_file():
                path.unlink()
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def create_zip_archive(files: list[tuple[str, bytes]]) -> bytes:
        """Create a zip archive in memory from a list of (archive_filename, file_bytes).

        Handles duplicate filenames gracefully by appending numeric counters.
        """
        buffer = io.BytesIO()
        used_names: set[str] = set()

        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for original_name, data in files:
                # Handle filename collisions in the ZIP
                name = original_name
                counter = 1
                base_stem = Path(original_name).stem
                suffix = Path(original_name).suffix

                while name in used_names:
                    name = f"{base_stem}_{counter}{suffix}"
                    counter += 1

                used_names.add(name)
                zip_file.writestr(name, data)

        return buffer.getvalue()


# Default singleton instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Retrieve global storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service

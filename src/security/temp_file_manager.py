# src/security/temp_file_manager.py
import os
import tempfile
import hashlib
import atexit
import time
from pathlib import Path
from typing import Dict, List, Optional, Generator
from contextlib import contextmanager
import threading


class SecureTempFileManager:
    """Secure temporary file management with automatic cleanup and tracking"""

    def __init__(self, base_dir: Optional[str] = None, max_age_hours: int = 24):
        self.base_dir = base_dir or tempfile.gettempdir()
        self.max_age_hours = max_age_hours
        self._active_files: Dict[str, Dict] = {}
        self._lock = threading.Lock()

        self._ensure_secure_temp_dir()
        atexit.register(self.cleanup_all_files)

    def _ensure_secure_temp_dir(self) -> None:
        """Ensure temp directory exists with secure permissions"""
        secure_temp_dir = Path(self.base_dir) / "secure_uploads"
        secure_temp_dir.mkdir(mode=0o700, exist_ok=True)
        self.secure_dir = secure_temp_dir

    def create_secure_temp_file(
        self,
        content: bytes,
        original_filename: str,
        file_hash: str,
        user_id: Optional[str] = None
    ) -> str:
        """Create secure temporary file with tracking"""

        suffix = Path(original_filename).suffix
        safe_name = self._sanitize_filename(Path(original_filename).stem)
        prefix = f"secure_{safe_name}_{file_hash[:8]}_"

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                prefix=prefix,
                dir=str(self.secure_dir),
                mode='wb'
            ) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            os.chmod(temp_path, 0o600)

            file_info = {
                'path': temp_path,
                'original_filename': original_filename,
                'file_hash': file_hash,
                'user_id': user_id,
                'created_at': time.time(),
                'size': len(content),
                'accessed_at': time.time()
            }

            with self._lock:
                self._active_files[temp_path] = file_info

            return temp_path

        except Exception as e:
            raise Exception(f"Failed to create secure temp file: {str(e)}")

    @contextmanager
    def secure_temp_file_context(
        self,
        content: bytes,
        original_filename: str,
        file_hash: str,
        user_id: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Context manager for automatic cleanup of temp files"""
        temp_path = None
        try:
            temp_path = self.create_secure_temp_file(
                content, original_filename, file_hash, user_id
            )
            yield temp_path
        finally:
            if temp_path:
                self.cleanup_file(temp_path)

    def access_file(self, temp_path: str) -> bool:
        """Mark file as accessed and validate it exists"""
        with self._lock:
            if temp_path in self._active_files:
                if os.path.exists(temp_path):
                    self._active_files[temp_path]['accessed_at'] = time.time()
                    return True
                else:
                    del self._active_files[temp_path]
                    return False
            return False

    def cleanup_file(self, temp_path: str) -> bool:
        """Securely cleanup a specific temporary file"""
        try:
            if os.path.exists(temp_path):
                self._secure_delete(temp_path)

            with self._lock:
                if temp_path in self._active_files:
                    del self._active_files[temp_path]

            return True

        except Exception as e:
            print(f"⚠️ Failed to cleanup temp file {temp_path}: {e}")
            return False

    def cleanup_old_files(self) -> int:
        """Clean up files older than max_age_hours"""
        cleaned_count = 0
        current_time = time.time()
        max_age_seconds = self.max_age_hours * 3600

        with self._lock:
            files_to_cleanup = []
            for temp_path, file_info in self._active_files.items():
                if current_time - file_info['created_at'] > max_age_seconds:
                    files_to_cleanup.append(temp_path)

        for temp_path in files_to_cleanup:
            if self.cleanup_file(temp_path):
                cleaned_count += 1

        return cleaned_count

    def cleanup_all_files(self) -> int:
        """Clean up all tracked temporary files"""
        cleaned_count = 0

        with self._lock:
            files_to_cleanup = list(self._active_files.keys())

        for temp_path in files_to_cleanup:
            if self.cleanup_file(temp_path):
                cleaned_count += 1

        return cleaned_count

    def get_file_info(self, temp_path: str) -> Optional[Dict]:
        """Get information about a tracked temporary file"""
        with self._lock:
            return self._active_files.get(temp_path, {}).copy()

    def list_active_files(self, user_id: Optional[str] = None) -> List[Dict]:
        """List all active temporary files, optionally filtered by user"""
        with self._lock:
            files = []
            for file_info in self._active_files.values():
                if user_id is None or file_info.get('user_id') == user_id:
                    files.append(file_info.copy())
            return files

    def get_stats(self) -> Dict:
        """Get statistics about temporary file usage"""
        with self._lock:
            total_files = len(self._active_files)
            total_size = sum(info['size'] for info in self._active_files.values())

            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'secure_dir': str(self.secure_dir),
                'max_age_hours': self.max_age_hours
            }

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe use"""
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        sanitized = ''.join(c if c in safe_chars else '_' for c in filename)
        return sanitized[:50]

    def _secure_delete(self, file_path: str) -> None:
        """Securely delete file by overwriting before deletion"""
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)

                with open(file_path, 'r+b') as f:
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

                os.remove(file_path)

        except Exception as e:
            try:
                os.remove(file_path)
            except Exception:
                pass
            raise e


_global_temp_manager = None

def get_temp_file_manager() -> SecureTempFileManager:
    """Get global secure temp file manager instance"""
    global _global_temp_manager
    if _global_temp_manager is None:
        _global_temp_manager = SecureTempFileManager()
    return _global_temp_manager

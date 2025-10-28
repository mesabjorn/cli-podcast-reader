import datetime
import os
from pathlib import Path
from typing import Optional

from dataclasses import dataclass


@dataclass
class CacheFileData:
    filename: str
    data: str | bytes
    timestamp: str


class CacheManager:
    def __init__(self, cache_dir: Path, file_lifetime_seconds: int = 3600):
        self.cache = cache_dir
        self.FILE_LIFETIME = file_lifetime_seconds
        # Ensure cache directory exists
        self.cache.mkdir(parents=True, exist_ok=True)

    def write(
        self, filename: str, data: bytes, timestamp: Optional[datetime.datetime] = None
    ) -> bool:
        """Write data to cache with an optional timestamp.

        Args:
            filename: Name of the cache file
            data: Binary data to store
            timestamp: Optional timestamp to store (defaults to current time)

        Returns:
            bool: True if write was successful, False otherwise
        """
        path = self.cache / filename
        try:
            # Use atomic write by writing to temp file first
            temp_path = path.with_suffix(".tmp")

            timestamp_str = (timestamp or datetime.datetime.now()).isoformat()
            if len(timestamp_str) > 16:
                timestamp_str = timestamp_str[:16]  # Ensure consistent length

            with open(temp_path, "wb") as f:
                f.write(timestamp_str.encode("utf-8"))
                f.write(data)

            # Atomic rename (works on both Unix and Windows)
            temp_path.replace(path)
            return True

        except OSError as e:
            print(f"Failed to write cache {filename}: {e}")
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass
            return False

    def read(self, filename: str, encoding=None) -> CacheFileData | None:
        """Read data from cache.

        Args:
            filename: Name of the cache file

        Returns:
            tuple of (data, timestamp) if successful, None otherwise
        """
        path = self.cache / filename
        if not path.exists():
            return None

        try:
            with open(path, "rb") as f:
                timestamp_bytes = f.read(16)
                try:
                    timestamp_str = timestamp_bytes.decode("utf-8")
                    timestamp = datetime.datetime.fromisoformat(timestamp_str)
                except (UnicodeDecodeError, ValueError) as e:
                    print(f"Invalid timestamp in cache {filename}: {e}")
                    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(path))

                if self.is_file_expired(timestamp):
                    return None

                data = f.read()
                return CacheFileData(
                    filename=path,
                    data=data.decode(encoding) if encoding else data,
                    timestamp=timestamp_str,
                )

        except OSError as e:
            print(f"Failed to read cache {filename}: {e}")
            return None

    def is_file_expired(self, timestamp: datetime.datetime):
        # Check if cached file is expired
        current_time = datetime.datetime.now()
        return (current_time - timestamp).total_seconds() > self.FILE_LIFETIME

    def clear(self, filename: Optional[str] = None) -> bool:
        """Clear cache entry or entire cache.

        Args:
            filename: If specified, clears only this file. Otherwise clears all cache.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if filename:
                (self.cache / filename).unlink()
            else:
                for item in self.cache.glob("*"):
                    item.unlink()
            return True
        except OSError as e:
            print(f"Failed to clear cache: {e}")
            return False

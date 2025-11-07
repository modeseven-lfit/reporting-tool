# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Advanced caching module for INFO.yaml data.

Provides multi-level caching with TTL (time-to-live), LRU eviction,
and persistent storage support for parsed INFO.yaml data, URL validation
results, and enrichment data.
"""

import hashlib
import json
import logging
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """
    Represents a single cache entry with metadata.

    Attributes:
        key: Cache key
        value: Cached value
        created_at: Unix timestamp when entry was created
        accessed_at: Unix timestamp when entry was last accessed
        access_count: Number of times entry has been accessed
        ttl: Time-to-live in seconds (None = no expiration)
        size_bytes: Approximate size in bytes
    """

    key: str
    value: T
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """
        Check if the cache entry has expired.

        Args:
            current_time: Current time (defaults to time.time())

        Returns:
            True if expired, False otherwise
        """
        if self.ttl is None:
            return False

        if current_time is None:
            current_time = time.time()

        return (current_time - self.created_at) > self.ttl

    def touch(self) -> None:
        """Update access time and increment access count."""
        self.accessed_at = time.time()
        self.access_count += 1


class LRUCache(Generic[T]):
    """
    LRU (Least Recently Used) cache with TTL support.

    Features:
    - Automatic eviction based on size or entry count
    - Time-to-live (TTL) expiration
    - Access tracking for statistics
    - Thread-safe operations
    """

    def __init__(
        self,
        max_entries: int = 1000,
        max_size_bytes: Optional[int] = None,
        default_ttl: Optional[float] = None,
    ):
        """
        Initialize the LRU cache.

        Args:
            max_entries: Maximum number of entries (default: 1000)
            max_size_bytes: Maximum total size in bytes (None = unlimited)
            default_ttl: Default time-to-live in seconds (None = no expiration)
        """
        self.max_entries = max_entries
        self.max_size_bytes = max_size_bytes
        self.default_ttl = default_ttl

        self._cache: Dict[str, CacheEntry[T]] = {}
        self._total_size_bytes = 0

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(
            f"LRUCache initialized: max_entries={max_entries}, "
            f"max_size_bytes={max_size_bytes}, default_ttl={default_ttl}"
        )

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return default

        # Check if expired
        if entry.is_expired():
            self._misses += 1
            self._evict_entry(key)
            return default

        # Update access metadata
        entry.touch()
        self._hits += 1

        return entry.value

    def set(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
        """
        # Calculate size
        size_bytes = self._estimate_size(value)

        # Check if we need to evict existing entry
        if key in self._cache:
            self._evict_entry(key)

        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=0,
            ttl=ttl if ttl is not None else self.default_ttl,
            size_bytes=size_bytes,
        )

        # Evict if necessary
        self._evict_if_necessary(size_bytes)

        # Add to cache
        self._cache[key] = entry
        self._total_size_bytes += size_bytes

        self.logger.debug(
            f"Cached entry: key={key}, size={size_bytes}B, "
            f"total_entries={len(self._cache)}"
        )

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        if key in self._cache:
            self._evict_entry(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all entries from the cache."""
        count = len(self._cache)
        self._cache.clear()
        self._total_size_bytes = 0
        self.logger.info(f"Cleared {count} entries from cache")

    def _evict_entry(self, key: str) -> None:
        """Evict a specific entry from the cache."""
        entry = self._cache.pop(key, None)
        if entry:
            self._total_size_bytes -= entry.size_bytes
            self._evictions += 1

    def _evict_if_necessary(self, incoming_size: int) -> None:
        """
        Evict entries if necessary to make room for new entry.

        Args:
            incoming_size: Size of entry being added
        """
        # Check entry count limit
        while len(self._cache) >= self.max_entries:
            self._evict_lru()

        # Check size limit
        if self.max_size_bytes is not None:
            while (
                self._total_size_bytes + incoming_size > self.max_size_bytes
                and self._cache
            ):
                self._evict_lru()

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return

        # Find entry with oldest access time
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].accessed_at,
        )

        self._evict_entry(lru_key)
        self.logger.debug(f"Evicted LRU entry: {lru_key}")

    def _estimate_size(self, value: T) -> int:
        """
        Estimate the size of a value in bytes.

        Args:
            value: Value to estimate

        Returns:
            Estimated size in bytes
        """
        try:
            # Use pickle to estimate size
            return len(pickle.dumps(value))
        except Exception:
            # Fallback estimate
            return 1024  # 1KB default

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (
            (self._hits / total_requests * 100) if total_requests > 0 else 0.0
        )

        return {
            "entries": len(self._cache),
            "max_entries": self.max_entries,
            "size_bytes": self._total_size_bytes,
            "max_size_bytes": self.max_size_bytes,
            "size_mb": round(self._total_size_bytes / (1024 * 1024), 2),
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": round(hit_rate, 2),
        }

    def prune_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries pruned
        """
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if entry.is_expired(current_time)
        ]

        for key in expired_keys:
            self._evict_entry(key)

        if expired_keys:
            self.logger.info(f"Pruned {len(expired_keys)} expired entries")

        return len(expired_keys)


class PersistentCache:
    """
    Persistent cache that stores data to disk.

    Provides persistent storage for cache data across program runs,
    with support for JSON and pickle serialization.
    """

    def __init__(
        self,
        cache_dir: Path,
        format: str = "json",
        compression: bool = False,
    ):
        """
        Initialize the persistent cache.

        Args:
            cache_dir: Directory for cache files
            format: Serialization format ('json' or 'pickle')
            compression: Enable compression (not yet implemented)
        """
        self.cache_dir = Path(cache_dir)
        self.format = format
        self.compression = compression

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"PersistentCache initialized: dir={cache_dir}, format={format}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from persistent storage.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return None

        try:
            if self.format == "json":
                with open(cache_file, "r") as f:
                    return json.load(f)
            elif self.format == "pickle":
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
            else:
                self.logger.error(f"Unknown format: {self.format}")
                return None
        except Exception as e:
            self.logger.warning(f"Failed to load cache file {cache_file}: {e}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """
        Set a value in persistent storage.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if successful, False otherwise
        """
        cache_file = self._get_cache_file(key)

        try:
            if self.format == "json":
                with open(cache_file, "w") as f:
                    json.dump(value, f, indent=2)
            elif self.format == "pickle":
                with open(cache_file, "wb") as f:
                    pickle.dump(value, f)
            else:
                self.logger.error(f"Unknown format: {self.format}")
                return False

            return True
        except Exception as e:
            self.logger.warning(f"Failed to save cache file {cache_file}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from persistent storage.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        cache_file = self._get_cache_file(key)

        if cache_file.exists():
            try:
                cache_file.unlink()
                return True
            except Exception as e:
                self.logger.warning(f"Failed to delete cache file {cache_file}: {e}")
                return False

        return False

    def clear(self) -> int:
        """
        Clear all cache files.

        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*"):
            if cache_file.is_file():
                try:
                    cache_file.unlink()
                    count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete {cache_file}: {e}")

        self.logger.info(f"Cleared {count} cache files")
        return count

    def _get_cache_file(self, key: str) -> Path:
        """
        Get the cache file path for a key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        # Hash the key to create a safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]

        extension = "json" if self.format == "json" else "pkl"
        return self.cache_dir / f"{key_hash}.{extension}"


class MultiLevelCache(Generic[T]):
    """
    Multi-level cache combining memory (LRU) and persistent storage.

    Provides a two-tier caching system:
    - Level 1: Fast in-memory LRU cache
    - Level 2: Persistent disk cache

    Data flows from L2 to L1 on cache hits, providing optimal performance
    for frequently accessed data while maintaining long-term persistence.
    """

    def __init__(
        self,
        memory_cache: LRUCache[T],
        disk_cache: Optional[PersistentCache] = None,
    ):
        """
        Initialize the multi-level cache.

        Args:
            memory_cache: In-memory LRU cache (L1)
            disk_cache: Persistent disk cache (L2, optional)
        """
        self.memory_cache = memory_cache
        self.disk_cache = disk_cache

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(
            f"MultiLevelCache initialized: "
            f"memory={memory_cache is not None}, "
            f"disk={disk_cache is not None}"
        )

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get a value from the cache.

        Checks L1 (memory) first, then L2 (disk) if not found.
        Promotes disk values to memory on hit.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        # Check L1 (memory)
        value = self.memory_cache.get(key)
        if value is not None:
            self.logger.debug(f"L1 cache hit: {key}")
            return value

        # Check L2 (disk)
        if self.disk_cache is not None:
            value = self.disk_cache.get(key)
            if value is not None:
                self.logger.debug(f"L2 cache hit: {key}, promoting to L1")
                # Promote to L1
                self.memory_cache.set(key, value)
                return value  # type: ignore[no-any-return]

        return default

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.

        Writes to both L1 (memory) and L2 (disk).

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        # Write to L1
        self.memory_cache.set(key, value, ttl=ttl)

        # Write to L2
        if self.disk_cache is not None:
            self.disk_cache.set(key, value)

    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.

        Deletes from both L1 and L2.

        Args:
            key: Cache key
        """
        self.memory_cache.delete(key)

        if self.disk_cache is not None:
            self.disk_cache.delete(key)

    def clear(self) -> None:
        """Clear both L1 and L2 caches."""
        self.memory_cache.clear()

        if self.disk_cache is not None:
            self.disk_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all cache levels.

        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "memory": self.memory_cache.get_stats(),
        }

        if self.disk_cache is not None:
            cache_dir = self.disk_cache.cache_dir
            file_count = len(list(cache_dir.glob("*")))
            stats["disk"] = {
                "entries": file_count,
                "cache_dir": str(cache_dir),
            }

        return stats


def create_info_yaml_cache(
    cache_dir: Optional[Path] = None,
    max_memory_entries: int = 1000,
    ttl: Optional[float] = 3600,  # 1 hour default
    enable_disk_cache: bool = True,
) -> MultiLevelCache:
    """
    Factory function to create a configured multi-level cache for INFO.yaml data.

    Args:
        cache_dir: Directory for disk cache (None = use temp dir)
        max_memory_entries: Maximum entries in memory cache
        ttl: Default time-to-live in seconds
        enable_disk_cache: Enable persistent disk cache

    Returns:
        Configured MultiLevelCache instance
    """
    # Create memory cache
    memory_cache: LRUCache[Any] = LRUCache(
        max_entries=max_memory_entries,
        max_size_bytes=100 * 1024 * 1024,  # 100MB
        default_ttl=ttl,
    )

    # Create disk cache if enabled
    disk_cache = None
    if enable_disk_cache:
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "reporting-tool" / "info-yaml"
        disk_cache = PersistentCache(cache_dir, format="pickle")

    return MultiLevelCache(memory_cache, disk_cache)

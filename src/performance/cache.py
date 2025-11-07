# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Enhanced caching system for repository analysis.

This module provides intelligent caching for repository metadata and git operations
to significantly improve performance on repeated analyses.

Classes:
    CacheManager: Main cache coordinator
    RepositoryCache: Repository metadata caching
    GitOperationCache: Git command result caching
    CacheStats: Cache performance statistics
    CacheEntry: Individual cache entry
    CacheKey: Cache key generation

Example:
    >>> from src.performance.cache import CacheManager
    >>> cache = CacheManager(cache_dir=".cache", ttl=3600)
    >>> cache.set("repo:owner/name:metadata", metadata)
    >>> cached = cache.get("repo:owner/name:metadata")
    >>> stats = cache.get_stats()
    >>> print(f"Hit rate: {stats.hit_rate:.1%}")
"""

import hashlib
import json
import logging
import os
import pickle
import shutil
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Types of cached data."""
    REPOSITORY_METADATA = "repo_metadata"
    GIT_OPERATION = "git_operation"
    API_RESPONSE = "api_response"
    ANALYSIS_RESULT = "analysis_result"


@dataclass
class CacheEntry:
    """Individual cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    ttl: float
    size_bytes: int
    cache_type: CacheType
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl <= 0:  # Never expires
            return False
        return time.time() - self.created_at > self.ttl

    def age_seconds(self) -> float:
        """Get age in seconds."""
        return time.time() - self.created_at

    def touch(self) -> None:
        """Update access time and count."""
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    invalidations: int = 0
    expirations: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    oldest_entry_age: float = 0.0
    newest_entry_age: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate

    @property
    def total_size_mb(self) -> float:
        """Get total size in megabytes."""
        return self.total_size_bytes / (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "invalidations": self.invalidations,
            "expirations": self.expirations,
            "evictions": self.evictions,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "total_size_bytes": self.total_size_bytes,
            "total_size_mb": self.total_size_mb,
            "entry_count": self.entry_count,
            "oldest_entry_age": self.oldest_entry_age,
            "newest_entry_age": self.newest_entry_age,
        }

    def format(self) -> str:
        """Format statistics as string."""
        return f"""Cache Statistics:
  Requests: {self.hits + self.misses:,} ({self.hits:,} hits, {self.misses:,} misses)
  Hit Rate: {self.hit_rate:.1%}
  Sets: {self.sets:,}
  Invalidations: {self.invalidations:,}
  Expirations: {self.expirations:,}
  Evictions: {self.evictions:,}
  Size: {self.total_size_mb:.2f} MB ({self.entry_count:,} entries)
  Age Range: {self.newest_entry_age:.1f}s - {self.oldest_entry_age:.1f}s"""


class CacheKey:
    """Utilities for generating cache keys."""

    @staticmethod
    def repository(repo_url: str, ref: Optional[str] = None) -> str:
        """Generate key for repository metadata."""
        key = f"repo:{repo_url}"
        if ref:
            key += f":{ref}"
        return CacheKey._hash(key)

    @staticmethod
    def git_operation(repo_url: str, operation: str, params: Optional[Dict] = None) -> str:
        """Generate key for git operation result."""
        key = f"git:{repo_url}:{operation}"
        if params:
            # Sort params for consistent keys
            param_str = json.dumps(params, sort_keys=True)
            key += f":{param_str}"
        return CacheKey._hash(key)

    @staticmethod
    def api_response(endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate key for API response."""
        key = f"api:{endpoint}"
        if params:
            param_str = json.dumps(params, sort_keys=True)
            key += f":{param_str}"
        return CacheKey._hash(key)

    @staticmethod
    def analysis_result(repo_url: str, analysis_type: str, config: Optional[Dict] = None) -> str:
        """Generate key for analysis result."""
        key = f"analysis:{repo_url}:{analysis_type}"
        if config:
            config_str = json.dumps(config, sort_keys=True)
            key += f":{config_str}"
        return CacheKey._hash(key)

    @staticmethod
    def _hash(key: str) -> str:
        """Hash key to reasonable length."""
        # Keep first part human-readable, hash the rest
        parts = key.split(":", 2)
        if len(parts) > 2:
            prefix = ":".join(parts[:2])
            suffix = hashlib.sha256(parts[2].encode()).hexdigest()[:16]
            return f"{prefix}:{suffix}"
        return key


class CacheManager:
    """Main cache manager for repository analysis."""

    def __init__(
        self,
        cache_dir: Union[str, Path] = ".report-cache",
        ttl: float = 3600,
        max_size_mb: float = 1000,
        auto_cleanup: bool = True,
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache storage
            ttl: Default time-to-live in seconds (0 = never expire)
            max_size_mb: Maximum cache size in megabytes
            auto_cleanup: Automatically clean expired entries
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.max_size_mb = max_size_mb
        self.auto_cleanup = auto_cleanup

        # In-memory cache
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

        # Statistics
        self._stats = CacheStats()

        # Initialize cache directory
        self._init_cache_dir()

        # Load existing cache
        self._load_cache()

        logger.info(
            f"Cache initialized: dir={self.cache_dir}, ttl={self.ttl}s, "
            f"max_size={self.max_size_mb}MB"
        )

    def _init_cache_dir(self) -> None:
        """Initialize cache directory structure."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for different cache types
        for cache_type in CacheType:
            (self.cache_dir / cache_type.value).mkdir(exist_ok=True)

    def _get_cache_file(self, key: str, cache_type: CacheType) -> Path:
        """Get cache file path for key."""
        # Use first 2 chars of key for subdirectory (sharding)
        subdir = key[:2] if len(key) >= 2 else "00"
        cache_subdir = self.cache_dir / cache_type.value / subdir
        cache_subdir.mkdir(parents=True, exist_ok=True)
        return cache_subdir / f"{key}.pkl"

    def _load_cache(self) -> None:
        """Load cache entries from disk."""
        loaded = 0
        expired = 0

        for cache_type in CacheType:
            type_dir = self.cache_dir / cache_type.value
            if not type_dir.exists():
                continue

            for cache_file in type_dir.rglob("*.pkl"):
                try:
                    with open(cache_file, "rb") as f:
                        entry: CacheEntry = pickle.load(f)

                    if entry.is_expired():
                        cache_file.unlink()
                        expired += 1
                    else:
                        self._cache[entry.key] = entry
                        loaded += 1
                except Exception as e:
                    logger.warning(f"Failed to load cache entry {cache_file}: {e}")
                    cache_file.unlink(missing_ok=True)

        if loaded > 0:
            logger.info(f"Loaded {loaded} cache entries from disk ({expired} expired)")

        self._update_stats()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                logger.debug(f"Cache miss: {key}")
                return None

            if entry.is_expired():
                self._invalidate_entry(key, entry)
                self._stats.misses += 1
                self._stats.expirations += 1
                logger.debug(f"Cache expired: {key}")
                return None

            entry.touch()
            self._stats.hits += 1
            logger.debug(f"Cache hit: {key} (age={entry.age_seconds():.1f}s)")
            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        cache_type: CacheType = CacheType.REPOSITORY_METADATA,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
            cache_type: Type of cache entry

        Returns:
            True if cached successfully
        """
        if ttl is None:
            ttl = self.ttl

        with self._lock:
            # Serialize to get size
            try:
                serialized = pickle.dumps(value)
                size_bytes = len(serialized)
            except Exception as e:
                logger.error(f"Failed to serialize value for {key}: {e}")
                return False

            # Check if we need to evict
            if self.auto_cleanup:
                self._maybe_evict(size_bytes)

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl,
                size_bytes=size_bytes,
                cache_type=cache_type,
            )

            # Store in memory
            self._cache[key] = entry
            self._stats.sets += 1

            # Persist to disk
            try:
                cache_file = self._get_cache_file(key, cache_type)
                with open(cache_file, "wb") as f:
                    pickle.dump(entry, f)
                logger.debug(
                    f"Cached: {key} (size={size_bytes/1024:.1f}KB, ttl={ttl}s)"
                )
            except Exception as e:
                logger.error(f"Failed to persist cache entry {key}: {e}")
                # Keep in memory even if disk write fails

            self._update_stats()
            return True

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was invalidated
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False

            self._invalidate_entry(key, entry)
            self._stats.invalidations += 1
            self._update_stats()
            return True

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all entries matching pattern.

        Args:
            pattern: Pattern to match (supports * wildcard)

        Returns:
            Number of entries invalidated
        """
        import fnmatch

        with self._lock:
            keys_to_invalidate = [
                key for key in self._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]

            for key in keys_to_invalidate:
                entry = self._cache[key]
                self._invalidate_entry(key, entry)

            self._stats.invalidations += len(keys_to_invalidate)
            self._update_stats()

            logger.info(f"Invalidated {len(keys_to_invalidate)} entries matching '{pattern}'")
            return len(keys_to_invalidate)

    def _invalidate_entry(self, key: str, entry: CacheEntry) -> None:
        """Remove entry from cache."""
        # Remove from memory
        del self._cache[key]

        # Remove from disk
        cache_file = self._get_cache_file(key, entry.cache_type)
        cache_file.unlink(missing_ok=True)

        logger.debug(f"Invalidated: {key}")

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()

            # Clear disk cache
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self._init_cache_dir()

            # Reset statistics
            old_stats = self._stats
            self._stats = CacheStats()
            self._stats.invalidations = old_stats.invalidations + count

            logger.info(f"Cleared {count} cache entries")
            return count

    def cleanup(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries cleaned up
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                entry = self._cache[key]
                self._invalidate_entry(key, entry)

            self._stats.expirations += len(expired_keys)
            self._update_stats()

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)

    def _maybe_evict(self, needed_bytes: int) -> None:
        """Evict entries if cache is too full."""
        max_bytes = int(self.max_size_mb * 1024 * 1024)
        current_bytes = sum(entry.size_bytes for entry in self._cache.values())

        if current_bytes + needed_bytes <= max_bytes:
            return

        # Need to evict - use LRU strategy
        entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_accessed
        )

        evicted = 0
        for key, entry in entries:
            if current_bytes + needed_bytes <= max_bytes:
                break

            self._invalidate_entry(key, entry)
            current_bytes -= entry.size_bytes
            evicted += 1

        self._stats.evictions += evicted
        logger.info(f"Evicted {evicted} entries to make space")

    def _update_stats(self) -> None:
        """Update cache statistics."""
        if not self._cache:
            self._stats.entry_count = 0
            self._stats.total_size_bytes = 0
            self._stats.oldest_entry_age = 0.0
            self._stats.newest_entry_age = 0.0
            return

        self._stats.entry_count = len(self._cache)
        self._stats.total_size_bytes = sum(
            entry.size_bytes for entry in self._cache.values()
        )

        ages = [entry.age_seconds() for entry in self._cache.values()]
        self._stats.oldest_entry_age = max(ages)
        self._stats.newest_entry_age = min(ages)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            self._update_stats()
            return self._stats

    def get_entries(self, cache_type: Optional[CacheType] = None) -> List[CacheEntry]:
        """
        Get all cache entries.

        Args:
            cache_type: Filter by cache type (None = all)

        Returns:
            List of cache entries
        """
        with self._lock:
            if cache_type is None:
                return list(self._cache.values())
            return [
                entry for entry in self._cache.values()
                if entry.cache_type == cache_type
            ]


class RepositoryCache:
    """Cache for repository metadata."""

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize repository cache.

        Args:
            cache_manager: Underlying cache manager
        """
        self.cache = cache_manager

    def get_metadata(self, repo_url: str, ref: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached repository metadata.

        Args:
            repo_url: Repository URL
            ref: Git reference (branch/tag/commit)

        Returns:
            Cached metadata or None
        """
        key = CacheKey.repository(repo_url, ref)
        return self.cache.get(key)

    def set_metadata(
        self,
        repo_url: str,
        metadata: Dict[str, Any],
        ref: Optional[str] = None,
        ttl: Optional[float] = None,
    ) -> bool:
        """
        Cache repository metadata.

        Args:
            repo_url: Repository URL
            metadata: Metadata to cache
            ref: Git reference
            ttl: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        key = CacheKey.repository(repo_url, ref)
        return self.cache.set(key, metadata, ttl, CacheType.REPOSITORY_METADATA)

    def invalidate_repository(self, repo_url: str) -> int:
        """
        Invalidate all cache entries for a repository.

        Args:
            repo_url: Repository URL

        Returns:
            Number of entries invalidated
        """
        # Hash the repo URL to match cache keys
        pattern = f"repo:{repo_url}:*"
        hashed_pattern = CacheKey._hash(pattern).replace("*", "*")
        return self.cache.invalidate_pattern(hashed_pattern)


class GitOperationCache:
    """Cache for git operation results."""

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize git operation cache.

        Args:
            cache_manager: Underlying cache manager
        """
        self.cache = cache_manager

    def get_operation(
        self,
        repo_url: str,
        operation: str,
        params: Optional[Dict] = None,
    ) -> Optional[Any]:
        """
        Get cached git operation result.

        Args:
            repo_url: Repository URL
            operation: Operation name (e.g., 'log', 'diff', 'blame')
            params: Operation parameters

        Returns:
            Cached result or None
        """
        key = CacheKey.git_operation(repo_url, operation, params)
        return self.cache.get(key)

    def set_operation(
        self,
        repo_url: str,
        operation: str,
        result: Any,
        params: Optional[Dict] = None,
        ttl: Optional[float] = None,
    ) -> bool:
        """
        Cache git operation result.

        Args:
            repo_url: Repository URL
            operation: Operation name
            result: Operation result
            params: Operation parameters
            ttl: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        key = CacheKey.git_operation(repo_url, operation, params)
        return self.cache.set(key, result, ttl, CacheType.GIT_OPERATION)

    def invalidate_repository(self, repo_url: str) -> int:
        """
        Invalidate all git operation cache entries for a repository.

        Args:
            repo_url: Repository URL

        Returns:
            Number of entries invalidated
        """
        pattern = f"git:{repo_url}:*"
        hashed_pattern = CacheKey._hash(pattern).replace("*", "*")
        return self.cache.invalidate_pattern(hashed_pattern)


class APIResponseCache:
    """Cache for API responses."""

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize API response cache.

        Args:
            cache_manager: Underlying cache manager
        """
        self.cache = cache_manager

    def get_response(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> Optional[Any]:
        """
        Get cached API response.

        Args:
            endpoint: API endpoint
            params: Request parameters

        Returns:
            Cached response or None
        """
        key = CacheKey.api_response(endpoint, params)
        return self.cache.get(key)

    def set_response(
        self,
        endpoint: str,
        response: Any,
        params: Optional[Dict] = None,
        ttl: Optional[float] = None,
    ) -> bool:
        """
        Cache API response.

        Args:
            endpoint: API endpoint
            response: API response
            params: Request parameters
            ttl: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        key = CacheKey.api_response(endpoint, params)
        return self.cache.set(key, response, ttl, CacheType.API_RESPONSE)


class AnalysisResultCache:
    """Cache for analysis results."""

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize analysis result cache.

        Args:
            cache_manager: Underlying cache manager
        """
        self.cache = cache_manager

    def get_result(
        self,
        repo_url: str,
        analysis_type: str,
        config: Optional[Dict] = None,
    ) -> Optional[Any]:
        """
        Get cached analysis result.

        Args:
            repo_url: Repository URL
            analysis_type: Type of analysis
            config: Analysis configuration

        Returns:
            Cached result or None
        """
        key = CacheKey.analysis_result(repo_url, analysis_type, config)
        return self.cache.get(key)

    def set_result(
        self,
        repo_url: str,
        analysis_type: str,
        result: Any,
        config: Optional[Dict] = None,
        ttl: Optional[float] = None,
    ) -> bool:
        """
        Cache analysis result.

        Args:
            repo_url: Repository URL
            analysis_type: Type of analysis
            result: Analysis result
            config: Analysis configuration
            ttl: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        key = CacheKey.analysis_result(repo_url, analysis_type, config)
        return self.cache.set(key, result, ttl, CacheType.ANALYSIS_RESULT)

    def invalidate_repository(self, repo_url: str) -> int:
        """
        Invalidate all analysis results for a repository.

        Args:
            repo_url: Repository URL

        Returns:
            Number of entries invalidated
        """
        pattern = f"analysis:{repo_url}:*"
        hashed_pattern = CacheKey._hash(pattern).replace("*", "*")
        return self.cache.invalidate_pattern(hashed_pattern)


def create_cache_manager(
    cache_dir: Union[str, Path] = ".report-cache",
    ttl: float = 3600,
    max_size_mb: float = 1000,
    auto_cleanup: bool = True,
) -> CacheManager:
    """
    Create a cache manager with default settings.

    Args:
        cache_dir: Directory for cache storage
        ttl: Default time-to-live in seconds
        max_size_mb: Maximum cache size in megabytes
        auto_cleanup: Automatically clean expired entries

    Returns:
        Configured cache manager
    """
    return CacheManager(
        cache_dir=cache_dir,
        ttl=ttl,
        max_size_mb=max_size_mb,
        auto_cleanup=auto_cleanup,
    )

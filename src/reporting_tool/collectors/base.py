# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Base collector interface for the reporting-tool package.

This module defines the abstract base class that all data collectors
must implement, providing a consistent interface for data collection
from various sources.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for data collectors.

    All collectors must implement the collect() method to gather
    data from their respective sources (Git repositories, APIs, etc.).
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the collector.

        Args:
            config: Configuration dictionary for the collector
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def collect(self, source: Path, **kwargs) -> Dict[str, Any]:
        """
        Collect data from the specified source.

        This is the main method that subclasses must implement to
        perform their specific data collection logic.

        Args:
            source: Path to the data source (e.g., repository directory)
            **kwargs: Additional collector-specific arguments

        Returns:
            Dictionary containing collected data

        Raises:
            CollectionError: If data collection fails
        """
        pass

    def validate_source(self, source: Path) -> bool:
        """
        Validate that the source exists and is accessible.

        Args:
            source: Path to validate

        Returns:
            True if source is valid, False otherwise
        """
        if not source.exists():
            self.logger.error(f"Source does not exist: {source}")
            return False

        if not source.is_dir():
            self.logger.error(f"Source is not a directory: {source}")
            return False

        return True

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value with a default fallback.

        Args:
            key: Configuration key (supports dot notation, e.g., 'api.github.enabled')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def is_enabled(self) -> bool:
        """
        Check if this collector is enabled in configuration.

        Returns:
            True if collector is enabled (default: True)
        """
        return bool(self.get_config_value('enabled', True))

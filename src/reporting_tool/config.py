# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Configuration management for the reporting-tool package.

This module handles:
- Loading YAML configuration files
- Merging template and project configurations
- Validating configuration values
- Computing configuration digests
- Setting up time windows
"""

from pathlib import Path
from typing import Any, Dict, Optional, List
import yaml
import json
import hashlib
import logging
from datetime import datetime, timedelta

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base dictionary
        override: Override dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Parsed configuration dictionary

    Raises:
        ConfigurationError: If file cannot be loaded or parsed
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config is None:
                return {}
            if not isinstance(config, dict):
                raise ConfigurationError(f"Configuration file must contain a YAML dictionary: {config_path}")
            return config
    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in configuration file {config_path}: {e}")
    except Exception as e:
        raise ConfigurationError(f"Error loading configuration file {config_path}: {e}")


def load_configuration(
    project: str,
    config_dir: Optional[Path] = None,
    template_config: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load and merge configuration files.

    Loads template configuration and project-specific configuration,
    then merges them with project config taking precedence.

    Args:
        project: Project name
        config_dir: Directory containing configuration files
        template_config: Template configuration file name (default: template.config)

    Returns:
        Merged configuration dictionary

    Raises:
        ConfigurationError: If configuration cannot be loaded
    """
    if config_dir is None:
        config_dir = Path("config")

    if template_config is None:
        template_config = "template.config"

    # Load template configuration
    template_path = config_dir / template_config
    if not template_path.exists():
        logger.warning(f"Template configuration not found: {template_path}")
        template = {}
    else:
        template = load_yaml_config(template_path)
        logger.debug(f"Loaded template configuration from {template_path}")

    # Load project configuration
    project_path = config_dir / f"{project}.yaml"
    if not project_path.exists():
        # Try .config extension for backward compatibility
        project_path = config_dir / f"{project}.config"

    if not project_path.exists():
        raise ConfigurationError(
            f"Project configuration not found: {config_dir}/{project}.yaml or {project}.config"
        )

    project_config = load_yaml_config(project_path)
    logger.debug(f"Loaded project configuration from {project_path}")

    # Merge configurations
    merged_config = deep_merge_dicts(template, project_config)

    # Ensure project name is set
    merged_config['project'] = project

    return merged_config


def compute_config_digest(config: Dict[str, Any]) -> str:
    """
    Compute SHA256 digest of configuration for caching purposes.

    Args:
        config: Configuration dictionary

    Returns:
        Hexadecimal digest string
    """
    config_json = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_json.encode()).hexdigest()


def setup_time_windows(config: Dict[str, Any]) -> Dict[str, datetime]:
    """
    Set up time windows from configuration.

    Converts time window configurations (e.g., "90d", "1y") into
    actual datetime objects for filtering.

    Args:
        config: Configuration dictionary with time_windows section

    Returns:
        Dictionary mapping window names to datetime cutoff points
    """
    time_windows = {}
    now = datetime.now()

    if 'time_windows' not in config:
        logger.warning("No time_windows defined in configuration, using defaults")
        return {
            '30d': now - timedelta(days=30),
            '90d': now - timedelta(days=90),
            '1y': now - timedelta(days=365),
        }

    for window_name, window_config in config['time_windows'].items():
        if 'days' in window_config:
            days = window_config['days']
            time_windows[window_name] = now - timedelta(days=days)
        else:
            logger.warning(f"Time window '{window_name}' missing 'days' field, skipping")

    return time_windows


def validate_loaded_config(config: Dict[str, Any]) -> None:
    """
    Validate loaded configuration has required fields.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigurationError: If required fields are missing or invalid
    """
    required_fields = ['project']

    for field in required_fields:
        if field not in config:
            raise ConfigurationError(f"Required configuration field missing: {field}")

    # Validate time windows if present
    if 'time_windows' in config:
        if not isinstance(config['time_windows'], dict):
            raise ConfigurationError("time_windows must be a dictionary")

        for window_name, window_config in config['time_windows'].items():
            if not isinstance(window_config, dict):
                raise ConfigurationError(f"Time window '{window_name}' must be a dictionary")
            if 'days' not in window_config:
                raise ConfigurationError(f"Time window '{window_name}' missing 'days' field")
            if not isinstance(window_config['days'], int) or window_config['days'] <= 0:
                raise ConfigurationError(
                    f"Time window '{window_name}' days must be a positive integer"
                )

    # Validate activity thresholds if present
    if 'activity_thresholds' in config:
        if not isinstance(config['activity_thresholds'], dict):
            raise ConfigurationError("activity_thresholds must be a dictionary")

    logger.debug("Configuration validation passed")


def save_resolved_config(config: Dict[str, Any], output_path: Path) -> None:
    """
    Save resolved/merged configuration to file.

    Args:
        config: Configuration dictionary to save
        output_path: Path where to save the configuration
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved resolved configuration to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save configuration to {output_path}: {e}")


def write_config_to_step_summary(config: Dict[str, Any]) -> None:
    """
    Write configuration to GitHub Actions step summary.

    This writes a formatted version of the configuration to the
    GITHUB_STEP_SUMMARY file for visibility in GitHub Actions.

    Args:
        config: Configuration dictionary to write
    """
    import os

    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if not step_summary:
        return

    try:
        with open(step_summary, 'a') as f:
            f.write("\n## 📋 Configuration\n\n")
            f.write("```yaml\n")
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            f.write("```\n")
    except Exception as e:
        logger.warning(f"Failed to write configuration to step summary: {e}")

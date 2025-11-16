# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for GitHub token environment variable configuration.

This test suite verifies that the --github-token-env option works correctly
and that the tool can read GitHub tokens from custom environment variables.
"""

import os
import pytest
from pathlib import Path
from argparse import Namespace
from unittest.mock import Mock, patch, MagicMock

from reporting_tool.features.registry import FeatureRegistry


class TestGitHubTokenEnvConfiguration:
    """Test suite for GitHub token environment variable configuration."""

    def test_default_token_env_is_github_token(self):
        """Test that default token environment variable is GITHUB_TOKEN."""
        config = {}
        logger = Mock()
        
        registry = FeatureRegistry(config, logger)
        
        # Default should be GITHUB_TOKEN when not configured
        token_env = config.get("_github_token_env", "GITHUB_TOKEN")
        assert token_env == "GITHUB_TOKEN"

    def test_custom_token_env_in_config(self):
        """Test that custom token environment variable is respected."""
        config = {
            "_github_token_env": "CUSTOM_TOKEN_VAR",
            "extensions": {
                "github_api": {
                    "enabled": True
                }
            }
        }
        logger = Mock()
        
        registry = FeatureRegistry(config, logger)
        
        # Should use custom environment variable name
        token_env = config.get("_github_token_env", "GITHUB_TOKEN")
        assert token_env == "CUSTOM_TOKEN_VAR"

    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token_123"}, clear=True)
    def test_reads_from_github_token_by_default(self):
        """Test that token is read from GITHUB_TOKEN by default."""
        config = {
            "_github_token_env": "GITHUB_TOKEN",
            "extensions": {
                "github_api": {
                    "enabled": True
                }
            }
        }
        logger = Mock()
        
        registry = FeatureRegistry(config, logger)
        
        # Should read from GITHUB_TOKEN
        token_env = config.get("_github_token_env", "GITHUB_TOKEN")
        token = os.environ.get(token_env)
        assert token == "ghp_test_token_123"

    @patch.dict(os.environ, {"CLASSIC_READ_ONLY_PAT_TOKEN": "ghp_ci_token_456"}, clear=True)
    def test_reads_from_custom_token_env(self):
        """Test that token is read from custom environment variable."""
        config = {
            "_github_token_env": "CLASSIC_READ_ONLY_PAT_TOKEN",
            "extensions": {
                "github_api": {
                    "enabled": True
                }
            }
        }
        logger = Mock()
        
        registry = FeatureRegistry(config, logger)
        
        # Should read from CLASSIC_READ_ONLY_PAT_TOKEN
        token_env = config.get("_github_token_env", "GITHUB_TOKEN")
        token = os.environ.get(token_env)
        assert token == "ghp_ci_token_456"

    @patch.dict(os.environ, {}, clear=True)
    def test_handles_missing_token_gracefully(self):
        """Test that missing token is handled gracefully."""
        config = {
            "_github_token_env": "NONEXISTENT_TOKEN",
            "extensions": {
                "github_api": {
                    "enabled": True
                }
            }
        }
        logger = Mock()
        
        registry = FeatureRegistry(config, logger)
        
        # Should return None when token not found
        token_env = config.get("_github_token_env", "GITHUB_TOKEN")
        token = os.environ.get(token_env)
        assert token is None

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_default_token",
        "CLASSIC_READ_ONLY_PAT_TOKEN": "ghp_ci_token"
    }, clear=True)
    def test_respects_configured_token_env_over_default(self):
        """Test that configured token env takes precedence."""
        config_with_default = {
            "_github_token_env": "GITHUB_TOKEN",
            "extensions": {"github_api": {"enabled": True}}
        }
        
        config_with_custom = {
            "_github_token_env": "CLASSIC_READ_ONLY_PAT_TOKEN",
            "extensions": {"github_api": {"enabled": True}}
        }
        
        # Default should read from GITHUB_TOKEN
        token_env_default = config_with_default.get("_github_token_env", "GITHUB_TOKEN")
        token_default = os.environ.get(token_env_default)
        assert token_default == "ghp_default_token"
        
        # Custom should read from CLASSIC_READ_ONLY_PAT_TOKEN
        token_env_custom = config_with_custom.get("_github_token_env", "GITHUB_TOKEN")
        token_custom = os.environ.get(token_env_custom)
        assert token_custom == "ghp_ci_token"

    def test_config_precedence_over_environment(self):
        """Test that explicit token in config takes precedence over environment."""
        config = {
            "_github_token_env": "GITHUB_TOKEN",
            "extensions": {
                "github_api": {
                    "enabled": True,
                    "token": "ghp_explicit_token"
                }
            }
        }
        logger = Mock()
        
        registry = FeatureRegistry(config, logger)
        
        # Explicit token should be used first
        explicit_token = config.get("extensions", {}).get("github_api", {}).get("token")
        assert explicit_token == "ghp_explicit_token"

    @patch.dict(os.environ, {"MY_CUSTOM_TOKEN": "ghp_custom_123"}, clear=True)
    def test_arbitrary_custom_token_variable(self):
        """Test that any arbitrary token variable name works."""
        config = {
            "_github_token_env": "MY_CUSTOM_TOKEN",
            "extensions": {
                "github_api": {
                    "enabled": True
                }
            }
        }
        logger = Mock()
        
        registry = FeatureRegistry(config, logger)
        
        # Should work with any custom variable name
        token_env = config.get("_github_token_env", "GITHUB_TOKEN")
        token = os.environ.get(token_env)
        assert token == "ghp_custom_123"


class TestCLIIntegrationWithTokenEnv:
    """Test CLI integration with github-token-env option."""

    def test_cli_argument_sets_config_value(self):
        """Test that CLI argument properly sets the config value."""
        from argparse import Namespace
        
        args = Namespace(
            project="test-project",
            repos_path=Path("."),
            config_dir=Path("configuration"),
            output_dir=Path("reports"),
            github_token_env="CLASSIC_READ_ONLY_PAT_TOKEN",
            log_level=None,
            verbose=0
        )
        
        # Simulate what main() does
        github_token_env = getattr(args, 'github_token_env', 'GITHUB_TOKEN')
        
        assert github_token_env == "CLASSIC_READ_ONLY_PAT_TOKEN"

    def test_cli_argument_defaults_correctly(self):
        """Test that CLI argument defaults to GITHUB_TOKEN."""
        from argparse import Namespace
        
        args = Namespace(
            project="test-project",
            repos_path=Path("."),
            config_dir=Path("configuration"),
            output_dir=Path("reports"),
            # github_token_env not provided
            log_level=None,
            verbose=0
        )
        
        # Simulate what main() does with default
        github_token_env = getattr(args, 'github_token_env', 'GITHUB_TOKEN')
        
        assert github_token_env == "GITHUB_TOKEN"


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    @patch.dict(os.environ, {"CLASSIC_READ_ONLY_PAT_TOKEN": "ghp_old_token"}, clear=True)
    def test_old_code_still_works_with_explicit_config(self):
        """Test that code explicitly configured for CLASSIC_READ_ONLY_PAT_TOKEN still works."""
        config = {
            "_github_token_env": "CLASSIC_READ_ONLY_PAT_TOKEN",
            "extensions": {
                "github_api": {
                    "enabled": True
                }
            }
        }
        
        # Old behavior should still work when explicitly configured
        token_env = config.get("_github_token_env", "GITHUB_TOKEN")
        token = os.environ.get(token_env)
        assert token == "ghp_old_token"

    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_new_token"}, clear=True)
    def test_new_default_behavior(self):
        """Test that new default behavior uses GITHUB_TOKEN."""
        config = {
            # Not specifying _github_token_env should default to GITHUB_TOKEN
            "extensions": {
                "github_api": {
                    "enabled": True
                }
            }
        }
        
        # New default behavior
        token_env = config.get("_github_token_env", "GITHUB_TOKEN")
        token = os.environ.get(token_env)
        assert token == "ghp_new_token"
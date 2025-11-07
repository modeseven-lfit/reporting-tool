# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Dry Run Validation Module

Comprehensive pre-flight checks for validating configuration and system state
before executing repository analysis.

Phase 9: CLI & UX Improvements
"""

import logging
import os
import shutil
import socket
from pathlib import Path
from typing import Optional, Tuple
import urllib.request
import urllib.error

from .errors import (
    ConfigurationError,
    APIError,
    PermissionError,
    DiskSpaceError,
    NetworkError,
    ValidationError,
)


class ValidationResult:
    """
    Result of a validation check.

    Attributes:
        passed: Whether the validation passed
        message: Description of the result
        suggestion: Optional suggestion for fixing failures
        severity: 'error', 'warning', or 'info'
    """

    def __init__(
        self,
        passed: bool,
        message: str,
        suggestion: Optional[str] = None,
        severity: str = 'error'
    ):
        """Initialize validation result."""
        self.passed = passed
        self.message = message
        self.suggestion = suggestion
        self.severity = severity

    def __repr__(self) -> str:
        """String representation."""
        status = "✓" if self.passed else "✗"
        return f"{status} {self.message}"


class DryRunValidator:
    """
    Comprehensive validation for dry run mode.

    Performs pre-flight checks including:
    - Configuration schema and semantic validation
    - API connectivity and credentials
    - Filesystem permissions and disk space
    - Required tools and dependencies

    Example:
        >>> validator = DryRunValidator(config, logger)
        >>> success, results = validator.validate_all()
        >>> if not success:
        ...     validator.print_results(results)
    """

    def __init__(self, config: dict, logger: Optional[logging.Logger] = None):
        """
        Initialize validator.

        Args:
            config: Configuration dictionary
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def validate_all(self, skip_network: bool = False) -> Tuple[bool, list[ValidationResult]]:
        """
        Run all validation checks.

        Args:
            skip_network: Skip network connectivity checks

        Returns:
            Tuple of (success: bool, results: list[ValidationResult])
        """
        results = []

        # Configuration validation
        results.append(self._validate_config_structure())
        results.append(self._validate_required_fields())
        results.append(self._validate_project_name())
        results.append(self._validate_repos_path())

        # API validation
        results.append(self._validate_api_credentials())

        if not skip_network:
            results.append(self._validate_network_connectivity())
            results.append(self._validate_api_endpoints())

        # Filesystem validation
        results.append(self._validate_output_directory())
        results.append(self._validate_disk_space())
        results.append(self._validate_cache_directory())

        # System validation
        results.append(self._validate_git_available())
        results.append(self._validate_python_version())

        # Determine overall success
        has_errors = any(not r.passed and r.severity == 'error' for r in results)
        success = not has_errors

        return success, results

    def _validate_config_structure(self) -> ValidationResult:
        """Validate configuration has required structure."""
        try:
            required_sections = ['project', 'paths', 'output']
            missing = [s for s in required_sections if s not in self.config]

            if missing:
                return ValidationResult(
                    False,
                    f"Configuration missing sections: {', '.join(missing)}",
                    "Check config.yaml against config.example.yaml"
                )

            return ValidationResult(True, "Configuration structure valid")

        except Exception as e:
            return ValidationResult(
                False,
                f"Configuration structure validation failed: {e}",
                "Ensure config.yaml is valid YAML"
            )

    def _validate_required_fields(self) -> ValidationResult:
        """Validate required configuration fields are present."""
        required_fields = {
            'project.name': lambda c: c.get('project', {}).get('name'),
            'paths.repos': lambda c: c.get('paths', {}).get('repos'),
            'output.dir': lambda c: c.get('output', {}).get('dir'),
        }

        missing = []
        for field_path, getter in required_fields.items():
            if not getter(self.config):
                missing.append(field_path)

        if missing:
            return ValidationResult(
                False,
                f"Required fields missing: {', '.join(missing)}",
                "Add missing fields to config.yaml"
            )

        return ValidationResult(True, "All required fields present")

    def _validate_project_name(self) -> ValidationResult:
        """Validate project name is valid."""
        project_name = self.config.get('project', {}).get('name', '')

        if not project_name:
            return ValidationResult(
                False,
                "Project name is empty",
                "Set project.name in config.yaml or use --project argument"
            )

        if len(project_name) > 100:
            return ValidationResult(
                False,
                f"Project name too long ({len(project_name)} chars, max 100)",
                "Use a shorter project name"
            )

        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        found_invalid = [c for c in invalid_chars if c in project_name]

        if found_invalid:
            return ValidationResult(
                False,
                f"Project name contains invalid characters: {', '.join(found_invalid)}",
                "Use only alphanumeric, dash, and underscore characters"
            )

        return ValidationResult(True, f"Project name valid: '{project_name}'")

    def _validate_repos_path(self) -> ValidationResult:
        """Validate repositories path exists and is accessible."""
        repos_path = self.config.get('paths', {}).get('repos')

        if not repos_path:
            return ValidationResult(
                False,
                "Repositories path not configured",
                "Set paths.repos in config.yaml or use --repos-path argument"
            )

        path = Path(repos_path)

        if not path.exists():
            return ValidationResult(
                False,
                f"Repositories path does not exist: {repos_path}",
                "Create directory or specify correct path"
            )

        if not path.is_dir():
            return ValidationResult(
                False,
                f"Repositories path is not a directory: {repos_path}",
                "Specify a directory containing repositories"
            )

        # Check if readable
        if not os.access(path, os.R_OK):
            return ValidationResult(
                False,
                f"Cannot read repositories directory: {repos_path}",
                "Check directory permissions",
                severity='error'
            )

        # Count repositories (directories with .git)
        try:
            repos = [d for d in path.iterdir() if d.is_dir() and (d / '.git').exists()]
            repo_count = len(repos)

            if repo_count == 0:
                return ValidationResult(
                    True,
                    f"No repositories found in {repos_path}",
                    "Ensure repositories are cloned to this directory",
                    severity='warning'
                )

            return ValidationResult(
                True,
                f"Found {repo_count} repositories in {repos_path}"
            )

        except PermissionError:
            return ValidationResult(
                False,
                f"Cannot list repositories directory: {repos_path}",
                "Check directory permissions"
            )

    def _validate_api_credentials(self) -> ValidationResult:
        """Validate API credentials are configured."""
        api_config = self.config.get('api', {})

        # Check GitHub token
        github_token = api_config.get('github', {}).get('token')
        gerrit_auth = api_config.get('gerrit', {}).get('auth')

        warnings = []

        if not github_token:
            warnings.append("GitHub token not configured")
        elif github_token.startswith('ghp_') and len(github_token) < 40:
            warnings.append("GitHub token appears invalid (too short)")

        if not gerrit_auth:
            warnings.append("Gerrit auth not configured")

        if warnings:
            return ValidationResult(
                True,
                "API credentials: " + ", ".join(warnings),
                "Configure tokens in config.yaml or environment variables",
                severity='warning'
            )

        return ValidationResult(True, "API credentials configured")

    def _validate_network_connectivity(self) -> ValidationResult:
        """Validate network connectivity."""
        try:
            # Try to resolve a well-known host
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return ValidationResult(True, "Network connectivity available")

        except (socket.timeout, socket.error):
            return ValidationResult(
                True,
                "Network connectivity check failed",
                "Check network connection or use --skip-network-checks",
                severity='warning'
            )

    def _validate_api_endpoints(self) -> ValidationResult:
        """Validate API endpoints are reachable."""
        api_config = self.config.get('api', {})
        endpoints = []

        # GitHub API
        github_url = api_config.get('github', {}).get('url', 'https://api.github.com')
        if github_url:
            endpoints.append(('GitHub', github_url))

        # Gerrit API
        gerrit_url = api_config.get('gerrit', {}).get('url')
        if gerrit_url:
            endpoints.append(('Gerrit', gerrit_url))

        unreachable = []

        for name, url in endpoints:
            try:
                # Simple connectivity check (HEAD request)
                req = urllib.request.Request(url, method='HEAD')
                urllib.request.urlopen(req, timeout=5)
            except (urllib.error.URLError, urllib.error.HTTPError, Exception):
                unreachable.append(name)

        if unreachable:
            return ValidationResult(
                True,
                f"API endpoints unreachable: {', '.join(unreachable)}",
                "Check network, VPN, or API URLs in configuration",
                severity='warning'
            )

        return ValidationResult(True, f"All {len(endpoints)} API endpoints reachable")

    def _validate_output_directory(self) -> ValidationResult:
        """Validate output directory is writable."""
        output_dir = self.config.get('output', {}).get('dir', 'output')
        path = Path(output_dir)

        # Create if doesn't exist
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            return ValidationResult(
                False,
                f"Cannot create output directory: {output_dir}",
                "Check parent directory permissions or choose different path"
            )

        # Check writable
        if not os.access(path, os.W_OK):
            return ValidationResult(
                False,
                f"Output directory not writable: {output_dir}",
                "Check directory permissions"
            )

        return ValidationResult(True, f"Output directory writable: {output_dir}")

    def _validate_disk_space(self) -> ValidationResult:
        """Validate sufficient disk space available."""
        output_dir = self.config.get('output', {}).get('dir', 'output')
        path = Path(output_dir)

        try:
            # Ensure directory exists
            path.mkdir(parents=True, exist_ok=True)

            # Check disk space
            stat = shutil.disk_usage(path)
            free_gb = stat.free / (1024 ** 3)

            # Warn if less than 1GB
            if free_gb < 1.0:
                return ValidationResult(
                    True,
                    f"Low disk space: {free_gb:.2f} GB available",
                    "Free up disk space or use different output directory",
                    severity='warning'
                )

            return ValidationResult(
                True,
                f"Disk space available: {free_gb:.2f} GB"
            )

        except Exception as e:
            return ValidationResult(
                True,
                f"Could not check disk space: {e}",
                severity='warning'
            )

    def _validate_cache_directory(self) -> ValidationResult:
        """Validate cache directory if caching is enabled."""
        if not self.config.get('cache', {}).get('enabled', False):
            return ValidationResult(True, "Caching disabled (skipped)", severity='info')

        cache_dir = self.config.get('cache', {}).get('dir', '.cache/repo-metrics')
        path = Path(cache_dir)

        try:
            path.mkdir(parents=True, exist_ok=True)

            if not os.access(path, os.W_OK):
                return ValidationResult(
                    True,
                    f"Cache directory not writable: {cache_dir}",
                    "Check permissions or disable caching with --no-cache",
                    severity='warning'
                )

            return ValidationResult(True, f"Cache directory writable: {cache_dir}")

        except PermissionError:
            return ValidationResult(
                True,
                f"Cannot create cache directory: {cache_dir}",
                "Disable caching or choose different cache directory",
                severity='warning'
            )

    def _validate_git_available(self) -> ValidationResult:
        """Validate git command is available."""
        if shutil.which('git') is None:
            return ValidationResult(
                False,
                "Git command not found in PATH",
                "Install git or ensure it's in your PATH"
            )

        return ValidationResult(True, "Git command available")

    def _validate_python_version(self) -> ValidationResult:
        """Validate Python version meets requirements."""
        import sys

        major, minor = sys.version_info[:2]
        version_str = f"{major}.{minor}"

        # Require Python 3.8+
        if major < 3 or (major == 3 and minor < 8):
            return ValidationResult(
                False,
                f"Python {version_str} is too old (requires 3.8+)",
                "Upgrade to Python 3.8 or newer"
            )

        return ValidationResult(True, f"Python version: {version_str}")

    def print_results(self, results: list[ValidationResult]) -> None:
        """
        Print validation results in formatted output.

        Args:
            results: List of validation results
        """
        print("\n" + "=" * 70)
        print("🔍 DRY RUN VALIDATION RESULTS")
        print("=" * 70 + "\n")

        # Group by severity
        errors = [r for r in results if not r.passed and r.severity == 'error']
        warnings = [r for r in results if r.severity == 'warning']
        successes = [r for r in results if r.passed and r.severity != 'warning']
        info = [r for r in results if r.severity == 'info']

        # Print errors
        if errors:
            print("❌ ERRORS:")
            for result in errors:
                print(f"  {result}")
                if result.suggestion:
                    print(f"     💡 {result.suggestion}")
            print()

        # Print warnings
        if warnings:
            print("⚠️  WARNINGS:")
            for result in warnings:
                print(f"  {result}")
                if result.suggestion:
                    print(f"     💡 {result.suggestion}")
            print()

        # Print successes
        if successes:
            print("✅ PASSED:")
            for result in successes:
                print(f"  {result}")
            print()

        # Print info
        if info:
            for result in info:
                print(f"ℹ️  {result}")

        # Summary
        print("-" * 70)
        total = len(results)
        passed = len([r for r in results if r.passed])
        failed = len(errors)
        warned = len(warnings)

        print(f"Total checks: {total}")
        print(f"Passed: {passed}")
        if failed:
            print(f"Failed: {failed}")
        if warned:
            print(f"Warnings: {warned}")

        print("=" * 70)

        if errors:
            print("\n❌ Validation FAILED - fix errors before running")
        elif warnings:
            print("\n⚠️  Validation passed with WARNINGS - review before running")
        else:
            print("\n✅ All validations PASSED - ready to run!")

        print()


def dry_run(config: dict, logger: Optional[logging.Logger] = None, skip_network: bool = False) -> int:
    """
    Execute dry run validation.

    Validates configuration and system state without executing analysis.

    Args:
        config: Configuration dictionary
        logger: Optional logger instance
        skip_network: Skip network connectivity checks

    Returns:
        Exit code (0 for success, 1 for failure)

    Example:
        >>> config = load_config('config.yaml')
        >>> exit_code = dry_run(config)
        >>> sys.exit(exit_code)
    """
    validator = DryRunValidator(config, logger)
    success, results = validator.validate_all(skip_network=skip_network)
    validator.print_results(results)

    return 0 if success else 1


__all__ = [
    'ValidationResult',
    'DryRunValidator',
    'dry_run',
]

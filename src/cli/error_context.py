# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Error Context System

Provides rich contextual information for errors including:
- Recovery hints with step-by-step instructions
- Code examples for common fixes
- Related documentation links
- Auto-detection of common issues

Phase 13, Step 4: Enhanced Error Messages
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import os
import sys


class ErrorContext:
    """
    Rich error context with recovery information.

    Attributes:
        error_type: Type of error that occurred
        message: Error message
        context: Additional context information
        recovery_hints: Step-by-step recovery instructions
        examples: Code examples for fixing the issue
        related_errors: Related common errors
        doc_links: Relevant documentation links
    """

    def __init__(
        self,
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        recovery_hints: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
        related_errors: Optional[List[str]] = None,
        doc_links: Optional[List[str]] = None
    ):
        """Initialize error context."""
        self.error_type = error_type
        self.message = message
        self.context = context or {}
        self.recovery_hints = recovery_hints or []
        self.examples = examples or []
        self.related_errors = related_errors or []
        self.doc_links = doc_links or []

    def format(self, verbose: bool = False) -> str:
        """
        Format error context for display.

        Args:
            verbose: Include all details

        Returns:
            Formatted error message
        """
        lines = []

        # Error header
        lines.append(f"❌ {self.error_type}: {self.message}")
        lines.append("")

        # Context information
        if self.context:
            lines.append("📋 Context:")
            for key, value in self.context.items():
                lines.append(f"  • {key}: {value}")
            lines.append("")

        # Recovery hints
        if self.recovery_hints:
            lines.append("🔧 How to fix:")
            for i, hint in enumerate(self.recovery_hints, 1):
                lines.append(f"  {i}. {hint}")
            lines.append("")

        # Examples
        if self.examples and verbose:
            lines.append("💡 Examples:")
            for example in self.examples:
                lines.append(f"  {example}")
            lines.append("")

        # Related errors
        if self.related_errors and verbose:
            lines.append("🔗 Related issues:")
            for error in self.related_errors:
                lines.append(f"  • {error}")
            lines.append("")

        # Documentation links
        if self.doc_links:
            lines.append("📖 Documentation:")
            for link in self.doc_links:
                lines.append(f"  • {link}")
            lines.append("")

        return "\n".join(lines)


def detect_missing_config() -> ErrorContext:
    """Create context for missing configuration file."""
    return ErrorContext(
        error_type="Configuration Error",
        message="Configuration file not found",
        context={
            "expected_location": "config/template.yaml",
            "current_directory": os.getcwd()
        },
        recovery_hints=[
            "Copy config.example.yaml to config.yaml",
            "Edit config.yaml with your project settings",
            "Or specify a custom config with --config-dir /path/to/config"
        ],
        examples=[
            "cp config.example.yaml config.yaml",
            "python generate_reports.py --config-dir /custom/path"
        ],
        doc_links=[
            "docs/configuration.md",
            "docs/quick-start.md#configuration"
        ]
    )


def detect_invalid_yaml(file_path: Path, line: Optional[int] = None) -> ErrorContext:
    """
    Create context for invalid YAML syntax.

    Args:
        file_path: Path to YAML file
        line: Line number with error (if available)
    """
    context: dict[str, Any] = {
        "file": str(file_path),
        "common_causes": "indentation, tabs, special characters"
    }

    if line:
        context["line"] = line

    return ErrorContext(
        error_type="YAML Syntax Error",
        message=f"Invalid YAML syntax in {file_path}",
        context=context,
        recovery_hints=[
            "Check indentation - use spaces, not tabs",
            "Ensure colons have spaces after them (key: value)",
            "Quote strings with special characters",
            "Validate YAML online at yamllint.com"
        ],
        examples=[
            "✓ Correct:   project: my-project",
            "✗ Wrong:     project:my-project (missing space)",
            "✓ Correct:   name: 'project: name'",
            "✗ Wrong:     name: project: name (unquoted colon)"
        ],
        related_errors=[
            "ConfigurationError: missing required field",
            "ParserError: invalid character"
        ],
        doc_links=[
            "docs/configuration.md#yaml-syntax",
            "https://yaml.org/spec/1.2/spec.html"
        ]
    )


def detect_missing_repos_path(path: Path) -> ErrorContext:
    """Create context for missing repositories directory."""
    return ErrorContext(
        error_type="Invalid Argument",
        message=f"Repositories path does not exist: {path}",
        context={
            "provided_path": str(path),
            "absolute_path": str(path.absolute()),
            "current_directory": os.getcwd()
        },
        recovery_hints=[
            "Verify the path is correct",
            "Clone repositories to the specified location",
            "Or provide the correct path with --repos-path",
            "Check for typos in the path"
        ],
        examples=[
            "# Clone repositories first:",
            "mkdir -p ~/repos",
            "cd ~/repos && git clone https://github.com/org/repo.git",
            "",
            "# Then run with correct path:",
            "python generate_reports.py --project myproject --repos-path ~/repos"
        ],
        doc_links=[
            "docs/quick-start.md#cloning-repositories"
        ]
    )


def detect_github_auth_error(status_code: Optional[int] = None) -> ErrorContext:
    """
    Create context for GitHub authentication errors.

    Args:
        status_code: HTTP status code (401, 403, etc.)
    """
    context: dict[str, Any] = {"api": "GitHub"}
    if status_code:
        context["status_code"] = status_code

    if status_code == 401:
        message = "GitHub API authentication failed - invalid token"
        hints = [
            "Verify GITHUB_TOKEN environment variable is set",
            "Check that the token hasn't expired",
            "Generate a new personal access token at github.com/settings/tokens",
            "Ensure token has required scopes: repo, read:org"
        ]
    elif status_code == 403:
        message = "GitHub API access forbidden - insufficient permissions"
        hints = [
            "Check that your token has the required scopes",
            "For organization repos, ensure token has read:org scope",
            "For private repos, ensure token has repo scope",
            "Verify you have access to the repository/organization"
        ]
    else:
        message = "GitHub API authentication error"
        hints = [
            "Set GITHUB_TOKEN environment variable",
            "Generate a personal access token at github.com/settings/tokens",
            "Required scopes: repo, read:org",
            "Add to environment: export GITHUB_TOKEN=ghp_..."
        ]

    return ErrorContext(
        error_type="API Authentication Error",
        message=message,
        context=context,
        recovery_hints=hints,
        examples=[
            "# Generate token at: https://github.com/settings/tokens/new",
            "# Required scopes: repo, read:org",
            "",
            "# Set in environment:",
            "export GITHUB_TOKEN=ghp_your_token_here",
            "",
            "# Or in config.yaml:",
            "api:",
            "  github:",
            "    token: ${GITHUB_TOKEN}  # Reads from environment"
        ],
        related_errors=[
            "403 Forbidden - insufficient permissions",
            "404 Not Found - repository not accessible"
        ],
        doc_links=[
            "docs/github-token-setup.md",
            "GITHUB_TOKEN_REQUIREMENTS.md"
        ]
    )


def detect_rate_limit_error(api_name: str, reset_time: Optional[int] = None) -> ErrorContext:
    """
    Create context for API rate limit errors.

    Args:
        api_name: Name of API (GitHub, Gerrit, etc.)
        reset_time: Unix timestamp when rate limit resets
    """
    context = {"api": api_name}
    if reset_time:
        from datetime import datetime
        reset_dt = datetime.fromtimestamp(reset_time)
        context["rate_limit_reset"] = reset_dt.strftime("%Y-%m-%d %H:%M:%S")

    return ErrorContext(
        error_type="API Rate Limit",
        message=f"{api_name} API rate limit exceeded",
        context=context,
        recovery_hints=[
            f"Wait for {api_name} rate limit to reset" + (f" (at {context.get('rate_limit_reset')})" if reset_time else ""),
            "Use a different API token if available",
            "Reduce the number of API calls with caching",
            "Use --workers 1 to slow down parallel requests"
        ],
        examples=[
            "# Wait and retry:",
            "python generate_reports.py --project myproject ...",
            "",
            "# Or use caching to reduce API calls:",
            "python generate_reports.py --cache --project myproject ...",
            "",
            "# For GitHub, authenticated requests get higher limits:",
            "export GITHUB_TOKEN=ghp_your_token"
        ],
        related_errors=[
            "429 Too Many Requests",
            "403 Rate limit exceeded"
        ],
        doc_links=[
            f"docs/api-limits.md#{api_name.lower()}",
            "docs/troubleshooting.md#rate-limits"
        ]
    )


def detect_network_error(url: Optional[str] = None, error_type: Optional[str] = None) -> ErrorContext:
    """
    Create context for network connectivity errors.

    Args:
        url: URL that failed
        error_type: Type of network error (timeout, connection, dns, etc.)
    """
    context = {}
    if url:
        context["url"] = url
    if error_type:
        context["error_type"] = error_type

    hints = ["Check your internet connection"]
    examples = []

    if error_type == "timeout":
        hints.extend([
            "Increase timeout with --timeout 300",
            "Check if the server is responding",
            "Verify firewall is not blocking connections"
        ])
        examples.append("python generate_reports.py --timeout 300 ...")
    elif error_type == "dns":
        hints.extend([
            "Verify the hostname is correct",
            "Check DNS resolution: ping api.github.com",
            "Try using a different DNS server"
        ])
        examples.extend([
            "# Test DNS resolution:",
            "ping api.github.com",
            "nslookup api.github.com"
        ])
    elif error_type == "ssl":
        hints.extend([
            "Verify SSL certificates are installed",
            "Update CA certificates",
            "If using corporate proxy, check SSL inspection settings"
        ])
        examples.extend([
            "# Update certificates (Ubuntu/Debian):",
            "sudo apt-get update && sudo apt-get install --reinstall ca-certificates"
        ])
    else:
        hints.extend([
            "Verify you can reach the server",
            "Check proxy settings if behind a corporate firewall",
            "Test connectivity: curl -I https://api.github.com"
        ])
        examples.append("curl -I https://api.github.com")

    # Build message with error type
    msg_parts = []
    if error_type:
        msg_parts.append(f"{error_type.title()}")
    msg_parts.append("network connectivity error" if not error_type else "error")
    if url:
        msg_parts.append(f"for {url}")

    message = " ".join(msg_parts) if msg_parts else "Network connectivity error"

    return ErrorContext(
        error_type="Network Error",
        message=message,
        context=context,
        recovery_hints=hints,
        examples=examples,
        doc_links=[
            "docs/troubleshooting.md#network-issues",
            "docs/proxy-configuration.md"
        ]
    )


def detect_permission_error(path: Path, operation: str = "access") -> ErrorContext:
    """
    Create context for file permission errors.

    Args:
        path: Path that couldn't be accessed
        operation: Operation that failed (read, write, execute)
    """
    stat_info = None
    try:
        stat_info = path.stat()
    except:
        pass

    context = {
        "path": str(path),
        "operation": operation,
        "current_user": os.getenv("USER", "unknown")
    }

    if stat_info:
        import stat as stat_module
        mode = stat_module.filemode(stat_info.st_mode)
        context["permissions"] = mode

    return ErrorContext(
        error_type="Permission Error",
        message=f"Permission denied: cannot {operation} {path}",
        context=context,
        recovery_hints=[
            f"Check file permissions for {path}",
            "Ensure your user has the necessary permissions",
            "Try running with appropriate privileges if needed",
            "Or choose a different output directory you can write to"
        ],
        examples=[
            f"# Check permissions:",
            f"ls -la {path}",
            "",
            "# Fix permissions (if you own the file):",
            f"chmod u+rw {path}",
            "",
            "# Or use a different output directory:",
            "python generate_reports.py --output-dir ~/my-reports ..."
        ],
        doc_links=[
            "docs/troubleshooting.md#permission-errors"
        ]
    )


def detect_disk_space_error(path: Path) -> ErrorContext:
    """Create context for disk space errors."""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024**3)
        context = {
            "path": str(path),
            "free_space": f"{free_gb:.2f} GB"
        }
    except:
        context = {"path": str(path)}

    return ErrorContext(
        error_type="Disk Space Error",
        message=f"Insufficient disk space at {path}",
        context=context,
        recovery_hints=[
            "Free up disk space",
            "Use a different output directory with more space",
            "Use --no-cache to reduce disk usage",
            "Use --output-format json to skip HTML generation"
        ],
        examples=[
            "# Check disk space:",
            "df -h",
            "",
            "# Use different output directory:",
            "python generate_reports.py --output-dir /mnt/data/reports ...",
            "",
            "# Reduce disk usage:",
            "python generate_reports.py --no-cache --output-format json ..."
        ],
        doc_links=[
            "docs/troubleshooting.md#disk-space"
        ]
    )


def detect_validation_error(
    field: str,
    value: Any,
    expected: str,
    config_path: Optional[Path] = None
) -> ErrorContext:
    """
    Create context for validation errors.

    Args:
        field: Field that failed validation
        value: Invalid value
        expected: Expected value format
        config_path: Path to config file
    """
    context = {
        "field": field,
        "provided_value": str(value),
        "expected_format": expected
    }

    if config_path:
        context["config_file"] = str(config_path)

    return ErrorContext(
        error_type="Validation Error",
        message=f"Invalid value for '{field}'",
        context=context,
        recovery_hints=[
            f"Update the '{field}' field in your configuration",
            f"Expected format: {expected}",
            "Check config.example.yaml for valid examples",
            "Validate your config with: --dry-run"
        ],
        examples=[
            f"# In config.yaml:",
            f"{field}: <valid_value>  # {expected}",
            "",
            "# Validate before running:",
            "python generate_reports.py --dry-run ..."
        ],
        doc_links=[
            "docs/configuration.md#validation",
            "docs/configuration.md#schema"
        ]
    )


def auto_detect_error_context(error: Exception, **kwargs) -> ErrorContext:
    """
    Automatically detect error context based on exception.

    Args:
        error: The exception that was raised
        **kwargs: Additional context (path, api_name, etc.)

    Returns:
        ErrorContext with appropriate recovery information
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # File not found errors
    if isinstance(error, FileNotFoundError) or "not found" in error_str:
        if "config" in error_str:
            return detect_missing_config()
        elif "path" in kwargs:
            return detect_missing_repos_path(Path(kwargs["path"]))

    # YAML errors
    if "yaml" in error_type.lower() or "yaml" in error_str:
        path = kwargs.get("path", Path("config.yaml"))
        line = kwargs.get("line")
        return detect_invalid_yaml(Path(path), line)

    # Permission errors
    if isinstance(error, PermissionError) or "permission" in error_str:
        path = kwargs.get("path", Path("."))
        operation = kwargs.get("operation", "access")
        return detect_permission_error(Path(path), operation)

    # Network errors
    if "network" in error_str or "connection" in error_str or "timeout" in error_str:
        url = kwargs.get("url")
        net_error_type = None
        if "timeout" in error_str:
            net_error_type = "timeout"
        elif "dns" in error_str or "resolve" in error_str:
            net_error_type = "dns"
        elif "ssl" in error_str or "certificate" in error_str:
            net_error_type = "ssl"

        ctx = detect_network_error(url, net_error_type)
        # Preserve original error message if it has more detail
        if len(str(error)) > len(ctx.message):
            ctx.message = str(error)
        return ctx

    # API errors
    if "401" in error_str or "unauthorized" in error_str:
        return detect_github_auth_error(401)
    elif "403" in error_str:
        if "rate limit" in error_str:
            api_name = kwargs.get("api_name", "GitHub")
            reset_time = kwargs.get("reset_time")
            return detect_rate_limit_error(api_name, reset_time)
        else:
            return detect_github_auth_error(403)

    # Disk space errors
    if "disk" in error_str or "space" in error_str or isinstance(error, OSError):
        path = kwargs.get("path", Path("."))
        return detect_disk_space_error(Path(path))

    # Generic fallback
    return ErrorContext(
        error_type=error_type,
        message=str(error),
        context=kwargs,
        recovery_hints=[
            "Check the error message for details",
            "Run with --verbose for more information",
            "Consult documentation for troubleshooting"
        ],
        doc_links=["docs/troubleshooting.md"]
    )


__all__ = [
    "ErrorContext",
    "detect_missing_config",
    "detect_invalid_yaml",
    "detect_missing_repos_path",
    "detect_github_auth_error",
    "detect_rate_limit_error",
    "detect_network_error",
    "detect_permission_error",
    "detect_disk_space_error",
    "detect_validation_error",
    "auto_detect_error_context",
]

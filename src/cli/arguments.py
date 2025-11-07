# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Enhanced Argument Parser

Provides improved command-line argument parsing with:
- Better help text and examples
- New features (--list-features, --dry-run, --output-format)
- Verbose/quiet modes
- Validation and error handling

Phase 9: CLI & UX Improvements
"""

import argparse
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from .exit_codes import ExitCode
from .errors import InvalidArgumentError


class OutputFormat(Enum):
    """Supported output formats."""
    JSON = 'json'
    MARKDOWN = 'md'
    HTML = 'html'
    ALL = 'all'

    def __str__(self):
        return self.value


class VerbosityLevel(Enum):
    """Verbosity levels for logging."""
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3
    TRACE = 4


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create enhanced argument parser with improved help text.

    Returns:
        Configured ArgumentParser instance

    Example:
        >>> parser = create_argument_parser()
        >>> args = parser.parse_args(['--project', 'test', '--repos-path', '.'])
    """
    parser = argparse.ArgumentParser(
        prog='generate_reports.py',
        description='''
Repository Analysis Report Generator

Generate comprehensive analysis reports for repository collections including:
- Commit activity and contributor statistics
- CI/CD workflow status (Jenkins, GitHub Actions)
- Feature detection (Dependabot, pre-commit, ReadTheDocs, etc.)
- Organization and contributor rankings
- Inactive repository identification
        '''.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage
  %(prog)s --project my-project --repos-path /path/to/repos

  # With custom configuration
  %(prog)s --project my-project --repos-path ./repos --config-dir ./config

  # Validate configuration without running
  %(prog)s --project my-project --repos-path ./repos --dry-run

  # List all available feature checks
  %(prog)s --list-features

  # Generate only HTML report with verbose output
  %(prog)s --project my-project --repos-path ./repos --output-format html -vv

  # Show resolved configuration
  %(prog)s --project my-project --repos-path ./repos --show-config

Exit Codes:
  0 - Success (no errors or warnings)
  1 - Error (configuration, API, or processing failure)
  2 - Partial success (warnings or incomplete data)
  3 - Invalid arguments or usage
  4 - System error (permissions, disk space, etc.)

For more information, see docs/CLI_REFERENCE.md
        '''
    )

    # Required arguments (except in special modes)
    required = parser.add_argument_group('required arguments')
    required.add_argument(
        '--project',
        required=False,  # Made optional - validated later if not in special mode
        metavar='NAME',
        help='''
        Project name for reporting.
        Used for configuration overrides and output file naming.
        Example: --project my-project
        '''
    )
    required.add_argument(
        '--repos-path',
        required=False,  # Made optional - validated later if not in special mode
        type=Path,
        metavar='PATH',
        help='''
        Path to directory containing cloned repositories.
        All subdirectories will be analyzed as repositories.
        Example: --repos-path /workspace/repos
        '''
    )

    # Configuration options
    config = parser.add_argument_group('configuration options')
    config.add_argument(
        '--config-dir',
        type=Path,
        metavar='PATH',
        help='''
        Configuration directory containing YAML config files.
        Default: ./config
        Example: --config-dir /etc/repo-reports/config
        '''
    )
    config.add_argument(
        '--output-dir',
        type=Path,
        metavar='PATH',
        help='''
        Output directory for generated reports.
        Default: ./output
        Example: --output-dir /var/reports/output
        '''
    )

    # Output format options
    output = parser.add_argument_group('output options')
    output.add_argument(
        '--output-format',
        type=str,
        choices=['json', 'md', 'html', 'all'],
        default='all',
        metavar='FORMAT',
        help='''
        Output format(s) to generate.
        Choices: json, md, html, all
        Default: all
        Example: --output-format html
        '''
    )

    output.add_argument(
        '--no-zip',
        action='store_true',
        help='Skip ZIP bundle creation'
    )

    # Behavioral options
    behavior = parser.add_argument_group('behavioral options')
    behavior.add_argument(
        '--cache',
        action='store_true',
        help='Enable caching of git metrics to speed up subsequent runs'
    )
    behavior.add_argument(
        '--workers',
        type=int,
        metavar='N',
        help='''
        Number of worker threads for parallel processing.
        Default: CPU count
        Example: --workers 8
        '''
    )

    # Verbosity options (mutually exclusive)
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='''
        Increase verbosity level. Can be used multiple times.
        -v: INFO, -vv: DEBUG, -vvv: TRACE
        '''
    )
    verbosity.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-error output (errors and warnings only)'
    )

    # Special modes
    modes = parser.add_argument_group('special modes')
    modes.add_argument(
        '--init',
        action='store_true',
        help='''
        Run interactive configuration wizard to create a new config file.
        Guides you through all configuration options with smart defaults.
        Example: --init
        '''
    )
    modes.add_argument(
        '--init-template',
        type=str,
        choices=['minimal', 'standard', 'full'],
        metavar='TEMPLATE',
        help='''
        Create configuration from template without interactive prompts.
        Requires --project. Choices: minimal, standard, full
        Example: --init-template standard --project my-project
        '''
    )
    modes.add_argument(
        '--config-output',
        type=Path,
        metavar='PATH',
        help='''
        Output path for configuration file (used with --init or --init-template).
        Default: config/{project}.yaml
        Example: --config-output custom-config.yaml
        '''
    )
    modes.add_argument(
        '--dry-run',
        action='store_true',
        help='''
        Validate configuration and setup without executing analysis.
        Useful for testing configuration changes.
        Example: --dry-run
        '''
    )
    modes.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate configuration file and exit (alias for --dry-run)'
    )
    modes.add_argument(
        '--list-features',
        action='store_true',
        help='List all available feature checks and exit'
    )
    modes.add_argument(
        '--show-feature',
        type=str,
        metavar='NAME',
        help='Show detailed information about a specific feature and exit'
    )
    modes.add_argument(
        '--show-config',
        action='store_true',
        help='Display resolved configuration and exit'
    )

    # Advanced options
    advanced = parser.add_argument_group('advanced options')
    advanced.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        metavar='LEVEL',
        help='Override log level from configuration'
    )
    advanced.add_argument(
        '--cache-dir',
        type=Path,
        metavar='PATH',
        help='Custom cache directory (default: .cache/repo-metrics)'
    )
    advanced.add_argument(
        '--config-override',
        action='append',
        metavar='KEY=VALUE',
        help='''
        Override configuration values.
        Can be used multiple times.
        Example: --config-override api.github.token=ghp_xxx
        '''
    )

    return parser


def parse_arguments(args: Optional[list[str]] = None) -> argparse.Namespace:
    """
    Parse and validate command-line arguments.

    Args:
        args: Optional list of arguments (defaults to sys.argv)

    Returns:
        Parsed arguments namespace

    Raises:
        InvalidArgumentError: If arguments are invalid or conflicting

    Example:
        >>> args = parse_arguments(['--project', 'test', '--repos-path', '.'])
        >>> print(args.project)
        test
    """
    parser = create_argument_parser()
    parsed_args = parser.parse_args(args)

    # Post-parse validation
    validate_arguments(parsed_args)

    return parsed_args


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate parsed arguments for consistency and correctness.

    Args:
        args: Parsed arguments namespace

    Raises:
        InvalidArgumentError: If arguments are invalid or conflicting
    """
    # Check if we're in a special mode that doesn't need standard arguments
    special_mode = (
        getattr(args, 'list_features', False) or
        getattr(args, 'show_feature', None) is not None or
        getattr(args, 'init', False)
    )

    # For --init-template, we need --project but not --repos-path
    template_mode = getattr(args, 'init_template', None) is not None
    if template_mode and not getattr(args, 'project', None):
        raise InvalidArgumentError(
            "The --init-template mode requires --project",
            suggestion="Provide --project with your project name when using --init-template"
        )

    # Require --project and --repos-path unless in special mode or template mode
    if not special_mode and not template_mode:
        if not hasattr(args, 'project') or not args.project:
            raise InvalidArgumentError(
                "The --project argument is required",
                suggestion="Provide --project with your project name, or use --list-features to see available features"
            )
        if not hasattr(args, 'repos_path') or not args.repos_path:
            raise InvalidArgumentError(
                "The --repos-path argument is required",
                suggestion="Provide --repos-path with the path to your repositories directory"
            )


    # Validate paths exist where required
    if hasattr(args, 'repos_path') and args.repos_path:
        if not args.repos_path.exists():
            raise InvalidArgumentError(
                f"Repository path does not exist: {args.repos_path}",
                suggestion="Ensure the path is correct and accessible"
            )
        if not args.repos_path.is_dir():
            raise InvalidArgumentError(
                f"Repository path is not a directory: {args.repos_path}",
                suggestion="Provide a path to a directory containing repositories"
            )

    # Validate worker count
    if hasattr(args, 'workers') and args.workers is not None:
        if args.workers < 1:
            raise InvalidArgumentError(
                f"Worker count must be at least 1, got: {args.workers}",
                suggestion="Use --workers 1 or higher"
            )
        if args.workers > 32:
            raise InvalidArgumentError(
                f"Worker count seems too high: {args.workers}",
                suggestion="Consider using --workers 16 or lower for stability"
            )

    # Handle validate-only as alias for dry-run
    if hasattr(args, 'validate_only') and args.validate_only:
        args.dry_run = True


def get_verbosity_level(args: argparse.Namespace) -> VerbosityLevel:
    """
    Determine verbosity level from arguments.

    Args:
        args: Parsed arguments

    Returns:
        VerbosityLevel enum value

    Example:
        >>> args = parse_arguments(['-vv'])
        >>> level = get_verbosity_level(args)
        >>> print(level)
        VerbosityLevel.DEBUG
    """
    if hasattr(args, 'quiet') and args.quiet:
        return VerbosityLevel.QUIET

    if hasattr(args, 'verbose'):
        verbose_count = args.verbose
        if verbose_count == 0:
            return VerbosityLevel.NORMAL
        elif verbose_count == 1:
            return VerbosityLevel.VERBOSE
        elif verbose_count == 2:
            return VerbosityLevel.DEBUG
        else:
            return VerbosityLevel.TRACE

    return VerbosityLevel.NORMAL


def get_log_level(args: argparse.Namespace) -> str:
    """
    Determine log level from arguments.

    Args:
        args: Parsed arguments

    Returns:
        Log level string (DEBUG, INFO, WARNING, ERROR)

    Example:
        >>> args = parse_arguments(['-v'])
        >>> level = get_log_level(args)
        >>> print(level)
        INFO
    """
    # Explicit log level takes precedence
    if hasattr(args, 'log_level') and args.log_level:
        return str(args.log_level)

    # Otherwise determine from verbosity
    verbosity = get_verbosity_level(args)

    if verbosity == VerbosityLevel.QUIET:
        return 'WARNING'
    elif verbosity == VerbosityLevel.NORMAL:
        return 'INFO'
    elif verbosity == VerbosityLevel.VERBOSE:
        return 'INFO'
    elif verbosity == VerbosityLevel.DEBUG:
        return 'DEBUG'
    else:  # TRACE
        return 'DEBUG'


def get_output_formats(args: argparse.Namespace) -> list[OutputFormat]:
    """
    Determine which output formats to generate.

    Args:
        args: Parsed arguments

    Returns:
        List of OutputFormat enum values

    Example:
        >>> args = parse_arguments(['--output-format', 'html'])
        >>> formats = get_output_formats(args)
        >>> print(formats)
        [<OutputFormat.HTML: 'html'>]
    """
    # Handle --output-format argument
    # Handle --output-format
    if hasattr(args, 'output_format'):
        format_str = args.output_format.lower()

        if format_str == 'all':
            return [OutputFormat.JSON, OutputFormat.MARKDOWN, OutputFormat.HTML]
        elif format_str == 'json':
            return [OutputFormat.JSON]
        elif format_str == 'md':
            return [OutputFormat.MARKDOWN]
        elif format_str == 'html':
            return [OutputFormat.HTML]

    # Default: all formats
    return [OutputFormat.JSON, OutputFormat.MARKDOWN, OutputFormat.HTML]


def should_generate_zip(args: argparse.Namespace) -> bool:
    """
    Determine if ZIP bundle should be generated.

    Args:
        args: Parsed arguments

    Returns:
        True if ZIP should be generated, False otherwise
    """
    return not (hasattr(args, 'no_zip') and args.no_zip)


def is_special_mode(args: argparse.Namespace) -> bool:
    """
    Check if running in a special mode (dry-run, list-features, etc.).

    Special modes exit early without full analysis.

    Args:
        args: Parsed arguments

    Returns:
        True if in special mode, False otherwise
    """
    special_flags = ['dry_run', 'validate_only', 'list_features', 'show_feature', 'show_config', 'init']
    return any(getattr(args, flag, False) for flag in special_flags) or getattr(args, 'init_template', None) is not None


def is_wizard_mode(args: argparse.Namespace) -> bool:
    """
    Check if running in wizard mode (--init or --init-template).

    Args:
        args: Parsed arguments

    Returns:
        True if in wizard mode, False otherwise
    """
    return getattr(args, 'init', False) or getattr(args, 'init_template', None) is not None


__all__ = [
    'create_argument_parser',
    'parse_arguments',
    'validate_arguments',
    'get_verbosity_level',
    'get_log_level',
    'get_output_formats',
    'should_generate_zip',
    'is_special_mode',
    'is_wizard_mode',
    'OutputFormat',
    'VerbosityLevel',
]

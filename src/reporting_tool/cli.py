# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Modern CLI interface using Typer for reporting-tool.

This module provides a rich, user-friendly command-line interface with:
- Type-safe argument parsing
- Beautiful output formatting with Rich
- Shell completion support
- Interactive help and documentation
- Modern CLI conventions
"""

import sys
from pathlib import Path
from typing import Optional, List
from enum import Enum

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from typing_extensions import Annotated

# Initialize Typer app with rich formatting
app = typer.Typer(
    name="reporting-tool",
    help="📊 Comprehensive Multi-Repository Analysis Tool",
    add_completion=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
)

# Rich console for beautiful output
console = Console()


class OutputFormat(str, Enum):
    """Output format options."""
    JSON = "json"
    MARKDOWN = "md"
    HTML = "html"
    ALL = "all"


class InitTemplate(str, Enum):
    """Configuration template options."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"


class ExitCode(int, Enum):
    """Standard exit codes."""
    SUCCESS = 0
    ERROR = 1
    PARTIAL = 2
    USAGE_ERROR = 3
    SYSTEM_ERROR = 4


# Version callback
def version_callback(value: bool):
    """Show version and exit."""
    if value:
        from reporting_tool import __version__
        rprint(f"[bold cyan]reporting-tool[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.command()
def generate(
    # Required arguments
    project: Annotated[
        Optional[str],
        typer.Option(
            "--project",
            "-p",
            help="Project name for reporting and configuration",
            rich_help_panel="Required Arguments",
        ),
    ] = None,
    repos_path: Annotated[
        Optional[Path],
        typer.Option(
            "--repos-path",
            "-r",
            help="Path to directory containing cloned repositories",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            rich_help_panel="Required Arguments",
        ),
    ] = None,

    # Configuration options
    config_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--config-dir",
            help="Configuration directory containing YAML files",
            exists=True,
            file_okay=False,
            dir_okay=True,
            rich_help_panel="Configuration",
        ),
    ] = None,
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--output-dir",
            "-o",
            help="Output directory for generated reports",
            rich_help_panel="Configuration",
        ),
    ] = None,

    # Output options
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--output-format",
            "-f",
            help="Output format(s) to generate",
            rich_help_panel="Output Options",
        ),
    ] = OutputFormat.ALL,
    no_zip: Annotated[
        bool,
        typer.Option(
            "--no-zip",
            help="Skip ZIP bundle creation",
            rich_help_panel="Output Options",
        ),
    ] = False,

    # Behavioral options
    cache: Annotated[
        bool,
        typer.Option(
            "--cache",
            help="Enable caching of git metrics for faster subsequent runs",
            rich_help_panel="Performance",
        ),
    ] = False,
    workers: Annotated[
        Optional[int],
        typer.Option(
            "--workers",
            "-w",
            help="Number of worker threads (default: CPU count, 'auto' for optimal)",
            min=1,
            rich_help_panel="Performance",
        ),
    ] = None,

    # Verbosity options
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity (-v: INFO, -vv: DEBUG, -vvv: TRACE)",
            rich_help_panel="Logging",
        ),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress non-error output",
            rich_help_panel="Logging",
        ),
    ] = False,

    # Validation options
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Validate configuration without executing analysis",
            rich_help_panel="Validation",
        ),
    ] = False,
    show_config: Annotated[
        bool,
        typer.Option(
            "--show-config",
            help="Display resolved configuration and exit",
            rich_help_panel="Validation",
        ),
    ] = False,

    # Version
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
):
    """
    Generate comprehensive analysis reports for repository collections.

    Analyzes Git repositories to generate detailed reports including:

    • 📈 Commit activity and contributor statistics

    • 🔍 CI/CD workflow status (Jenkins, GitHub Actions)

    • ✨ Feature detection (Dependabot, pre-commit, ReadTheDocs, etc.)

    • 👥 Organization and contributor rankings

    • 📊 Inactive repository identification

    \b
    Examples:
        # Basic usage
        reporting-tool generate --project my-project --repos-path ./repos

        # With custom configuration
        reporting-tool generate -p my-project -r ./repos --config-dir ./config

        # Validate without running
        reporting-tool generate -p my-project -r ./repos --dry-run

        # Generate only HTML with verbose output
        reporting-tool generate -p my-project -r ./repos -f html -vv

        # With caching and parallel processing
        reporting-tool generate -p my-project -r ./repos --cache --workers 8
    """
    # Import here to avoid circular imports and speed up CLI loading
    from reporting_tool.main import main as reporting_main
    from argparse import Namespace

    # Validate required arguments
    if not project:
        console.print("[red]Error:[/red] --project is required")
        raise typer.Exit(code=ExitCode.USAGE_ERROR)
    if not repos_path:
        console.print("[red]Error:[/red] --repos-path is required")
        raise typer.Exit(code=ExitCode.USAGE_ERROR)

    # Build arguments namespace for main function
    args = Namespace(
        project=project,
        repos_path=repos_path,
        config_dir=config_dir or Path("configuration"),
        output_dir=output_dir or Path("reports"),
        output_format=output_format.value,
        no_zip=no_zip,
        no_html=output_format not in [OutputFormat.HTML, OutputFormat.ALL],
        cache=cache,
        workers=workers,
        verbose=verbose,
        quiet=quiet,
        validate_only=dry_run,
        show_config=show_config,
        log_level=None,
    )

    # Set log level based on verbosity
    if quiet:
        args.log_level = "ERROR"
    elif verbose >= 2:
        args.log_level = "DEBUG"
    elif verbose >= 1:
        args.log_level = "INFO"

    # Call main function directly
    try:
        exit_code = reporting_main(args)
        raise typer.Exit(code=exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(code=130)


@app.command()
def init(
    project: Annotated[
        Optional[str],
        typer.Option(
            "--project",
            "-p",
            help="Project name for the new configuration",
        ),
    ] = None,
    template: Annotated[
        Optional[InitTemplate],
        typer.Option(
            "--template",
            "-t",
            help="Use a template instead of interactive wizard",
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output path for configuration file",
        ),
    ] = None,
):
    """
    Initialize a new configuration file for a project.

    Runs an interactive configuration wizard or uses a template to create
    a new project configuration file with smart defaults.

    \b
    Templates:
        minimal   - Basic configuration with essential settings only
        standard  - Recommended configuration with common features enabled
        full      - Complete configuration with all options documented

    \b
    Examples:
        # Interactive wizard
        reporting-tool init

        # Create from template
        reporting-tool init --project my-project --template standard

        # Custom output location
        reporting-tool init -p my-project -t minimal -o custom.yaml
    """
    # TODO: Implement configuration wizard
    console.print("[yellow]Configuration wizard coming soon![/yellow]")
    console.print("\nFor now, create configuration files manually:")
    console.print("1. Create a 'configuration' directory")
    console.print("2. Add 'template.config' with default settings")
    console.print("3. Add '<project-name>.config' with project-specific overrides")
    console.print("\nSee examples in the documentation.")
    raise typer.Exit(code=0)


@app.command()
def list_features():
    """
    List all available feature detection checks.

    Displays a comprehensive list of features that can be automatically
    detected in repositories, including:

    • CI/CD systems (Jenkins, GitHub Actions, GitLab CI)

    • Dependency management (requirements.txt, package.json, pom.xml)

    • Documentation (README, docs/, ReadTheDocs)

    • Code quality tools (pre-commit, linters, formatters)

    • Security tools (Dependabot, CodeQL, vulnerability scanning)
    """
    # TODO: Implement feature listing
    console.print("[yellow]Feature listing coming soon![/yellow]")
    console.print("\nAvailable features include:")
    console.print("• CI/CD systems (Jenkins, GitHub Actions, GitLab CI)")
    console.print("• Dependency management (requirements.txt, package.json, pom.xml)")
    console.print("• Documentation (README, docs/, ReadTheDocs)")
    console.print("• Code quality tools (pre-commit, linters, formatters)")
    console.print("• Security tools (Dependabot, CodeQL)")
    raise typer.Exit(code=0)


@app.command()
def validate(
    config: Annotated[
        Path,
        typer.Argument(
            help="Configuration file to validate",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
):
    """
    Validate a configuration file.

    Checks configuration file for:

    • ✅ Valid YAML syntax

    • 🔍 Required fields present

    • 📝 Correct data types and values

    • ⚠️  Deprecated options

    • 💡 Optimization suggestions

    \b
    Examples:
        # Validate a config file
        reporting-tool validate config/my-project.yaml

        # Validate with verbose output
        reporting-tool validate config/my-project.yaml -v
    """
    # TODO: Implement proper configuration validation
    console.print(f"[yellow]Validating configuration:[/yellow] {config}")
    console.print("[yellow]Configuration validation coming soon![/yellow]")
    console.print("\nFor now, run with --dry-run flag:")
    console.print(f"  reporting-tool generate --project test --repos-path . --dry-run")
    raise typer.Exit(code=0)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
):
    """
    📊 Reporting Tool - Comprehensive Multi-Repository Analysis Tool

    A modern Python package for analyzing Git repositories and generating
    comprehensive reports with metrics, feature detection, and contributor analysis.

    \b
    🚀 Quick Start:
        reporting-tool generate --project my-project --repos-path ./repos

    \b
    📖 Common Commands:
        generate        Generate analysis reports (main command)
        init            Create a new configuration file
        list-features   Show all available feature detections
        validate        Validate a configuration file

    \b
    📚 Documentation:
        https://reporting-tool.readthedocs.io

    \b
    🐛 Report Issues:
        https://github.com/lf-it/reporting-tool/issues
    """
    if ctx.invoked_subcommand is None:
        # No subcommand provided, show help
        console.print(ctx.get_help())


def cli_main():
    """Entry point for console script."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"[red bold]Error:[/red bold] {e}")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            console.print_exception()
        raise typer.Exit(code=ExitCode.ERROR)


if __name__ == "__main__":
    cli_main()

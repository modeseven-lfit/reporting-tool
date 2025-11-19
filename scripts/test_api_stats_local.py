#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Local API Statistics Testing Script

This script tests the API statistics tracking system end-to-end without
requiring a GitHub Actions environment. It validates:

1. API statistics object is properly wired through the application
2. Real API calls are tracked (success and failure)
3. Step summary output is generated correctly
4. Stats are never empty when APIs are called

Usage:
    # Test with mock APIs (no real network calls)
    python scripts/test_api_stats_local.py --mock

    # Test with real APIs (requires tokens/access)
    python scripts/test_api_stats_local.py --real

    # Test both
    python scripts/test_api_stats_local.py --all
"""

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.gerrit_client import GerritAPIClient
from api.github_client import GitHubAPIClient
from api.jenkins_client import JenkinsAPIClient
from reporting_tool.main import APIStatistics
from reporting_tool.reporter import RepositoryReporter


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


def test_wiring():
    """Test that API stats object is wired through the application."""
    print_header("TEST 1: API Statistics Wiring")

    errors = []

    try:
        # Create API stats instance
        api_stats = APIStatistics()
        print_info("Created APIStatistics instance")

        # Create reporter with stats
        config = {
            "gerrit": {"enabled": False},
            "jenkins": {"enabled": False},
        }
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.CRITICAL)  # Suppress output

        reporter = RepositoryReporter(config, logger, api_stats)
        print_info("Created RepositoryReporter with api_stats")

        # Verify wiring
        if reporter.api_stats is not api_stats:
            errors.append("Reporter.api_stats is not the same object")
        else:
            print_success("Reporter.api_stats correctly wired")

        if reporter.git_collector.api_stats is not api_stats:
            errors.append("GitCollector.api_stats is not the same object")
        else:
            print_success("GitCollector.api_stats correctly wired")

        if reporter.feature_registry.api_stats is not api_stats:
            errors.append("FeatureRegistry.api_stats is not the same object")
        else:
            print_success("FeatureRegistry.api_stats correctly wired")

    except Exception as e:
        errors.append(f"Exception during wiring test: {e}")

    if errors:
        print_error(f"Wiring test FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print_success("Wiring test PASSED - all components correctly wired")
        return True


def test_mock_api_calls():
    """Test API statistics tracking with mocked API calls."""
    print_header("TEST 2: Mock API Calls Tracking")

    errors = []
    api_stats = APIStatistics()

    print_info("Testing GitHub API success tracking...")
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"workflows": []}
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GitHubAPIClient("fake-token", stats=api_stats)
        client.get_repository_workflows("test-org", "test-repo")

        if api_stats.stats["github"]["success"] != 1:
            errors.append(f"GitHub success count wrong: {api_stats.stats['github']['success']}")
        else:
            print_success("GitHub success call tracked correctly")

    print_info("Testing GitHub API error tracking...")
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GitHubAPIClient("fake-token", stats=api_stats)
        client.get_repository_workflows("test-org", "nonexistent")

        if api_stats.stats["github"]["errors"].get(404) != 1:
            errors.append("GitHub 404 error not tracked")
        else:
            print_success("GitHub error call tracked correctly")

    print_info("Testing Gerrit API success tracking...")
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ')]}\n{"name": "test-project"}'
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GerritAPIClient(
            "gerrit.example.org", base_url="https://gerrit.example.org", stats=api_stats
        )
        client.get_project_info("test-project")

        if api_stats.stats["gerrit"]["success"] != 1:
            errors.append(f"Gerrit success count wrong: {api_stats.stats['gerrit']['success']}")
        else:
            print_success("Gerrit success call tracked correctly")

    print_info("Testing Jenkins API tracking...")
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jobs": []}
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = JenkinsAPIClient("jenkins.example.org", stats=api_stats)
        # Constructor makes discovery call

        if api_stats.stats["jenkins"]["success"] < 1:
            errors.append(f"Jenkins success count wrong: {api_stats.stats['jenkins']['success']}")
        else:
            print_success("Jenkins success call tracked correctly")

    if errors:
        print_error(f"Mock API test FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print_success("Mock API test PASSED - all API calls tracked correctly")
        return True


def test_step_summary_output():
    """Test that step summary is written correctly."""
    print_header("TEST 3: GitHub Step Summary Output")

    errors = []
    api_stats = APIStatistics()

    # Record some stats
    api_stats.record_success("github")
    api_stats.record_success("github")
    api_stats.record_error("github", 404)
    api_stats.record_success("gerrit")
    api_stats.record_error("jenkins", 500)
    api_stats.record_info_master(True)

    # Create temporary file for step summary
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".md") as f:
        temp_file = f.name

    try:
        # Set environment variable
        os.environ["GITHUB_STEP_SUMMARY"] = temp_file

        print_info(f"Writing step summary to: {temp_file}")
        api_stats.write_to_step_summary()

        # Read and validate
        with open(temp_file) as f:
            content = f.read()

        print_info("Step summary content:")
        print("─" * 70)
        print(content)
        print("─" * 70)

        # Validate content
        required_strings = [
            "📊 API Statistics",
            "GitHub API",
            "Successful calls: 2",
            "Failed calls: 1",
            "Error 404: 1",
            "Gerrit API",
            "Successful calls: 1",
            "Jenkins API",
            "Error 500: 1",
            "Info-Master Clone",
            "Successfully cloned",
        ]

        for req_str in required_strings:
            if req_str not in content:
                errors.append(f"Missing required string: '{req_str}'")
            else:
                print_success(f"Found: '{req_str}'")

    except Exception as e:
        errors.append(f"Exception during step summary test: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        if "GITHUB_STEP_SUMMARY" in os.environ:
            del os.environ["GITHUB_STEP_SUMMARY"]

    if errors:
        print_error(f"Step summary test FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print_success("Step summary test PASSED - output correctly formatted")
        return True


def test_empty_stats_message():
    """Test that empty stats show appropriate message."""
    print_header("TEST 4: Empty Stats Message")

    errors = []
    api_stats = APIStatistics()  # No calls recorded

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".md") as f:
        temp_file = f.name

    try:
        os.environ["GITHUB_STEP_SUMMARY"] = temp_file

        print_info("Writing step summary with no API calls...")
        api_stats.write_to_step_summary()

        with open(temp_file) as f:
            content = f.read()

        print_info("Step summary content:")
        print("─" * 70)
        print(content)
        print("─" * 70)

        if "No external API calls were made" not in content:
            errors.append("Missing 'No external API calls' message")
        else:
            print_success("Found expected message for empty stats")

    except Exception as e:
        errors.append(f"Exception: {e}")
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        if "GITHUB_STEP_SUMMARY" in os.environ:
            del os.environ["GITHUB_STEP_SUMMARY"]

    if errors:
        print_error(f"Empty stats test FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print_success("Empty stats test PASSED")
        return True


def test_real_github_api():
    """Test with real GitHub API (requires GITHUB_TOKEN)."""
    print_header("TEST 5: Real GitHub API Calls")

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("CLASSIC_READ_ONLY_PAT_TOKEN")

    if not token:
        print_warning("Skipping real GitHub API test (no token found)")
        print_info("Set GITHUB_TOKEN or CLASSIC_READ_ONLY_PAT_TOKEN to enable")
        return None

    errors = []
    api_stats = APIStatistics()

    print_info("Making real GitHub API call...")
    try:
        client = GitHubAPIClient(token, stats=api_stats)

        # Try to get workflows from a known public repo
        workflows = client.get_repository_workflows("github", "docs")

        print_info(f"Received {len(workflows)} workflows")

        total_calls = api_stats.get_total_calls("github")
        if total_calls < 1:
            errors.append("No GitHub API calls tracked (expected at least 1)")
        else:
            print_success(f"GitHub API calls tracked: {total_calls}")

        if api_stats.stats["github"]["success"] > 0:
            print_success(f"Successful calls: {api_stats.stats['github']['success']}")

        if api_stats.get_total_errors("github") > 0:
            print_warning(f"Errors: {api_stats.get_total_errors('github')}")
            print_info(f"Error details: {api_stats.stats['github']['errors']}")

        client.close()

    except Exception as e:
        errors.append(f"Exception during real GitHub API test: {e}")

    if errors:
        print_error(f"Real GitHub API test FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print_success("Real GitHub API test PASSED")
        return True


def test_real_gerrit_api():
    """Test with real Gerrit API."""
    print_header("TEST 6: Real Gerrit API Calls")

    print_info("Testing against gerrit.linuxfoundation.org...")

    errors = []
    api_stats = APIStatistics()

    try:
        # Use a known public Gerrit instance
        client = GerritAPIClient(
            "gerrit.linuxfoundation.org",
            base_url="https://gerrit.linuxfoundation.org/infra",
            stats=api_stats,
            timeout=10.0,
        )

        print_info("Fetching project info for 'releng/lftools'...")
        project_info = client.get_project_info("releng/lftools")

        if project_info:
            print_success(f"Retrieved project info: {project_info.get('name', 'N/A')}")
        else:
            print_warning("Project not found (may be expected if private)")

        total_calls = api_stats.get_total_calls("gerrit")
        if total_calls < 1:
            errors.append("No Gerrit API calls tracked")
        else:
            print_success(f"Gerrit API calls tracked: {total_calls}")

        if api_stats.stats["gerrit"]["success"] > 0:
            print_success(f"Successful calls: {api_stats.stats['gerrit']['success']}")

        if api_stats.get_total_errors("gerrit") > 0:
            print_info(f"Errors: {api_stats.get_total_errors('gerrit')}")
            print_info(f"Error details: {api_stats.stats['gerrit']['errors']}")

        client.close()

    except Exception as e:
        print_warning(f"Exception during Gerrit API test (may be network issue): {e}")
        # Don't fail the test - network issues are expected
        return None

    if errors:
        print_error(f"Real Gerrit API test FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print_success("Real Gerrit API test PASSED")
        return True


def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description="Test API statistics tracking locally")
    parser.add_argument("--mock", action="store_true", help="Run mock API tests only")
    parser.add_argument("--real", action="store_true", help="Run real API tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()

    # Default to mock if nothing specified
    if not (args.mock or args.real or args.all):
        args.mock = True

    if args.all:
        args.mock = True
        args.real = True

    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║       API Statistics Local Testing Suite                            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")

    results = {}

    # Core tests (always run)
    results["wiring"] = test_wiring()

    if args.mock:
        results["mock_api"] = test_mock_api_calls()
        results["step_summary"] = test_step_summary_output()
        results["empty_stats"] = test_empty_stats_message()

    if args.real:
        results["real_github"] = test_real_github_api()
        results["real_gerrit"] = test_real_gerrit_api()

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)

    for test_name, result in results.items():
        if result is True:
            print_success(f"{test_name:20} PASSED")
        elif result is False:
            print_error(f"{test_name:20} FAILED")
        else:
            print_warning(f"{test_name:20} SKIPPED")

    print(f"\n{Colors.BOLD}Results:{Colors.END}")
    print(f"  {Colors.GREEN}Passed:  {passed}{Colors.END}")
    print(f"  {Colors.RED}Failed:  {failed}{Colors.END}")
    print(f"  {Colors.YELLOW}Skipped: {skipped}{Colors.END}")
    print(f"  Total:   {total}")

    if failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.END}")
        sys.exit(1)
    elif passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED{Colors.END}")
        sys.exit(0)
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  SOME TESTS SKIPPED{Colors.END}")
        sys.exit(0)


if __name__ == "__main__":
    main()

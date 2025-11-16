#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
CI-Management Integration Validation Script

This script validates that CI-Management integration is working correctly
by testing the configuration, initialization, and job allocation process.

Usage:
    python scripts/validate_ci_management.py [project_name]
    
Examples:
    python scripts/validate_ci_management.py onap
    python scripts/validate_ci_management.py opendaylight
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.jenkins_client import JenkinsAPIClient, CI_MANAGEMENT_AVAILABLE
from config.loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def print_section(title: str, char: str = "=") -> None:
    """Print a formatted section header."""
    print()
    print(char * 80)
    print(title)
    print(char * 80)
    print()


def check_ci_management_available() -> bool:
    """Check if CI-Management modules are available."""
    print_section("Step 1: Check CI-Management Module Availability")
    
    if CI_MANAGEMENT_AVAILABLE:
        print("✅ CI-Management modules are available")
        return True
    else:
        print("❌ CI-Management modules are NOT available")
        print()
        print("To install CI-Management modules:")
        print("  pip install -e .")
        print()
        return False


def load_project_config(project_name: str) -> dict:
    """Load project configuration."""
    print_section("Step 2: Load Project Configuration")
    
    try:
        config = load_config(project_name)
        print(f"✅ Successfully loaded configuration for project: {project_name}")
        print()
        
        # Display CI-Management config
        ci_mgmt = config.get("ci_management", {})
        if ci_mgmt:
            print("CI-Management Configuration:")
            print(f"  Enabled: {ci_mgmt.get('enabled', False)}")
            print(f"  URL: {ci_mgmt.get('url', 'Not configured')}")
            print(f"  Branch: {ci_mgmt.get('branch', 'master')}")
            print(f"  Cache Dir: {ci_mgmt.get('cache_dir', '/tmp')}")
        else:
            print("⚠️  No CI-Management configuration found")
        
        print()
        return config
        
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return {}


def validate_jenkins_config(config: dict) -> bool:
    """Validate Jenkins configuration."""
    print_section("Step 3: Validate Jenkins Configuration")
    
    jenkins_config = config.get("jenkins", {})
    
    if not jenkins_config.get("enabled", False):
        print("❌ Jenkins integration is not enabled")
        print()
        print("To enable Jenkins:")
        print("  jenkins:")
        print("    enabled: true")
        print("    host: 'jenkins.example.org'")
        print()
        return False
    
    host = jenkins_config.get("host", "")
    if not host:
        print("❌ Jenkins host is not configured")
        return False
    
    print(f"✅ Jenkins is configured: {host}")
    print()
    return True


def validate_ci_management_config(config: dict) -> bool:
    """Validate CI-Management configuration."""
    print_section("Step 4: Validate CI-Management Configuration")
    
    ci_mgmt = config.get("ci_management", {})
    
    if not ci_mgmt:
        print("❌ No CI-Management configuration found")
        print()
        print("To enable CI-Management, add to your config:")
        print("  ci_management:")
        print("    enabled: true")
        print("    url: 'https://gerrit.example.org/r/ci-management'")
        print()
        return False
    
    if not ci_mgmt.get("enabled", False):
        print("⚠️  CI-Management is configured but NOT enabled")
        print()
        print("To enable, set:")
        print("  ci_management:")
        print("    enabled: true")
        print()
        return False
    
    url = ci_mgmt.get("url", "")
    if not url:
        print("❌ CI-Management URL is not configured")
        print()
        print("Add the ci-management repository URL:")
        print("  ci_management:")
        print("    url: 'https://gerrit.example.org/r/ci-management'")
        print()
        return False
    
    print("✅ CI-Management configuration is valid")
    print(f"   URL: {url}")
    print(f"   Branch: {ci_mgmt.get('branch', 'master')}")
    print()
    return True


def test_jenkins_connection(config: dict) -> bool:
    """Test Jenkins API connection."""
    print_section("Step 5: Test Jenkins API Connection")
    
    jenkins_config = config.get("jenkins", {})
    host = jenkins_config.get("host", "")
    timeout = jenkins_config.get("timeout", 30.0)
    
    try:
        print(f"Connecting to Jenkins: {host}")
        # Don't pass ci_management_config yet - just test connection
        client = JenkinsAPIClient(host, timeout)
        
        # Try to get jobs
        jobs = client.get_all_jobs()
        job_count = len(jobs.get("jobs", []))
        
        if job_count > 0:
            print(f"✅ Successfully connected to Jenkins")
            print(f"   Found {job_count} total jobs")
            print()
            client.close()
            return True
        else:
            print("⚠️  Connected but no jobs found")
            print()
            client.close()
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to Jenkins: {e}")
        print()
        return False


def test_ci_management_initialization(config: dict) -> bool:
    """Test CI-Management initialization."""
    print_section("Step 6: Test CI-Management Initialization")
    
    jenkins_config = config.get("jenkins", {})
    ci_mgmt_config = config.get("ci_management", {})
    
    host = jenkins_config.get("host", "")
    timeout = jenkins_config.get("timeout", 30.0)
    
    try:
        print("Initializing Jenkins client with CI-Management...")
        client = JenkinsAPIClient(
            host, 
            timeout,
            ci_management_config=ci_mgmt_config
        )
        
        if client.ci_management_enabled:
            print("✅ CI-Management initialization successful")
            
            if client.ci_management_parser:
                summary = client.ci_management_parser.get_project_summary()
                print()
                print("CI-Management Summary:")
                print(f"   Gerrit Projects: {summary['gerrit_projects']}")
                print(f"   JJB Project Blocks: {summary['jjb_project_blocks']}")
                print(f"   Total Jobs: {summary['total_jobs']}")
                print(f"   Templates Loaded: {summary['templates_loaded']}")
                print()
            
            client.close()
            return True
        else:
            print("⚠️  CI-Management is not enabled")
            print("   Check logs above for initialization errors")
            print()
            client.close()
            return False
            
    except Exception as e:
        print(f"❌ CI-Management initialization failed: {e}")
        print()
        return False


def test_job_allocation(config: dict, test_projects: list) -> bool:
    """Test job allocation for sample projects."""
    print_section("Step 7: Test Job Allocation")
    
    jenkins_config = config.get("jenkins", {})
    ci_mgmt_config = config.get("ci_management", {})
    
    host = jenkins_config.get("host", "")
    timeout = jenkins_config.get("timeout", 30.0)
    
    try:
        client = JenkinsAPIClient(
            host, 
            timeout,
            ci_management_config=ci_mgmt_config
        )
        
        if not client.ci_management_enabled:
            print("⚠️  CI-Management not enabled, cannot test job allocation")
            client.close()
            return False
        
        allocated_jobs = set()
        
        for project in test_projects:
            print(f"Testing project: {project}")
            
            jobs = client.get_jobs_for_project(project, allocated_jobs)
            
            if jobs:
                print(f"  ✅ Found {len(jobs)} jobs for {project}")
                for job in jobs[:3]:  # Show first 3
                    print(f"     - {job.get('name', 'unknown')}")
                if len(jobs) > 3:
                    print(f"     ... and {len(jobs) - 3} more")
            else:
                print(f"  ⚠️  No jobs found for {project}")
            
            print()
        
        client.close()
        print("✅ Job allocation test complete")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Job allocation test failed: {e}")
        print()
        return False


def generate_summary(results: dict) -> None:
    """Generate validation summary."""
    print_section("Validation Summary", "=")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"Total Checks: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print()
    
    print("Results:")
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {check}")
    
    print()
    
    if all(results.values()):
        print("🎉 All validation checks passed!")
        print()
        print("CI-Management integration is ready to use.")
        print("Run your reports and check logs for CI-Management messages:")
        print("  - 'CI-Management initialized'")
        print("  - 'Using CI-Management for project: ...'")
        print("  - 'CI-Management: Found X/Y jobs'")
    else:
        print("⚠️  Some validation checks failed.")
        print()
        print("Review the failures above and:")
        print("  1. Fix configuration issues")
        print("  2. Check network connectivity")
        print("  3. Verify repository URLs")
        print("  4. Re-run this validation script")
    
    print()


def main():
    """Main validation workflow."""
    parser = argparse.ArgumentParser(
        description="Validate CI-Management integration configuration and setup"
    )
    parser.add_argument(
        "project",
        nargs="?",
        default="onap",
        help="Project name to validate (default: onap)"
    )
    parser.add_argument(
        "--test-projects",
        nargs="+",
        help="Specific projects to test job allocation (e.g., aai/babel ccsdk/apps)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print_section("CI-Management Integration Validation", "=")
    print(f"Project: {args.project}")
    print()
    
    results = {}
    
    # Step 1: Check module availability
    results["Module Availability"] = check_ci_management_available()
    if not results["Module Availability"]:
        generate_summary(results)
        return 1
    
    # Step 2: Load configuration
    config = load_project_config(args.project)
    results["Configuration Load"] = bool(config)
    if not config:
        generate_summary(results)
        return 1
    
    # Step 3: Validate Jenkins config
    results["Jenkins Configuration"] = validate_jenkins_config(config)
    
    # Step 4: Validate CI-Management config
    results["CI-Management Configuration"] = validate_ci_management_config(config)
    
    # Step 5: Test Jenkins connection
    if results["Jenkins Configuration"]:
        results["Jenkins Connection"] = test_jenkins_connection(config)
    else:
        results["Jenkins Connection"] = False
    
    # Step 6: Test CI-Management initialization
    if results["CI-Management Configuration"] and results["Jenkins Connection"]:
        results["CI-Management Initialization"] = test_ci_management_initialization(config)
    else:
        results["CI-Management Initialization"] = False
    
    # Step 7: Test job allocation (optional)
    if results["CI-Management Initialization"]:
        # Use provided test projects or defaults based on project
        test_projects = args.test_projects or get_default_test_projects(args.project)
        if test_projects:
            results["Job Allocation"] = test_job_allocation(config, test_projects)
        else:
            print_section("Step 7: Test Job Allocation")
            print("⚠️  No test projects specified, skipping job allocation test")
            print()
            results["Job Allocation"] = None  # Skip this check
    else:
        results["Job Allocation"] = False
    
    # Generate summary
    generate_summary({k: v for k, v in results.items() if v is not None})
    
    # Return exit code
    return 0 if all(v for v in results.values() if v is not None) else 1


def get_default_test_projects(project_name: str) -> list:
    """Get default test projects for common project types."""
    defaults = {
        "onap": ["aai/babel", "aai/aai-common", "ccsdk/apps"],
        "opendaylight": ["aaa", "controller", "integration/distribution"],
        "o-ran-sc": ["aiml-fw/athp/sdk/feature-store", "ric-plt/e2"],
    }
    return defaults.get(project_name.lower(), [])


if __name__ == "__main__":
    sys.exit(main())
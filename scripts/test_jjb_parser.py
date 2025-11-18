# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

#!/usr/bin/env python3
"""
Test script for JJB parser.

This script demonstrates the CI-Management parser by:
1. Loading templates from global-jjb
2. Parsing project definitions from ci-management
3. Expanding job names for sample projects
4. Showing the mapping from Gerrit projects to Jenkins jobs
"""

import logging
import sys
from pathlib import Path


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ci_management.jjb_parser import CIManagementParser


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Run JJB parser tests."""
    # Paths to cloned repositories
    ci_management_path = Path("/tmp/ci-management")
    global_jjb_path = Path("/tmp/releng-global-jjb")

    # Check if repos exist
    if not ci_management_path.exists():
        logger.error(f"CI-Management not found at {ci_management_path}")
        logger.error(
            "Please clone: git clone https://gerrit.onap.org/r/ci-management /tmp/ci-management"
        )
        return 1

    if not global_jjb_path.exists():
        logger.error(f"Global-JJB not found at {global_jjb_path}")
        logger.error(
            "Please clone: git clone https://github.com/lfit/releng-global-jjb /tmp/releng-global-jjb"
        )
        return 1

    # Initialize parser
    logger.info("=" * 80)
    logger.info("Initializing CI-Management Parser")
    logger.info("=" * 80)
    parser = CIManagementParser(ci_management_path, global_jjb_path)

    # Load templates
    logger.info("\n" + "=" * 80)
    logger.info("Loading JJB Templates from global-jjb")
    logger.info("=" * 80)
    parser.load_templates()

    # Test sample projects
    test_projects = [
        "aai/babel",
        "aai/aai-common",
        "ccsdk/apps",
        "integration",
        "sdc",
        "policy/engine",
    ]

    logger.info("\n" + "=" * 80)
    logger.info("Testing Sample Projects")
    logger.info("=" * 80)

    for project in test_projects:
        logger.info(f"\n--- Project: {project} ---")

        # Find JJB file
        jjb_file = parser.find_jjb_file(project)
        if jjb_file:
            logger.info(f"JJB File: {jjb_file.relative_to(ci_management_path)}")
        else:
            logger.warning(f"No JJB file found for {project}")
            continue

        # Parse jobs
        job_names = parser.parse_project_jobs(project)
        logger.info(f"Expected Jobs ({len(job_names)}):")
        for job_name in sorted(job_names):
            logger.info(f"  - {job_name}")

    # Get overall summary
    logger.info("\n" + "=" * 80)
    logger.info("Overall Summary")
    logger.info("=" * 80)
    summary = parser.get_project_summary()
    logger.info(f"Gerrit Projects: {summary['gerrit_projects']}")
    logger.info(f"JJB Project Blocks: {summary['jjb_project_blocks']}")
    logger.info(f"Total Job Definitions: {summary['total_jobs']}")
    logger.info(f"Templates Loaded: {summary['templates_loaded']}")

    # Show sample projects with most jobs
    logger.info("\n" + "=" * 80)
    logger.info("Projects with Most Job Definitions")
    logger.info("=" * 80)
    all_projects = parser.get_all_projects()
    project_job_counts = {}
    for gerrit_project, jjb_projects in all_projects.items():
        job_count = sum(len(p.jobs) for p in jjb_projects)
        project_job_counts[gerrit_project] = job_count

    # Sort by job count
    sorted_projects = sorted(project_job_counts.items(), key=lambda x: x[1], reverse=True)

    logger.info("\nTop 10 projects by job count:")
    for i, (project, count) in enumerate(sorted_projects[:10], 1):
        logger.info(f"{i:2d}. {project:40s} : {count:3d} jobs")

    # Test specific project in detail
    logger.info("\n" + "=" * 80)
    logger.info("Detailed Example: aai/babel")
    logger.info("=" * 80)

    project = "aai/babel"
    jjb_file = parser.find_jjb_file(project)
    if jjb_file:
        logger.info(f"\nJJB File: {jjb_file}")

        # Get the parsed projects
        if project in parser._project_cache:
            jjb_projects = parser._project_cache[project]
            logger.info(f"\nFound {len(jjb_projects)} project blocks:")
            for jjb_proj in jjb_projects:
                logger.info(f"\n  Project Block: {jjb_proj.name}")
                logger.info(f"  Gerrit Project: {jjb_proj.gerrit_project}")
                logger.info(f"  Job Templates ({len(jjb_proj.jobs)}):")
                for job in jjb_proj.jobs:
                    logger.info(f"    - {job.template_name}")
                    if job.expanded_names:
                        for expanded in job.expanded_names:
                            logger.info(f"      → {expanded}")

        # Get all expected job names
        job_names = parser.parse_project_jobs(project)
        logger.info(f"\n  All Expected Job Names ({len(job_names)}):")
        for job_name in sorted(job_names):
            logger.info(f"    {job_name}")

    logger.info("\n" + "=" * 80)
    logger.info("Test Complete!")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())

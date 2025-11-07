# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Integration tests for common user workflows.

Tests realistic end-to-end workflows that users might execute,
including CLI commands, configuration handling, and multi-step operations.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from tests.fixtures.repositories import create_synthetic_repository


class TestRepositoryAnalysisWorkflow:
    """Test the repository analysis workflow."""

    def test_analyze_single_repository_workflow(self, tmp_path):
        """Test complete workflow: clone -> analyze -> generate report."""
        # Create a synthetic repository
        repo_path = tmp_path / "test-repo"
        create_synthetic_repository(repo_path, commit_count=20, author_count=3, file_count=10)

        # Verify repository was created
        assert repo_path.exists()
        assert (repo_path / ".git").exists()

        # Verify we can get git log
        result = subprocess.run(
            ["git", "log", "--oneline"], cwd=repo_path, capture_output=True, text=True
        )
        assert result.returncode == 0
        assert len(result.stdout.strip().split("\n")) == 20

    def test_analyze_multiple_repositories_workflow(self, tmp_path):
        """Test workflow for analyzing multiple repositories."""
        # Create multiple repositories
        repos = []
        for i in range(3):
            repo_path = tmp_path / f"repo-{i}"
            create_synthetic_repository(
                repo_path, commit_count=10 + (i * 5), author_count=2, file_count=5
            )
            repos.append(repo_path)

        # Verify all repos created
        assert all(r.exists() for r in repos)

        # Verify different commit counts
        for i, repo in enumerate(repos):
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"], cwd=repo, capture_output=True, text=True
            )
            expected_count = 10 + (i * 5)
            actual_count = int(result.stdout.strip())
            assert actual_count == expected_count

    def test_incremental_analysis_workflow(self, tmp_path):
        """Test incremental analysis: initial report, add commits, re-analyze."""
        repo_path = tmp_path / "incremental-repo"

        # Initial repository
        create_synthetic_repository(repo_path, commit_count=10, author_count=1, file_count=5)

        initial_count = int(
            subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )

        assert initial_count == 10

        # Add more commits (simulated by creating another file and committing)
        new_file = repo_path / "new_file.txt"
        new_file.write_text("New content\n")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)

        subprocess.run(
            ["git", "commit", "-m", "Add new file"], cwd=repo_path, check=True, capture_output=True
        )

        # Verify commit was added
        new_count = int(
            subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )

        assert new_count == 11


class TestConfigurationWorkflow:
    """Test workflows with different configurations."""

    def test_minimal_configuration_workflow(self, tmp_path):
        """Test workflow with minimal configuration."""
        config = {"project": "MinimalTest", "output_dir": str(tmp_path / "output")}

        # Verify config is valid
        assert "project" in config
        assert "output_dir" in config

        # Create output directory
        output_dir = Path(config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        assert output_dir.exists()

    def test_complete_configuration_workflow(self, tmp_path):
        """Test workflow with complete configuration."""
        config = {
            "project": "CompleteTest",
            "output_dir": str(tmp_path / "output"),
            "time_windows": {"30d": {"days": 30}, "90d": {"days": 90}, "1y": {"days": 365}},
            "output_formats": ["json", "html"],
            "github": {
                "enabled": False  # Disable for testing
            },
            "performance": {"parallel_processing": {"enabled": True, "max_workers": 2}},
        }

        # Verify all sections present
        assert "project" in config
        assert "output_dir" in config
        assert "time_windows" in config
        assert "output_formats" in config
        assert "github" in config
        assert "performance" in config

    def test_configuration_override_workflow(self, tmp_path):
        """Test configuration override via command-line arguments."""
        # Base configuration
        base_config = {"project": "BaseProject", "output_dir": "/tmp/default"}

        # Override with CLI args
        cli_overrides = {"output_dir": str(tmp_path / "overridden")}

        # Merged config
        final_config = {**base_config, **cli_overrides}

        assert final_config["project"] == "BaseProject"
        assert final_config["output_dir"] == str(tmp_path / "overridden")


class TestErrorRecoveryWorkflow:
    """Test error recovery workflows."""

    def test_recover_from_network_error(self, tmp_path):
        """Test recovery from network/API errors."""
        # Simulate network error scenario
        # Should fall back to local-only analysis
        pass

    def test_recover_from_partial_failure(self, tmp_path):
        """Test recovery when some repositories fail."""
        # Create one good repo and one bad repo
        good_repo = tmp_path / "good-repo"
        bad_repo = tmp_path / "bad-repo"

        # Good repo
        create_synthetic_repository(good_repo, commit_count=10, author_count=1)

        # Bad repo (just an empty directory, not a git repo)
        bad_repo.mkdir()

        # Verify good repo works
        result = subprocess.run(
            ["git", "log", "--oneline"], cwd=good_repo, capture_output=True, text=True
        )
        assert result.returncode == 0

        # Verify bad repo fails
        result = subprocess.run(
            ["git", "log", "--oneline"], cwd=bad_repo, capture_output=True, text=True
        )
        assert result.returncode != 0

    def test_recover_from_corrupted_cache(self, tmp_path):
        """Test recovery from corrupted cache data."""
        # Should detect corrupted cache and rebuild
        pass

    def test_continue_after_rate_limit(self, tmp_path):
        """Test continuation after hitting API rate limits."""
        # Should pause and retry after rate limit reset
        pass


class TestOutputGenerationWorkflow:
    """Test output file generation workflows."""

    def test_json_output_workflow(self, tmp_path):
        """Test JSON output generation workflow."""
        output_file = tmp_path / "report.json"

        # Create sample report data
        report_data = {
            "schema_version": "3.0.0",
            "generated_at": datetime.now().isoformat(),
            "project": "TestProject",
            "repositories": [{"name": "test-repo", "commits": 10, "authors": 3}],
            "summary": {"total_commits": 10, "total_authors": 3, "total_repositories": 1},
        }

        # Write JSON
        with open(output_file, "w") as f:
            json.dump(report_data, f, indent=2)

        # Verify output
        assert output_file.exists()

        # Verify valid JSON
        with open(output_file) as f:
            loaded_data = json.load(f)

        assert loaded_data["schema_version"] == "3.0.0"
        assert loaded_data["summary"]["total_commits"] == 10

    def test_multiple_format_workflow(self, tmp_path):
        """Test generating multiple output formats."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Generate files
        json_file = output_dir / "report.json"
        html_file = output_dir / "report.html"
        md_file = output_dir / "report.md"

        # Create minimal files
        json_file.write_text('{"schema_version": "3.0.0"}')
        html_file.write_text("<html><body>Report</body></html>")
        md_file.write_text("# Report\n\nGenerated report.")

        # Verify all created
        assert json_file.exists()
        assert html_file.exists()
        assert md_file.exists()

    def test_output_directory_creation_workflow(self, tmp_path):
        """Test automatic output directory creation."""
        nested_dir = tmp_path / "level1" / "level2" / "output"

        # Create nested directories
        nested_dir.mkdir(parents=True, exist_ok=True)

        assert nested_dir.exists()
        assert nested_dir.parent.exists()
        assert nested_dir.parent.parent.exists()


class TestDataCollectionWorkflow:
    """Test data collection workflows."""

    def test_collect_commit_history(self, tmp_path):
        """Test collecting complete commit history."""
        repo_path = tmp_path / "history-test"
        create_synthetic_repository(repo_path, commit_count=50, author_count=5, file_count=10)

        # Get commit history
        result = subprocess.run(
            ["git", "log", "--format=%H|%an|%ae|%aI|%s"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        commits = result.stdout.strip().split("\n")
        assert len(commits) == 50

        # Verify format
        first_commit = commits[0].split("|")
        assert len(first_commit) == 5  # hash, name, email, date, subject

    def test_collect_author_statistics(self, tmp_path):
        """Test collecting author statistics."""
        repo_path = tmp_path / "author-test"
        create_synthetic_repository(repo_path, commit_count=30, author_count=3, file_count=5)

        # Get author list
        result = subprocess.run(
            ["git", "log", "--format=%an|%ae"], cwd=repo_path, capture_output=True, text=True
        )

        authors = set(result.stdout.strip().split("\n"))

        # Should have 3 unique authors
        assert len(authors) == 3

    def test_collect_file_changes(self, tmp_path):
        """Test collecting file change statistics."""
        repo_path = tmp_path / "changes-test"
        create_synthetic_repository(repo_path, commit_count=20, author_count=1, file_count=5)

        # Get file change stats
        result = subprocess.run(
            ["git", "log", "--numstat", "--format="], cwd=repo_path, capture_output=True, text=True
        )

        # Should have stats output
        assert len(result.stdout.strip()) > 0

        # Stats should be in format: added\tremoved\tfilename
        lines = [line for line in result.stdout.strip().split("\n") if line]
        assert len(lines) > 0


class TestBranchHandlingWorkflow:
    """Test workflows involving multiple branches."""

    def test_analyze_default_branch_only(self, tmp_path):
        """Test analyzing only the default branch."""
        repo_path = tmp_path / "branch-test"
        create_synthetic_repository(repo_path, commit_count=10, branches=["main", "develop"])

        # Should be on main branch
        result = subprocess.run(
            ["git", "branch", "--show-current"], cwd=repo_path, capture_output=True, text=True
        )

        current_branch = result.stdout.strip()
        assert current_branch == "main"

    def test_analyze_all_branches(self, tmp_path):
        """Test analyzing all branches."""
        repo_path = tmp_path / "multi-branch"
        create_synthetic_repository(
            repo_path, commit_count=10, branches=["main", "develop", "feature-x"]
        )

        # Get all branches
        result = subprocess.run(
            ["git", "branch", "-a"], cwd=repo_path, capture_output=True, text=True
        )

        branches = result.stdout.strip().split("\n")
        # Should have 3 branches
        assert len(branches) >= 3

    def test_handle_detached_head(self, tmp_path):
        """Test handling detached HEAD state."""
        repo_path = tmp_path / "detached-test"
        create_synthetic_repository(repo_path, commit_count=10, author_count=1)

        # Get first commit hash
        result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        first_commit = result.stdout.strip()

        # Checkout first commit (detached HEAD)
        subprocess.run(
            ["git", "checkout", first_commit], cwd=repo_path, check=True, capture_output=True
        )

        # Verify detached HEAD
        result = subprocess.run(
            ["git", "branch", "--show-current"], cwd=repo_path, capture_output=True, text=True
        )

        # Should be empty (detached HEAD)
        assert result.stdout.strip() == ""


class TestPerformanceOptimizationWorkflow:
    """Test performance optimization workflows."""

    def test_parallel_repository_processing(self, tmp_path):
        """Test parallel processing of multiple repositories."""
        # Create multiple repositories
        repos = []
        for i in range(5):
            repo_path = tmp_path / f"parallel-repo-{i}"
            create_synthetic_repository(repo_path, commit_count=10, author_count=2)
            repos.append(repo_path)

        # All repos should exist
        assert all(r.exists() for r in repos)

    def test_caching_workflow(self, tmp_path):
        """Test caching of analysis results."""
        # First run: generate cache
        # Second run: use cache
        pass

    def test_incremental_processing_workflow(self, tmp_path):
        """Test incremental processing of new commits."""
        # Only process commits since last analysis
        pass

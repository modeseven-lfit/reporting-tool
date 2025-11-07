# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for RenderContextBuilder.

Tests data preparation and context building for template rendering.

Phase 8: Renderer Modernization
"""

from datetime import datetime

from rendering.context_builder import RenderContextBuilder


class TestRenderContextBuilderInit:
    """Test RenderContextBuilder initialization."""

    def test_init_with_valid_data(self):
        """Test initialization with valid analysis data."""
        data = {"project_name": "Test Project", "repositories": []}
        builder = RenderContextBuilder(data)

        assert builder.data == data
        assert builder.logger is not None

    def test_init_with_empty_data(self):
        """Test initialization with empty data."""
        builder = RenderContextBuilder({})

        assert builder.data == {}
        assert builder.logger is not None

    def test_init_stores_reference_not_copy(self):
        """Test that builder stores reference to data."""
        data = {"project_name": "Test", "repositories": []}
        builder = RenderContextBuilder(data)

        # Modify original data
        data["test_key"] = "test_value"

        # Builder should see the change
        assert "test_key" in builder.data


class TestRenderContextBuilderBuild:
    """Test complete context building."""

    def test_build_returns_all_sections(self):
        """Test that build returns all required context sections."""
        data = {"project_name": "Test Project", "repositories": []}
        builder = RenderContextBuilder(data)
        context = builder.build()

        assert "project" in context
        assert "summary" in context
        assert "repositories" in context
        assert "authors" in context
        assert "workflows" in context
        assert "metadata" in context
        assert "time_windows" in context

    def test_build_with_complete_data(self):
        """Test building context with complete analysis data."""
        data = {
            "project_name": "Complete Project",
            "repositories": [
                {
                    "name": "repo1",
                    "path": "/path/to/repo1",
                    "total_commits": 100,
                    "active": True,
                    "first_commit_date": "2024-01-01",
                    "last_commit_date": "2025-01-01",
                    "primary_language": "Python",
                    "description": "Test repo",
                    "workflows": [],
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 50}
                    ],
                }
            ],
            "time_windows": [
                {
                    "name": "Last 30 days",
                    "start_date": "2024-12-01",
                    "end_date": "2025-01-01",
                    "total_commits": 20,
                    "active_authors": 1,
                }
            ],
            "version": "1.0.0",
        }

        builder = RenderContextBuilder(data)
        context = builder.build()

        # Verify all sections are populated
        assert context["project"]["name"] == "Complete Project"
        assert context["summary"]["total_repositories"] == 1
        assert len(context["repositories"]) == 1
        assert len(context["authors"]) == 1
        assert len(context["time_windows"]) == 1
        assert context["metadata"]["generator_version"] == "1.0.0"


class TestProjectContext:
    """Test project context building."""

    def test_project_context_with_no_repos(self):
        """Test project context when no repositories."""
        data = {"project_name": "Empty Project", "repositories": []}
        builder = RenderContextBuilder(data)

        project = builder._build_project_context()

        assert project["name"] == "Empty Project"
        assert project["total_repos"] == 0
        assert project["active_repos"] == 0
        assert project["total_commits"] == 0
        assert project["total_authors"] == 0

    def test_project_context_with_multiple_repos(self):
        """Test project context with multiple repositories."""
        data = {
            "project_name": "Multi Repo Project",
            "repositories": [
                {
                    "name": "repo1",
                    "total_commits": 100,
                    "active": True,
                    "authors": [
                        {"email": "alice@example.com", "commit_count": 50},
                        {"email": "bob@example.com", "commit_count": 50},
                    ],
                },
                {
                    "name": "repo2",
                    "total_commits": 50,
                    "active": False,
                    "authors": [
                        {"email": "alice@example.com", "commit_count": 30},
                        {"email": "charlie@example.com", "commit_count": 20},
                    ],
                },
            ],
        }

        builder = RenderContextBuilder(data)
        project = builder._build_project_context()

        assert project["total_repos"] == 2
        assert project["active_repos"] == 1
        assert project["total_commits"] == 150
        assert project["total_authors"] == 3  # alice, bob, charlie

    def test_project_context_deduplicates_authors(self):
        """Test that project context counts unique authors."""
        data = {
            "project_name": "Test",
            "repositories": [
                {"authors": [{"email": "alice@example.com"}, {"email": "bob@example.com"}]},
                {
                    "authors": [
                        {"email": "alice@example.com"},  # Duplicate
                        {"email": "charlie@example.com"},
                    ]
                },
            ],
        }

        builder = RenderContextBuilder(data)
        project = builder._build_project_context()

        assert project["total_authors"] == 3  # alice, bob, charlie

    def test_project_context_handles_missing_email(self):
        """Test that project context skips authors without email."""
        data = {
            "project_name": "Test",
            "repositories": [
                {
                    "authors": [
                        {"email": "alice@example.com"},
                        {"name": "No Email"},  # Missing email
                        {"email": None},  # Null email
                    ]
                }
            ],
        }

        builder = RenderContextBuilder(data)
        project = builder._build_project_context()

        assert project["total_authors"] == 1  # Only alice

    def test_project_context_date_range(self):
        """Test project context includes date range."""
        data = {"project_name": "Test", "repositories": []}

        builder = RenderContextBuilder(data)
        project = builder._build_project_context()

        assert "date_range" in project

    def test_project_context_unknown_name(self):
        """Test project context with missing project name."""
        data = {"repositories": []}
        builder = RenderContextBuilder(data)

        project = builder._build_project_context()

        assert project["name"] == "Unknown Project"


class TestSummaryContext:
    """Test summary context building."""

    def test_summary_with_empty_repos(self):
        """Test summary with no repositories."""
        data = {"repositories": []}
        builder = RenderContextBuilder(data)

        summary = builder._build_summary_context()

        assert summary["total_repositories"] == 0
        assert summary["total_commits"] == 0
        assert summary["total_authors"] == 0
        assert summary["avg_commits_per_repo"] == 0
        assert summary["avg_commits_per_author"] == 0

    def test_summary_calculates_averages(self):
        """Test summary calculates correct averages."""
        data = {
            "repositories": [
                {
                    "total_commits": 100,
                    "authors": [{"email": "alice@example.com"}, {"email": "bob@example.com"}],
                },
                {
                    "total_commits": 200,
                    "authors": [{"email": "alice@example.com"}, {"email": "charlie@example.com"}],
                },
            ]
        }

        builder = RenderContextBuilder(data)
        summary = builder._build_summary_context()

        assert summary["total_repositories"] == 2
        assert summary["total_commits"] == 300
        assert summary["total_authors"] == 3
        assert summary["avg_commits_per_repo"] == 150.0
        assert summary["avg_commits_per_author"] == 100.0

    def test_summary_handles_zero_division(self):
        """Test summary handles division by zero gracefully."""
        data = {"repositories": []}
        builder = RenderContextBuilder(data)

        summary = builder._build_summary_context()

        # Should not raise ZeroDivisionError
        assert summary["avg_commits_per_repo"] == 0
        assert summary["avg_commits_per_author"] == 0


class TestRepositoriesContext:
    """Test repositories context building."""

    def test_repositories_enrichment(self):
        """Test repositories are enriched with additional data."""
        data = {
            "repositories": [
                {
                    "name": "test-repo",
                    "path": "/path/to/repo",
                    "total_commits": 100,
                    "authors": [{"email": "alice@example.com"}],
                    "active": True,
                    "last_commit_date": "2025-01-01",
                    "first_commit_date": "2024-01-01",
                    "primary_language": "Python",
                    "workflows": [{"name": "CI"}],
                    "description": "Test repository",
                }
            ]
        }

        builder = RenderContextBuilder(data)
        repos = builder._build_repositories_context()

        assert len(repos) == 1
        repo = repos[0]

        assert repo["name"] == "test-repo"
        assert repo["path"] == "/path/to/repo"
        assert repo["total_commits"] == 100
        assert repo["total_authors"] == 1
        assert repo["active"] is True
        assert repo["last_commit_date"] == "2025-01-01"
        assert repo["first_commit_date"] == "2024-01-01"
        assert repo["primary_language"] == "Python"
        assert repo["has_ci"] is True
        assert len(repo["workflows"]) == 1
        assert repo["description"] == "Test repository"

    def test_repositories_sorted_by_commits(self):
        """Test repositories are sorted by commit count descending."""
        data = {
            "repositories": [
                {"name": "repo1", "total_commits": 50},
                {"name": "repo2", "total_commits": 200},
                {"name": "repo3", "total_commits": 100},
            ]
        }

        builder = RenderContextBuilder(data)
        repos = builder._build_repositories_context()

        assert repos[0]["name"] == "repo2"  # 200 commits
        assert repos[1]["name"] == "repo3"  # 100 commits
        assert repos[2]["name"] == "repo1"  # 50 commits

    def test_repositories_has_ci_flag(self):
        """Test has_ci flag is set correctly."""
        data = {
            "repositories": [
                {"name": "with_ci", "workflows": [{"name": "CI"}]},
                {"name": "without_ci", "workflows": []},
                {"name": "no_workflows_key"},
            ]
        }

        builder = RenderContextBuilder(data)
        repos = builder._build_repositories_context()

        # Find repos by name
        with_ci = next(r for r in repos if r["name"] == "with_ci")
        without_ci = next(r for r in repos if r["name"] == "without_ci")
        no_workflows = next(r for r in repos if r["name"] == "no_workflows_key")

        assert with_ci["has_ci"] is True
        assert without_ci["has_ci"] is False
        assert no_workflows["has_ci"] is False

    def test_repositories_default_values(self):
        """Test repositories use default values for missing fields."""
        data = {
            "repositories": [{}]  # Empty repo
        }

        builder = RenderContextBuilder(data)
        repos = builder._build_repositories_context()

        repo = repos[0]
        assert repo["name"] == "Unknown"
        assert repo["path"] == ""
        assert repo["total_commits"] == 0
        assert repo["total_authors"] == 0
        assert repo["active"] is False
        assert repo["primary_language"] == "Unknown"
        assert repo["description"] == ""


class TestAuthorsContext:
    """Test authors context building."""

    def test_authors_aggregation(self):
        """Test authors are aggregated across repositories."""
        data = {
            "repositories": [
                {
                    "name": "repo1",
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 50}
                    ],
                },
                {
                    "name": "repo2",
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 30},
                        {"name": "Bob", "email": "bob@example.com", "commit_count": 20},
                    ],
                },
            ]
        }

        builder = RenderContextBuilder(data)
        authors = builder._build_authors_context()

        assert len(authors) == 2

        # Alice should have combined commits
        alice = next(a for a in authors if a["email"] == "alice@example.com")
        assert alice["total_commits"] == 80  # 50 + 30
        assert alice["repos_count"] == 2
        assert set(alice["repos"]) == {"repo1", "repo2"}

        # Bob should have single repo
        bob = next(a for a in authors if a["email"] == "bob@example.com")
        assert bob["total_commits"] == 20
        assert bob["repos_count"] == 1
        assert bob["repos"] == ["repo2"]

    def test_authors_sorted_by_commits(self):
        """Test authors are sorted by total commits descending."""
        data = {
            "repositories": [
                {
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 50},
                        {"name": "Bob", "email": "bob@example.com", "commit_count": 150},
                        {"name": "Charlie", "email": "charlie@example.com", "commit_count": 100},
                    ]
                }
            ]
        }

        builder = RenderContextBuilder(data)
        authors = builder._build_authors_context()

        assert authors[0]["email"] == "bob@example.com"  # 150 commits
        assert authors[1]["email"] == "charlie@example.com"  # 100 commits
        assert authors[2]["email"] == "alice@example.com"  # 50 commits

    def test_authors_skips_missing_email(self):
        """Test authors without email are skipped."""
        data = {
            "repositories": [
                {
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 50},
                        {"name": "No Email", "commit_count": 30},  # Missing email
                        {"name": "Null Email", "email": None, "commit_count": 20},  # Null email
                    ]
                }
            ]
        }

        builder = RenderContextBuilder(data)
        authors = builder._build_authors_context()

        assert len(authors) == 1
        assert authors[0]["email"] == "alice@example.com"

    def test_authors_repos_sorted(self):
        """Test author's repos list is sorted."""
        data = {
            "repositories": [
                {
                    "name": "zebra",
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 10}
                    ],
                },
                {
                    "name": "alpha",
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 10}
                    ],
                },
                {
                    "name": "beta",
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 10}
                    ],
                },
            ]
        }

        builder = RenderContextBuilder(data)
        authors = builder._build_authors_context()

        assert authors[0]["repos"] == ["alpha", "beta", "zebra"]

    def test_authors_default_commit_count(self):
        """Test authors handle missing commit_count."""
        data = {
            "repositories": [
                {
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com"}  # No commit_count
                    ]
                }
            ]
        }

        builder = RenderContextBuilder(data)
        authors = builder._build_authors_context()

        assert authors[0]["total_commits"] == 0


class TestWorkflowsContext:
    """Test workflows context building."""

    def test_workflows_aggregation(self):
        """Test workflows are aggregated across repositories."""
        data = {
            "repositories": [
                {
                    "name": "repo1",
                    "workflows": [
                        {"name": "CI", "status": "success", "state": "active", "url": "http://ci1"}
                    ],
                },
                {
                    "name": "repo2",
                    "workflows": [
                        {
                            "name": "Deploy",
                            "status": "failure",
                            "state": "active",
                            "url": "http://deploy",
                        }
                    ],
                },
            ]
        }

        builder = RenderContextBuilder(data)
        workflows = builder._build_workflows_context()

        assert workflows["total_workflows"] == 2
        assert len(workflows["workflows"]) == 2
        assert workflows["repos_with_ci"] == 2

    def test_workflows_status_counts(self):
        """Test workflow status counting."""
        data = {
            "repositories": [
                {
                    "workflows": [
                        {"name": "CI1", "status": "success"},
                        {"name": "CI2", "status": "success"},
                        {"name": "CI3", "status": "failure"},
                        {"name": "CI4", "status": "pending"},
                    ]
                }
            ]
        }

        builder = RenderContextBuilder(data)
        workflows = builder._build_workflows_context()

        assert workflows["status_counts"]["success"] == 2
        assert workflows["status_counts"]["failure"] == 1
        assert workflows["status_counts"]["pending"] == 1

    def test_workflows_default_status(self):
        """Test workflows handle missing status."""
        data = {
            "repositories": [
                {
                    "workflows": [
                        {"name": "CI"}  # Missing status and state
                    ]
                }
            ]
        }

        builder = RenderContextBuilder(data)
        workflows = builder._build_workflows_context()

        wf = workflows["workflows"][0]
        assert wf["status"] == "unknown"
        assert wf["state"] == "unknown"
        assert wf["url"] == ""

    def test_workflows_repos_with_ci(self):
        """Test counting repos with CI."""
        data = {
            "repositories": [
                {"name": "repo1", "workflows": [{"name": "CI"}]},
                {"name": "repo2", "workflows": [{"name": "CI"}]},
                {"name": "repo3", "workflows": []},
                {"name": "repo4"},  # No workflows key
            ]
        }

        builder = RenderContextBuilder(data)
        workflows = builder._build_workflows_context()

        assert workflows["repos_with_ci"] == 2


class TestMetadataContext:
    """Test metadata context building."""

    def test_metadata_generated_at(self):
        """Test metadata includes generation timestamp."""
        data = {"project_name": "Test"}
        builder = RenderContextBuilder(data)

        metadata = builder._build_metadata_context()

        assert "generated_at" in metadata
        assert "generated_at_human" in metadata

        # Should be valid ISO format
        datetime.fromisoformat(metadata["generated_at"])

    def test_metadata_version(self):
        """Test metadata includes generator version."""
        data = {"version": "1.2.3"}
        builder = RenderContextBuilder(data)

        metadata = builder._build_metadata_context()

        assert metadata["generator_version"] == "1.2.3"

    def test_metadata_default_version(self):
        """Test metadata uses default for missing version."""
        data = {}
        builder = RenderContextBuilder(data)

        metadata = builder._build_metadata_context()

        assert metadata["generator_version"] == "unknown"

    def test_metadata_report_format(self):
        """Test metadata includes report format."""
        data = {}
        builder = RenderContextBuilder(data)

        metadata = builder._build_metadata_context()

        assert metadata["report_format"] == "modern"


class TestTimeWindowsContext:
    """Test time windows context building."""

    def test_time_windows_enrichment(self):
        """Test time windows are enriched properly."""
        data = {
            "time_windows": [
                {
                    "name": "Last 30 days",
                    "start_date": "2024-12-01",
                    "end_date": "2025-01-01",
                    "total_commits": 100,
                    "active_authors": 5,
                }
            ]
        }

        builder = RenderContextBuilder(data)
        windows = builder._build_time_windows_context()

        assert len(windows) == 1
        assert windows[0]["name"] == "Last 30 days"
        assert windows[0]["start_date"] == "2024-12-01"
        assert windows[0]["end_date"] == "2025-01-01"
        assert windows[0]["total_commits"] == 100
        assert windows[0]["active_authors"] == 5

    def test_time_windows_default_values(self):
        """Test time windows use default values."""
        data = {
            "time_windows": [{}]  # Empty window
        }

        builder = RenderContextBuilder(data)
        windows = builder._build_time_windows_context()

        assert windows[0]["name"] == "Unknown"
        assert windows[0]["total_commits"] == 0
        assert windows[0]["active_authors"] == 0

    def test_time_windows_missing(self):
        """Test missing time_windows returns empty list."""
        data = {}
        builder = RenderContextBuilder(data)

        windows = builder._build_time_windows_context()

        assert windows == []


class TestDateRangeCalculation:
    """Test date range calculation."""

    def test_date_range_with_commits(self):
        """Test date range calculation with commit dates."""
        data = {
            "repositories": [
                {"first_commit_date": "2024-01-01", "last_commit_date": "2024-06-01"},
                {"first_commit_date": "2023-01-01", "last_commit_date": "2025-01-01"},
            ]
        }

        builder = RenderContextBuilder(data)
        date_range = builder._calculate_date_range()

        assert date_range["start_date"] == "2023-01-01"
        assert date_range["end_date"] == "2025-01-01"

    def test_date_range_no_dates(self):
        """Test date range when no dates available."""
        data = {"repositories": [{}]}
        builder = RenderContextBuilder(data)

        date_range = builder._calculate_date_range()

        assert date_range["start_date"] is None
        assert date_range["end_date"] is None

    def test_date_range_partial_dates(self):
        """Test date range with partial dates."""
        data = {
            "repositories": [
                {"first_commit_date": "2024-01-01"},
                {"last_commit_date": "2025-01-01"},
            ]
        }

        builder = RenderContextBuilder(data)
        date_range = builder._calculate_date_range()

        assert date_range["start_date"] == "2024-01-01"
        assert date_range["end_date"] == "2025-01-01"


class TestValidation:
    """Test context validation."""

    def test_validate_with_required_fields(self):
        """Test validation passes with required fields."""
        data = {"project_name": "Test Project", "repositories": []}
        builder = RenderContextBuilder(data)

        assert builder.validate() is True

    def test_validate_missing_project_name(self):
        """Test validation fails without project_name."""
        data = {"repositories": []}
        builder = RenderContextBuilder(data)

        assert builder.validate() is False

    def test_validate_missing_repositories(self):
        """Test validation fails without repositories."""
        data = {"project_name": "Test"}
        builder = RenderContextBuilder(data)

        assert builder.validate() is False

    def test_validate_empty_data(self):
        """Test validation fails with empty data."""
        builder = RenderContextBuilder({})

        assert builder.validate() is False

    def test_validate_logs_errors(self, caplog):
        """Test validation logs errors for missing keys."""
        import logging

        data = {}
        builder = RenderContextBuilder(data)

        with caplog.at_level(logging.ERROR):
            result = builder.validate()

        assert result is False
        assert "Missing required key" in caplog.text


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_repository_list(self):
        """Test handling of empty repository list."""
        data = {"project_name": "Empty", "repositories": []}
        builder = RenderContextBuilder(data)

        context = builder.build()

        assert context["project"]["total_repos"] == 0
        assert context["summary"]["total_commits"] == 0
        assert context["repositories"] == []
        assert context["authors"] == []

    def test_repository_without_authors(self):
        """Test handling repository without authors."""
        data = {
            "repositories": [
                {"name": "repo1", "total_commits": 100}  # No authors key
            ]
        }

        builder = RenderContextBuilder(data)
        context = builder.build()

        repo = context["repositories"][0]
        assert repo["total_authors"] == 0

    def test_large_dataset(self):
        """Test handling large dataset."""
        # Create 100 repos with 10 unique authors each
        repos = []
        for i in range(100):
            authors = [
                {
                    "name": f"Author{i}_{j}",
                    "email": f"author{i}_{j}@example.com",
                    "commit_count": 10,
                }
                for j in range(10)
            ]
            repos.append({"name": f"repo{i}", "total_commits": 100, "authors": authors})

        data = {"project_name": "Large", "repositories": repos}
        builder = RenderContextBuilder(data)

        context = builder.build()

        assert context["project"]["total_repos"] == 100
        assert context["project"]["total_commits"] == 10000
        assert len(context["authors"]) == 1000  # 100 repos * 10 unique authors each

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        data = {
            "project_name": "测试项目 🚀",
            "repositories": [
                {
                    "name": "repo-émoji-👍",
                    "description": "Repository with émojis and ñoñ-ASCII çhãrs",
                    "authors": [
                        {"name": "Jöhn Döe", "email": "jöhn@éxample.com", "commit_count": 10}
                    ],
                }
            ],
        }

        builder = RenderContextBuilder(data)
        context = builder.build()

        assert context["project"]["name"] == "测试项目 🚀"
        assert context["repositories"][0]["name"] == "repo-émoji-👍"
        assert context["authors"][0]["name"] == "Jöhn Döe"

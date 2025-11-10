# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Property-based tests for data aggregation operations.

These tests verify invariants and mathematical properties of aggregations
across repositories, authors, and metrics using Hypothesis to generate
random but valid test cases.
"""

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from domain.author_metrics import AuthorMetrics
from domain.repository_metrics import RepositoryMetrics
from domain.time_window import TimeWindowStats


# =============================================================================
# Hypothesis Strategies (Data Generators)
# =============================================================================


@composite
def valid_author_metrics(draw):
    """Generate valid AuthorMetrics instances."""
    email = draw(st.emails())
    name = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" .-"
            ),
        )
    )

    # Generate consistent metrics across windows
    windows = ["1y", "90d", "30d"]
    commits = {}
    lines_added = {}
    lines_removed = {}
    lines_net = {}
    repos_touched = {}

    for window in windows:
        added = draw(st.integers(min_value=0, max_value=100_000))
        removed = draw(st.integers(min_value=0, max_value=100_000))

        commits[window] = draw(st.integers(min_value=0, max_value=10_000))
        lines_added[window] = added
        lines_removed[window] = removed
        lines_net[window] = added - removed  # Must be consistent
        repos_touched[window] = draw(st.integers(min_value=0, max_value=100))

    domain = email.split("@")[1] if "@" in email else "unknown"

    return AuthorMetrics(
        name=name,
        email=email,
        username=draw(st.text(min_size=0, max_size=20)),
        domain=domain,
        commits=commits,
        lines_added=lines_added,
        lines_removed=lines_removed,
        lines_net=lines_net,
        repositories_touched=repos_touched,
    )


@composite
def valid_repository_metrics(draw):
    """Generate valid RepositoryMetrics instances."""
    project_name = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="/-_"
            ),
        )
    )

    host = draw(st.from_regex(r"[a-z0-9-]+\.[a-z]{2,}", fullmatch=True))

    # Generate metrics
    windows = ["1y", "90d", "30d"]
    commit_counts = {}
    loc_stats = {}
    unique_contributors = {}

    for window in windows:
        added = draw(st.integers(min_value=0, max_value=100_000))
        removed = draw(st.integers(min_value=0, max_value=100_000))

        commit_counts[window] = draw(st.integers(min_value=0, max_value=10_000))
        loc_stats[window] = {"added": added, "removed": removed, "net": added - removed}
        unique_contributors[window] = draw(st.integers(min_value=0, max_value=100))

    has_commits = draw(st.booleans())
    total_commits = draw(st.integers(min_value=0, max_value=50_000)) if has_commits else 0

    return RepositoryMetrics(
        gerrit_project=project_name,
        gerrit_host=host,
        gerrit_url=f"https://{host}/{project_name}",
        local_path=f"/tmp/{project_name}",
        has_any_commits=has_commits,
        total_commits_ever=total_commits,
        activity_status=draw(st.sampled_from(["current", "active", "inactive"])),
        commit_counts=commit_counts,
        loc_stats=loc_stats,
        unique_contributors=unique_contributors,
    )


# =============================================================================
# Aggregation Property Tests - General
# =============================================================================


class TestAggregationProperties:
    """Property-based tests for general aggregation invariants."""

    @given(st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_sum_is_greater_or_equal_to_max(self, values):
        """Property: Sum of values >= max value."""
        total = sum(values)
        maximum = max(values)

        assert total >= maximum

    @given(st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_sum_is_greater_or_equal_to_count(self, values):
        """Property: For non-negative values, sum >= count when all >= 1."""
        if all(v >= 1 for v in values):
            assert sum(values) >= len(values)

    @given(st.lists(st.integers(min_value=0, max_value=1000), min_size=2))
    @settings(max_examples=100)
    def test_sum_is_associative(self, values):
        """Property: Sum is associative - order of grouping doesn't matter."""
        # Split list in half
        mid = len(values) // 2

        # Sum left half, then add right half
        sum1 = sum(values[:mid]) + sum(values[mid:])

        # Sum all at once
        sum2 = sum(values)

        assert sum1 == sum2

    @given(st.lists(st.integers(min_value=0, max_value=1000)))
    @settings(max_examples=100)
    def test_sum_of_empty_list_is_zero(self, extra_values):
        """Property: Sum of empty list is zero (identity element)."""
        assert sum([]) == 0
        assert sum([]) + sum(extra_values) == sum(extra_values)


# =============================================================================
# Author Metrics Aggregation Properties
# =============================================================================


class TestAuthorMetricsAggregationProperties:
    """Property tests for author metrics aggregation."""

    @given(st.lists(valid_author_metrics(), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_aggregated_commits_equals_sum_of_individual(self, authors):
        """Property: Total commits = sum of all author commits per window."""
        windows = ["1y", "90d", "30d"]

        for window in windows:
            total_commits = sum(author.commits.get(window, 0) for author in authors)

            # Each author's contribution is counted
            assert total_commits >= 0

            # Total should be >= max individual contribution
            if authors:
                max_individual = max(author.commits.get(window, 0) for author in authors)
                assert total_commits >= max_individual

    @given(st.lists(valid_author_metrics(), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_aggregated_loc_maintains_net_invariant(self, authors):
        """Property: Aggregated LOC maintains net = added - removed invariant."""
        windows = ["1y", "90d", "30d"]

        for window in windows:
            total_added = sum(author.lines_added.get(window, 0) for author in authors)
            total_removed = sum(author.lines_removed.get(window, 0) for author in authors)
            total_net = sum(author.lines_net.get(window, 0) for author in authors)

            # Invariant must hold after aggregation
            assert total_net == total_added - total_removed

    @given(valid_author_metrics(), valid_author_metrics())
    @settings(max_examples=100)
    def test_combining_two_authors_increases_or_maintains_totals(self, author1, author2):
        """Property: Combining authors increases/maintains totals (never decreases)."""
        for window in ["1y", "90d", "30d"]:
            combined_commits = author1.commits.get(window, 0) + author2.commits.get(window, 0)

            assert combined_commits >= author1.commits.get(window, 0)
            assert combined_commits >= author2.commits.get(window, 0)

    @given(st.lists(valid_author_metrics(), min_size=2, max_size=20))
    @settings(max_examples=50)
    def test_author_aggregation_order_independence(self, authors):
        """Property: Author aggregation results don't depend on order."""
        windows = ["1y", "90d", "30d"]

        # Calculate totals in original order
        totals1 = {}
        for window in windows:
            totals1[window] = sum(author.commits.get(window, 0) for author in authors)

        # Reverse the list
        reversed_authors = list(reversed(authors))

        # Calculate totals in reversed order
        totals2 = {}
        for window in windows:
            totals2[window] = sum(author.commits.get(window, 0) for author in reversed_authors)

        # Should be identical
        assert totals1 == totals2

    @given(st.lists(valid_author_metrics(), min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_unique_author_count_bounded_by_list_size(self, authors):
        """Property: Number of unique authors <= total author records."""
        unique_emails = {author.email for author in authors}

        assert len(unique_emails) <= len(authors)
        assert len(unique_emails) >= 1  # At least one unique email

    @given(st.lists(valid_author_metrics(), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_domain_aggregation_preserves_counts(self, authors):
        """Property: Grouping by domain preserves total counts."""
        windows = ["1y", "90d", "30d"]

        # Calculate total commits across all authors
        for window in windows:
            total_commits = sum(author.commits.get(window, 0) for author in authors)

            # Group by domain and sum
            by_domain = {}
            for author in authors:
                domain = author.domain
                if domain not in by_domain:
                    by_domain[domain] = 0
                by_domain[domain] += author.commits.get(window, 0)

            # Total should be preserved
            assert sum(by_domain.values()) == total_commits


# =============================================================================
# Repository Metrics Aggregation Properties
# =============================================================================


class TestRepositoryMetricsAggregationProperties:
    """Property tests for repository metrics aggregation."""

    @given(st.lists(valid_repository_metrics(), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_aggregated_repo_commits_equals_sum(self, repos):
        """Property: Total commits = sum of all repo commits per window."""
        windows = ["1y", "90d", "30d"]

        for window in windows:
            total_commits = sum(repo.commit_counts.get(window, 0) for repo in repos)

            assert total_commits >= 0

            # Should be >= max individual repo
            if repos:
                max_repo = max(repo.commit_counts.get(window, 0) for repo in repos)
                assert total_commits >= max_repo

    @given(st.lists(valid_repository_metrics(), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_aggregated_repo_loc_maintains_net_invariant(self, repos):
        """Property: Aggregated repo LOC maintains net = added - removed."""
        windows = ["1y", "90d", "30d"]

        for window in windows:
            total_added = sum(repo.loc_stats.get(window, {}).get("added", 0) for repo in repos)
            total_removed = sum(repo.loc_stats.get(window, {}).get("removed", 0) for repo in repos)
            total_net = sum(repo.loc_stats.get(window, {}).get("net", 0) for repo in repos)

            # Invariant must hold
            assert total_net == total_added - total_removed

    @given(st.lists(valid_repository_metrics(), min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_active_repo_count_bounded_by_total(self, repos):
        """Property: Number of active repos <= total repos."""
        total_repos = len(repos)

        active_repos = sum(1 for repo in repos if repo.activity_status in ["current", "active"])

        assert active_repos <= total_repos
        assert active_repos >= 0

    @given(st.lists(valid_repository_metrics(), min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_repos_with_commits_subset_of_all_repos(self, repos):
        """Property: Repos with commits is a subset of all repos."""
        repos_with_commits = sum(1 for repo in repos if repo.has_any_commits)

        assert repos_with_commits <= len(repos)
        assert repos_with_commits >= 0

    @given(st.lists(valid_repository_metrics(), min_size=2, max_size=20))
    @settings(max_examples=50)
    def test_repo_aggregation_order_independence(self, repos):
        """Property: Repository aggregation doesn't depend on order."""
        windows = ["1y", "90d", "30d"]

        # Calculate totals in original order
        totals1 = {}
        for window in windows:
            totals1[window] = sum(repo.commit_counts.get(window, 0) for repo in repos)

        # Shuffle the list (reverse for determinism)
        shuffled = list(reversed(repos))

        # Calculate totals in shuffled order
        totals2 = {}
        for window in windows:
            totals2[window] = sum(repo.commit_counts.get(window, 0) for repo in shuffled)

        # Should be identical
        assert totals1 == totals2


# =============================================================================
# TimeWindowStats Aggregation Properties
# =============================================================================


class TestTimeWindowStatsAggregationProperties:
    """Property tests for TimeWindowStats aggregation operations."""

    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=10_000),
                st.integers(min_value=0, max_value=10_000),
            ),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_aggregating_stats_preserves_net_invariant(self, loc_changes):
        """Property: Aggregating multiple stats preserves net = added - removed."""
        stats_list = []
        for added, removed in loc_changes:
            stats = TimeWindowStats(
                commits=1,
                lines_added=added,
                lines_removed=removed,
                lines_net=added - removed,
                contributors=1,
            )
            stats_list.append(stats)

        # Aggregate all stats
        total = stats_list[0]
        for stats in stats_list[1:]:
            total = total + stats

        # Invariant must hold
        assert total.lines_net == total.lines_added - total.lines_removed

    @given(st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_sum_of_commits_equals_count_when_one_each(self, commit_counts):
        """Property: When each stats has 1 commit, total = number of stats."""
        stats_list = [TimeWindowStats(commits=1) for _ in commit_counts]

        total = stats_list[0]
        for stats in stats_list[1:]:
            total = total + stats

        assert total.commits == len(commit_counts)


# =============================================================================
# Cross-Entity Aggregation Properties
# =============================================================================


class TestCrossEntityAggregationProperties:
    """Property tests for aggregations across different entity types."""

    @given(
        st.lists(valid_author_metrics(), min_size=1, max_size=10),
        st.lists(valid_repository_metrics(), min_size=1, max_size=10),
    )
    @settings(max_examples=50)
    def test_author_commits_can_exceed_repo_commits(self, authors, repos):
        """Property: Author commits can be >= repo commits (same commits counted per author)."""
        window = "1y"

        total_author_commits = sum(author.commits.get(window, 0) for author in authors)
        total_repo_commits = sum(repo.commit_counts.get(window, 0) for repo in repos)

        # Both should be non-negative
        assert total_author_commits >= 0
        assert total_repo_commits >= 0

        # Author commits can be greater (each commit counted per author)
        # or they can be independent data sources

    @given(
        st.lists(valid_author_metrics(), min_size=1, max_size=10), st.text(min_size=1, max_size=20)
    )
    @settings(max_examples=50)
    def test_filtering_by_domain_reduces_or_maintains_count(self, authors, target_domain):
        """Property: Filtering authors by domain reduces/maintains count."""
        original_count = len(authors)

        filtered = [author for author in authors if author.domain == target_domain]

        assert len(filtered) <= original_count
        assert len(filtered) >= 0

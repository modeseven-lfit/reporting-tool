# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Render Context Builder for Report Generation.

Separates data preparation from rendering logic, making context building
testable and reusable across different output formats.

Phase 8: Renderer Modernization
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import logging


class RenderContextBuilder:
    """
    Build rendering context from analysis data.

    Transforms raw analysis results into a structured context suitable
    for template rendering. Handles data validation, normalization, and
    enrichment.

    Example:
        >>> builder = RenderContextBuilder(analysis_data)
        >>> context = builder.build()
        >>> # context now contains all data needed for templates
    """

    def __init__(self, analysis_data: Dict[str, Any]):
        """
        Initialize context builder.

        Args:
            analysis_data: Raw analysis results from repository analysis
        """
        self.data = analysis_data
        self.logger = logging.getLogger(__name__)

    def build(self) -> Dict[str, Any]:
        """
        Build complete rendering context.

        Returns:
            Dictionary with all context data for templates:
                - project: Project-level metadata
                - summary: Summary statistics
                - repositories: Repository details
                - authors: Author metrics
                - workflows: CI/CD workflow information
                - metadata: Generation metadata
                - time_windows: Time-based metrics
        """
        return {
            'project': self._build_project_context(),
            'summary': self._build_summary_context(),
            'repositories': self._build_repositories_context(),
            'authors': self._build_authors_context(),
            'workflows': self._build_workflows_context(),
            'metadata': self._build_metadata_context(),
            'time_windows': self._build_time_windows_context(),
        }

    def _build_project_context(self) -> Dict[str, Any]:
        """
        Extract project-level information.

        Returns:
            Project context with name, totals, and high-level stats
        """
        repos = self.data.get('repositories', [])

        return {
            'name': self.data.get('project_name', 'Unknown Project'),
            'total_repos': len(repos),
            'active_repos': sum(1 for r in repos if r.get('active', False)),
            'total_commits': sum(r.get('total_commits', 0) for r in repos),
            'total_authors': len(set(
                a.get('email') for r in repos
                for a in r.get('authors', [])
                if a.get('email')
            )),
            'date_range': self._calculate_date_range(),
        }

    def _build_summary_context(self) -> Dict[str, Any]:
        """
        Build summary statistics.

        Returns:
            Aggregated metrics across all repositories
        """
        repos = self.data.get('repositories', [])

        total_commits = sum(r.get('total_commits', 0) for r in repos)
        total_authors = len(set(
            a.get('email') for r in repos
            for a in r.get('authors', [])
            if a.get('email')
        ))

        return {
            'total_repositories': len(repos),
            'total_commits': total_commits,
            'total_authors': total_authors,
            'avg_commits_per_repo': total_commits / len(repos) if repos else 0,
            'avg_commits_per_author': total_commits / total_authors if total_authors else 0,
        }

    def _build_repositories_context(self) -> List[Dict[str, Any]]:
        """
        Build repository list with enriched data.

        Returns:
            List of repository dictionaries with normalized data
        """
        repos = self.data.get('repositories', [])

        enriched_repos = []
        for repo in repos:
            enriched_repos.append({
                'name': repo.get('name', 'Unknown'),
                'path': repo.get('path', ''),
                'total_commits': repo.get('total_commits', 0),
                'total_authors': len(repo.get('authors', [])),
                'active': repo.get('active', False),
                'last_commit_date': repo.get('last_commit_date'),
                'first_commit_date': repo.get('first_commit_date'),
                'primary_language': repo.get('primary_language', 'Unknown'),
                'workflows': repo.get('workflows', []),
                'has_ci': len(repo.get('workflows', [])) > 0,
                'description': repo.get('description', ''),
            })

        # Sort by commit count (most active first)
        enriched_repos.sort(key=lambda r: r['total_commits'], reverse=True)

        return enriched_repos

    def _build_authors_context(self) -> List[Dict[str, Any]]:
        """
        Build author list with aggregated metrics.

        Returns:
            List of author dictionaries with contribution metrics
        """
        # Aggregate authors across all repos
        author_metrics: Dict[str, Dict[str, Any]] = {}

        for repo in self.data.get('repositories', []):
            for author in repo.get('authors', []):
                email = author.get('email')
                if not email:
                    continue

                if email not in author_metrics:
                    author_metrics[email] = {
                        'name': author.get('name', 'Unknown'),
                        'email': email,
                        'total_commits': 0,
                        'repos_contributed': set(),
                    }

                author_metrics[email]['total_commits'] += author.get('commit_count', 0)
                author_metrics[email]['repos_contributed'].add(repo.get('name'))

        # Convert to list and format
        authors = []
        for email, metrics in author_metrics.items():
            authors.append({
                'name': metrics['name'],
                'email': email,
                'total_commits': metrics['total_commits'],
                'repos_count': len(metrics['repos_contributed']),
                'repos': sorted(metrics['repos_contributed']),
            })

        # Sort by commit count (top contributors first)
        authors.sort(key=lambda a: a['total_commits'], reverse=True)

        return authors

    def _build_workflows_context(self) -> Dict[str, Any]:
        """
        Build CI/CD workflow summary.

        Returns:
            Workflow statistics and status
        """
        all_workflows = []

        for repo in self.data.get('repositories', []):
            for workflow in repo.get('workflows', []):
                all_workflows.append({
                    'repo': repo.get('name'),
                    'name': workflow.get('name'),
                    'status': workflow.get('status', 'unknown'),
                    'state': workflow.get('state', 'unknown'),
                    'url': workflow.get('url', ''),
                })

        # Aggregate status
        status_counts: Dict[str, int] = {}
        for wf in all_workflows:
            status = wf['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            'total_workflows': len(all_workflows),
            'workflows': all_workflows,
            'status_counts': status_counts,
            'repos_with_ci': sum(
                1 for r in self.data.get('repositories', [])
                if len(r.get('workflows', [])) > 0
            ),
        }

    def _build_metadata_context(self) -> Dict[str, Any]:
        """
        Build report generation metadata.

        Returns:
            Metadata about report generation
        """
        return {
            'generated_at': datetime.now().isoformat(),
            'generated_at_human': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generator_version': self.data.get('version', 'unknown'),
            'report_format': 'modern',
        }

    def _build_time_windows_context(self) -> List[Dict[str, Any]]:
        """
        Build time window statistics.

        Returns:
            List of time window periods with metrics
        """
        time_windows = self.data.get('time_windows', [])

        enriched_windows = []
        for window in time_windows:
            enriched_windows.append({
                'name': window.get('name', 'Unknown'),
                'start_date': window.get('start_date'),
                'end_date': window.get('end_date'),
                'total_commits': window.get('total_commits', 0),
                'active_authors': window.get('active_authors', 0),
            })

        return enriched_windows

    def _calculate_date_range(self) -> Dict[str, Optional[str]]:
        """
        Calculate overall date range across all repositories.

        Returns:
            Dictionary with start_date and end_date
        """
        all_dates = []

        for repo in self.data.get('repositories', []):
            if repo.get('first_commit_date'):
                all_dates.append(repo['first_commit_date'])
            if repo.get('last_commit_date'):
                all_dates.append(repo['last_commit_date'])

        if not all_dates:
            return {'start_date': None, 'end_date': None}

        return {
            'start_date': min(all_dates),
            'end_date': max(all_dates),
        }

    def validate(self) -> bool:
        """
        Validate that context has required data.

        Returns:
            True if valid, False otherwise
        """
        required_keys = ['project_name', 'repositories']

        for key in required_keys:
            if key not in self.data:
                self.logger.error(f"Missing required key in analysis data: {key}")
                return False

        return True

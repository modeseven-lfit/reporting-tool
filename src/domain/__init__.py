"""
Domain models for the repository reporting system.

This package contains dataclasses representing core business entities:
- RepositoryMetrics: Metrics for a single repository
- AuthorMetrics: Contributor statistics
- OrganizationMetrics: Organization-level aggregations
- WorkflowStatus: CI/CD workflow status information
- TimeWindow: Time period definitions

All domain models include:
- Type-safe attribute access
- Validation at construction
- Serialization to dict for JSON output
- Backwards compatibility with legacy dict-based code
"""

from .author_metrics import AuthorMetrics
from .organization_metrics import OrganizationMetrics
from .repository_metrics import RepositoryMetrics
from .time_window import TimeWindow, TimeWindowStats
from .workflow_status import WorkflowStatus

__all__ = [
    "AuthorMetrics",
    "OrganizationMetrics",
    "RepositoryMetrics",
    "TimeWindow",
    "TimeWindowStats",
    "WorkflowStatus",
]

# Version for domain model schema evolution
DOMAIN_MODEL_VERSION = "1.0.0"

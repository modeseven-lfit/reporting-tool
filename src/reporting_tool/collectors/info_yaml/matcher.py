# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Committer-to-author matcher module.

Provides fuzzy matching logic to match INFO.yaml committers to Git authors
based on email addresses and names.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class CommitterMatcher:
    """
    Matches INFO.yaml committers to Git authors.

    Uses email-based matching as primary strategy, with fallback to
    name-based fuzzy matching for cases where email doesn't match.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the matcher.

        Args:
            config: Optional configuration for matching behavior
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

        # Matching configuration
        self.email_match_enabled = self.config.get("email_match_enabled", True)
        self.name_match_enabled = self.config.get("name_match_enabled", True)
        self.case_sensitive = self.config.get("case_sensitive", False)

        # Build normalization patterns
        self._build_normalization_patterns()

    def _build_normalization_patterns(self) -> None:
        """Build regex patterns for email and name normalization."""
        # Email normalization: remove common patterns
        self.email_patterns = [
            (re.compile(r"\+[^@]+@"), "@"),  # Remove plus-addressing
            (re.compile(r"\."), ""),  # Remove dots (gmail style)
        ]

        # Name normalization patterns
        self.name_patterns = [
            (re.compile(r"[^\w\s]"), ""),  # Remove non-alphanumeric except spaces
            (re.compile(r"\s+"), " "),  # Normalize whitespace
        ]

    def match_committer_to_authors(
        self,
        committer_email: str,
        committer_name: str,
        authors: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best matching Git author for a committer.

        Tries email matching first, then falls back to name matching.

        Args:
            committer_email: Email from INFO.yaml
            committer_name: Name from INFO.yaml
            authors: List of Git author dictionaries with 'email' and 'name'

        Returns:
            Best matching author dict or None if no match found
        """
        if not authors:
            return None

        # Try email match first (most reliable)
        if self.email_match_enabled and committer_email:
            email_match = self._match_by_email(committer_email, authors)
            if email_match:
                self.logger.debug(
                    f"Matched '{committer_name}' via email: {committer_email}"
                )
                return email_match

        # Fall back to name matching
        if self.name_match_enabled and committer_name:
            name_match = self._match_by_name(committer_name, authors)
            if name_match:
                self.logger.debug(
                    f"Matched '{committer_name}' via name to author: "
                    f"{name_match.get('name', 'Unknown')}"
                )
                return name_match

        # No match found
        self.logger.debug(f"No match found for committer: {committer_name}")
        return None

    def _match_by_email(
        self, committer_email: str, authors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Match committer by email address.

        Args:
            committer_email: Email to match
            authors: List of author dictionaries

        Returns:
            Matching author or None
        """
        if not committer_email:
            return None

        # Normalize committer email
        normalized_committer = self._normalize_email(committer_email)

        # Try exact match first
        for author in authors:
            author_email = author.get("email", "")
            if not author_email:
                continue

            normalized_author = self._normalize_email(author_email)

            if normalized_committer == normalized_author:
                return author

        return None

    def _match_by_name(
        self, committer_name: str, authors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Match committer by name with fuzzy matching.

        Args:
            committer_name: Name to match
            authors: List of author dictionaries

        Returns:
            Best matching author or None
        """
        if not committer_name:
            return None

        # Normalize committer name
        normalized_committer = self._normalize_name(committer_name)

        # Try exact match first
        for author in authors:
            author_name = author.get("name", "")
            if not author_name:
                continue

            normalized_author = self._normalize_name(author_name)

            if normalized_committer == normalized_author:
                return author

        # Try partial matches (last name, first name, etc.)
        return self._fuzzy_name_match(normalized_committer, authors)

    def _fuzzy_name_match(
        self, normalized_committer: str, authors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Perform fuzzy name matching.

        Tries various strategies:
        - Last name match
        - First + Last name match
        - Contains match

        Args:
            normalized_committer: Normalized committer name
            authors: List of author dictionaries

        Returns:
            Best matching author or None
        """
        committer_parts = normalized_committer.lower().split()
        if not committer_parts:
            return None

        # Extract first and last name
        committer_first = committer_parts[0] if len(committer_parts) > 0 else ""
        committer_last = committer_parts[-1] if len(committer_parts) > 0 else ""

        best_match = None
        best_score = 0.0

        for author in authors:
            author_name = author.get("name", "")
            if not author_name:
                continue

            normalized_author = self._normalize_name(author_name).lower()
            author_parts = normalized_author.split()

            if not author_parts:
                continue

            author_first = author_parts[0] if len(author_parts) > 0 else ""
            author_last = author_parts[-1] if len(author_parts) > 0 else ""

            score = 0.0

            # Score based on matching components
            if committer_last and committer_last == author_last:
                score += 2  # Last name match is strong

            if committer_first and committer_first == author_first:
                score += 1  # First name match is weaker (more common)

            # Substring matching as fallback
            if committer_last and committer_last in normalized_author:
                score += 0.5

            # Update best match if this is better
            if score > best_score and score >= 2:  # Require at least last name match
                best_match = author
                best_score = score

        return best_match

    def _normalize_email(self, email: str) -> str:
        """
        Normalize email address for matching.

        Args:
            email: Raw email address

        Returns:
            Normalized email address
        """
        if not email:
            return ""

        normalized = email.strip()

        # Convert to lowercase unless case-sensitive
        if not self.case_sensitive:
            normalized = normalized.lower()

        # Apply normalization patterns
        for pattern, replacement in self.email_patterns:
            normalized = pattern.sub(replacement, normalized)

        return normalized

    def _normalize_name(self, name: str) -> str:
        """
        Normalize name for matching.

        Args:
            name: Raw name

        Returns:
            Normalized name
        """
        if not name:
            return ""

        normalized = name.strip()

        # Apply normalization patterns
        for pattern, replacement in self.name_patterns:
            normalized = pattern.sub(replacement, normalized)

        # Normalize whitespace
        normalized = " ".join(normalized.split())

        # Convert to lowercase unless case-sensitive
        if not self.case_sensitive:
            normalized = normalized.lower()

        return normalized

    def match_committers_bulk(
        self,
        committers: List[Dict[str, str]],
        authors: List[Dict[str, Any]],
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Match multiple committers to authors in bulk.

        Args:
            committers: List of committer dictionaries with 'email' and 'name'
            authors: List of author dictionaries

        Returns:
            Dictionary mapping committer email to matched author (or None)
        """
        results = {}

        for committer in committers:
            email = committer.get("email", "")
            name = committer.get("name", "")

            if not email and not name:
                continue

            match = self.match_committer_to_authors(email, name, authors)
            key = email if email else name
            results[key] = match

        return results

    def get_match_statistics(
        self,
        committers: List[Dict[str, str]],
        authors: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """
        Get matching statistics for a set of committers.

        Args:
            committers: List of committer dictionaries
            authors: List of author dictionaries

        Returns:
            Dictionary with match statistics
        """
        stats = {
            "total_committers": len(committers),
            "matched": 0,
            "unmatched": 0,
            "email_matches": 0,
            "name_matches": 0,
        }

        for committer in committers:
            email = committer.get("email", "")
            name = committer.get("name", "")

            if not email and not name:
                stats["unmatched"] += 1
                continue

            # Try email match
            email_match = None
            if email:
                email_match = self._match_by_email(email, authors)
                if email_match:
                    stats["matched"] += 1
                    stats["email_matches"] += 1
                    continue

            # Try name match
            if name:
                name_match = self._match_by_name(name, authors)
                if name_match:
                    stats["matched"] += 1
                    stats["name_matches"] += 1
                    continue

            stats["unmatched"] += 1

        return stats


def match_committer_to_authors(
    committer_email: str,
    committer_name: str,
    authors: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to match a single committer to authors.

    Args:
        committer_email: Email from INFO.yaml
        committer_name: Name from INFO.yaml
        authors: List of Git author dictionaries

    Returns:
        Best matching author dict or None
    """
    matcher = CommitterMatcher()
    return matcher.match_committer_to_authors(committer_email, committer_name, authors)

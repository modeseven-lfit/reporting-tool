# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
GitHub API Client

Client for interacting with GitHub API to fetch workflow run status,
repository information, and other GitHub-related data.

Extracted from generate_reports.py as part of Phase 2 refactoring.
Enhanced with standardized error handling and response envelopes.
"""

import logging
import os
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    from cli.errors import ConfigurationError
    raise ConfigurationError(
        "httpx package is required for GitHub API client",
        suggestion="Install with: pip install httpx"
    )

from .base_client import (
    APIResponse,
    APIError,
    ErrorType,
    BaseAPIClient,
)


class GitHubAPIClient(BaseAPIClient):
    """
    Client for interacting with GitHub API to fetch workflow run status.

    Provides methods to:
    - List workflows for a repository
    - Get workflow run status
    - Get comprehensive workflow status summaries

    Uses standardized response envelope pattern for consistent error handling.
    """

    def __init__(
        self,
        token: str,
        timeout: float = 30.0,
        stats: Optional[Any] = None,
        use_envelope: bool = False
    ):
        """
        Initialize GitHub API client with token.

        Args:
            token: GitHub Personal Access Token
            timeout: Request timeout in seconds
            stats: Statistics tracker object
            use_envelope: If True, use new envelope pattern; if False, use legacy dicts
        """
        super().__init__(timeout=timeout, stats=stats)

        self.token = token
        self.base_url = "https://api.github.com"
        self.use_envelope = use_envelope

        # Create httpx client with authentication
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "repository-reports/1.0.0",
            },
        )

        self.logger = logging.getLogger(__name__)

    def close(self):
        """Close the httpx client and clean up resources."""
        if hasattr(self, 'client'):
            self.client.close()

    def _write_to_step_summary(self, message: str) -> None:
        """
        Write a message to GitHub Step Summary if running in GitHub Actions.

        Args:
            message: Message to write to step summary
        """
        step_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if step_summary_file:
            try:
                with open(step_summary_file, "a") as f:
                    f.write(message + "\n")
            except Exception as e:
                self.logger.debug(f"Could not write to GITHUB_STEP_SUMMARY: {e}")

    def get_repository_workflows(
        self,
        owner: str,
        repo: str
    ) -> List[Dict[str, Any]]:
        """
        Get all workflows for a repository.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name

        Returns:
            List of workflow dictionaries (empty list on error)
        """
        try:
            url = f"/repos/{owner}/{repo}/actions/workflows"
            response = self.client.get(url)

            if response.status_code == 401:
                self._record_error("github", 401)
                error_msg = (
                    f"❌ **GitHub API Authentication Failed** for `{owner}/{repo}`\n\n"
                    "The GitHub token is invalid or has expired.\n\n"
                    "**Action Required:** Update the `CLASSIC_READ_ONLY_PAT_TOKEN` secret "
                    "with a valid Classic Personal Access Token.\n"
                )
                self.logger.error(
                    f"❌ Error: GitHub API query returned error code: 401 for {owner}/{repo}"
                )
                self._write_to_step_summary(error_msg)
                return []

            elif response.status_code == 403:
                self._record_error("github", 403)
                error_msg = (
                    f"⚠️ **GitHub API Permission Denied** for `{owner}/{repo}`\n\n"
                )
                try:
                    error_body = response.json()
                    error_message = error_body.get("message", response.text)
                    error_msg += f"Error: {error_message}\n\n"
                except Exception:
                    error_msg += f"Error: {response.text}\n\n"

                error_msg += (
                    "**Likely Cause:** The GitHub token lacks required permissions.\n\n"
                    "**Required Scopes:**\n"
                    "- `repo` (or at least `repo:status`)\n"
                    "- `actions:read`\n\n"
                    "**To Fix:** Update your Personal Access Token with these scopes.\n"
                )
                self.logger.error(
                    f"❌ Error: GitHub API query returned error code: 403 for {owner}/{repo}"
                )
                self._write_to_step_summary(error_msg)
                return []

            elif response.status_code == 200:
                self._record_success("github")
                data = response.json()
                workflows = []

                for workflow in data.get("workflows", []):
                    # Build standardized workflow data structure
                    workflow_path = workflow.get("path", "")
                    source_url = None
                    if workflow_path and owner and repo:
                        # Convert workflow path to GitHub source URL
                        source_url = (
                            f"https://github.com/{owner}/{repo}/blob/master/{workflow_path}"
                        )

                    # Compute color from status for consistency with Jenkins jobs
                    workflow_state = workflow.get("state", "unknown")
                    color = self._compute_workflow_color_from_state(workflow_state)

                    workflows.append({
                        "id": workflow.get("id"),
                        "name": workflow.get("name"),
                        "path": workflow_path,
                        "state": workflow_state,
                        "status": "unknown",
                        "color": color,
                        "urls": {
                            "workflow_page": (
                                f"https://github.com/{owner}/{repo}/actions/workflows/"
                                f"{os.path.basename(workflow_path) if workflow_path else ''}"
                            ),
                            "source": source_url,
                            "badge": workflow.get("badge_url"),
                        },
                    })

                return workflows

            elif response.status_code == 404:
                self._record_error("github", 404)
                self.logger.debug(f"Repository {owner}/{repo} not found or no access")
                return []

            else:
                self._record_error("github", response.status_code)
                self.logger.warning(
                    f"❌ Error: GitHub API query returned error code: "
                    f"{response.status_code} for {owner}/{repo}"
                )
                return []

        except Exception as e:
            self._record_exception("github")
            self.logger.error(
                f"❌ Error: GitHub API query exception for {owner}/{repo}: {e}"
            )
            return []

    def get_workflow_runs_status(
        self,
        owner: str,
        repo: str,
        workflow_id: int,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get recent workflow runs for a specific workflow to determine status.

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID
            limit: Maximum number of runs to fetch

        Returns:
            Dictionary with workflow status information (empty dict on error)
        """
        try:
            url = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
            params = {"per_page": limit, "page": 1}

            response = self.client.get(url, params=params)

            if response.status_code == 401:
                self._record_error("github", 401)
                self.logger.error(
                    f"❌ Error: GitHub API query returned error code: 401 for "
                    f"workflow {workflow_id} in {owner}/{repo}"
                )
                return {"status": "auth_error", "last_run": None}

            elif response.status_code == 403:
                self._record_error("github", 403)
                self.logger.error(
                    f"❌ Error: GitHub API query returned error code: 403 for "
                    f"workflow {workflow_id} in {owner}/{repo}"
                )
                return {"status": "permission_error", "last_run": None}

            elif response.status_code == 200:
                self._record_success("github")
                data = response.json()
                runs = data.get("workflow_runs", [])

                if not runs:
                    return {"status": "no_runs", "last_run": None}

                # Get the most recent run
                latest_run = runs[0]

                # Compute standardized status from conclusion and run status
                conclusion = latest_run.get("conclusion", "unknown")
                run_status = latest_run.get("status", "unknown")
                standardized_status = self._compute_workflow_status(
                    conclusion, run_status
                )

                return {
                    "status": standardized_status,
                    "conclusion": conclusion,
                    "run_status": run_status,
                    "last_run": {
                        "id": latest_run.get("id"),
                        "number": latest_run.get("run_number"),
                        "created_at": latest_run.get("created_at"),
                        "updated_at": latest_run.get("updated_at"),
                        "html_url": latest_run.get("html_url"),
                        "head_branch": latest_run.get("head_branch"),
                        "head_sha": (
                            latest_run.get("head_sha")[:7]
                            if latest_run.get("head_sha")
                            else None
                        ),
                    },
                }

            else:
                self._record_error("github", response.status_code)
                self.logger.warning(
                    f"❌ Error: GitHub API query returned error code: "
                    f"{response.status_code} for workflow {workflow_id} runs"
                )
                return {"status": "api_error", "last_run": None}

        except Exception as e:
            self._record_exception("github")
            self.logger.error(
                f"Error fetching workflow runs for {owner}/{repo}/workflows/{workflow_id}: {e}"
            )
            return {"status": "error", "last_run": None}

    def get_repository_workflow_status_summary(
        self,
        owner: str,
        repo: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive workflow status summary for a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with comprehensive workflow status information
        """
        workflows = self.get_repository_workflows(owner, repo)

        if not workflows:
            return {
                "has_workflows": False,
                "workflows": [],
                "overall_status": "no_workflows",
                "github_owner": owner,
                "github_repo": repo,
            }

        workflow_statuses = []
        active_workflows = [w for w in workflows if w.get("state") == "active"]

        for workflow in active_workflows:
            workflow_id = workflow.get("id")
            if workflow_id:
                status_info = self.get_workflow_runs_status(owner, repo, workflow_id)

                # Merge workflow info with status info
                merged_workflow = {**workflow, **status_info}

                # Update URLs with source URL if not already present
                if "urls" in merged_workflow and workflow.get("path"):
                    if not merged_workflow["urls"].get("source"):
                        merged_workflow["urls"]["source"] = (
                            f"https://github.com/{owner}/{repo}/blob/master/"
                            f"{workflow['path']}"
                        )

                # Update color based on runtime status if available
                if "status" in status_info and status_info["status"]:
                    merged_workflow["color"] = (
                        self._compute_workflow_color_from_runtime_status(
                            status_info["status"]
                        )
                    )

                workflow_statuses.append(merged_workflow)

        # Determine overall status
        if not workflow_statuses:
            overall_status = "no_active_workflows"
        else:
            latest_statuses = [w.get("status") for w in workflow_statuses]
            if any(status == "failure" for status in latest_statuses):
                overall_status = "has_failures"
            elif any(status == "success" for status in latest_statuses):
                overall_status = "has_successes"
            else:
                overall_status = "unknown"

        return {
            "has_workflows": True,
            "total_workflows": len(workflows),
            "active_workflows": len(active_workflows),
            "workflows": workflow_statuses,
            "overall_status": overall_status,
            "github_owner": owner,
            "github_repo": repo,
        }

    def _compute_workflow_color_from_runtime_status(self, status: str) -> str:
        """
        Convert runtime workflow status to color for consistency with Jenkins jobs.

        Args:
            status: Runtime workflow status ("success", "failure", "building", etc.)

        Returns:
            Color string compatible with Jenkins color scheme
        """
        if not status:
            return "grey"

        status_lower = status.lower()

        # Map runtime statuses to colors (matching Jenkins scheme)
        status_color_map = {
            "success": "blue",
            "failure": "red",
            "building": "blue_anime",
            "in_progress": "blue_anime",
            "cancelled": "grey",
            "skipped": "grey",
            "unknown": "grey",
            "error": "red",
            "no_runs": "grey",
        }

        return status_color_map.get(status_lower, "grey")

    def _compute_workflow_status(self, conclusion: str, run_status: str) -> str:
        """
        Convert GitHub workflow conclusion and run status to standardized status.

        GitHub conclusions: success, failure, neutral, cancelled, skipped,
                          timed_out, action_required
        GitHub run statuses: queued, in_progress, completed

        Args:
            conclusion: GitHub workflow conclusion
            run_status: GitHub workflow run status

        Returns:
            Standardized status string
        """
        if not conclusion and not run_status:
            return "unknown"

        # Handle in-progress workflows first
        if run_status in ("queued", "in_progress"):
            return "building"

        # Handle completed workflows by conclusion
        if run_status == "completed":
            conclusion_map = {
                "success": "success",
                "failure": "failure",
                "neutral": "success",
                "cancelled": "cancelled",
                "skipped": "skipped",
                "timed_out": "failure",
                "action_required": "failure",
            }
            return conclusion_map.get(conclusion, "unknown")

        return "unknown"

    def _compute_workflow_color_from_state(self, state: str) -> str:
        """
        Convert GitHub workflow state to color for consistency with Jenkins jobs.

        Args:
            state: GitHub workflow state ("active", "disabled", etc.)

        Returns:
            Color string compatible with Jenkins color scheme
        """
        if not state:
            return "grey"

        state_lower = state.lower()

        # Map workflow states to colors
        state_color_map = {
            "active": "blue",
            "disabled": "grey",
            "deleted": "red",
        }

        return state_color_map.get(state_lower, "grey")

"""
GitHub issue tracker integration.
"""

import json
import subprocess
from typing import Dict, List

from .base import IssueInfo, IssueStatus, IssueTracker


class GitHubIssueEngine(IssueTracker):
    """GitHub Issues integration using 'gh' CLI."""

    def get_issue_info(self, issue_ids: List[str]) -> Dict[str, IssueInfo]:
        results = {}
        for issue_id in issue_ids:
            try:
                # We assume issue_id is just the number for GitHub
                if not issue_id.isdigit():
                    continue

                cmd = [
                    "gh",
                    "issue",
                    "view",
                    issue_id,
                    "--json",
                    "state,assignees,createdAt",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                data = json.loads(result.stdout)
                state = data.get("state", "").upper()

                status = IssueStatus.UNKNOWN
                if state == "OPEN":
                    status = IssueStatus.OPEN
                elif state in ["CLOSED", "MERGED"]:
                    status = IssueStatus.CLOSED

                assignees = data.get("assignees", [])
                assignee = assignees[0].get("login") if assignees else None
                created_at = data.get("createdAt")

                results[issue_id] = IssueInfo(
                    id=issue_id, status=status, assignee=assignee, created_at=created_at
                )
            except Exception:
                results[issue_id] = IssueInfo(id=issue_id, status=IssueStatus.UNKNOWN)
        return results

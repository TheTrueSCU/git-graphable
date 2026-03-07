"""
GitLab issue tracker integration using glab CLI.
"""

import json
import subprocess
from typing import Dict, List

from .base import IssueInfo, IssueStatus, IssueTracker


class GitLabIssueEngine(IssueTracker):
    """GitLab Issues integration using 'glab' CLI."""

    def get_issue_info(self, issue_ids: List[str]) -> Dict[str, IssueInfo]:
        results = {}
        for issue_id in issue_ids:
            try:
                # We assume issue_id is the iid (number)
                cmd = ["glab", "issue", "view", issue_id, "-F", "json"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                data = json.loads(result.stdout)

                raw_state = data.get("state", "").upper()
                status = IssueStatus.UNKNOWN
                if raw_state == "OPENED":
                    status = IssueStatus.OPEN
                elif raw_state == "CLOSED":
                    status = IssueStatus.CLOSED

                assignees = data.get("assignees", [])
                assignee = assignees[0].get("username") if assignees else None
                created_at = data.get("created_at")

                results[issue_id] = IssueInfo(
                    id=issue_id, status=status, assignee=assignee, created_at=created_at
                )
            except Exception:
                results[issue_id] = IssueInfo(id=issue_id, status=IssueStatus.UNKNOWN)
        return results

"""
Jira issue tracker integration.
"""

import json
import os
from typing import Dict, List, Optional

from .base import IssueInfo, IssueStatus, IssueTracker


class JiraIssueEngine(IssueTracker):
    """Jira integration using REST API."""

    def __init__(self, url: Optional[str], token_env: str, closed_statuses: List[str]):
        self.url = (url or "").rstrip("/")
        self.token = os.environ.get(token_env)
        self.closed_statuses = [s.lower() for s in closed_statuses]

    def get_issue_info(self, issue_ids: List[str]) -> Dict[str, IssueInfo]:
        if not self.token:
            return {
                iid: IssueInfo(id=iid, status=IssueStatus.UNKNOWN) for iid in issue_ids
            }

        import urllib.request

        results = {}
        for issue_id in issue_ids:
            try:
                request_url = f"{self.url}/rest/api/2/issue/{issue_id}?fields=status,assignee,created"
                req = urllib.request.Request(request_url)
                req.add_header("Authorization", f"Bearer {self.token}")

                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    status_name = data["fields"]["status"]["name"].lower()

                    status = IssueStatus.OPEN
                    if status_name in self.closed_statuses:
                        status = IssueStatus.CLOSED

                    assignee_data = data["fields"].get("assignee")
                    assignee = (
                        assignee_data.get("displayName") if assignee_data else None
                    )
                    created_at = data["fields"].get("created")

                    results[issue_id] = IssueInfo(
                        id=issue_id,
                        status=status,
                        assignee=assignee,
                        created_at=created_at,
                    )
            except Exception:
                results[issue_id] = IssueInfo(id=issue_id, status=IssueStatus.UNKNOWN)
        return results

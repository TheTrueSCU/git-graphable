import json
import os
import shlex
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class IssueStatus:
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


@dataclass
class IssueInfo:
    id: str
    status: str
    assignee: Optional[str] = None
    created_at: Optional[str] = None  # ISO 8601 timestamp


class IssueTracker(ABC):
    """Base class for issue tracker integrations."""

    @abstractmethod
    def get_issue_info(self, issue_ids: List[str]) -> Dict[str, IssueInfo]:
        """Fetch info for a list of issue IDs. Returns ID -> IssueInfo map."""
        pass

    def get_statuses(self, issue_ids: List[str]) -> Dict[str, str]:
        """Backward compatible helper."""
        info = self.get_issue_info(issue_ids)
        return {iid: item.status for iid, item in info.items()}


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


class ScriptIssueEngine(IssueTracker):
    """Integration using a custom shell script."""

    def __init__(self, script_template: str):
        self.template = script_template

    def get_issue_info(self, issue_ids: List[str]) -> Dict[str, IssueInfo]:
        results = {}
        for issue_id in issue_ids:
            try:
                # Use shlex.quote to prevent command injection if the issue_id
                # contains malicious characters.
                safe_id = shlex.quote(issue_id)
                cmd_str = self.template.replace("{id}", safe_id)
                result = subprocess.run(
                    cmd_str, shell=True, capture_output=True, text=True, check=True
                )
                output = result.stdout.strip()
                # Simple parsing logic for script output: "STATUS,ASSIGNEE,CREATED_AT"
                parts = output.split(",")
                raw_status = parts[0].upper()
                assignee = parts[1].strip() if len(parts) > 1 else None
                created_at = parts[2].strip() if len(parts) > 2 else None

                status = IssueStatus.UNKNOWN
                if "OPEN" in raw_status:
                    status = IssueStatus.OPEN
                elif "CLOSED" in raw_status or "DONE" in raw_status:
                    status = IssueStatus.CLOSED

                results[issue_id] = IssueInfo(
                    id=issue_id, status=status, assignee=assignee, created_at=created_at
                )
            except Exception:
                results[issue_id] = IssueInfo(id=issue_id, status=IssueStatus.UNKNOWN)
        return results


def get_issue_engine(config: Any) -> Optional[IssueTracker]:
    """Factory to create the appropriate engine based on config."""
    engine_type = (getattr(config, "issue_engine", "") or "").lower()
    if engine_type == "github":
        return GitHubIssueEngine()
    elif engine_type == "jira":
        return JiraIssueEngine(
            url=getattr(config, "jira_url", "") or "",
            token_env=getattr(config, "jira_token_env", "JIRA_TOKEN"),
            closed_statuses=getattr(
                config, "jira_closed_statuses", ["Done", "Closed", "Resolved"]
            ),
        )
    elif engine_type == "script":
        return ScriptIssueEngine(
            script_template=getattr(config, "issue_script", "") or ""
        )

    return None

import json
import os
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IssueStatus:
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class IssueTracker(ABC):
    """Base class for issue tracker integrations."""

    @abstractmethod
    def get_statuses(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch statuses for a list of issue IDs. Returns ID -> IssueStatus map."""
        pass


class GitHubIssueEngine(IssueTracker):
    """GitHub Issues integration using 'gh' CLI."""

    def get_statuses(self, issue_ids: List[str]) -> Dict[str, str]:
        results = {}
        for issue_id in issue_ids:
            try:
                # We assume issue_id is just the number for GitHub
                if not issue_id.isdigit():
                    continue

                cmd = ["gh", "issue", "view", issue_id, "--json", "state"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                data = json.loads(result.stdout)
                state = data.get("state", "").upper()

                if state == "OPEN":
                    results[issue_id] = IssueStatus.OPEN
                elif state in ["CLOSED", "MERGED"]:
                    results[issue_id] = IssueStatus.CLOSED
                else:
                    results[issue_id] = IssueStatus.UNKNOWN
            except Exception:
                results[issue_id] = IssueStatus.UNKNOWN
        return results


class JiraIssueEngine(IssueTracker):
    """Jira integration using REST API."""

    def __init__(self, url: str, token_env: str, closed_statuses: List[str]):
        self.url = url.rstrip("/")
        self.token = os.environ.get(token_env)
        self.closed_statuses = [s.lower() for s in closed_statuses]

    def get_statuses(self, issue_ids: List[str]) -> Dict[str, str]:
        if not self.token:
            return {iid: IssueStatus.UNKNOWN for iid in issue_ids}

        import urllib.request

        results = {}
        for issue_id in issue_ids:
            try:
                request_url = f"{self.url}/rest/api/2/issue/{issue_id}?fields=status"
                req = urllib.request.Request(request_url)
                req.add_header("Authorization", f"Bearer {self.token}")

                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    status_name = data["fields"]["status"]["name"].lower()

                    if status_name in self.closed_statuses:
                        results[issue_id] = IssueStatus.CLOSED
                    else:
                        results[issue_id] = IssueStatus.OPEN
            except Exception:
                results[issue_id] = IssueStatus.UNKNOWN
        return results


class ScriptIssueEngine(IssueTracker):
    """Integration using a custom shell script."""

    def __init__(self, script_template: str):
        self.template = script_template

    def get_statuses(self, issue_ids: List[str]) -> Dict[str, str]:
        results = {}
        for issue_id in issue_ids:
            try:
                cmd_str = self.template.replace("{id}", issue_id)
                result = subprocess.run(
                    cmd_str, shell=True, capture_output=True, text=True, check=True
                )
                status = result.stdout.strip().upper()

                if "OPEN" in status:
                    results[issue_id] = IssueStatus.OPEN
                elif "CLOSED" in status or "DONE" in status:
                    results[issue_id] = IssueStatus.CLOSED
                else:
                    results[issue_id] = IssueStatus.UNKNOWN
            except Exception:
                results[issue_id] = IssueStatus.UNKNOWN
        return results


def get_issue_engine(config: Any) -> Optional[IssueTracker]:
    """Factory to create the appropriate engine based on config."""
    engine_type = getattr(config, "issue_engine", "").lower()

    if engine_type == "github":
        return GitHubIssueEngine()
    elif engine_type == "jira":
        return JiraIssueEngine(
            url=getattr(config, "jira_url", ""),
            token_env=getattr(config, "jira_token_env", "JIRA_TOKEN"),
            closed_statuses=getattr(
                config, "jira_closed_statuses", ["Done", "Closed", "Resolved"]
            ),
        )
    elif engine_type == "script":
        return ScriptIssueEngine(script_template=getattr(config, "issue_script", ""))

    return None

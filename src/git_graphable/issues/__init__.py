"""
Issue tracker integration package.
"""

from typing import Any, Optional

from .base import IssueInfo, IssueStatus, IssueTracker
from .github import GitHubIssueEngine
from .gitlab import GitLabIssueEngine
from .jira import JiraIssueEngine
from .script import ScriptIssueEngine


def get_issue_engine(config: Any) -> Optional[IssueTracker]:
    """Factory to create the appropriate engine based on config."""
    engine_type = (getattr(config, "issue_engine", "") or "").lower()
    if engine_type == "github":
        return GitHubIssueEngine()
    elif engine_type == "gitlab":
        return GitLabIssueEngine()
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
            script_template=getattr(config, "issue_script", "") or "",
            trusted=getattr(config, "trusted", False),
        )

    return None


__all__ = [
    "IssueInfo",
    "IssueStatus",
    "IssueTracker",
    "GitHubIssueEngine",
    "JiraIssueEngine",
    "ScriptIssueEngine",
    "get_issue_engine",
]

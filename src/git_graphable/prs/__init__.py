"""
Pull Request status provider package.
"""

from typing import Any, Optional

from .base import PullRequestInfo, PullRequestProvider
from .github import GitHubPullRequestProvider
from .gitlab import GitLabPullRequestProvider
from .script import ScriptPullRequestProvider


def get_pr_provider(config: Any) -> Optional[PullRequestProvider]:
    """Factory to create the appropriate PR provider based on config."""
    # Default to github for backward compatibility
    provider_type = (getattr(config, "pr_provider", "github") or "github").lower()

    if provider_type == "github":
        return GitHubPullRequestProvider()
    elif provider_type == "gitlab":
        return GitLabPullRequestProvider()
    elif provider_type == "script":
        return ScriptPullRequestProvider(
            script_path=getattr(config, "pr_script", "") or ""
        )

    return None


__all__ = [
    "PullRequestInfo",
    "PullRequestProvider",
    "GitHubPullRequestProvider",
    "ScriptPullRequestProvider",
    "get_pr_provider",
]

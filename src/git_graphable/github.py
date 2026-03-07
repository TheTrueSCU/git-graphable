"""
Backward compatibility shim for github-related PR logic.
"""

from typing import Dict, List

from .prs.base import PullRequestInfo
from .prs.github import GitHubPullRequestProvider


def get_repo_prs(repo_path: str) -> List[PullRequestInfo]:
    """Backward compatible helper."""
    return GitHubPullRequestProvider().get_repo_prs(repo_path)


def map_prs_to_commits(prs: List[PullRequestInfo]) -> Dict[str, PullRequestInfo]:
    """Backward compatible helper."""
    # We use an instance here to access the base method
    from .prs.base import PullRequestProvider

    class Shim(PullRequestProvider):
        def get_repo_prs(self, repo_path: str):
            return []

    return Shim().map_prs_to_commits(prs)

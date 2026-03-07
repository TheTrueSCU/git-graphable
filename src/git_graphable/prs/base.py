"""
Base models and ABC for Pull Request providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PullRequestInfo:
    number: int
    title: str
    state: str
    is_draft: bool
    head_ref_name: str
    head_ref_oid: str
    merge_commit_oid: Optional[str]
    mergeable: str


class PullRequestProvider(ABC):
    """Base class for Pull Request providers."""

    @abstractmethod
    def get_repo_prs(self, repo_path: str) -> List[PullRequestInfo]:
        """Fetch all PRs for the repository."""
        pass

    def map_prs_to_commits(
        self, prs: List[PullRequestInfo]
    ) -> Dict[str, PullRequestInfo]:
        """Map commit OIDs to PR info."""
        mapping = {}
        for pr in prs:
            if pr.head_ref_oid:
                mapping[pr.head_ref_oid] = pr
            if pr.merge_commit_oid:
                mapping[pr.merge_commit_oid] = pr
        return mapping

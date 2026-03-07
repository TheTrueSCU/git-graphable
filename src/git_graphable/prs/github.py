"""
GitHub Pull Request provider.
"""

import json
import subprocess
from typing import List

from .base import PullRequestInfo, PullRequestProvider


class GitHubPullRequestProvider(PullRequestProvider):
    """GitHub PR integration using 'gh' CLI."""

    def get_repo_prs(self, repo_path: str) -> List[PullRequestInfo]:
        """Fetch all PRs for the repository using gh CLI."""
        try:
            # Check if gh is installed
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

        try:
            # Fetch PRs
            cmd = [
                "gh",
                "pr",
                "list",
                "--state",
                "all",
                "--limit",
                "1000",
                "--json",
                "number,title,state,isDraft,headRefName,headRefOid,mergeCommit,mergeable",
                "--",
            ]
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)

            prs = []
            for item in data:
                merge_commit = item.get("mergeCommit")
                merge_commit_oid = merge_commit.get("oid") if merge_commit else None

                prs.append(
                    PullRequestInfo(
                        number=item["number"],
                        title=item["title"],
                        state=item["state"],
                        is_draft=item["isDraft"],
                        head_ref_name=item["headRefName"],
                        head_ref_oid=item["headRefOid"],
                        merge_commit_oid=merge_commit_oid,
                        mergeable=item["mergeable"],
                    )
                )
            return prs
        except Exception:
            return []

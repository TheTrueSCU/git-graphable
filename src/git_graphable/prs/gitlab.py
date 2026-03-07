"""
GitLab Merge Request provider using glab CLI.
"""

import json
import subprocess
from typing import List

from .base import PullRequestInfo, PullRequestProvider


class GitLabPullRequestProvider(PullRequestProvider):
    """GitLab MR integration using 'glab' CLI."""

    def get_repo_prs(self, repo_path: str) -> List[PullRequestInfo]:
        """Fetch all MRs for the repository using glab CLI."""
        try:
            # Check if glab is installed
            subprocess.run(["glab", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

        try:
            # Fetch MRs
            # -F json returns full MR objects
            cmd = ["glab", "mr", "list", "--all", "-F", "json"]
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)

            prs = []
            for item in data:
                # glab uses 'opened', 'closed', 'merged'
                state = item["state"].upper()
                if state == "OPENED":
                    state = "OPEN"

                # glab has 'sha' for head and 'merge_commit_sha'
                prs.append(
                    PullRequestInfo(
                        number=item["iid"],
                        title=item["title"],
                        state=state,
                        is_draft=item.get("draft", False)
                        or item.get("work_in_progress", False),
                        head_ref_name=item["source_branch"],
                        head_ref_oid=item["sha"],
                        merge_commit_oid=item.get("merge_commit_sha"),
                        mergeable=item.get("merge_status", "can_be_merged").upper(),
                    )
                )
            return prs
        except Exception:
            return []

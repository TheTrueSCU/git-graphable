"""
Script-based Pull Request provider.
"""

import json
import subprocess
from typing import List

from .base import PullRequestInfo, PullRequestProvider


class ScriptPullRequestProvider(PullRequestProvider):
    """Integration using a custom shell script."""

    def __init__(self, script_path: str):
        self.script_path = script_path

    def get_repo_prs(self, repo_path: str) -> List[PullRequestInfo]:
        if not self.script_path:
            return []

        try:
            # Run the script. It should output JSON array of PR objects.
            result = subprocess.run(
                [self.script_path, repo_path],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            prs = []
            for item in data:
                prs.append(
                    PullRequestInfo(
                        number=item["number"],
                        title=item["title"],
                        state=item["state"],
                        is_draft=item.get("is_draft", False),
                        head_ref_name=item["head_ref_name"],
                        head_ref_oid=item["head_ref_oid"],
                        merge_commit_oid=item.get("merge_commit_oid"),
                        mergeable=item.get("mergeable", "UNKNOWN"),
                    )
                )
            return prs
        except Exception:
            return []

import json
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PullRequestInfo:
    number: int
    title: str
    state: str
    is_draft: bool
    head_ref_oid: str
    merge_commit_oid: Optional[str]
    mergeable: str


def get_repo_prs(repo_path: str) -> List[PullRequestInfo]:
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
            "number,title,state,isDraft,headRefOid,mergeCommit,mergeable",
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
                    head_ref_oid=item["headRefOid"],
                    merge_commit_oid=merge_commit_oid,
                    mergeable=item["mergeable"],
                )
            )
        return prs
    except Exception:
        return []


def map_prs_to_commits(prs: List[PullRequestInfo]) -> Dict[str, PullRequestInfo]:
    """Map commit OIDs to PR info.
    Maps both headRefOid and mergeCommitOid to the PR.
    """
    mapping = {}
    for pr in prs:
        if pr.head_ref_oid:
            mapping[pr.head_ref_oid] = pr
        if pr.merge_commit_oid:
            mapping[pr.merge_commit_oid] = pr
    return mapping

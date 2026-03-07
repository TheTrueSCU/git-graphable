"""
External highlights (GitHub PRs, Issue Trackers, Releases).
"""

import re
import subprocess
from datetime import datetime
from typing import Optional

from graphable import Graph

from ..core import GitCommit, GitLogConfig
from ..issues import IssueStatus, get_issue_engine
from ..models import Tag
from ..prs import get_pr_provider
from .visual import find_node


def _apply_pr_highlights(
    graph: Graph[GitCommit],
    config: GitLogConfig,
    repo_path: Optional[str],
    force: bool = False,
):
    """Highlight commits based on Pull Request status."""
    if not repo_path:
        return

    provider = get_pr_provider(config)
    if not provider:
        return

    prs = provider.get_repo_prs(repo_path)
    pr_map = provider.map_prs_to_commits(prs)

    for commit in graph:
        sha = commit.reference.hash
        if sha in pr_map:
            pr = pr_map[sha]
            commit.add_tag(Tag.PR_STATUS.value)
            if pr.state == "OPEN":
                if pr.is_draft:
                    commit.add_tag(Tag.PR_DRAFT.value)
                else:
                    commit.add_tag(Tag.PR_OPEN.value)
            elif pr.state == "MERGED":
                commit.add_tag(Tag.PR_MERGED.value)
            elif pr.state == "CLOSED":
                commit.add_tag(Tag.PR_CLOSED.value)

            if pr.mergeable == "CONFLICTING":
                commit.add_tag(Tag.PR_CONFLICT.value)


def _apply_squash_highlights(
    graph: Graph[GitCommit],
    config: GitLogConfig,
    repo_path: Optional[str],
    force: bool = False,
):
    """Detect and highlight 'logical' merges from squashed PRs."""
    if not repo_path:
        return

    provider = get_pr_provider(config)
    if not provider:
        return

    prs = provider.get_repo_prs(repo_path)
    merged_prs = [pr for pr in prs if pr.state == "MERGED" and pr.merge_commit_oid]
    commits_by_hash = {c.reference.hash: c for c in graph}

    for pr in merged_prs:
        if pr.merge_commit_oid in commits_by_hash:
            squash_commit = commits_by_hash[pr.merge_commit_oid]
            squash_commit.add_tag(Tag.SQUASH_COMMIT.value)
            branch_tag = f"{Tag.BRANCH.value}{pr.head_ref_name}"
            squash_ancestors = set(graph.ancestors(squash_commit))
            potential_squashed = [
                c
                for c in graph
                if branch_tag in c.tags
                and c not in squash_ancestors
                and c != squash_commit
            ]
            if potential_squashed:
                tips = []
                for c in potential_squashed:
                    is_tip = True
                    for child, _ in graph.internal_dependents(c):
                        if child in potential_squashed:
                            is_tip = False
                            break
                    if is_tip:
                        tips.append(c)
                for tip in tips:
                    # For squash merges, the 'logical' edge doesn't exist in Git,
                    # so we must create it in the graph.
                    # In this graph's convention, child nodes add_dependency(parent).
                    # The squash commit is the 'new' parent of the old tip.
                    tip.add_dependency(
                        squash_commit, **{Tag.EDGE_LOGICAL_MERGE.value: True}
                    )
                    tip.add_tag(Tag.SQUASHED.value)


def _apply_issue_highlights(
    graph: Graph[GitCommit],
    config: GitLogConfig,
    repo_path: Optional[str],
    force: bool = False,
):
    """Highlight inconsistencies between Git/PR status and Issue Tracker status."""
    if not config.issue_pattern:
        return

    pattern = re.compile(config.issue_pattern)
    issue_to_commits = {}

    # 1. Extract IDs and map to commits
    for commit in graph:
        # Check branches
        for branch in commit.reference.branches:
            matches = pattern.findall(branch)
            for issue_id in matches:
                issue_to_commits.setdefault(issue_id, set()).add(commit)

        # Check message
        matches = pattern.findall(commit.reference.message)
        for issue_id in matches:
            issue_to_commits.setdefault(issue_id, set()).add(commit)

    if not issue_to_commits:
        return

    # 2. Fetch issue info
    engine = get_issue_engine(config)
    if not engine:
        return

    issue_info_map = engine.get_issue_info(list(issue_to_commits.keys()))

    # 3. Compare and Tag
    base_branch = config.development_branch
    base_tip = find_node(graph, base_branch)
    if not base_tip:
        base_branch = config.production_branch
        base_tip = find_node(graph, base_branch)

    base_reach = set()
    if base_tip:
        base_reach = set(graph.ancestors(base_tip))
        base_reach.add(base_tip)

    for issue_id, commits in issue_to_commits.items():
        info = issue_info_map.get(issue_id)
        if not info or info.status == IssueStatus.UNKNOWN:
            continue

        ext_status = info.status
        ext_assignee = (info.assignee or "").lower()
        ext_created = info.created_at

        for commit in commits:
            # A. Status Comparison (Always tag for hygiene)
            git_status = IssueStatus.UNKNOWN
            if commit.is_tagged(Tag.PR_OPEN.value):
                git_status = IssueStatus.OPEN
            elif commit.is_tagged(Tag.PR_MERGED.value) or commit.is_tagged(
                Tag.PR_CLOSED.value
            ):
                git_status = IssueStatus.CLOSED
            else:
                if (
                    commit.reference.branches
                    and base_branch not in commit.reference.branches
                ):
                    if commit not in base_reach:
                        git_status = IssueStatus.OPEN

            if git_status != IssueStatus.UNKNOWN and git_status != ext_status:
                commit.add_tag(Tag.ISSUE_INCONSISTENCY.value)
                commit.add_tag(f"issue_status:{ext_status.lower()}")

            # B. Assignee Comparison (Always tag for hygiene)
            if ext_assignee:
                author_raw = commit.reference.author
                git_author = config.author_mapping.get(author_raw, author_raw).lower()
                if git_author != ext_assignee:
                    commit.add_tag(Tag.COLLABORATION_GAP.value)
                    commit.add_tag(f"issue_assignee:{ext_assignee}")

            # C. Longevity Mismatch (Always tag for hygiene)
            if ext_created:
                try:
                    clean_ts = ext_created.replace("Z", "+00:00")
                    created_dt = datetime.fromisoformat(clean_ts)
                    issue_ts = created_dt.timestamp()
                    commit_ts = commit.reference.timestamp
                    diff_sec = abs(commit_ts - issue_ts)
                    diff_days = diff_sec / 86400
                    if diff_days > config.longevity_threshold_days:
                        commit.add_tag(Tag.LONGEVITY_MISMATCH.value)
                        commit.add_tag(f"longevity_gap:{int(diff_days)}")
                except Exception:
                    pass


def _apply_release_highlights(
    graph: Graph[GitCommit],
    config: GitLogConfig,
    repo_path: Optional[str],
    force: bool = False,
):
    """Highlight issues marked as 'Released' but not reachable from a Git tag."""
    if not config.issue_pattern or not repo_path:
        return

    # 1. Get all SHAs reachable from tags
    try:
        cmd = ["git", "rev-list", "--tags"]
        result = subprocess.run(
            cmd, cwd=repo_path, capture_output=True, text=True, check=True
        )
        released_shas = set(result.stdout.splitlines())
    except Exception:
        return

    # 2. Extract Issue IDs from graph
    pattern = re.compile(config.issue_pattern)
    issue_to_commits = {}
    for commit in graph:
        for branch in commit.reference.branches:
            matches = pattern.findall(branch)
            for issue_id in matches:
                issue_to_commits.setdefault(issue_id, set()).add(commit)
        matches = pattern.findall(commit.reference.message)
        for issue_id in matches:
            issue_to_commits.setdefault(issue_id, set()).add(commit)

    if not issue_to_commits:
        return

    # 3. Fetch issue info
    engine = get_issue_engine(config)
    if not engine:
        return

    issue_info_map = engine.get_issue_info(list(issue_to_commits.keys()))

    for issue_id, commits in issue_to_commits.items():
        info = issue_info_map.get(issue_id)
        if not info or info.status != IssueStatus.CLOSED:
            continue

        # It's 'Closed/Released' in tracker. Is it tagged in Git?
        for commit in commits:
            if commit.reference.hash not in released_shas:
                commit.add_tag(Tag.RELEASE_INCONSISTENCY.value)

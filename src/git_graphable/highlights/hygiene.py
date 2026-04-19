"""
Hygiene highlights (WIP, direct push, stale branches, etc).
"""

import time

from graphable.graph import AcyclicGraph

from ..core import GitCommit, GitLogConfig
from ..models import Tag
from .visual import find_node


def _should_ignore(commit: GitCommit, rule: str, config: GitLogConfig) -> bool:
    """Check if a commit should be ignored for a specific hygiene rule."""
    if not config.ignore:
        return False

    # Check exact SHA or prefix
    for key, rules in config.ignore.items():
        if commit.reference.hash.startswith(key):
            if rule in rules or "all" in rules:
                return True

    return False


def _apply_divergence_highlights(
    graph: AcyclicGraph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight divergence/behind analysis from a base branch/hash."""
    base_branch = (config.highlight_diverging_from or "").strip()
    if force and not base_branch:
        base_branch = config.production_branch

    base_node = find_node(graph, base_branch) if base_branch else None
    if force and not base_node:
        base_branch = config.production_branch
        base_node = find_node(graph, base_branch) if base_branch else None

    if base_node:
        base_reach = set(graph.ancestors(base_node))
        base_reach.add(base_node)

        for commit in graph:
            if (
                commit.reference.branches
                and base_branch not in commit.reference.branches
            ):
                branch_reach = set(graph.ancestors(commit))
                branch_reach.add(commit)

                if base_reach - branch_reach:
                    if not _should_ignore(commit, "divergence", config):
                        commit.add_tag(Tag.BEHIND.value)


def _apply_orphan_highlights(
    graph: AcyclicGraph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight dangling/orphan commits."""
    branch_reachable = set()
    for commit in graph:
        if commit.reference.branches:
            branch_reachable.update(graph.ancestors(commit))
            branch_reachable.add(commit)

    for commit in graph:
        if commit not in branch_reachable:
            if not _should_ignore(commit, "orphan", config):
                commit.add_tag(Tag.ORPHAN.value)


def _apply_stale_highlights(
    graph: AcyclicGraph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight stale branch tips."""
    now = time.time()
    stale_threshold_sec = config.stale_days * 86400

    for commit in graph:
        if commit.reference.branches:
            age_sec = now - commit.reference.timestamp
            if age_sec > 0:
                ratio = min(age_sec / stale_threshold_sec, 1.0)
                gb_value = int(255 - (ratio * 85))  # 255 -> 170
                color = f"#ff{gb_value:02x}{gb_value:02x}"
                commit.add_tag(f"{Tag.STALE_COLOR.value}{color}")

                # ONLY apply visual highlight if explicitly requested
                if config.highlight_stale and not _should_ignore(
                    commit, "stale", config
                ):
                    commit.add_tag(Tag.COLOR.value)


def _apply_long_running_highlights(
    graph: AcyclicGraph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight long-running branches."""
    now = time.time()
    threshold_sec = config.long_running_days * 86400
    if config.long_running_days == 0:
        threshold_sec = -1

    base_branch = config.long_running_base or config.development_branch
    base_tip = find_node(graph, base_branch)
    if not base_tip and not config.long_running_base:
        base_branch = config.production_branch
        base_tip = find_node(graph, base_branch)

    if base_tip:
        base_reach = set(graph.ancestors(base_tip))
        base_reach.add(base_tip)

        for tip in graph:
            if tip.reference.branches and base_branch not in tip.reference.branches:
                branch_reach = set(graph.ancestors(tip))
                branch_reach.add(tip)

                unique_commits = branch_reach - base_reach
                if unique_commits:
                    oldest_unique = min(
                        unique_commits, key=lambda c: c.reference.timestamp
                    )
                    age_sec = now - oldest_unique.reference.timestamp

                    if age_sec > threshold_sec:
                        for commit in unique_commits:
                            if not _should_ignore(commit, "long_running", config):
                                commit.add_tag(Tag.LONG_RUNNING.value)
                                for parent, _ in graph.internal_depends_on(commit):
                                    if parent in unique_commits or parent in base_reach:
                                        commit.set_edge_attribute(
                                            parent, Tag.EDGE_LONG_RUNNING.value, True
                                        )


def _apply_wip_highlights(
    graph: AcyclicGraph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight commits with WIP/TODO keywords in message."""
    import re

    # Use word boundaries to avoid matching keywords inside other words (e.g. 'swiping')
    # We also ignore cases.
    patterns = [
        re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE) for k in config.wip_keywords
    ]

    for commit in graph:
        if _should_ignore(commit, "wip", config):
            continue
        message = commit.reference.message
        if any(p.search(message) for p in patterns):
            commit.add_tag(Tag.WIP.value)


def _apply_direct_push_highlights(
    graph: AcyclicGraph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight non-merge commits made directly to protected branches."""
    protected = {
        config.production_branch,
        config.development_branch,
        *config.critical_branches,
    }

    for commit in graph:
        if _should_ignore(commit, "direct_push", config):
            continue
        if len(commit.reference.parents) > 1:
            continue
        for branch in commit.reference.branches:
            if branch in protected:
                if not commit.reference.parents:
                    continue
                commit.add_tag(Tag.DIRECT_PUSH.value)
                break


def _apply_back_merge_highlights(
    graph: AcyclicGraph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight redundant merges (base branch merged into feature branch)."""

    base_branch = config.development_branch
    base_tip = find_node(graph, base_branch)
    if not base_tip:
        base_branch = config.production_branch
        base_tip = find_node(graph, base_branch)

    if not base_tip:
        return

    base_reach = set(graph.ancestors(base_tip))
    base_reach.add(base_tip)

    for commit in graph:
        if len(commit.reference.parents) <= 1:
            continue
        if base_branch in commit.reference.branches:
            continue
        parents = []
        for p_sha in commit.reference.parents:
            parent_node = next((c for c in graph if c.reference.hash == p_sha), None)
            if parent_node:
                parents.append(parent_node)
        if len(parents) < 2:
            continue
        has_base_parent = any(p in base_reach for p in parents)
        has_non_base_parent = any(p not in base_reach for p in parents)
        if has_base_parent and has_non_base_parent:
            if not _should_ignore(commit, "back_merge", config):
                commit.add_tag(Tag.BACK_MERGE.value)


def _apply_silo_highlights(
    graph: AcyclicGraph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight branches with high commit counts but low author diversity."""

    base_branch = config.development_branch
    base_tip = find_node(graph, base_branch)
    if not base_tip:
        base_branch = config.production_branch
        base_tip = find_node(graph, base_branch)

    if not base_tip:
        return

    base_reach = set(graph.ancestors(base_tip))
    base_reach.add(base_tip)

    for tip in graph:
        if tip.reference.branches and base_branch not in tip.reference.branches:
            branch_reach = set(graph.ancestors(tip))
            branch_reach.add(tip)
            unique_commits = branch_reach - base_reach
            if len(unique_commits) >= config.silo_commit_threshold:
                authors = {c.reference.author for c in unique_commits}
                if len(authors) <= config.silo_author_count:
                    if not _should_ignore(tip, "silo", config):
                        tip.add_tag(Tag.CONTRIBUTOR_SILO.value)

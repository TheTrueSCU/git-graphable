import time
from typing import Optional

from graphable import Graph

from .core import Engine, GitCommit, GitLogConfig
from .models import Tag


def apply_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, repo_path: Optional[str] = None
):
    """Apply highlighting tags based on configuration."""
    is_html = config.engine == Engine.HTML

    _apply_pr_highlights(graph, config, repo_path, force=is_html)
    _apply_author_highlights(graph, config, force=is_html)
    _apply_critical_highlights(graph, config, force=is_html)
    _apply_distance_highlights(graph, config, force=is_html)
    _apply_path_highlights(graph, config)
    _apply_divergence_highlights(graph, config, force=is_html)
    _apply_orphan_highlights(graph, config, force=is_html)
    _apply_stale_highlights(graph, config, force=is_html)
    _apply_long_running_highlights(graph, config, force=is_html)
    _apply_wip_highlights(graph, config, force=is_html)
    _apply_direct_push_highlights(graph, config, force=is_html)
    _apply_squash_highlights(graph, config, repo_path, force=is_html)
    _apply_back_merge_highlights(graph, config, force=is_html)
    _apply_silo_highlights(graph, config, force=is_html)
    _apply_issue_highlights(graph, config, repo_path, force=is_html)
    _apply_release_highlights(graph, config, repo_path, force=is_html)


def _apply_release_highlights(
    graph: Graph[GitCommit],
    config: GitLogConfig,
    repo_path: Optional[str],
    force: bool = False,
):
    """Highlight issues marked as 'Released' but not reachable from a Git tag."""
    if not force and not config.highlight_release_inconsistencies:
        return

    if not config.issue_pattern or not repo_path:
        return

    import re
    import subprocess

    from .issues import IssueStatus, get_issue_engine

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


def _apply_issue_highlights(
    graph: Graph[GitCommit],
    config: GitLogConfig,
    repo_path: Optional[str],
    force: bool = False,
):
    """Highlight inconsistencies between Git/PR status and Issue Tracker status."""
    if (
        not force
        and not config.highlight_issue_inconsistencies
        and not config.highlight_collaboration_gaps
        and not config.highlight_longevity_mismatch
    ):
        return

    if not config.issue_pattern:
        return

    import re

    from .issues import IssueStatus, get_issue_engine

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
    def find_node(query: str) -> Optional[GitCommit]:
        for commit in graph:
            if query in commit.reference.branches or commit.reference.hash.startswith(
                query
            ):
                return commit
        return None

    base_branch = config.development_branch
    base_tip = find_node(base_branch)
    if not base_tip:
        base_branch = config.production_branch
        base_tip = find_node(base_branch)

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
            # A. Status Comparison
            if force or config.highlight_issue_inconsistencies:
                git_status = IssueStatus.UNKNOWN
                # Explicit PR tags take priority
                if commit.is_tagged(Tag.PR_OPEN.value):
                    git_status = IssueStatus.OPEN
                elif commit.is_tagged(Tag.PR_MERGED.value) or commit.is_tagged(
                    Tag.PR_CLOSED.value
                ):
                    git_status = IssueStatus.CLOSED
                else:
                    # If no PR, infer from topology: if it's a branch tip NOT in base, it's 'OPEN'
                    if (
                        commit.reference.branches
                        and base_branch not in commit.reference.branches
                    ):
                        if commit not in base_reach:
                            git_status = IssueStatus.OPEN

                if git_status != IssueStatus.UNKNOWN and git_status != ext_status:
                    commit.add_tag(Tag.ISSUE_INCONSISTENCY.value)
                    commit.add_tag(f"issue_status:{ext_status.lower()}")

            # B. Assignee Comparison (Collaboration Gap)
            if (force or config.highlight_collaboration_gaps) and ext_assignee:
                author_raw = commit.reference.author
                # Map author if alias exists
                git_author = config.author_mapping.get(author_raw, author_raw).lower()

                if git_author != ext_assignee:
                    commit.add_tag(Tag.COLLABORATION_GAP.value)
                    commit.add_tag(f"issue_assignee:{ext_assignee}")

            # C. Longevity Mismatch
            if (force or config.highlight_longevity_mismatch) and ext_created:
                try:
                    # Convert ext_created (ISO 8601) to timestamp
                    from datetime import datetime

                    clean_ts = ext_created.replace("Z", "+00:00")
                    created_dt = datetime.fromisoformat(clean_ts)
                    issue_ts = created_dt.timestamp()

                    commit_ts = commit.reference.timestamp

                    # Calculate difference in days
                    diff_sec = abs(commit_ts - issue_ts)
                    diff_days = diff_sec / 86400

                    if diff_days > config.longevity_threshold_days:
                        commit.add_tag(Tag.LONGEVITY_MISMATCH.value)
                        commit.add_tag(f"longevity_gap:{int(diff_days)}")
                except Exception:
                    pass  # Ignore parsing errors


def _apply_silo_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight branches with high commit counts but low author diversity."""
    if not force and not config.highlight_silos:
        return

    def find_base_tip(query: str) -> Optional[GitCommit]:
        for commit in graph:
            if query in commit.reference.branches or commit.reference.hash.startswith(
                query
            ):
                return commit
        return None

    base_branch = config.development_branch
    base_tip = find_base_tip(base_branch)
    if not base_tip:
        # Fallback to production branch
        base_branch = config.production_branch
        base_tip = find_base_tip(base_branch)

    if not base_tip:
        return

    base_reach = set(graph.ancestors(base_tip))
    base_reach.add(base_tip)

    for tip in graph:
        # Check each branch tip that is not the base branch itself
        if tip.reference.branches and base_branch not in tip.reference.branches:
            branch_reach = set(graph.ancestors(tip))
            branch_reach.add(tip)

            # Find commits unique to this branch
            unique_commits = branch_reach - base_reach
            if len(unique_commits) >= config.silo_commit_threshold:
                authors = {c.reference.author for c in unique_commits}
                if len(authors) <= config.silo_author_count:
                    # Mark the tip as a silo
                    tip.add_tag(Tag.CONTRIBUTOR_SILO.value)


def _apply_back_merge_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight redundant merges (base branch merged into feature branch)."""
    if not force and not config.highlight_back_merges:
        return

    # Use development_branch as base for determining 'redundant' merges
    def find_base_tip(query: str) -> Optional[GitCommit]:
        for commit in graph:
            if query in commit.reference.branches or commit.reference.hash.startswith(
                query
            ):
                return commit
        return None

    base_branch = config.development_branch
    base_tip = find_base_tip(base_branch)
    if not base_tip:
        # Fallback to production branch
        base_branch = config.production_branch
        base_tip = find_base_tip(base_branch)

    if not base_tip:
        return

    base_reach = set(graph.ancestors(base_tip))
    base_reach.add(base_tip)

    for commit in graph:
        # Check if it's a merge commit
        if len(commit.reference.parents) <= 1:
            continue

        # If this commit itself is on the base branch, it's a regular merge into base
        if base_branch in commit.reference.branches:
            continue

        # Check if one of the parents is in the base reach
        parents = []
        for p_sha in commit.reference.parents:
            # Find the parent node in the graph
            parent_node = next((c for c in graph if c.reference.hash == p_sha), None)
            if parent_node:
                parents.append(parent_node)

        if len(parents) < 2:
            continue

        has_base_parent = any(p in base_reach for p in parents)
        has_non_base_parent = any(p not in base_reach for p in parents)

        if has_base_parent and has_non_base_parent:
            # This is a back-merge!
            commit.add_tag(Tag.BACK_MERGE.value)


def _apply_squash_highlights(
    graph: Graph[GitCommit],
    config: GitLogConfig,
    repo_path: Optional[str],
    force: bool = False,
):
    """Detect and highlight 'logical' merges from squashed GitHub PRs."""
    if not force and not config.highlight_squashed:
        return

    if not repo_path:
        return

    from .github import get_repo_prs

    prs = get_repo_prs(repo_path)
    # Filter for merged PRs that have a head branch name
    merged_prs = [pr for pr in prs if pr.state == "MERGED" and pr.merge_commit_oid]

    commits_by_hash = {c.reference.hash: c for c in graph}

    for pr in merged_prs:
        if pr.merge_commit_oid in commits_by_hash:
            squash_commit = commits_by_hash[pr.merge_commit_oid]

            # Label the squash commit
            squash_commit.add_tag(Tag.SQUASH_COMMIT.value)

            # Find the original feature branch commits if they still exist locally.
            # They would be tagged with the branch name.
            branch_tag = f"{Tag.BRANCH.value}{pr.head_ref_name}"

            # Find commits that have this branch tag but are NOT reachable
            # from the squash commit's ancestors (meaning they were squashed).
            squash_ancestors = set(graph.ancestors(squash_commit))

            potential_squashed = [
                c
                for c in graph
                if branch_tag in c.tags
                and c not in squash_ancestors
                and c != squash_commit
            ]

            if potential_squashed:
                # Find the 'tip' of the squashed commits
                tips = []
                for c in potential_squashed:
                    is_tip = True
                    for child, _ in graph.internal_dependents(c):
                        if child in potential_squashed:
                            is_tip = False
                            break
                    if is_tip:
                        tips.append(c)

                # Link each tip logically to the squash commit
                for tip in tips:
                    squash_commit.set_edge_attribute(
                        tip, Tag.EDGE_LOGICAL_MERGE.value, True
                    )
                    # Also tag the tip as squashed
                    tip.add_tag(Tag.SQUASHED.value)


def _apply_wip_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight commits with WIP/TODO keywords in message."""
    if not force and not config.highlight_wip:
        return

    keywords = [k.lower() for k in config.wip_keywords]
    for commit in graph:
        message = commit.reference.message.lower()
        if any(k in message for k in keywords):
            commit.add_tag(Tag.WIP.value)


def _apply_direct_push_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight non-merge commits made directly to protected branches."""
    if not force and not config.highlight_direct_pushes:
        return

    protected = {
        config.production_branch,
        config.development_branch,
        *config.critical_branches,
    }

    for commit in graph:
        # Check if it's a non-merge commit (1 parent or 0 for root)
        if len(commit.reference.parents) > 1:
            continue

        # For each branch this commit is on, check if it's protected
        for branch in commit.reference.branches:
            if branch in protected:
                if not commit.reference.parents:
                    continue
                commit.add_tag(Tag.DIRECT_PUSH.value)
                break


def _apply_pr_highlights(
    graph: Graph[GitCommit],
    config: GitLogConfig,
    repo_path: Optional[str],
    force: bool = False,
):
    """Highlight commits based on GitHub PR status."""
    if not force and not config.highlight_pr_status:
        return

    if not repo_path:
        return

    from .github import get_repo_prs, map_prs_to_commits

    prs = get_repo_prs(repo_path)
    pr_map = map_prs_to_commits(prs)

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


def _apply_author_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Assign colors to different authors."""
    if not force and not config.highlight_authors:
        return

    authors = sorted(list(set(c.reference.author for c in graph)))
    palette = config.theme.author_palette
    author_to_color = {
        author: palette[i % len(palette)] for i, author in enumerate(authors)
    }

    is_html = config.engine == Engine.HTML
    for commit in graph:
        color = author_to_color.get(commit.reference.author)
        if color:
            if not is_html:
                commit.add_tag(f"{Tag.COLOR.value}{color}")
            # Always add author_highlight tag for HTML legend mapping
            commit.add_tag(f"{Tag.AUTHOR_HIGHLIGHT.value}{color}")


def _apply_distance_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight commits based on distance from a base branch/hash."""
    base_query = config.highlight_distance_from
    if not force and not base_query:
        return

    # If force but no query, default to development branch
    if force and not base_query:
        base_query = config.development_branch

    def find_base_node(query: str) -> Optional[GitCommit]:
        for commit in graph:
            if query in commit.reference.branches or commit.reference.hash.startswith(
                query
            ):
                return commit
        return None

    base_commit = find_base_node(base_query) if base_query else None

    if base_commit:
        distances = {base_commit: 0}
        queue = [(base_commit, 0)]
        visited = {base_commit}

        while queue:
            current, dist = queue.pop(0)
            for parent, _ in graph.internal_depends_on(current):
                if parent not in visited:
                    visited.add(parent)
                    distances[parent] = dist + 1
                    queue.append((parent, dist + 1))
            for child, _ in graph.internal_dependents(current):
                if child not in visited:
                    visited.add(child)
                    distances[child] = dist + 1
                    queue.append((child, dist + 1))

        if distances:
            max_dist = max(distances.values())
            for commit, dist in distances.items():
                intensity = int(230 * (dist / max_dist)) if max_dist > 0 else 0
                color = f"#{intensity:02x}{intensity:02x}ff"
                commit.add_tag(f"{Tag.DISTANCE_COLOR.value}{color}")
                if (
                    not force
                    and not config.highlight_authors
                    and not config.highlight_stale
                ):
                    commit.add_tag(f"{Tag.COLOR.value}{color}")


def _apply_path_highlights(graph: Graph[GitCommit], config: GitLogConfig):
    """Highlight path between two SHAs."""
    if not config.highlight_path:
        return

    start_input, end_input = config.highlight_path

    def find_node(query: str) -> Optional[GitCommit]:
        for commit in graph:
            if query in commit.reference.branches or commit.reference.hash.startswith(
                query
            ):
                return commit
        return None

    start_node = find_node(start_input)
    end_node = find_node(end_input)

    if start_node and end_node:
        path_graph = graph.subgraph_between(start_node, end_node)
        path_nodes = set(path_graph)
        for commit in path_nodes:
            for parent, _ in graph.internal_depends_on(commit):
                if parent in path_nodes:
                    commit.set_edge_attribute(parent, Tag.EDGE_PATH.value, True)


def _apply_divergence_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight divergence/behind analysis from a base branch/hash."""
    base_branch = (config.highlight_diverging_from or "").strip()
    if not force and not base_branch:
        return

    if force and not base_branch:
        base_branch = config.production_branch

    def find_divergence_node(query: str) -> Optional[GitCommit]:
        for commit in graph:
            if query in commit.reference.branches or commit.reference.hash.startswith(
                query
            ):
                return commit
        return None

    base_node = find_divergence_node(base_branch)

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
                    commit.add_tag(Tag.BEHIND.value)


def _apply_orphan_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight dangling/orphan commits."""
    if not force and not config.highlight_orphans:
        return

    branch_reachable = set()
    for commit in graph:
        if commit.reference.branches:
            branch_reachable.update(graph.ancestors(commit))
            branch_reachable.add(commit)

    for commit in graph:
        if commit not in branch_reachable:
            commit.add_tag(Tag.ORPHAN.value)


def _apply_stale_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight stale branch tips."""
    if not force and not config.highlight_stale:
        return

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
                if not force and not config.highlight_authors:
                    commit.add_tag(f"{Tag.COLOR.value}{color}")


def _apply_long_running_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight long-running branches."""
    if not force and not config.highlight_long_running:
        return

    now = time.time()
    threshold_sec = config.long_running_days * 86400
    if config.long_running_days == 0:
        threshold_sec = -1

    def find_base_tip(query: str) -> Optional[GitCommit]:
        for commit in graph:
            if query in commit.reference.branches or commit.reference.hash.startswith(
                query
            ):
                return commit
        return None

    base_branch = config.long_running_base or config.development_branch
    base_tip = find_base_tip(base_branch)
    if not base_tip and not config.long_running_base:
        base_branch = config.production_branch
        base_tip = find_base_tip(base_branch)

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
                            commit.add_tag(Tag.LONG_RUNNING.value)
                            for parent, _ in graph.internal_depends_on(commit):
                                if parent in unique_commits or parent in base_reach:
                                    commit.set_edge_attribute(
                                        parent, Tag.EDGE_LONG_RUNNING.value, True
                                    )


def _apply_critical_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Ensure critical branches are tagged for overlay support."""
    if not force and not config.highlight_critical:
        return

    critical_set = {
        config.production_branch,
        config.development_branch,
        *config.critical_branches,
    }
    for commit in graph:
        for branch in commit.reference.branches:
            if branch in critical_set:
                commit.add_tag(Tag.CRITICAL.value)
                break

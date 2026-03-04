import time
from typing import Optional

from graphable import Graph

from .core import GitCommit, GitLogConfig
from .models import Tag


def apply_highlights(graph: Graph[GitCommit], config: GitLogConfig):
    """Apply highlighting tags based on configuration."""

    # 1. Author highlighting
    if config.highlight_authors:
        authors = sorted(list(set(c.reference.author for c in graph)))
        palette = [
            "#FFD700",
            "#C0C0C0",
            "#CD7F32",
            "#ADD8E6",
            "#90EE90",
            "#F08080",
            "#E6E6FA",
            "#FFE4E1",
        ]
        author_to_color = {
            author: palette[i % len(palette)] for i, author in enumerate(authors)
        }

        for commit in graph:
            color = author_to_color.get(commit.reference.author)
            if color:
                commit.add_tag(f"{Tag.COLOR.value}{color}")

    # 2. Distance highlighting
    if config.highlight_distance_from:

        def find_base_node(query: str) -> Optional[GitCommit]:
            for commit in graph:
                if (
                    query in commit.reference.branches
                    or commit.reference.hash.startswith(query)
                ):
                    return commit
            return None

        base_commit = find_base_node(config.highlight_distance_from)

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
                    if not config.highlight_authors and not config.highlight_stale:
                        commit.add_tag(f"{Tag.COLOR.value}{color}")

    # 3. Path highlighting
    if config.highlight_path:
        start_input, end_input = config.highlight_path

        def find_node(query: str) -> Optional[GitCommit]:
            for commit in graph:
                if (
                    query in commit.reference.branches
                    or commit.reference.hash.startswith(query)
                ):
                    return commit
            return None

        start_node = find_node(start_input)
        end_node = find_node(end_input)

        if start_node and end_node:
            path_graph = graph.subgraph_between(start_node, end_node)
            path_nodes = set(path_graph)
            for commit in path_nodes:
                # Tag edges that connect nodes within this path
                for parent, _ in graph.internal_depends_on(commit):
                    if parent in path_nodes:
                        commit.set_edge_attribute(parent, Tag.EDGE_PATH.value, True)

    # 4. Divergence highlighting
    if config.highlight_diverging_from:

        def find_divergence_node(query: str) -> Optional[GitCommit]:
            for commit in graph:
                if (
                    query in commit.reference.branches
                    or commit.reference.hash.startswith(query)
                ):
                    return commit
            return None

        base_node = find_divergence_node(config.highlight_diverging_from)

        if base_node:
            base_reach = set(graph.ancestors(base_node))
            base_reach.add(base_node)
            other_reach = set()
            for commit in graph:
                if (
                    commit.reference.branches
                    and config.highlight_diverging_from not in commit.reference.branches
                ):
                    other_reach.update(graph.ancestors(commit))
                    other_reach.add(commit)

            behind_commits = base_reach - other_reach
            for commit in behind_commits:
                commit.add_tag(Tag.BEHIND.value)

    # 5. Orphan highlighting
    if config.highlight_orphans:
        branch_reachable = set()
        for commit in graph:
            if commit.reference.branches:
                branch_reachable.update(graph.ancestors(commit))
                branch_reachable.add(commit)

        for commit in graph:
            if commit not in branch_reachable:
                commit.add_tag(Tag.ORPHAN.value)

    # 6. Stale branch detection
    if config.highlight_stale:
        now = time.time()
        stale_threshold_sec = config.highlight_stale * 86400

        for commit in graph:
            if commit.reference.branches:
                age_sec = now - commit.reference.timestamp
                if age_sec > 0:
                    ratio = min(age_sec / stale_threshold_sec, 1.0)
                    gb_value = int(255 - (ratio * 85))  # 255 -> 170
                    color = f"#ff{gb_value:02x}{gb_value:02x}"
                    commit.add_tag(f"{Tag.STALE_COLOR.value}{color}")
                    if not config.highlight_authors:
                        commit.add_tag(f"{Tag.COLOR.value}{color}")

    # 7. Long-running branch detection
    if config.highlight_long_running is not None:
        now = time.time()
        # Use a small negative threshold for 0 to handle near-instant commits in tests
        threshold_sec = config.highlight_long_running * 86400
        if config.highlight_long_running == 0:
            threshold_sec = -1

        def find_base_tip(query: str) -> Optional[GitCommit]:
            for commit in graph:
                if (
                    query in commit.reference.branches
                    or commit.reference.hash.startswith(query)
                ):
                    return commit
            return None

        base_tip = find_base_tip(config.long_running_base)
        if base_tip:
            base_reach = set(graph.ancestors(base_tip))
            base_reach.add(base_tip)

            for tip in graph:
                if (
                    tip.reference.branches
                    and config.long_running_base not in tip.reference.branches
                ):
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

"""
Visual highlights (colors, paths, critical branches).
"""

from typing import Optional

from graphable import Graph

from ..core import GitCommit, GitLogConfig
from ..models import Tag


def _apply_author_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Assign colors to different authors."""
    authors = sorted(list(set(c.reference.author for c in graph)))
    palette = config.theme.author_palette
    author_to_color = {
        author: palette[i % len(palette)] for i, author in enumerate(authors)
    }

    for commit in graph:
        color = author_to_color.get(commit.reference.author)
        if color:
            # ONLY apply visual 'color:' tag if requested or HTML (hidden)
            if config.highlight_authors:
                commit.add_tag(f"{Tag.COLOR.value}{color}")

            # Always add helper tag for HTML legend
            commit.add_tag(f"{Tag.AUTHOR_HIGHLIGHT.value}{color}")


def _apply_critical_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Ensure critical branches are tagged for overlay support."""
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


def _apply_distance_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, force: bool = False
):
    """Highlight commits based on distance from a base branch/hash."""
    base_query = config.highlight_distance_from
    if force and not base_query:
        base_query = config.development_branch

    base_commit = find_node(graph, base_query) if base_query else None
    if force and not base_commit:
        base_query = config.production_branch
        base_commit = find_node(graph, base_query) if base_query else None

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

                # ONLY apply visual highlight if explicitly requested
                if config.highlight_distance_from:
                    commit.add_tag(f"{Tag.COLOR.value}{color}")


def _apply_path_highlights(graph: Graph[GitCommit], config: GitLogConfig):
    """Highlight path between two SHAs."""
    if not config.highlight_path:
        return

    start_input, end_input = config.highlight_path

    start_node = find_node(graph, start_input)
    end_node = find_node(graph, end_input)

    if start_node and end_node:
        path_graph = graph.subgraph_between(start_node, end_node)
        path_nodes = set(path_graph)
        for commit in path_nodes:
            for parent, _ in graph.internal_depends_on(commit):
                if parent in path_nodes:
                    commit.set_edge_attribute(parent, Tag.EDGE_PATH.value, True)


def find_node(graph: Graph[GitCommit], query: str) -> Optional[GitCommit]:
    """Helper to find a node by branch name or SHA prefix."""
    for commit in graph:
        if query in commit.reference.branches or commit.reference.hash.startswith(
            query
        ):
            return commit
    return None

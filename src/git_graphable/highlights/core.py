"""
Core highlights application logic.
"""

from typing import Optional

from graphable import Graph

from ..core import Engine, GitCommit, GitLogConfig
from .external import (
    _apply_issue_highlights,
    _apply_pr_highlights,
    _apply_release_highlights,
    _apply_squash_highlights,
)
from .hygiene import (
    _apply_back_merge_highlights,
    _apply_direct_push_highlights,
    _apply_divergence_highlights,
    _apply_long_running_highlights,
    _apply_orphan_highlights,
    _apply_silo_highlights,
    _apply_stale_highlights,
    _apply_wip_highlights,
)
from .visual import (
    _apply_author_highlights,
    _apply_critical_highlights,
    _apply_distance_highlights,
    _apply_path_highlights,
)


def apply_highlights(
    graph: Graph[GitCommit], config: GitLogConfig, repo_path: Optional[str] = None
):
    """Apply highlighting tags based on configuration."""
    is_html = config.engine == Engine.HTML

    # We now always apply hygiene tags so the summary/score is stable.
    # The 'force=True' ensures tags are added to nodes.
    # The CLI flags now only control the VISUAL highlighting (color: tags).

    _apply_pr_highlights(graph, config, repo_path, force=True)
    _apply_author_highlights(graph, config, force=is_html)
    _apply_critical_highlights(graph, config, force=True)
    _apply_distance_highlights(graph, config, force=is_html)
    _apply_path_highlights(graph, config)
    _apply_divergence_highlights(graph, config, force=True)
    _apply_orphan_highlights(graph, config, force=True)
    _apply_stale_highlights(graph, config, force=True)
    _apply_long_running_highlights(graph, config, force=True)
    _apply_wip_highlights(graph, config, force=True)
    _apply_direct_push_highlights(graph, config, force=True)
    _apply_squash_highlights(graph, config, repo_path, force=True)
    _apply_back_merge_highlights(graph, config, force=True)
    _apply_silo_highlights(graph, config, force=True)
    _apply_issue_highlights(graph, config, repo_path, force=True)
    _apply_release_highlights(graph, config, repo_path, force=True)

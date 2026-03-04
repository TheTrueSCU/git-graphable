import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from graphable import Graph, Graphable


@dataclass
class CommitMetadata:
    hash: str
    parents: List[str]
    branches: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timestamp: int = 0
    author: str = ""
    message: str = ""


@dataclass
class GitLogConfig:
    """Configuration for retrieving git log."""

    simplify: bool = False
    limit: Optional[int] = None
    date_format: str = "%Y%m%d%H%M%S"
    highlight_critical: List[str] = field(default_factory=list)
    highlight_authors: bool = False
    highlight_distance_from: Optional[str] = None  # For distance highlighting
    highlight_path: Optional[Tuple[str, str]] = None  # (start_input, end_input)
    highlight_diverging_from: Optional[str] = None  # For divergence analysis
    highlight_orphans: bool = False
    highlight_stale: Optional[int] = None  # Days
    highlight_long_running: Optional[int] = None  # Days
    long_running_base: str = "main"


class GitCommit(Graphable[CommitMetadata]):
    """A Git commit represented as a graphable object."""

    def __init__(self, metadata: CommitMetadata, config: GitLogConfig):
        super().__init__(metadata)
        from .models import Tag

        # Add metadata as tags for filtering/formatting
        self.add_tag(f"{Tag.AUTHOR.value}{metadata.author}")
        for branch in metadata.branches:
            self.add_tag(f"{Tag.BRANCH.value}{branch}")
            if branch in config.highlight_critical:
                self.add_tag(Tag.CRITICAL.value)

        for tag in metadata.tags:
            self.add_tag(f"{Tag.TAG.value}{tag}")

        self.add_tag(Tag.GIT_COMMIT.value)


def generate_summary(graph: Graph[GitCommit]) -> Dict[str, List[GitCommit]]:
    """Generate a summary of flagged commits."""
    from .models import Tag

    summary = {
        "Critical": [],
        "Behind Base": [],
        "Orphan": [],
        "Stale": [],
        "Long-Running": [],
    }

    for commit in graph:
        if commit.is_tagged(Tag.CRITICAL.value):
            summary["Critical"].append(commit)
        if commit.is_tagged(Tag.BEHIND.value):
            summary["Behind Base"].append(commit)
        if commit.is_tagged(Tag.ORPHAN.value):
            summary["Orphan"].append(commit)
        if commit.is_tagged(Tag.STALE_COLOR.value):
            summary["Stale"].append(commit)
        if commit.is_tagged(Tag.LONG_RUNNING.value):
            # Only count branch tips for long-running summary to avoid redundancy
            if commit.reference.branches:
                summary["Long-Running"].append(commit)

    return summary


def process_repo(input_path: str, config: GitLogConfig) -> Graph[GitCommit]:
    """Clones (if URL) and processes the repo, returning a Graph of GitCommits."""
    from .highlighter import apply_highlights
    from .parser import get_git_log

    repo_path = input_path
    temp_dir = None

    if input_path.startswith(("http://", "https://", "git@", "ssh://")):
        temp_dir = tempfile.mkdtemp()
        try:
            import subprocess

            subprocess.run(
                ["git", "clone", input_path, temp_dir], check=True, capture_output=True
            )
            repo_path = temp_dir
        except Exception as e:
            if temp_dir:
                shutil.rmtree(temp_dir)
            raise RuntimeError(f"Failed to clone repository: {e}")

    try:
        if not os.path.exists(os.path.join(repo_path, ".git")):
            raise RuntimeError(f"{repo_path} is not a git repository.")

        commits_dict = get_git_log(repo_path, config=config)

        for sha, commit in commits_dict.items():
            for p_sha in commit.reference.parents:
                if p_sha in commits_dict:
                    commit.requires(commits_dict[p_sha])

        graph = Graph(list(commits_dict.values()))
        apply_highlights(graph, config)
        return graph

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

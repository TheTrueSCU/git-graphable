import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

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

    # Branch Roles for Hygiene Defaults
    production_branch: str = "main"
    development_branch: str = "main"

    simplify: bool = False
    limit: Optional[int] = None
    date_format: str = "%Y%m%d%H%M%S"
    highlight_critical: bool = False
    critical_branches: List[str] = field(default_factory=list)
    highlight_authors: bool = False
    highlight_distance_from: Optional[str] = None  # For distance highlighting
    highlight_path: Optional[Tuple[str, str]] = None  # (start_input, end_input)
    highlight_diverging_from: Optional[str] = None  # For divergence analysis
    highlight_orphans: bool = False
    highlight_stale: bool = False
    stale_days: int = 30
    highlight_long_running: bool = False
    long_running_days: int = 30
    long_running_base: Optional[str] = None  # Defaults to development_branch
    highlight_pr_status: bool = False

    @classmethod
    def from_toml(cls, file_path: str) -> "GitLogConfig":
        """Load configuration from a TOML file."""
        import tomllib

        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)

            # Look for [tool.git-graphable] or just [git-graphable]
            config_data = data.get("tool", {}).get(
                "git-graphable", data.get("git-graphable", {})
            )

            # Handle highlight_path tuple
            if "highlight_path" in config_data and isinstance(
                config_data["highlight_path"], list
            ):
                config_data["highlight_path"] = tuple(config_data["highlight_path"])

            return cls(
                **{
                    k: v
                    for k, v in config_data.items()
                    if k in cls.__dataclass_fields__
                }
            )
        except Exception:
            return cls()

    def merge(self, other: Dict[str, Any]) -> "GitLogConfig":
        """Merge a dictionary of overrides into this config."""
        new_config = GitLogConfig()
        # Initialize with current values
        for field_name in self.__dataclass_fields__:
            setattr(new_config, field_name, getattr(self, field_name))

        # Override with non-None values from 'other'
        for key, value in other.items():
            if value is not None and key in self.__dataclass_fields__:
                # Special case for lists: only override if not empty
                if isinstance(value, list) and not value:
                    continue
                setattr(new_config, key, value)

        return new_config


class GitCommit(Graphable[CommitMetadata]):
    """A Git commit represented as a graphable object."""

    def __init__(self, metadata: CommitMetadata, config: GitLogConfig):
        super().__init__(metadata)
        from .models import Tag

        # Determine critical branches
        critical_set = set(config.critical_branches)
        critical_set.add(config.production_branch)
        critical_set.add(config.development_branch)

        # Add metadata as tags for filtering/formatting
        self.add_tag(f"{Tag.AUTHOR.value}{metadata.author}")
        for branch in metadata.branches:
            self.add_tag(f"{Tag.BRANCH.value}{branch}")
            if config.highlight_critical and branch in critical_set:
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
        "PR: Open": [],
        "PR: Merged": [],
        "PR: Closed": [],
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

        if commit.is_tagged(Tag.PR_OPEN.value):
            summary["PR: Open"].append(commit)
        if commit.is_tagged(Tag.PR_MERGED.value):
            summary["PR: Merged"].append(commit)
        if commit.is_tagged(Tag.PR_CLOSED.value):
            summary["PR: Closed"].append(commit)

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
        apply_highlights(graph, config, repo_path=repo_path)
        return graph

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

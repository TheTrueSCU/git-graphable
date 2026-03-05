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
    highlight_wip: bool = False
    wip_keywords: List[str] = field(
        default_factory=lambda: ["wip", "todo", "fixup!", "squash!", "temp", "bug"]
    )
    highlight_direct_pushes: bool = False
    highlight_squashed: bool = False
    highlight_back_merges: bool = False
    highlight_silos: bool = False
    silo_commit_threshold: int = 20
    silo_author_count: int = 1
    min_hygiene_score: int = 80

    # Issue Tracker Integration
    highlight_issue_inconsistencies: bool = False
    issue_pattern: Optional[str] = None  # e.g. [A-Z]+-[0-9]+
    issue_engine: Optional[str] = None  # github, jira, script
    jira_url: Optional[str] = None
    jira_token_env: str = "JIRA_TOKEN"
    jira_closed_statuses: List[str] = field(
        default_factory=lambda: ["Done", "Closed", "Resolved"]
    )
    issue_script: Optional[str] = None
    highlight_release_inconsistencies: bool = False
    released_statuses: List[str] = field(default_factory=lambda: ["Released"])
    highlight_collaboration_gaps: bool = False
    author_mapping: Dict[str, str] = field(default_factory=dict)
    highlight_longevity_mismatch: bool = False
    longevity_threshold_days: int = (
        14  # Max diff between Issue created and first commit
    )

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


def generate_summary(graph: Graph[GitCommit], config: GitLogConfig) -> Dict[str, Any]:
    """Generate a summary of flagged commits."""
    from .hygiene import HygieneScorer
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
        "WIP": [],
        "Direct Pushes": [],
        "Squashed PRs": [],
        "Back-Merges": [],
        "Contributor Silos": [],
        "Issue Inconsistencies": [],
        "Release Inconsistencies": [],
        "Collaboration Gaps": [],
        "Longevity Mismatches": [],
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

        if commit.is_tagged(Tag.WIP.value):
            summary["WIP"].append(commit)
        if commit.is_tagged(Tag.DIRECT_PUSH.value):
            summary["Direct Pushes"].append(commit)
        if commit.is_tagged(Tag.SQUASH_COMMIT.value):
            summary["Squashed PRs"].append(commit)
        if commit.is_tagged(Tag.BACK_MERGE.value):
            summary["Back-Merges"].append(commit)
        if commit.is_tagged(Tag.CONTRIBUTOR_SILO.value):
            summary["Contributor Silos"].append(commit)
        if commit.is_tagged(Tag.ISSUE_INCONSISTENCY.value):
            summary["Issue Inconsistencies"].append(commit)
        if commit.is_tagged(Tag.RELEASE_INCONSISTENCY.value):
            summary["Release Inconsistencies"].append(commit)
        if commit.is_tagged(Tag.COLLABORATION_GAP.value):
            summary["Collaboration Gaps"].append(commit)
        if commit.is_tagged(Tag.LONGEVITY_MISMATCH.value):
            summary["Longevity Mismatches"].append(commit)

    # Calculate Hygiene Score
    scorer = HygieneScorer(graph, config)
    summary["Hygiene Score"] = scorer.calculate()

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

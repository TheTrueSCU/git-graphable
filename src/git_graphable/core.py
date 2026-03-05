from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from graphable import Graph, Graphable


@dataclass
class CommitMetadata:
    hash: str
    author: str = ""
    timestamp: float = 0.0
    message: str = ""
    parents: List[str] = field(default_factory=list)
    branches: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class HygieneWeights:
    direct_push_penalty: int = 15
    direct_push_cap: int = 45
    pr_conflict_penalty: int = 10
    pr_conflict_cap: int = 30
    orphan_commit_penalty: int = 2
    orphan_commit_cap: int = 10
    wip_commit_penalty: int = 3
    wip_commit_cap: int = 15
    stale_branch_penalty: int = 5
    stale_branch_cap: int = 20
    long_running_branch_penalty: int = 10
    long_running_branch_cap: int = 30
    divergence_penalty: int = 5
    back_merge_penalty: int = 5
    back_merge_cap: int = 25
    contributor_silo_penalty: int = 10
    contributor_silo_cap: int = 30
    issue_inconsistency_penalty: int = 10
    issue_inconsistency_cap: int = 30
    release_inconsistency_penalty: int = 10
    release_inconsistency_cap: int = 30
    collaboration_gap_penalty: int = 5
    collaboration_gap_cap: int = 25
    longevity_mismatch_penalty: int = 5
    longevity_mismatch_cap: int = 20


@dataclass
class StyleInfo:
    stroke: Optional[str] = None
    fill: Optional[str] = None
    width: Optional[int] = None
    dash: Optional[str] = None  # None, "dashed", "dotted"
    opacity: Optional[float] = None


@dataclass
class ThemeConfig:
    critical: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="red", width=4)
    )
    wip: StyleInfo = field(default_factory=lambda: StyleInfo(fill="#ffff00"))
    behind: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="orange", dash="dashed", width=2)
    )
    orphan: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="grey", dash="dashed", opacity=0.6)
    )
    long_running: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="purple", width=3)
    )
    pr_conflict: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="red", width=6)
    )
    direct_push: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="#ff0000", dash="dashed", width=8)
    )
    back_merge: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="orange", dash="dashed", width=4)
    )
    contributor_silo: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="blue", width=6)
    )

    # PR Status Fills
    pr_open: StyleInfo = field(default_factory=lambda: StyleInfo(fill="#28a745"))
    pr_merged: StyleInfo = field(default_factory=lambda: StyleInfo(fill="#6f42c1"))
    pr_closed: StyleInfo = field(default_factory=lambda: StyleInfo(fill="#d73a49"))
    pr_draft: StyleInfo = field(default_factory=lambda: StyleInfo(fill="#808080"))

    # Edges
    edge_path: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="#FFA500", width=4)
    )
    edge_long_running: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="purple", width=3)
    )
    edge_logical_merge: StyleInfo = field(
        default_factory=lambda: StyleInfo(stroke="#808080", dash="dashed", width=2)
    )

    # Palette
    author_palette: List[str] = field(
        default_factory=lambda: [
            "#FFD700",
            "#C0C0C0",
            "#CD7F32",
            "#ADD8E6",
            "#90EE90",
            "#F08080",
            "#E6E6FA",
            "#FFE4E1",
        ]
    )


@dataclass
class GitLogConfig:
    simplify: bool = False
    limit: Optional[int] = None
    date_format: str = "%Y%m%d%H%M%S"
    highlight_authors: bool = False
    highlight_distance_from: Optional[str] = None
    highlight_path: Optional[Tuple[str, str]] = None
    highlight_diverging_from: Optional[str] = None
    highlight_orphans: bool = False
    highlight_stale: bool = False
    stale_days: int = 30
    highlight_critical: bool = False
    production_branch: str = "main"
    development_branch: str = "develop"
    critical_branches: List[str] = field(default_factory=list)
    highlight_long_running: bool = False
    long_running_days: int = 14
    long_running_base: Optional[str] = None
    highlight_wip: bool = False
    wip_keywords: List[str] = field(
        default_factory=lambda: ["wip", "fixup!", "squash!"]
    )
    highlight_direct_pushes: bool = False
    highlight_pr_status: bool = False
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
    hygiene_weights: HygieneWeights = field(default_factory=HygieneWeights)
    theme: ThemeConfig = field(default_factory=ThemeConfig)

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

            # Handle nested hygiene_weights
            weights_data = config_data.pop("hygiene_weights", {})
            # Handle nested theme
            theme_data = config_data.pop("theme", {})

            config = cls(
                **{
                    k: v
                    for k, v in config_data.items()
                    if k in cls.__dataclass_fields__
                }
            )
            if weights_data:
                for k, v in weights_data.items():
                    if hasattr(config.hygiene_weights, k):
                        setattr(config.hygiene_weights, k, v)

            if theme_data:
                for k, v in theme_data.items():
                    if hasattr(config.theme, k):
                        if isinstance(v, dict):
                            # It's a StyleInfo override
                            current_style = getattr(config.theme, k)
                            for s_k, s_v in v.items():
                                if hasattr(current_style, s_k):
                                    setattr(current_style, s_k, s_v)
                        else:
                            # It's likely the author_palette list
                            setattr(config.theme, k, v)

            return config
        except Exception:
            return cls()

    def merge(self, other: Dict[str, Any]) -> "GitLogConfig":
        """Merge a dictionary of overrides into this config."""
        new_config = GitLogConfig()
        # Initialize with current values
        for field_name in self.__dataclass_fields__:
            val = getattr(self, field_name)
            if isinstance(val, HygieneWeights):
                # Deep copy for HygieneWeights
                setattr(new_config, field_name, HygieneWeights(**asdict(val)))
            elif isinstance(val, ThemeConfig):
                # Deep copy for ThemeConfig
                new_theme = ThemeConfig()
                for t_field in val.__dataclass_fields__:
                    t_val = getattr(val, t_field)
                    if isinstance(t_val, StyleInfo):
                        setattr(new_theme, t_field, StyleInfo(**asdict(t_val)))
                    else:
                        setattr(new_theme, t_field, t_val)
                setattr(new_config, field_name, new_theme)
            else:
                setattr(new_config, field_name, val)

        # Override with non-None values from 'other'
        for key, value in other.items():
            if value is not None and key in self.__dataclass_fields__:
                if key == "hygiene_weights" and isinstance(value, dict):
                    # Merge weights if provided as dict
                    for w_key, w_val in value.items():
                        if hasattr(new_config.hygiene_weights, w_key):
                            setattr(new_config.hygiene_weights, w_key, w_val)
                elif key == "theme" and isinstance(value, dict):
                    # Merge theme if provided as dict
                    for t_key, t_val in value.items():
                        if hasattr(new_config.theme, t_key):
                            if isinstance(t_val, dict):
                                current_style = getattr(new_config.theme, t_key)
                                for s_key, s_val in t_val.items():
                                    if hasattr(current_style, s_key):
                                        setattr(current_style, s_key, s_val)
                            else:
                                setattr(new_config.theme, t_key, t_val)
                elif isinstance(value, list) and not value:
                    # Special case for lists: only override if not empty
                    continue
                else:
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
        "PR Status": [],
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
        if commit.is_tagged(Tag.PR_STATUS.value):
            summary["PR Status"].append(commit)
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


def process_repo(repo_path: str, config: GitLogConfig) -> Graph[GitCommit]:
    """Process a repository and return a graph of commits."""
    from .parser import get_git_log

    commits_dict = get_git_log(repo_path, config)
    graph = Graph()

    # Create nodes
    for node in commits_dict.values():
        graph.add_node(node)

    # Create edges (parent -> child)
    for node in commits_dict.values():
        for parent_hash in node.reference.parents:
            if parent_hash in commits_dict:
                parent = commits_dict[parent_hash]
                # In Git, parents are 'depended on' by children
                node.add_dependency(parent)

    # Apply highlights
    from .highlighter import apply_highlights

    apply_highlights(graph, config, repo_path)

    return graph

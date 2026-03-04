import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from graphable import Graph, Graphable
from graphable.enums import Engine
from graphable.views import (
    D2StylingConfig,
    GraphvizStylingConfig,
    MermaidStylingConfig,
    PlantUmlStylingConfig,
    export_topology_d2,
    export_topology_d2_image,
    export_topology_graphviz_dot,
    export_topology_graphviz_image,
    export_topology_mermaid_image,
    export_topology_mermaid_mmd,
    export_topology_plantuml,
    export_topology_plantuml_image,
)


@dataclass
class CommitMetadata:
    hash: str
    parents: List[str]
    branches: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timestamp: int = 0
    author: str = ""


class GitCommit(Graphable[CommitMetadata]):
    """A Git commit represented as a graphable object."""

    def __init__(self, metadata: CommitMetadata):
        super().__init__(metadata)

        # Add metadata as tags for filtering/formatting
        self.add_tag(f"author:{metadata.author}")
        for branch in metadata.branches:
            self.add_tag(f"branch:{branch}")
        for tag in metadata.tags:
            self.add_tag(f"tag:{tag}")

        self.add_tag("git_commit")


def run_git_command(args: List[str], cwd: Optional[str] = None) -> str:
    """Run a git command and return its output."""
    try:
        return subprocess.check_output(
            ["git"] + args, cwd=cwd, text=True, stderr=subprocess.PIPE
        ).strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e.stderr}", file=sys.stderr)
        raise


def parse_ref_names(ref_names: str) -> tuple[List[str], List[str]]:
    """Parse git log ref names (%D) into branches and tags."""
    branches = []
    tags = []
    if not ref_names:
        return branches, tags

    parts = [p.strip() for p in ref_names.split(",")]
    for part in parts:
        if part.startswith("tag: "):
            tags.append(part[len("tag: ") :])
        elif "->" in part:
            branches.append(part.split("->")[-1].strip())
        elif part == "HEAD":
            continue
        else:
            branches.append(part)
    return branches, tags


@dataclass
class GitLogConfig:
    """Configuration for retrieving git log."""

    simplify: bool = False
    limit: Optional[int] = None
    date_format: str = "%Y%m%d%H%M%S"


def get_git_log(repo_path: str, config: GitLogConfig) -> Dict[str, GitCommit]:
    """Retrieve git log and parse into GitCommit objects."""
    format_str = "%H|%P|%D|%at|%an"
    args = ["log", "--all", f"--format={format_str}"]
    if config.simplify:
        args.append("--simplify-by-decoration")
    if config.limit:
        args.append(f"-n {config.limit}")

    output = run_git_command(args, cwd=repo_path)

    commits: Dict[str, GitCommit] = {}
    for line in output.split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) < 5:
            continue

        sha = parts[0]
        parents = parts[1].split() if parts[1] else []
        refs = parts[2]
        timestamp = parts[3]
        author = parts[4]

        branches, tags = parse_ref_names(refs)

        metadata = CommitMetadata(
            hash=sha,
            parents=parents,
            branches=branches,
            tags=tags,
            timestamp=int(timestamp) if timestamp.isdigit() else 0,
            author=author,
        )
        commits[sha] = GitCommit(metadata)

    return commits


def get_node_text(
    node: GitCommit, date_format: str = "%Y%m%d%H%M%S", engine: Engine = Engine.MERMAID
) -> str:
    """Generate node text for a commit, specialized for the visualization engine."""
    meta = node.reference

    def sanitize(s: str) -> str:
        if engine == Engine.MERMAID:
            # Mermaid unquoted labels are fragile
            for char in "[](){}|":
                s = s.replace(char, " ")
            return " ".join(s.split())
        elif engine == Engine.D2:
            # D2 labels will be quoted, but we should escape internal quotes
            return s.replace('"', '\\"')
        return s

    branches = [
        sanitize(t[len("branch:") :]) for t in node.tags if t.startswith("branch:")
    ]
    tags = [sanitize(t[len("tag:") :]) for t in node.tags if t.startswith("tag:")]
    author_raw = next(
        (t[len("author:") :] for t in node.tags if t.startswith("author:")), meta.author
    )
    author = sanitize(author_raw)

    display_label = f"{meta.hash[:7]}"

    # Use different separators/newlines based on engine
    sep = " - "
    newline = " - "
    if engine == Engine.D2:
        newline = "\\n"  # D2 supports \n in labels
    elif engine == Engine.GRAPHVIZ:
        newline = "\\n"
    elif engine == Engine.PLANTUML:
        newline = "\\n"

    if branches:
        display_label += f"{sep}{', '.join(branches)}"
    if tags:
        display_label += f"{sep}tags: {', '.join(tags)}"

    dt_str = (
        datetime.fromtimestamp(meta.timestamp).strftime(date_format)
        if meta.timestamp
        else ""
    )
    label = f"{display_label}{newline}{author}{newline}{dt_str}"

    if engine == Engine.D2:
        # Wrap in quotes for D2 since graphable doesn't
        return f'"{label}"'

    return label


def export_graph(
    graph: Graph[GitCommit],
    output_path: str,
    config: GitLogConfig,
    engine: Engine = Engine.MERMAID,
    as_image: bool = False,
) -> None:
    """Export the graph to a file using the specified engine."""

    def label_fnc(n):
        return get_node_text(n, config.date_format, engine)

    def node_ref_fnc(n):
        return n.reference.hash

    if engine == Engine.MERMAID:
        styling_config = MermaidStylingConfig(
            node_ref_fnc=node_ref_fnc, node_text_fnc=label_fnc
        )
        fnc = export_topology_mermaid_image if as_image else export_topology_mermaid_mmd
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.GRAPHVIZ:
        styling_config = GraphvizStylingConfig(
            node_ref_fnc=node_ref_fnc, node_label_fnc=label_fnc
        )
        fnc = (
            export_topology_graphviz_image if as_image else export_topology_graphviz_dot
        )
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.D2:
        styling_config = D2StylingConfig(
            node_ref_fnc=node_ref_fnc, node_label_fnc=label_fnc
        )
        fnc = export_topology_d2_image if as_image else export_topology_d2
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.PLANTUML:
        styling_config = PlantUmlStylingConfig(
            node_ref_fnc=node_ref_fnc, node_label_fnc=label_fnc
        )
        fnc = export_topology_plantuml_image if as_image else export_topology_plantuml
        graph.export(fnc, output_path, config=styling_config)
    else:
        # Fallback to generic write
        graph.write(output_path)


def process_repo(input_path: str, config: GitLogConfig) -> Graph[GitCommit]:
    """Clones (if URL) and processes the repo, returning a Graph of GitCommits."""
    repo_path = input_path
    temp_dir = None

    if input_path.startswith(("http://", "https://", "git@", "ssh://")):
        temp_dir = tempfile.mkdtemp()
        try:
            subprocess.run(
                ["git", "clone", input_path, temp_dir], check=True, capture_output=True
            )
            repo_path = temp_dir
        except subprocess.CalledProcessError as e:
            if temp_dir:
                shutil.rmtree(temp_dir)
            raise RuntimeError(f"Failed to clone repository: {e.stderr.decode()}")

    try:
        if not os.path.exists(os.path.join(repo_path, ".git")):
            raise RuntimeError(f"{repo_path} is not a git repository.")

        commits_dict = get_git_log(repo_path, config=config)

        for sha, commit in commits_dict.items():
            for p_sha in commit.reference.parents:
                if p_sha in commits_dict:
                    commit.requires(commits_dict[p_sha])

        return Graph(list(commits_dict.values()))

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

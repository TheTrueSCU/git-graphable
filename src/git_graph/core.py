import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

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


class GitCommit(Graphable[CommitMetadata]):
    """A Git commit represented as a graphable object."""

    def __init__(self, metadata: CommitMetadata, config: GitLogConfig):
        super().__init__(metadata)

        # Add metadata as tags for filtering/formatting
        self.add_tag(f"author:{metadata.author}")
        for branch in metadata.branches:
            self.add_tag(f"branch:{branch}")
            if branch in config.highlight_critical:
                self.add_tag("critical")

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


def get_git_log(repo_path: str, config: GitLogConfig) -> Dict[str, GitCommit]:
    """Retrieve git log and parse into GitCommit objects."""
    format_str = "%H|%P|%D|%at|%an|%s"
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
        if len(parts) < 6:
            continue

        sha = parts[0]
        parents = parts[1].split() if parts[1] else []
        refs = parts[2]
        timestamp = parts[3]
        author = parts[4]
        message = parts[5]

        branches, tags = parse_ref_names(refs)

        metadata = CommitMetadata(
            hash=sha,
            parents=parents,
            branches=branches,
            tags=tags,
            timestamp=int(timestamp) if timestamp.isdigit() else 0,
            author=author,
            message=message,
        )
        commits[sha] = GitCommit(metadata, config)

    return commits


def get_node_text(
    node: GitCommit, date_format: str = "%Y%m%d%H%M%S", engine: Engine = Engine.MERMAID
) -> str:
    """Generate node text for a commit, specialized for the visualization engine."""
    meta = node.reference

    def sanitize(s: str) -> str:
        if engine == Engine.MERMAID:
            for char in "[](){}|":
                s = s.replace(char, " ")
            return " ".join(s.split())
        elif engine == Engine.D2:
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

    sep = " - "
    newline = " - "
    if engine == Engine.D2:
        newline = "\\n"
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
        return f'"{label}"'

    return label


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
                commit.add_tag(f"color:{color}")

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
                    commit.add_tag(f"distance_color:{color}")
                    if not config.highlight_authors and not config.highlight_stale:
                        commit.add_tag(f"color:{color}")

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
                for parent, _ in graph.internal_depends_on(commit):
                    if parent in path_nodes:
                        commit.set_edge_attribute(parent, "highlight", True)

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
                commit.add_tag("behind")

    # 5. Orphan highlighting
    if config.highlight_orphans:
        branch_reachable = set()
        for commit in graph:
            if commit.reference.branches:
                branch_reachable.update(graph.ancestors(commit))
                branch_reachable.add(commit)

        for commit in graph:
            if commit not in branch_reachable:
                commit.add_tag("orphan")

    # 6. Stale branch detection
    if config.highlight_stale:
        now = time.time()
        stale_threshold_sec = config.highlight_stale * 86400

        for commit in graph:
            # We only care about branch tips
            if commit.reference.branches:
                age_sec = now - commit.reference.timestamp
                if age_sec > 0:
                    # Ratio of staleness up to threshold
                    # 0 = fresh (white), 1 = stale (dusty red)
                    ratio = min(age_sec / stale_threshold_sec, 1.0)

                    # Gradient from white (#ffffff) to dusty red (#ffaaaa)
                    # We keep red channel at 255, decrease green and blue
                    gb_value = int(255 - (ratio * 85))  # 255 -> 170 (aa)
                    color = f"#ff{gb_value:02x}{gb_value:02x}"

                    commit.add_tag(f"stale_color:{color}")
                    # Stale highlighting takes priority for branch tips unless author/path is active
                    if not config.highlight_authors:
                        commit.add_tag(f"color:{color}")


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

    def get_generic_style(node: Graphable[Any]) -> dict[str, str]:
        styles = {}
        for tag in node.tags:
            if tag.startswith("color:"):
                color = tag.split(":", 1)[1]
                if engine == Engine.D2:
                    styles.update(
                        {
                            "fill": color,
                            "font-color": "black"
                            if color.startswith("#F") or color.startswith("#E")
                            else "white",
                        }
                    )
                elif engine == Engine.GRAPHVIZ:
                    styles.update({"fillcolor": color, "style": "filled"})

        if node.is_tagged("critical"):
            if engine == Engine.D2:
                styles["stroke"] = "red"
                styles["stroke-width"] = "6"
                styles["double-border"] = "true"
            elif engine == Engine.GRAPHVIZ:
                styles["color"] = "red"
                styles["penwidth"] = "5"
                styles["style"] = styles.get("style", "") + ",bold"

        if node.is_tagged("behind"):
            if engine == Engine.D2:
                styles["stroke"] = "orange"
                styles["stroke-dash"] = "5"
            elif engine == Engine.GRAPHVIZ:
                styles["color"] = "orange"
                styles["style"] = styles.get("style", "") + ",dashed"

        if node.is_tagged("orphan"):
            if engine == Engine.D2:
                styles["stroke"] = "grey"
                styles["stroke-dash"] = "3"
                styles["opacity"] = "0.6"
            elif engine == Engine.GRAPHVIZ:
                styles["color"] = "grey"
                styles["style"] = styles.get("style", "") + ",dashed"

        return styles

    def get_generic_link_style(
        node: Graphable[Any], subnode: Graphable[Any]
    ) -> dict[str, str]:
        styles = {}
        if node.edge_attributes(subnode).get("highlight"):
            if engine == Engine.D2:
                styles.update({"stroke": "#FFA500", "stroke-width": "6"})
            elif engine == Engine.GRAPHVIZ:
                styles.update({"color": "#FFA500", "penwidth": "4"})
        return styles

    if engine == Engine.MERMAID:

        def mermaid_style(node: Graphable[Any]) -> Optional[str]:
            style_parts = []
            for tag in node.tags:
                if tag.startswith("color:"):
                    color = tag.split(":", 1)[1]
                    style_parts.append(f"fill:{color}")
                    style_parts.append(
                        "color:black"
                        if color.startswith("#F") or color.startswith("#E")
                        else "color:white"
                    )
            if node.is_tagged("critical"):
                style_parts.append("stroke:red,stroke-width:4px")
            if node.is_tagged("behind"):
                style_parts.append(
                    "stroke:orange,stroke-width:2px,stroke-dasharray: 5 5"
                )
            if node.is_tagged("orphan"):
                style_parts.append(
                    "stroke:grey,stroke-width:1px,stroke-dasharray: 3 3,opacity:0.5"
                )
            return ",".join(style_parts) if style_parts else None

        def mermaid_link_style(
            node: Graphable[Any], subnode: Graphable[Any]
        ) -> Optional[str]:
            if node.edge_attributes(subnode).get("highlight"):
                return "stroke:#FFA500,stroke-width:4px"
            return None

        styling_config = MermaidStylingConfig(
            node_ref_fnc=node_ref_fnc,
            node_text_fnc=label_fnc,
            node_style_fnc=mermaid_style,
            link_style_fnc=mermaid_link_style,
        )
        fnc = export_topology_mermaid_image if as_image else export_topology_mermaid_mmd
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.GRAPHVIZ:
        styling_config = GraphvizStylingConfig(
            node_ref_fnc=node_ref_fnc,
            node_label_fnc=label_fnc,
            node_attr_fnc=get_generic_style,
            edge_attr_fnc=get_generic_link_style,
        )
        fnc = (
            export_topology_graphviz_image if as_image else export_topology_graphviz_dot
        )
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.D2:
        styling_config = D2StylingConfig(
            node_ref_fnc=node_ref_fnc,
            node_label_fnc=label_fnc,
            node_style_fnc=get_generic_style,
            edge_style_fnc=get_generic_link_style,
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

        graph = Graph(list(commits_dict.values()))
        apply_highlights(graph, config)
        return graph

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

from datetime import datetime
from typing import Any, Optional

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

from .core import GitCommit, GitLogConfig
from .models import Tag


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
        sanitize(t[len(Tag.BRANCH.value) :])
        for t in node.tags
        if t.startswith(Tag.BRANCH.value)
    ]
    tags = [
        sanitize(t[len(Tag.TAG.value) :])
        for t in node.tags
        if t.startswith(Tag.TAG.value)
    ]
    author_raw = next(
        (
            t[len(Tag.AUTHOR.value) :]
            for t in node.tags
            if t.startswith(Tag.AUTHOR.value)
        ),
        meta.author,
    )
    author = sanitize(author_raw)

    display_label = f"{meta.hash[:7]}"

    # Add PR status if present
    for tag in node.tags:
        if tag == Tag.PR_OPEN.value:
            display_label += " [PR Open]"
        elif tag == Tag.PR_MERGED.value:
            display_label += " [PR Merged]"
        elif tag == Tag.PR_CLOSED.value:
            display_label += " [PR Closed]"
        elif tag == Tag.PR_DRAFT.value:
            display_label += " [PR Draft]"

        if tag == Tag.PR_CONFLICT.value:
            display_label += " (CONFLICT)"

        if tag == Tag.WIP.value:
            display_label += " [WIP]"
        if tag == Tag.DIRECT_PUSH.value:
            display_label += " [DIRECT]"
        if tag == Tag.SQUASH_COMMIT.value:
            display_label += " [SQUASH]"
        if tag == Tag.SQUASHED.value:
            display_label += " [SQUASHED]"

    sep = " - "
    newline = " - "
    if engine in [Engine.D2, Engine.GRAPHVIZ, Engine.PLANTUML]:
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

    if engine == Engine.MERMAID:
        # Mermaid labels need quotes if they contain brackets or special chars
        safe_label = label.replace('"', '\\"')
        return f'"{safe_label}"'

    return label


def get_generic_style(node: Graphable[Any], engine: Engine) -> dict[str, str]:
    styles = {}

    # WIP highlighting (Yellow fill)
    if node.is_tagged(Tag.WIP.value):
        if engine == Engine.D2:
            styles.update({"fill": "#ffff00", "font-color": "black"})
        elif engine == Engine.GRAPHVIZ:
            styles.update({"fillcolor": "#ffff00", "style": "filled"})

    for tag in node.tags:
        if tag.startswith(Tag.COLOR.value):
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

    if node.is_tagged(Tag.CRITICAL.value):
        if engine == Engine.D2:
            styles["stroke"] = "red"
            styles["stroke-width"] = "6"
            styles["double-border"] = "true"
        elif engine == Engine.GRAPHVIZ:
            styles["color"] = "red"
            styles["penwidth"] = "5"
            styles["style"] = styles.get("style", "") + ",bold"

    if node.is_tagged(Tag.BEHIND.value):
        if engine == Engine.D2:
            styles["stroke"] = "orange"
            styles["stroke-dash"] = "5"
        elif engine == Engine.GRAPHVIZ:
            styles["color"] = "orange"
            styles["style"] = styles.get("style", "") + ",dashed"

    if node.is_tagged(Tag.ORPHAN.value):
        if engine == Engine.D2:
            styles["stroke"] = "grey"
            styles["stroke-dash"] = "3"
            styles["opacity"] = "0.6"
        elif engine == Engine.GRAPHVIZ:
            styles["color"] = "grey"
            styles["style"] = styles.get("style", "") + ",dashed"

    if node.is_tagged(Tag.LONG_RUNNING.value):
        if engine == Engine.D2:
            styles["stroke"] = "purple"
            styles["stroke-width"] = "4"
        elif engine == Engine.GRAPHVIZ:
            styles["color"] = "purple"
            styles["penwidth"] = "3"

    if node.is_tagged(Tag.PR_CONFLICT.value):
        if engine == Engine.D2:
            styles["stroke"] = "red"
            styles["stroke-width"] = "8"
        elif engine == Engine.GRAPHVIZ:
            styles["color"] = "red"
            styles["penwidth"] = "6"

    if node.is_tagged(Tag.DIRECT_PUSH.value):
        if engine == Engine.D2:
            styles["stroke"] = "#ff0000"
            styles["stroke-width"] = "10"
            styles["stroke-dash"] = "2"
        elif engine == Engine.GRAPHVIZ:
            styles["color"] = "#ff0000"
            styles["penwidth"] = "8"
            styles["style"] = styles.get("style", "") + ",dashed"

    return styles


def get_generic_link_style(
    node: Graphable[Any], subnode: Graphable[Any], engine: Engine
) -> dict[str, str]:
    styles = {}
    if node.edge_attributes(subnode).get(Tag.EDGE_PATH.value):
        if engine == Engine.D2:
            styles.update({"stroke": "#FFA500", "stroke-width": "6"})
        elif engine == Engine.GRAPHVIZ:
            styles.update({"color": "#FFA500", "penwidth": "4"})
    elif node.edge_attributes(subnode).get(Tag.EDGE_LONG_RUNNING.value):
        if engine == Engine.D2:
            styles.update({"stroke": "purple", "stroke-width": "4"})
        elif engine == Engine.GRAPHVIZ:
            styles.update({"color": "purple", "penwidth": "3"})
    elif node.edge_attributes(subnode).get(Tag.EDGE_LOGICAL_MERGE.value):
        if engine == Engine.D2:
            styles.update(
                {"stroke": "#808080", "stroke-width": "2", "stroke-dash": "5"}
            )
        elif engine == Engine.GRAPHVIZ:
            styles.update({"color": "#808080", "style": "dashed", "penwidth": "1"})
    return styles


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

        def mermaid_style(node: Graphable[Any]) -> Optional[str]:
            style_parts = []

            # WIP
            if node.is_tagged(Tag.WIP.value):
                style_parts.append("fill:#ffff00,color:black")

            for tag in node.tags:
                if tag.startswith(Tag.COLOR.value):
                    color = tag.split(":", 1)[1]
                    style_parts.append(f"fill:{color}")
                    style_parts.append(
                        "color:black"
                        if color.startswith("#F") or color.startswith("#E")
                        else "color:white"
                    )
            if node.is_tagged(Tag.CRITICAL.value):
                style_parts.append("stroke:red,stroke-width:4px")
            if node.is_tagged(Tag.BEHIND.value):
                style_parts.append(
                    "stroke:orange,stroke-width:2px,stroke-dasharray: 5 5"
                )
            if node.is_tagged(Tag.ORPHAN.value):
                style_parts.append(
                    "stroke:#666,stroke-width:2px,stroke-dasharray: 3 3"
                )
            if node.is_tagged(Tag.LONG_RUNNING.value) and not node.is_tagged(
                Tag.CRITICAL.value
            ):
                style_parts.append("stroke:purple,stroke-width:3px")
            if node.is_tagged(Tag.PR_CONFLICT.value):
                style_parts.append("stroke:red,stroke-width:6px")
            if node.is_tagged(Tag.DIRECT_PUSH.value):
                style_parts.append(
                    "stroke:#ff0000,stroke-width:8px,stroke-dasharray: 2 2"
                )
            return ",".join(style_parts) if style_parts else None

        def mermaid_link_style(
            node: Graphable[Any], subnode: Graphable[Any]
        ) -> Optional[str]:
            attrs = node.edge_attributes(subnode)
            if attrs.get(Tag.EDGE_PATH.value):
                return "stroke:#FFA500,stroke-width:4px"
            if attrs.get(Tag.EDGE_LONG_RUNNING.value):
                return "stroke:purple,stroke-width:3px"
            if attrs.get(Tag.EDGE_LOGICAL_MERGE.value):
                return "stroke:#808080,stroke-width:2px,stroke-dasharray: 5 5"
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
            node_attr_fnc=lambda n: get_generic_style(n, Engine.GRAPHVIZ),
            edge_attr_fnc=lambda n, sn: get_generic_link_style(n, sn, Engine.GRAPHVIZ),
        )
        fnc = (
            export_topology_graphviz_image if as_image else export_topology_graphviz_dot
        )
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.D2:
        styling_config = D2StylingConfig(
            node_ref_fnc=node_ref_fnc,
            node_label_fnc=label_fnc,
            node_style_fnc=lambda n: get_generic_style(n, Engine.D2),
            edge_style_fnc=lambda n, sn: get_generic_link_style(n, sn, Engine.D2),
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

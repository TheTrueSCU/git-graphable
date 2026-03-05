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

from .core import GitCommit, GitLogConfig, StyleInfo
from .models import Tag


def get_contrast_color(hex_color: str) -> str:
    """Determine if black or white text should be used based on color luminance."""
    color = hex_color.lstrip("#")
    if len(color) == 3:
        color = "".join([c * 2 for c in color])

    try:
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        # Perceived luminance formula (W3C standard)
        luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
        return "black" if luminance > 0.5 else "white"
    except (ValueError, IndexError):
        return "black"


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
        if tag == Tag.BACK_MERGE.value:
            display_label += " [BACK-MERGE]"
        if tag == Tag.CONTRIBUTOR_SILO.value:
            display_label += " [SILO]"
        if tag == Tag.ISSUE_INCONSISTENCY.value:
            display_label += " [ISSUE-DESYNC]"
        if tag == Tag.RELEASE_INCONSISTENCY.value:
            display_label += " [NOT-RELEASED]"
        if tag == Tag.COLLABORATION_GAP.value:
            display_label += " [COLLAB-GAP]"
        if tag == Tag.LONGEVITY_MISMATCH.value:
            display_label += " [LONGEVITY]"

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


def _map_to_d2(style: StyleInfo) -> dict[str, str]:
    d2 = {}
    if style.stroke:
        d2["stroke"] = style.stroke
    if style.fill:
        d2["fill"] = style.fill
        d2["font-color"] = get_contrast_color(style.fill)
    if style.width:
        d2["stroke-width"] = str(style.width)
    if style.dash == "dashed":
        d2["stroke-dash"] = "5"
    elif style.dash == "dotted":
        d2["stroke-dash"] = "2"
    if style.opacity is not None:
        d2["opacity"] = str(style.opacity)
    return d2


def _map_to_gv(style: StyleInfo) -> dict[str, str]:
    gv = {}
    if style.stroke:
        gv["color"] = style.stroke
    if style.fill:
        gv["fillcolor"] = style.fill
        gv["style"] = "filled"
    if style.width:
        gv["penwidth"] = str(style.width)
    if style.dash == "dashed":
        gv["style"] = gv.get("style", "") + ",dashed"
    elif style.dash == "dotted":
        gv["style"] = gv.get("style", "") + ",dotted"
    return gv


def get_generic_style(
    node: Graphable[Any], engine: Engine, config: GitLogConfig
) -> dict[str, str]:
    styles = {}
    theme = config.theme

    def apply(style: StyleInfo):
        if engine == Engine.D2:
            styles.update(_map_to_d2(style))
        elif engine == Engine.GRAPHVIZ:
            styles.update(_map_to_gv(style))

    # Fill tags (Author, Distance, Stale)
    for tag in node.tags:
        if tag.startswith(Tag.COLOR.value):
            color = tag.split(":", 1)[1]
            apply(StyleInfo(fill=color))

    # WIP
    if node.is_tagged(Tag.WIP.value):
        apply(theme.wip)

    # PR States
    if node.is_tagged(Tag.PR_OPEN.value):
        apply(theme.pr_open)
    elif node.is_tagged(Tag.PR_MERGED.value):
        apply(theme.pr_merged)
    elif node.is_tagged(Tag.PR_CLOSED.value):
        apply(theme.pr_closed)
    elif node.is_tagged(Tag.PR_DRAFT.value):
        apply(theme.pr_draft)

    # Overlays (Strokes)
    if node.is_tagged(Tag.CRITICAL.value):
        apply(theme.critical)
        if engine == Engine.D2:
            styles["double-border"] = "true"
        elif engine == Engine.GRAPHVIZ:
            styles["style"] = styles.get("style", "") + ",bold"

    if node.is_tagged(Tag.BEHIND.value):
        apply(theme.behind)

    if node.is_tagged(Tag.ORPHAN.value):
        apply(theme.orphan)

    if node.is_tagged(Tag.LONG_RUNNING.value):
        apply(theme.long_running)

    if node.is_tagged(Tag.PR_CONFLICT.value):
        apply(theme.pr_conflict)

    if node.is_tagged(Tag.DIRECT_PUSH.value):
        apply(theme.direct_push)

    if node.is_tagged(Tag.BACK_MERGE.value):
        apply(theme.back_merge)

    if node.is_tagged(Tag.CONTRIBUTOR_SILO.value):
        apply(theme.contributor_silo)

    return styles


def get_generic_link_style(
    node: Graphable[Any], subnode: Graphable[Any], engine: Engine, config: GitLogConfig
) -> dict[str, str]:
    styles = {}
    theme = config.theme

    def apply(style: StyleInfo):
        if engine == Engine.D2:
            styles.update(_map_to_d2(style))
        elif engine == Engine.GRAPHVIZ:
            styles.update(_map_to_gv(style))

    attrs = node.edge_attributes(subnode)
    if attrs.get(Tag.EDGE_PATH.value):
        apply(theme.edge_path)
    elif attrs.get(Tag.EDGE_LONG_RUNNING.value):
        apply(theme.edge_long_running)
    elif attrs.get(Tag.EDGE_LOGICAL_MERGE.value):
        apply(theme.edge_logical_merge)

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

        def _map_to_mermaid(style: StyleInfo) -> str:
            parts = []
            if style.fill:
                parts.append(f"fill:{style.fill}")
                parts.append(f"color:{get_contrast_color(style.fill)}")
            if style.stroke:
                parts.append(f"stroke:{style.stroke}")
            if style.width:
                parts.append(f"stroke-width:{style.width}px")
            if style.dash == "dashed":
                parts.append("stroke-dasharray: 5 5")
            elif style.dash == "dotted":
                parts.append("stroke-dasharray: 2 2")
            return ",".join(parts)

        def mermaid_style(node: Graphable[Any]) -> Optional[str]:
            style_parts = []
            theme = config.theme

            # 1. Fill base (Author, Distance, Stale)
            for tag in node.tags:
                if tag.startswith(Tag.COLOR.value):
                    color = tag.split(":", 1)[1]
                    style_parts.append(f"fill:{color}")
                    style_parts.append(f"color:{get_contrast_color(color)}")

            # 2. State Fills (WIP, PR Status)
            if node.is_tagged(Tag.WIP.value):
                style_parts.append(_map_to_mermaid(theme.wip))
            elif node.is_tagged(Tag.PR_OPEN.value):
                style_parts.append(_map_to_mermaid(theme.pr_open))
            elif node.is_tagged(Tag.PR_MERGED.value):
                style_parts.append(_map_to_mermaid(theme.pr_merged))
            elif node.is_tagged(Tag.PR_CLOSED.value):
                style_parts.append(_map_to_mermaid(theme.pr_closed))
            elif node.is_tagged(Tag.PR_DRAFT.value):
                style_parts.append(_map_to_mermaid(theme.pr_draft))

            # 3. Overlays (Strokes)
            if node.is_tagged(Tag.CRITICAL.value):
                style_parts.append(_map_to_mermaid(theme.critical))
            if node.is_tagged(Tag.BEHIND.value):
                style_parts.append(_map_to_mermaid(theme.behind))
            if node.is_tagged(Tag.ORPHAN.value):
                style_parts.append(_map_to_mermaid(theme.orphan))
            if node.is_tagged(Tag.LONG_RUNNING.value) and not node.is_tagged(
                Tag.CRITICAL.value
            ):
                style_parts.append(_map_to_mermaid(theme.long_running))
            if node.is_tagged(Tag.PR_CONFLICT.value):
                style_parts.append(_map_to_mermaid(theme.pr_conflict))
            if node.is_tagged(Tag.DIRECT_PUSH.value):
                style_parts.append(_map_to_mermaid(theme.direct_push))
            if node.is_tagged(Tag.BACK_MERGE.value):
                style_parts.append(_map_to_mermaid(theme.back_merge))
            if node.is_tagged(Tag.CONTRIBUTOR_SILO.value):
                style_parts.append(_map_to_mermaid(theme.contributor_silo))

            return ",".join(style_parts) if style_parts else None

        def mermaid_link_style(
            node: Graphable[Any], subnode: Graphable[Any]
        ) -> Optional[str]:
            attrs = node.edge_attributes(subnode)
            theme = config.theme
            if attrs.get(Tag.EDGE_PATH.value):
                return _map_to_mermaid(theme.edge_path)
            if attrs.get(Tag.EDGE_LONG_RUNNING.value):
                return _map_to_mermaid(theme.edge_long_running)
            if attrs.get(Tag.EDGE_LOGICAL_MERGE.value):
                return _map_to_mermaid(theme.edge_logical_merge)
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
            node_attr_fnc=lambda n: get_generic_style(n, Engine.GRAPHVIZ, config),
            edge_attr_fnc=lambda n, sn: get_generic_link_style(
                n, sn, Engine.GRAPHVIZ, config
            ),
        )
        fnc = (
            export_topology_graphviz_image if as_image else export_topology_graphviz_dot
        )
        graph.export(fnc, output_path, config=styling_config)
    elif engine == Engine.D2:
        styling_config = D2StylingConfig(
            node_ref_fnc=node_ref_fnc,
            node_label_fnc=label_fnc,
            node_style_fnc=lambda n: get_generic_style(n, Engine.D2, config),
            edge_style_fnc=lambda n, sn: get_generic_link_style(
                n, sn, Engine.D2, config
            ),
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

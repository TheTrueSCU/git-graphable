from datetime import datetime
from typing import Any, Dict, List, Optional

from graphable import Graph, Graphable
from graphable.views import (
    CytoscapeStylingConfig,
    D2StylingConfig,
    GraphvizStylingConfig,
    HtmlStylingConfig,
    MermaidStylingConfig,
    export_topology_d2,
    export_topology_d2_image,
    export_topology_graphviz_dot,
    export_topology_graphviz_image,
    export_topology_html,
    export_topology_mermaid_image,
    export_topology_mermaid_mmd,
)

from .core import Engine, GitCommit, GitLogConfig, StyleInfo
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
    if engine in [Engine.D2, Engine.GRAPHVIZ]:
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


def _get_cytoscape_stylesheet(config: GitLogConfig) -> List[Dict[str, Any]]:
    """Generate Cytoscape stylesheet from theme config."""
    theme = config.theme
    stylesheet = [
        {
            "selector": "node",
            "style": {
                "background-color": "#007bff",
                "label": "data(label)",
                "color": "#333",
                "text-valign": "center",
                "text-halign": "center",
                "width": "60px",
                "height": "60px",
                "font-size": "12px",
                "text-wrap": "wrap",
                "text-max-width": "150px",
            },
        },
        {
            "selector": "node:selected",
            "style": {
                "border-width": "4px",
                "border-color": "#ff0",
                "background-color": "#0056b3",
            },
        },
        {
            "selector": "edge",
            "style": {
                "width": 2,
                "line-color": "#ccc",
                "target-arrow-color": "#ccc",
                "target-arrow-shape": "triangle",
                "curve-style": "bezier",
            },
        },
    ]

    # Map tags to styles
    tag_styles = {
        Tag.WIP.value: theme.wip,
        Tag.PR_OPEN.value: theme.pr_open,
        Tag.PR_MERGED.value: theme.pr_merged,
        Tag.PR_CLOSED.value: theme.pr_closed,
        Tag.PR_DRAFT.value: theme.pr_draft,
        Tag.CRITICAL.value: theme.critical,
        Tag.BEHIND.value: theme.behind,
        Tag.ORPHAN.value: theme.orphan,
        Tag.LONG_RUNNING.value: theme.long_running,
        Tag.PR_CONFLICT.value: theme.pr_conflict,
        Tag.DIRECT_PUSH.value: theme.direct_push,
        Tag.BACK_MERGE.value: theme.back_merge,
        Tag.CONTRIBUTOR_SILO.value: theme.contributor_silo,
        Tag.ISSUE_INCONSISTENCY.value: theme.issue_inconsistency,
        Tag.RELEASE_INCONSISTENCY.value: theme.release_inconsistency,
        Tag.COLLABORATION_GAP.value: theme.collaboration_gap,
        Tag.LONGEVITY_MISMATCH.value: theme.longevity_mismatch,
    }

    for tag, style in tag_styles.items():
        cy_style = {}
        if style.fill:
            cy_style["background-color"] = style.fill
            cy_style["color"] = get_contrast_color(style.fill)
        if style.stroke:
            cy_style["border-color"] = style.stroke
            cy_style["border-width"] = str(style.width or 2)
            cy_style["border-style"] = (
                "dashed" if style.dash in ["dashed", "dotted"] else "solid"
            )
        if tag == Tag.CRITICAL.value:
            cy_style["shape"] = "diamond"

        if cy_style:
            stylesheet.append({"selector": f"node[tags *= '{tag}']", "style": cy_style})

    # Edge Styles
    edge_tag_styles = {
        Tag.EDGE_PATH.value: theme.edge_path,
        Tag.EDGE_LONG_RUNNING.value: theme.edge_long_running,
        Tag.EDGE_LOGICAL_MERGE.value: theme.edge_logical_merge,
    }

    for tag, style in edge_tag_styles.items():
        cy_style = {}
        if style.stroke:
            cy_style["line-color"] = style.stroke
            cy_style["width"] = style.width or 2
        if style.dash == "dashed":
            cy_style["line-style"] = "dashed"
        elif style.dash == "dotted":
            cy_style["line-style"] = "dotted"

        if cy_style:
            stylesheet.append({"selector": f"edge[tags *= '{tag}']", "style": cy_style})

    return stylesheet


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
    elif engine == Engine.HTML:
        # For HTML we use CytoscapeStylingConfig to pass tags and metadata
        def node_data_fnc(n):
            data = {
                "id": n.reference.hash,
                "label": get_node_text(n, config.date_format, engine),
                "author": n.reference.author,
                "hash": n.reference.hash,
                "message": n.reference.message,
                "tags": list(n.tags),
            }
            return data

        def edge_data_fnc(n, sn):
            attrs = n.edge_attributes(sn)
            # Encode active tags as true in metadata
            tags = [
                tag
                for tag in [
                    Tag.EDGE_PATH.value,
                    Tag.EDGE_LONG_RUNNING.value,
                    Tag.EDGE_LOGICAL_MERGE.value,
                ]
                if attrs.get(tag)
            ]
            return {"tags": tags}

        cy_config = CytoscapeStylingConfig(
            reference_fnc=node_ref_fnc,
            node_data_fnc=node_data_fnc,
            edge_data_fnc=edge_data_fnc,
        )
        html_config = HtmlStylingConfig(
            title=f"Git Graph: {config.production_branch}",
            cy_config=cy_config,
        )
        graph.export(export_topology_html, output_path, config=html_config)

        # Inject custom styles into the generated HTML
        import os

        if os.path.exists(output_path):
            import json
            import re

            full_stylesheet = _get_cytoscape_stylesheet(config)

            # Separate base stylesheet from tag-based rules
            # This ensures Cytoscape doesn't have "baked-in" styles that conflict with JS
            base_stylesheet = [
                s for s in full_stylesheet if "tags *=" not in s["selector"]
            ]

            # Map of tag to style for JS
            tag_to_style = {}
            for s in full_stylesheet:
                if "tags *=" in s["selector"]:
                    match = re.search(r"tags \*= '([^']+)'", s["selector"])
                    if match:
                        tag_to_style[match.group(1)] = s["style"]

            # Discover dynamic tags from the graph and add them to tag_to_style
            dynamic_tags = set()
            has_prs = False
            for node in graph:
                if Tag.PR_STATUS.value in node.tags:
                    has_prs = True
                for tag in node.tags:
                    if any(
                        tag.startswith(p)
                        for p in [
                            Tag.AUTHOR_HIGHLIGHT.value,
                            Tag.DISTANCE_COLOR.value,
                            Tag.STALE_COLOR.value,
                        ]
                    ) or tag in [
                        Tag.PR_OPEN.value,
                        Tag.PR_MERGED.value,
                        Tag.PR_CLOSED.value,
                        Tag.PR_DRAFT.value,
                        Tag.WIP.value,
                    ]:
                        dynamic_tags.add(tag)

            for tag in dynamic_tags:
                if any(
                    tag.startswith(p)
                    for p in [
                        Tag.AUTHOR_HIGHLIGHT.value,
                        Tag.DISTANCE_COLOR.value,
                        Tag.STALE_COLOR.value,
                    ]
                ):
                    color = tag.split(":", 1)[1]
                    tag_to_style[tag] = {
                        "background-color": color,
                        "color": get_contrast_color(color),
                    }

            cy_style_json = json.dumps(base_stylesheet, indent=2)

            with open(output_path, "r") as f:
                html_content = f.read()

            # Add CSS for the toggleable legend
            legend_css = """
        .legend {
            position: absolute;
            bottom: 20px;
            left: 10px;
            z-index: 999;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            font-size: 0.85em;
            max-height: 50vh;
            overflow-y: auto;
            min-width: 180px;
        }
        .legend h4 { margin: 0 0 8px 0; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
        .legend-section { margin-bottom: 12px; }
        .legend-section-title { font-weight: bold; margin-bottom: 6px; display: block; color: #555; font-size: 0.9em; }
        .legend-item { display: flex; align-items: center; margin-bottom: 4px; cursor: pointer; padding: 2px 4px; border-radius: 3px; }
        .legend-item:hover { background: #f0f0f0; }
        .legend-color { width: 12px; height: 12px; border-radius: 2px; margin-right: 8px; border: 1px solid #999; flex-shrink: 0; }
        .legend-label { flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .legend-input { margin-left: 10px; flex-shrink: 0; }
    </style>"""
            new_html = html_content.replace("    </style>", legend_css)

            # Inject Dagre scripts and Legend HTML
            dagre_scripts = """
    <script src="https://unpkg.com/dagre@0.7.4/dist/dagre.js"></script>
    <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
</head>"""
            new_html = new_html.replace("</head>", dagre_scripts)

            # Build Legend HTML with categorization
            fill_modes = []  # Mutually exclusive (radio)
            overlays = []  # Independent (checkbox)

            # Categorize tags
            fill_tags = {
                Tag.PR_OPEN.value,
                Tag.PR_MERGED.value,
                Tag.PR_CLOSED.value,
                Tag.PR_DRAFT.value,
            }

            # Discover what dynamic categories exist
            has_authors = any(
                t.startswith(Tag.AUTHOR_HIGHLIGHT.value) for t in dynamic_tags
            )
            has_distance = any(
                t.startswith(Tag.DISTANCE_COLOR.value) for t in dynamic_tags
            )
            has_stale = any(t.startswith(Tag.STALE_COLOR.value) for t in dynamic_tags)

            # 1. Fill Modes (Radio)
            fill_modes.append(
                '<div class="legend-item" onclick="setMode(\'none\', event)">'
                '<div class="legend-color" style="background-color: #007bff"></div>'
                '<span class="legend-label">Default</span>'
                '<input type="radio" name="fill-mode" id="mode-none" class="legend-input" checked onclick="event.stopPropagation(); setMode(\'none\', event)">'
                "</div>"
            )

            if has_authors:
                fill_modes.append(
                    '<div class="legend-item" onclick="setMode(\'authors\', event)">'
                    '<div class="legend-color" style="background: linear-gradient(to right, #ff0000, #00ff00, #0000ff)"></div>'
                    '<span class="legend-label">Authors</span>'
                    '<input type="radio" name="fill-mode" id="mode-authors" class="legend-input" onclick="event.stopPropagation(); setMode(\'authors\', event)">'
                    "</div>"
                )

            if has_distance:
                fill_modes.append(
                    '<div class="legend-item" onclick="setMode(\'distance\', event)">'
                    '<div class="legend-color" style="background: linear-gradient(to right, #eee, #00f)"></div>'
                    '<span class="legend-label">Distance</span>'
                    '<input type="radio" name="fill-mode" id="mode-distance" class="legend-input" onclick="event.stopPropagation(); setMode(\'distance\', event)">'
                    "</div>"
                )

            if has_stale:
                fill_modes.append(
                    '<div class="legend-item" onclick="setMode(\'stale\', event)">'
                    '<div class="legend-color" style="background: linear-gradient(to right, #f00, #ff0)"></div>'
                    '<span class="legend-label">Staleness</span>'
                    '<input type="radio" name="fill-mode" id="mode-stale" class="legend-input" onclick="event.stopPropagation(); setMode(\'stale\', event)">'
                    "</div>"
                )

            if has_prs:
                fill_modes.append(
                    '<div class="legend-item" onclick="setMode(\'pr_status\', event)">'
                    '<div class="legend-color" style="background: #28a745"></div>'
                    '<span class="legend-label">PR Status</span>'
                    '<input type="radio" name="fill-mode" id="mode-pr_status" class="legend-input" onclick="event.stopPropagation(); setMode(\'pr_status\', event)">'
                    "</div>"
                )

            # 2. Overlays (Checkbox)
            for tag, style in tag_to_style.items():
                if (
                    not any(
                        tag.startswith(p)
                        for p in [
                            Tag.AUTHOR_HIGHLIGHT.value,
                            Tag.DISTANCE_COLOR.value,
                            Tag.STALE_COLOR.value,
                        ]
                    )
                    and tag not in fill_tags
                    and tag != Tag.PR_STATUS.value
                ):
                    color = (
                        style.get("border-color") or style.get("line-color") or "#ccc"
                    )
                    label = tag.replace(":", " ").replace("_", " ").title()
                    label = label.replace("Contributor Silo", "Silo").replace(
                        "Release Inconsistency", "Rel. Gap"
                    )
                    is_checked = "checked" if tag == Tag.CRITICAL.value else ""
                    overlays.append(
                        f'<div class="legend-item" onclick="toggleOverlay(\'{tag}\', event)">'
                        f'<div class="legend-color" style="border-color: {color}; border-width: 2px; background: none;"></div>'
                        f'<span class="legend-label">{label}</span>'
                        f'<input type="checkbox" id="overlay-{tag}" class="legend-input" {is_checked} onclick="event.stopPropagation(); toggleOverlay(\'{tag}\', event)">'
                        f"</div>"
                    )

            legend_html = f"""
    <div class="legend" id="legend">
        <h4>Git Graph</h4>
        <div class="legend-section">
            <span class="legend-section-title">Color Mode</span>
            {"".join(fill_modes)}
        </div>
        <div class="legend-section">
            <span class="legend-section-title">Overlays</span>
            {"".join(overlays)}
        </div>
    </div>
    <div id="cy"></div>"""
            new_html = re.sub(r'<div\s+id="cy".*?</div>', legend_html, new_html)

            pattern = r"style:\s*\[.*?\]"
            replacement = f"style: {cy_style_json}"
            new_html = re.sub(pattern, replacement, new_html, flags=re.DOTALL)

            layout_config = {
                "name": "dagre",
                "rankDir": "BT",
                "nodeSep": 50,
                "edgeSep": 10,
                "rankSep": 100,
                "nodeDimensionsIncludeLabels": True,
                "animate": False,
            }
            cy_config_json = json.dumps(layout_config, indent=2)
            new_html = re.sub(
                r"layout:\s*\{.*?\}",
                f"layout: {cy_config_json}",
                new_html,
                flags=re.DOTALL,
            )

            # Ensure 'cyGraph' is globally accessible for testing
            new_html = re.sub(
                r"var\s+cy\s*=\s*cytoscape\(\{",
                "window.cyGraph = cytoscape({",
                new_html,
            )

            toggle_logic = f"""
        var tagStyles = {json.dumps(tag_to_style, indent=2)};
        var activeMode = 'none';
        var disabledOverlays = new Set();
        var fillTags = ["{Tag.PR_OPEN.value}", "{Tag.PR_MERGED.value}", "{Tag.PR_CLOSED.value}", "{Tag.PR_DRAFT.value}"];

        function syncOverlayState() {{
            disabledOverlays.clear();
            document.querySelectorAll('.legend-input[type="checkbox"]').forEach(function(cb) {{
                var tag = cb.id.replace('overlay-', '');
                if (!cb.checked) {{ disabledOverlays.add(tag); }}
            }});
        }}

        function setMode(mode, event) {{
            activeMode = mode;
            var radio = document.getElementById('mode-' + mode);
            if (radio) radio.checked = true;
            applyStyles();
        }}

        function toggleOverlay(tag, event) {{
            var checkbox = document.getElementById('overlay-' + tag);
            if (event && event.target !== checkbox) {{ checkbox.checked = !checkbox.checked; }}
            if (checkbox.checked) {{ disabledOverlays.delete(tag); }} 
            else {{ disabledOverlays.add(tag); }}
            applyStyles();
        }}

        function applyStyles() {{
            if (typeof cyGraph === 'undefined') return;
            
            // 1. Reset base styles
            cyGraph.nodes().style({{
                'background-color': '#007bff', 'color': '#333', 'border-width': 0,
                'border-color': 'transparent', 'shape': 'ellipse', 'opacity': 1
            }});
            cyGraph.edges().style({{ 'line-color': '#ccc', 'width': 2, 'line-style': 'solid', 'opacity': 1 }});

            // 2. Apply Fill Mode
            if (activeMode === 'authors') {{
                cyGraph.nodes().filter(n => (n.data('tags') || []).some(t => t.startsWith('{Tag.AUTHOR_HIGHLIGHT.value}'))).forEach(function(el) {{
                    var tag = el.data('tags').find(t => t.startsWith('{Tag.AUTHOR_HIGHLIGHT.value}'));
                    if (tag && tagStyles[tag]) el.style(tagStyles[tag]);
                }});
            }} else if (activeMode === 'distance') {{
                cyGraph.nodes().filter(n => (n.data('tags') || []).some(t => t.startsWith('{Tag.DISTANCE_COLOR.value}'))).forEach(function(el) {{
                    var tag = el.data('tags').find(t => t.startsWith('{Tag.DISTANCE_COLOR.value}'));
                    if (tag && tagStyles[tag]) el.style(tagStyles[tag]);
                }});
            }} else if (activeMode === 'stale') {{
                cyGraph.nodes().filter(n => (n.data('tags') || []).some(t => t.startsWith('{Tag.STALE_COLOR.value}'))).forEach(function(el) {{
                    var tag = el.data('tags').find(t => t.startsWith('{Tag.STALE_COLOR.value}'));
                    if (tag && tagStyles[tag]) el.style(tagStyles[tag]);
                }});
            }} else if (activeMode === 'pr_status') {{
                fillTags.forEach(function(tag) {{
                    if (tagStyles[tag]) {{ cyGraph.nodes().filter(n => (n.data('tags') || []).includes(tag)).style(tagStyles[tag]); }}
                }});
            }}

            // 3. Apply Overlays (Skipping Fill Tags to prevent conflicts)
            Object.keys(tagStyles).forEach(function(tag) {{
                if (fillTags.includes(tag) || tag === '{Tag.PR_STATUS.value}') return;
                if (tag.startsWith('{Tag.AUTHOR_HIGHLIGHT.value}') || tag.startsWith('{Tag.DISTANCE_COLOR.value}') || tag.startsWith('{Tag.STALE_COLOR.value}')) return;
                if (disabledOverlays.has(tag)) return;
                
                var selector = (tag.includes('edge') || tag.includes('highlight') || tag.includes('logical_merge') || tag.includes('long_running_edge')) ? 'edge' : 'node';
                cyGraph.elements(selector).filter(el => (el.data('tags') || []).includes(tag)).style(tagStyles[tag]);
            }});
            
            // 4. Re-apply selection style
            cyGraph.elements(':selected').style({{ 'border-width': '4px', 'border-color': '#ff0', 'background-color': '#0056b3' }});
        }}

        function initStyles() {{
            if (typeof cyGraph !== 'undefined') {{ syncOverlayState(); applyStyles(); }} 
            else {{ setTimeout(initStyles, 50); }}
        }}
        initStyles();
        """
            new_html = re.sub(
                r"\s*// Live Reload Logic.*?\(function\(\) \{.*?\}\)\(\);",
                toggle_logic,
                new_html,
                flags=re.DOTALL,
            )
            with open(output_path, "w") as f:
                f.write(new_html)
    else:
        graph.write(output_path)

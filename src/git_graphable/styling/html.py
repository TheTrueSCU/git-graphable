"""
HTML and Cytoscape-specific styling logic.
"""

import json
import os
import re
from typing import Any, Dict, List

from graphable import Graph
from graphable.views import (
    CytoscapeStylingConfig,
    HtmlStylingConfig,
    export_topology_html,
)

from ..core import Engine, GitCommit, GitLogConfig
from ..models import Tag
from ..templates import DAGRE_SCRIPTS, LEGEND_CSS, LEGEND_HTML, get_toggle_logic
from .base import get_contrast_color, get_node_text


def export_html(
    graph: Graph[GitCommit],
    output_path: str,
    config: GitLogConfig,
    node_ref_fnc: Any,
) -> None:
    """Helper to export interactive HTML graph."""

    def node_data_fnc(n):
        return {
            "id": n.reference.hash,
            "label": get_node_text(n, config.date_format, Engine.HTML),
            "author": n.reference.author,
            "hash": n.reference.hash,
            "message": n.reference.message,
            "tags": list(n.tags),
        }

    def edge_data_fnc(n, sn):
        attrs = n.edge_attributes(sn)
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

    if not os.path.exists(output_path):
        return

    full_stylesheet = _get_cytoscape_stylesheet(config)
    base_stylesheet = [s for s in full_stylesheet if "tags *=" not in s["selector"]]

    tag_to_style = {}
    for s in full_stylesheet:
        if "tags *=" in s["selector"]:
            match = re.search(r"tags \*= '([^']+)'", s["selector"])
            if match:
                tag_to_style[match.group(1)] = s["style"]

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

    with open(output_path, "r") as f:
        html_content = f.read()

    new_html = html_content.replace("    </style>", LEGEND_CSS)
    new_html = new_html.replace("</head>", DAGRE_SCRIPTS)

    fill_modes = [
        '<div class="legend-item" onclick="setMode(\'none\', event)">'
        '<div class="legend-color" style="background-color: #007bff"></div>'
        '<span class="legend-label">Default</span>'
        '<input type="radio" name="fill-mode" id="mode-none" class="legend-input" checked onclick="event.stopPropagation(); setMode(\'none\', event)">'
        "</div>"
    ]

    categories = [
        (
            Tag.AUTHOR_HIGHLIGHT.value,
            "authors",
            "Authors",
            "linear-gradient(to right, #ff0000, #00ff00, #0000ff)",
        ),
        (
            Tag.DISTANCE_COLOR.value,
            "distance",
            "Distance",
            "linear-gradient(to right, #eee, #00f)",
        ),
        (
            Tag.STALE_COLOR.value,
            "stale",
            "Staleness",
            "linear-gradient(to right, #f00, #ff0)",
        ),
    ]

    for prefix, mode, label, gradient in categories:
        if any(t.startswith(prefix) for t in dynamic_tags):
            fill_modes.append(
                f'<div class="legend-item" onclick="setMode(\'{mode}\', event)">'
                f'<div class="legend-color" style="background: {gradient}"></div>'
                f'<span class="legend-label">{label}</span>'
                f'<input type="radio" name="fill-mode" id="mode-{mode}" class="legend-input" onclick="event.stopPropagation(); setMode(\'{mode}\', event)">'
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

    overlays = []
    fill_tags = {
        Tag.PR_OPEN.value,
        Tag.PR_MERGED.value,
        Tag.PR_CLOSED.value,
        Tag.PR_DRAFT.value,
    }
    for tag, style in tag_to_style.items():
        if (
            not any(tag.startswith(p[0]) for p in categories)
            and tag not in fill_tags
            and tag != Tag.PR_STATUS.value
        ):
            color = style.get("border-color") or style.get("line-color") or "#ccc"
            label = tag.replace(":", " ").replace("_", " ").title()
            if tag == Tag.BEHIND.value:
                label = "Divergence"
            elif tag == Tag.WIP.value:
                label = "WIP"
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

    new_html = re.sub(
        r'<div\s+id="cy".*?</div>',
        LEGEND_HTML.format(fill_modes="".join(fill_modes), overlays="".join(overlays)),
        new_html,
    )
    new_html = re.sub(
        r"style:\s*\[.*?\]",
        f"style: {json.dumps(base_stylesheet, indent=2)}",
        new_html,
        flags=re.DOTALL,
    )

    layout_config = {
        "name": "dagre",
        "rankDir": "BT",
        "nodeSep": 50,
        "edgeSep": 10,
        "rankSep": 100,
        "nodeDimensionsIncludeLabels": True,
        "animate": False,
    }
    new_html = re.sub(
        r"layout:\s*\{.*?\}",
        f"layout: {json.dumps(layout_config, indent=2)}",
        new_html,
        flags=re.DOTALL,
    )
    new_html = re.sub(
        r"var\s+cy\s*=\s*cytoscape\(\{", "window.cyGraph = cytoscape({", new_html
    )

    toggle_logic = get_toggle_logic(json.dumps(tag_to_style, indent=2), Tag)
    new_html = re.sub(
        r"\s*// Live Reload Logic.*?\(function\(\) \{.*?\}\)\(\);",
        toggle_logic,
        new_html,
        flags=re.DOTALL,
    )

    with open(output_path, "w") as f:
        f.write(new_html)


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

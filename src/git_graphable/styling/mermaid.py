"""
Mermaid-specific styling logic.
"""

from typing import Any, Optional

from graphable import Graphable

from ..core import GitLogConfig, StyleInfo
from ..models import Tag
from .base import get_contrast_color


def mermaid_style(node: Graphable[Any], config: GitLogConfig) -> Optional[str]:
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
    node: Graphable[Any], subnode: Graphable[Any], config: GitLogConfig
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

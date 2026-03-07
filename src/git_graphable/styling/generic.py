"""
Generic styling logic for D2 and Graphviz engines.
"""

from typing import Any

from graphable import Graphable

from ..core import Engine, GitLogConfig, StyleInfo
from ..models import Tag
from .base import get_contrast_color


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

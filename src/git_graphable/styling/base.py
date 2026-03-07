"""
Core styling utilities and text generation for git-graphable.
"""

from datetime import datetime

from ..core import Engine, GitCommit
from ..models import Tag


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

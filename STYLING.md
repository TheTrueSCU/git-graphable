# Git Graphable Styling Guide

Git Graphable allows you to fully customize the visual presentation of your Git history graphs. This document outlines the default styles and how to override them.

## Default Node Styles

These styles are applied to commit nodes based on their state or identified hygiene patterns.

| Component | Stroke | Fill | Width | Dash | Opacity | Effect |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Critical** | `red` | - | `4` | `solid` | - | Thick Red Solid outline |
| **WIP** | - | `#ffff00` | - | - | - | Yellow background |
| **Divergence** | `orange` | - | `2` | `dashed`| - | Orange Dashed outline |
| **Orphan** | `grey` | - | - | `dashed`| `0.6` | Faded Grey Dashed outline |
| **Long Running**| `purple` | - | `3` | `solid` | - | Purple Solid outline |
| **PR Conflict** | `red` | - | `6` | `solid` | - | Very Thick Red outline |
| **Direct Push** | `#ff0000` | - | `8` | `dashed`| - | Thickest Red Dashed outline |
| **Back Merge** | `orange` | - | `4` | `dashed`| - | Thick Orange Dashed outline |
| **Silo** | `blue` | - | `6` | `solid` | - | Thick Blue Solid outline |
| **Issue Desync** | `orange` | - | `4` | `solid` | - | Thick Orange outline |
| **Release Gap** | `red` | - | `2` | `dashed`| - | Red Dashed outline |
| **Collab Gap** | `purple` | - | `4` | `dotted`| - | Purple Dotted outline |
| **Longevity** | `brown` | - | `3` | `solid` | - | Brown Solid outline |

## PR Status Colors

When `--highlight-pr-status` is enabled, commits belonging to Pull Requests are filled by state:

| State | Default Fill | Default Color Name |
| :--- | :--- | :--- |
| **PR Open** | `#28a745` | Green |
| **PR Merged** | `#6f42c1` | Purple |
| **PR Closed** | `#d73a49` | Red |
| **PR Draft** | `#808080` | Gray |

## Dynamic Highlighting (Gradients)

Some highlights use dynamic colors calculated based on commit metadata. These currently use hardcoded base colors:

| Feature | Fill Logic | Description |
| :--- | :--- | :--- |
| **Distance** | **Blue Gradient** | Fades from White (`#ffffff`) to Blue (`#e6e6ff`) based on topological distance. |
| **Stale Branch**| **Red Gradient** | Fades from White (`#ffffff`) to Red (`#ffaaaa`) based on branch age. |

## Default Edge Styles

Edge styles define the relationships between commits (e.g., parent-child, logical merges).

| Type | Stroke | Width | Dash | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Path** | `#FFA500` | `4` | `solid` | Highlighted path between two commits |
| **Long Running**| `purple` | `3` | `solid` | Commits on a long-running feature branch |
| **Logical Merge**| `#808080` | `2` | `dashed`| Links a squash-merge commit to its sources |

## Node Labels (Suffixes)

Labels are appended to the commit hash to provide immediate context without looking at colors.

| Suffix | Trigger |
| :--- | :--- |
| `[PR Open]` | Associated GitHub PR is Open |
| `[PR Merged]` | Associated GitHub PR is Merged |
| `[PR Closed]` | Associated GitHub PR is Closed |
| `[PR Draft]` | Associated GitHub PR is a Draft |
| `(CONFLICT)` | Associated GitHub PR has merge conflicts |
| `[WIP]` | Commit message contains "WIP", "fixup!", etc. |
| `[DIRECT]` | Non-merge commit pushed directly to protected branch |
| `[SQUASH]` | Commit is the result of a squashed PR |
| `[SQUASHED]` | Commit was part of a branch that was squashed |
| `[BACK-MERGE]` | Base branch was merged into this feature branch |
| `[SILO]` | Branch has many commits but only one author |
| `[ISSUE-DESYNC]`| Git branch is open but Issue Tracker ticket is closed |
| `[NOT-RELEASED]`| Issue is marked "Released" but commit isn't tagged in Git |
| `[COLLAB-GAP]` | Git commit author doesn't match Issue assignee |
| `[LONGEVITY]` | Large time gap between ticket creation and code activity |

## Author Palette

When `--highlight-authors` is enabled, authors are assigned colors from this default palette:

1.  `#FFD700` (Gold)
2.  `#C0C0C0` (Silver)
3.  `#CD7F32` (Bronze)
4.  `#ADD8E6` (Light Blue)
5.  `#90EE90` (Light Green)
6.  `#F08080` (Light Coral)
7.  `#E6E6FA` (Lavender)
8.  `#FFE4E1` (Misty Rose)

## Customizing Styles

### Via CLI (`--style`)

You can override specific properties using the `key:property:value` format.

```bash
# Change critical branch stroke to teal and width to 2
git-graphable . --style critical:stroke:teal --style critical:width:2

# Change PR Open fill to blue
git-graphable . --style pr_open:fill:blue
```

### Via TOML Configuration

Add a `[git-graphable.theme]` section to your `.git-graphable.toml` or `pyproject.toml`.

```toml
[git-graphable.theme]
author_palette = ["#008080", "#708090", "#DAA520"]

[git-graphable.theme.critical]
stroke = "teal"
width = 2

[git-graphable.theme.pr_open]
fill = "#00FF00"
```

## Engine Support Notes

*   **Mermaid**: Supports all properties. Width is mapped to `stroke-width`. Dash is mapped to `stroke-dasharray`.
*   **D2**: Supports all properties. `double-border` is automatically enabled for Critical nodes.
*   **Graphviz**: Supports all properties. `penwidth` is used for width. Dash is mapped to `style=dashed/dotted`.
*   **HTML**: Supports all properties via Cytoscape.js.

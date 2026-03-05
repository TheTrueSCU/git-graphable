# Git Graphable

A powerful Python tool to convert Git commit history into beautiful, interactive flowcharts using the `graphable` library. Supporting Mermaid, D2, Graphviz, and PlantUML.

## Git Plugin Support
When installed in your PATH, you can use this as a native Git plugin:
```bash
git graphable .
```

## Features

- **Multi-Engine Support**: Export to Mermaid (.mmd), D2 (.d2), Graphviz (.dot), or PlantUML (.puml).
- **Automatic Visualization**: Generates and opens an image (SVG/PNG) automatically if no output is specified.
- **Advanced Highlighting**: Visualize author patterns, topological distance, and specific merge paths.
- **GitHub Integration**: Highlight commits based on pull request status (Merged, Open, Closed, Draft) using the `gh` CLI.
- **Hygiene Analysis**: Identify commits that are "behind" a base branch with divergence analysis.
- **Flexible Input**: Works with local repository paths or remote Git URLs.
- **Dual CLI**: Modern Rich/Typer interface with a robust argparse fallback for bare environments.

## Installation

```bash
# Using uv (recommended)
uv sync --all-extras
```

## Usage

For a complete reference of all command-line options, see the [USAGE.md](USAGE.md) file.

```bash
# Basic usage (opens a Mermaid image)
uv run git-graphable .

# Highlight PR status (requires gh CLI)
uv run git-graphable . --highlight-pr-status

# Specify an engine and output file
uv run git-graphable https://github.com/TheTrueSCU/graphable/ --engine d2 -o graph.svg

# Simplify the graph (only show branches/tags)
uv run git-graphable . --simplify
```

## Highlighting Options

Git Graphable provides several ways to highlight commits and relationships. Multiple options can be combined to layer information.

| Option | Target | Effect | Conflicts With |
| :--- | :--- | :--- | :--- |
| `--highlight-authors` | **Fill** | Unique color per author | PR Status, Distance, Stale, WIP |
| `--highlight-pr-status` | **Fill/Stroke**| Color by PR state (Merged=Purple, Open=Green) | Authors, Distance, Stale, WIP |
| `--highlight-distance-from` | **Fill** | Blue gradient fading by distance | Authors, PR Status, Stale, WIP |
| `--highlight-stale` | **Fill** | Gradient white to red by age | Authors, PR Status, Distance, WIP |
| `--highlight-wip` | **Fill** | Yellow fill for WIP/TODO commits | Authors, PR Status, Distance, Stale |
| `--highlight-path` | **Edge** | Thick Orange edge connecting nodes | None |
| `--highlight-critical` | **Stroke** | Thick Red Solid outline | None |
| `--highlight-diverging-from` | **Stroke** | Orange Dashed outline | None |
| `--highlight-orphans` | **Stroke** | Grey Dashed outline | None |
| `--highlight-long-running` | **Stroke/Edge** | Purple outline and thick Purple edge | None |
| `--highlight-direct-pushes` | **Stroke** | Thick Red Dashed outline | None |

### Highlighting Priorities
- **Fill**: `--highlight-authors`, `--highlight-pr-status`, `--highlight-distance-from`, `--highlight-stale`, and `--highlight-wip` are mutually exclusive.
- **Edge**: Path highlighting (Thick Orange) takes priority over Long-Running highlighting (Thick Purple).
- **Stroke**: Critical outlines (Thick Red Solid) take priority over Direct Pushes (Thick Red Dashed), which take priority over PR Conflicts (Thick Red Solid), which take priority over all other outlines (Divergence, Orphan, Long-Running).

## Advanced Examples

### Hygiene Analysis
Identify problematic patterns like direct pushes to `main` or messy WIP commits:
```bash
uv run git-graphable . --highlight-direct-pushes --highlight-wip
```

### PR Status Highlighting
View the current state of all PRs in your repository graph:
```bash
uv run git-graphable . --highlight-pr-status
```

### Divergence Analysis (Hygiene)
Highlight commits that exist in `main` but are missing from your feature branches:
```bash
uv run git-graphable . --highlight-diverging-from main
```

### Large Repositories
For repositories with long histories, use the `--limit` flag to keep the graph readable and avoid engine rendering limits:
```bash
uv run git-graphable . --limit 100 --highlight-authors
```

## Configuration

Git Graphable can be configured via a TOML file (`.git-graphable.toml` or `pyproject.toml`). CLI flags always take precedence over configuration file settings.

### Configuration Locations
The tool searches for configuration in the following order:
1. File specified via `--config <path>`
2. `.git-graphable.toml` in the repository root
3. `pyproject.toml` in the repository root (under `[tool.git-graphable]`)

### Example `.git-graphable.toml`
```toml
[git-graphable]
production_branch = "main"
development_branch = "develop"
simplify = true
limit = 100
date_format = "%Y-%m-%d"
highlight_critical = true
critical_branches = ["main", "prod"]
highlight_pr_status = true
highlight_wip = true
wip_keywords = ["wip", "todo", "fixme", "temp"]
highlight_direct_pushes = true
```

### Example `pyproject.toml`
```toml
[tool.git-graphable]
development_branch = "main"
simplify = true
highlight_authors = true
```

## Development

Run tests and linting:
```bash
just check
```

### CI/CD
This project uses GitHub Actions for continuous integration and automated publishing:
- **CI**: Runs `just check` on all pushes and PRs to `main`.
- **Publish**: Automatically builds and publishes to PyPI when a version tag (`v*`) is pushed.

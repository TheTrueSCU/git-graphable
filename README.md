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

# Specify an engine and output file
uv run git-graphable https://github.com/TheTrueSCU/graphable/ --engine d2 -o graph.svg

# Simplify the graph (only show branches/tags)
uv run git-graphable . --simplify
```

## Highlighting Options

Git Graphable provides several ways to highlight commits and relationships. Multiple options can be combined to layer information.

| Option | Target | Effect | Conflicts With |
| :--- | :--- | :--- | :--- |
| `--highlight-authors` | **Fill** | Unique color per author | Distance, Stale |
| `--highlight-distance-from` | **Fill** | Blue gradient fading by distance | Authors, Stale |
| `--highlight-stale` | **Fill** | Gradient white to red by age | Authors, Distance |
| `--highlight-path` | **Edge** | Thick Orange edge connecting nodes | None |
| `--highlight-critical` | **Stroke** | Thick Red Solid outline | None |
| `--highlight-diverging-from` | **Stroke** | Orange Dashed outline | None |
| `--highlight-orphans` | **Stroke** | Grey Dashed outline | None |
| `--highlight-long-running` | **Stroke/Edge** | Purple outline and thick Purple edge | None |

### Highlighting Priorities
- **Fill**: `--highlight-authors`, `--highlight-distance-from`, and `--highlight-stale` are mutually exclusive.
- **Edge**: Path highlighting (Thick Orange) takes priority over Long-Running highlighting (Thick Purple).
- **Stroke**: Critical outlines (Thick Red) take priority over all other outlines (Divergence, Orphan, Long-Running).

## Advanced Examples

### Divergence Analysis (Hygiene)
Highlight commits that exist in `main` but are missing from your feature branches:
```bash
uv run git-graphable . --highlight-diverging-from main
```

### Path Highlighting
See the exact sequence of commits between a feature branch and a specific tag:
```bash
uv run git-graphable . --highlight-path develop..v1.0.0
```

### Large Repositories
For repositories with long histories, use the `--limit` flag to keep the graph readable and avoid engine rendering limits:
```bash
uv run git-graphable . --limit 100 --highlight-authors
```

## Development

Run tests and linting:
```bash
just check
```

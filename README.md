# Git Graphable

[![CI](https://github.com/TheTrueSCU/git-graphable/actions/workflows/ci.yml/badge.svg)](https://github.com/TheTrueSCU/git-graphable/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/endpoint?url=https://thetruescu.github.io/git-graphable/coverage.json)](https://thetruescu.github.io/git-graphable/)
[![Hygiene](https://img.shields.io/endpoint?url=https://thetruescu.github.io/git-graphable/hygiene_badge.json)](https://thetruescu.github.io/git-graphable/)


A powerful Python tool to convert Git commit history into beautiful, interactive flowcharts using the `graphable` library. Supporting Mermaid, D2, Graphviz, and HTML.

## Git Plugin Support
When installed in your PATH, you can use this as a native Git plugin:
```bash
git graphable analyze .
```

## 🚀 Live Interactive Demo
Check out the tool in action with our **[Live Interactive Demos](https://thetruescu.github.io/git-graphable/)**. Explore different hygiene scenarios and toggle overlays in real-time.


## Features

- **Multi-Engine Support**: Export to Mermaid (.mmd), D2 (.d2), Graphviz (.dot), or HTML (.html).
- **Automatic Visualization**: Generates and opens an image (PNG) automatically if no output is specified.
- **Advanced Highlighting**: Visualize author patterns, topological distance, and specific merge paths.
- **VCS Integration**: Highlight commits based on pull request/merge request status using `gh` (GitHub) or `glab` (GitLab) CLIs.
- **Hygiene Analysis**: Automatically detect WIP commits, direct pushes to protected branches, squashed PRs, back-merges, and contributor silos. Provides actionable intelligence with exact commit hashes and branch names.
- **Issue Tracker Integration**: Connect to Jira, GitHub Issues, GitLab Issues, or custom scripts to highlight status desyncs.
- **Security First**: Configuration trust mechanism enforces security by requiring explicit authorization (use `--trust`) to execute custom scripts or send credentials from repository-local configs.
- **Selective Ignores**: Suppress specific hygiene rules for given commit SHAs using the configuration file or `--ignore` CLI flag.
- **Remediation Guide**: Detailed guidelines in [HYGIENE.md](HYGIENE.md) help you reach a 100% score.
- **Dynamic Badges**: Host live Shields.io badges for Git Hygiene and Code Coverage on GitHub Pages.

## Installation

```bash
# Using uv (recommended)
uv sync --all-extras
```

## Usage

For a complete reference of all command-line options, see the [USAGE.md](USAGE.md) file. For visual demonstrations of all features, see [examples/EXAMPLES.md](examples/EXAMPLES.md).

```bash
# Basic usage (opens a Mermaid image)
uv run git-graphable analyze .

# Highlight PR status (requires gh CLI)
uv run git-graphable analyze . --highlight-pr-status

# Specify an engine and output file
uv run git-graphable analyze https://github.com/TheTrueSCU/graphable/ --engine d2 -o graph.svg

# Initialize a default configuration file
uv run git-graphable init

# Simplify the graph (only show branches/tags)
uv run git-graphable analyze . --simplify
```

## GitHub Action

Git Graphable can be easily integrated into your GitHub workflows to automatically generate hygiene reports on every push or pull request.

```yaml
jobs:
  git-hygiene:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Required to see full history

      - name: Generate Git Graph Reports
        uses: TheTrueSCU/git-graphable@v0.6.0
        with:
          production_branch: 'main'
          output_dir: 'reports'
```

### Inputs

The following inputs are available for the `git-graphable` action:

*   **`path`**
    *   Description: Path to the git repository
    *   Required: `false`
    *   Default: `'.'`
*   **`production_branch`**
    *   Description: The main production branch (e.g. main, master)
    *   Required: `false`
    *   Default: `'main'`
*   **`issue_engine`**
    *   Description: Issue tracker engine (github or jira)
    *   Required: `false`
*   **`github_token`**
    *   Description: GitHub token for issue integration
    *   Required: `false`
    *   Default: `${{ github.token }}`
*   **`output_dir`**
    *   Description: Directory to save the generated reports
    *   Required: `false`
    *   Default: `'git-graph-reports'`

The action generates a **simplified Mermaid summary** (for quick review) and a **full interactive HTML graph** (for deep-dive auditing), uploading them as workflow artifacts.

## Highlighting Options

Git Graphable provides several ways to highlight commits and relationships. Multiple options can be combined to layer information.

| Option | Target | Effect | Conflicts With |
| :--- | :--- | :--- | :--- |
| `--highlight-authors` | **Fill** | Unique color per author | PR Status, Distance, Stale |
| `--highlight-pr-status` | **Fill/Stroke**| Color by PR/MR state (Merged=Purple, Open=Green) | Authors, Distance, Stale |
| `--highlight-distance-from` | **Fill** | Blue gradient fading by distance | Authors, PR Status, Stale |
| `--highlight-stale` | **Fill** | Gradient white to red by age | Authors, PR Status, Distance |
| `--highlight-path` | **Edge** | Thick Orange edge connecting nodes | None |
| `--highlight-wip` | **Stroke/Fill** | Yellow highlight for WIP/TODO commits | None |
| `--highlight-critical` | **Stroke** | Thick Red Solid outline | None |
| `--highlight-diverging-from` | **Stroke** | Orange Dashed outline | None |
| `--highlight-orphans` | **Stroke** | Grey Dashed outline | None |
| `--highlight-long-running` | **Stroke/Edge** | Purple outline and thick Purple edge | None |
| `--highlight-direct-pushes` | **Stroke** | Thick Red Dashed outline | None |
| `--highlight-squashed` | **Stroke/Edge** | Grey Solid outline and dashed Grey logical merge edge | None |
| `--highlight-back-merges` | **Stroke** | Orange Dashed outline | None |
| `--highlight-silos` | **Stroke** | Blue Solid outline | None |
| `--highlight-issue-inconsistencies` | **Label** | Adds `[ISSUE-DESYNC]` label | None |
| `--highlight-release-inconsistencies`| **Label** | Adds `[NOT-RELEASED]` label | None |
| `--highlight-collaboration-gaps` | **Label** | Adds `[COLLAB-GAP]` label | None |
| `--highlight-longevity-mismatch` | **Label** | Adds `[LONGEVITY]` label | None |

For a full reference of the default visual styles and how to customize them, see [STYLING.md](STYLING.md).

## Advanced Examples

### Hygiene Analysis
Identify problematic patterns like direct pushes to `main`, messy WIP commits, back-merges from `main`, or contributor silos:
```bash
uv run git-graphable analyze . --highlight-direct-pushes --highlight-wip --highlight-squashed --highlight-back-merges --highlight-silos
```
> **Tip:** See [HYGIENE.md](HYGIENE.md) for a detailed guide on how to remediate these issues and improve your score.

### PR Status Highlighting
View the current state of all PRs in your repository graph:
```bash
uv run git-graphable analyze . --highlight-pr-status
```

### Divergence Analysis (Hygiene)
Highlight commits that exist in `main` but are missing from your feature branches:
```bash
uv run git-graphable analyze . --highlight-diverging-from main
```

### Issue Tracker Integration
Flag mismatches between your code and your tickets:
```bash
uv run git-graphable analyze . --highlight-issue-inconsistencies --issue-pattern "[A-Z]+-[0-9]+" --issue-engine jira --jira-url "https://your-org.atlassian.net"
```

### Customizable Scoring & Styling
Adjust hygiene penalties and visual styles to match your team's workflow:
```bash
# Aggressive penalty for direct pushes and custom teal color for critical branches
uv run git-graphable analyze . --check --penalty direct_push_penalty:50 --style critical:stroke:teal
```

### Interactive HTML Viewer
Generate a self-contained HTML file with a searchable graph, details sidebar, and an interactive legend to live-toggle all highlight modes:
```bash
uv run git-graphable analyze . --engine html -o graph.html
```

## Configuration

Git Graphable can be configured via a TOML file (`.git-graphable.toml` or `pyproject.toml`). CLI flags always take precedence over configuration file settings.

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
wip_keywords = ["wip", "todo", "fixme", "temp", "fixup!", "squash!"]
highlight_direct_pushes = true
highlight_squashed = true
highlight_back_merges = true
highlight_silos = true
silo_commit_threshold = 20
silo_author_count = 1

# Issue Tracker
highlight_issue_inconsistencies = true
highlight_release_inconsistencies = true
highlight_collaboration_gaps = true
highlight_longevity_mismatch = true
issue_pattern = "JIRA-[0-9]+"
issue_engine = "jira"
jira_url = "https://your-org.atlassian.net"
jira_closed_statuses = ["Done", "Closed", "Resolved"]
released_statuses = ["Released"]
author_mapping = { "Git Name" = "Jira Name" }
longevity_threshold_days = 14

# Custom Scoring
[git-graphable.hygiene_weights]
direct_push_penalty = 25
direct_push_cap = 75
wip_commit_penalty = 5

# Custom Theme
[git-graphable.theme.critical]
stroke = "teal"
width = 2

[git-graphable.theme.direct_push]
stroke = "magenta"
dash = "dotted"
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

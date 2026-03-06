# `git-graphable`

Git history hygiene analyzer and visualizer.

## Usage

```console
$ git-graphable [COMMAND] [ARGS]...
```

**Commands**:

* `analyze`: Analyze git history and generate a graph (default).
* `init`: Initialize a default `.git-graphable.toml` configuration file.

---

## `analyze`

Analyze git history and generate a graph. This is the default command; if no command is specified, `analyze` is assumed.

**Arguments**:

* `PATH`: Path to local directory or git URL  [required]

**Options**:

* `--config TEXT`: Path to TOML configuration file
* `--production-branch TEXT`: Production branch name (e.g. main, master)
* `--development-branch TEXT`: Development branch name (e.g. develop, main)
* `--date-format TEXT`: Date format for commit labels
* `--engine [mermaid|graphviz|d2|html]`: Visualization engine.
    *   **mermaid**: Static text export (default).
    *   **graphviz**: Static text export.
    *   **d2**: Static text export.
    *   **html**: **Interactive HTML Viewer**. Generates a self-contained file with a searchable graph, details sidebar, and a **dynamic legend** to toggle all highlight modes on/off.
* `-o, --output TEXT`: Output file path. If no output is provided, a temporary file is created and opened automatically.
* `--image`: Export as image even when output path is provided
* `--simplify`: Pass --simplify-by-decoration to git log
* `--limit INTEGER`: Limit the number of commits to process
* `--highlight-critical`: Highlight critical branches
* `--critical-branch TEXT`: Branch name to treat as critical
* `--highlight-authors`: Assign colors to different authors
* `--highlight-distance-from TEXT`: Base branch/hash for distance highlighting
* `--highlight-path TEXT`: Highlight path between two SHAs (START..END)
* `--highlight-diverging-from TEXT`: Base branch/hash for divergence/behind analysis
* `--highlight-orphans`: Highlight dangling/orphan commits
* `--highlight-stale`: Highlight stale branch tips
* `--stale-days INTEGER`: Threshold in days for stale branches
* `--highlight-long-running`: Highlight long-running branches
* `--long-running-days INTEGER`: Threshold in days for long-running branches
* `--long-running-base TEXT`: Base branch for long-running analysis
* `--highlight-pr-status`: Highlight commits based on GitHub PR status
* `--highlight-wip`: Highlight WIP/TODO commits
* `--wip-keyword TEXT`: Additional keyword to trigger WIP highlighting
* `--highlight-direct-pushes`: Highlight non-merge commits on protected branches
* `--highlight-squashed`: Highlight squashed PRs and logically link them
* `--highlight-back-merges`: Highlight redundant back-merges from base branch
* `--highlight-silos`: Highlight branches dominated by too few authors
* `--silo-threshold INTEGER`: Commit count threshold for silo detection
* `--silo-author-count INTEGER`: Author count threshold for silo detection
* `--highlight-issue-inconsistencies`: Highlight mismatches between Git and Issue Tracker
* `--issue-pattern TEXT`: Regex pattern to extract issue IDs
* `--issue-engine [github|jira|script]`: Engine to fetch issue statuses
* `--jira-url TEXT`: Base URL for Jira instance
* `--issue-script TEXT`: Shell command template for script engine
* `--highlight-release-inconsistencies`: Highlight issues marked Released but not tagged
* `--released-status TEXT`: External status name that counts as Released (multi-select)
* `--highlight-collaboration-gaps`: Highlight when Git author doesn't match Ticket assignee
* `--author-mapping TEXT`: Map Git author to Ticket assignee (format: git_name:ticket_name)
* `--highlight-longevity-mismatch`: Highlight large gap between issue creation and first commit
* `--longevity-days INTEGER`: Threshold in days for longevity mismatch detection
* `--penalty TEXT`: Override hygiene penalty (format: metric:value, e.g. direct_push_penalty:20)
* `--check`: Exit with non-zero if hygiene score is below threshold
* `--min-score INTEGER`: Minimum hygiene score required for --check
* `--bare`: Force bare mode (no rich output)
* `--help`: Show this message and exit.

---

## `init`

Initialize a default `.git-graphable.toml` configuration file.

**Options**:

* `-o, --output TEXT`: Path to create the config file  [default: .git-graphable.toml]
* `-f, --force`: Overwrite existing config file
* `--help`: Show this message and exit.

# `git-graphable`

Git graph to Mermaid/Graphviz/D2/HTML converter.

**Usage**:

```console
$ git-graphable [OPTIONS] PATH
```

**Arguments**:

* `PATH`: Path to local directory or git URL  [required]

**Options**:

* `--config TEXT`: Path to TOML configuration file
* `--production-branch TEXT`: Production branch name (e.g. main, master)
* `--development-branch TEXT`: Development branch name (e.g. develop, main)
* `--date-format TEXT`: Date format for commit labels  [default: %Y%m%d%H%M%S]
* `--engine [mermaid|graphviz|d2|html]`: Visualization engine (mermaid, graphviz, d2, html) [default: mermaid]
* `-o, --output TEXT`: Output file path
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
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

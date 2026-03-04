# `git-graphable`

Git graph to Mermaid/Graphviz/D2/PlantUML converter.

**Usage**:

```console
$ git-graphable [OPTIONS] PATH
```

**Arguments**:

* `PATH`: Path to local directory or git URL  [required]

**Options**:

* `--date-format TEXT`: Date format for commit labels  [default: %Y%m%d%H%M%S]
* `--engine [mermaid|graphviz|d2|plantuml]`: Visualization engine  [default: mermaid]
* `-o, --output TEXT`: Output file path
* `--image`: Export as image even when output path is provided
* `--simplify`: Pass --simplify-by-decoration to git log
* `--limit INTEGER`: Limit the number of commits to process
* `--highlight-critical TEXT`: Branch names to highlight as critical
* `--highlight-authors`: Assign colors to different authors
* `--highlight-distance-from TEXT`: Base branch/hash for distance highlighting
* `--highlight-path TEXT`: Highlight path between two SHAs (START..END)
* `--highlight-diverging-from TEXT`: Base branch/hash for divergence/behind analysis
* `--highlight-orphans`: Highlight dangling/orphan commits
* `--highlight-stale INTEGER`: Threshold in days to highlight stale branch tips
* `--highlight-long-running INTEGER`: Threshold in days to highlight long-running branches
* `--long-running-base TEXT`: Base branch for long-running analysis  [default: main]
* `--bare`: Force bare mode (no rich output)
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

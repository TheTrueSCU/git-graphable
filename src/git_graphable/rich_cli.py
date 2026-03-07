import importlib.resources
import os
from typing import List, Optional

import typer
from rich.console import Console

from .cli_utils import parse_style_overrides
from .commands import convert_command
from .core import Engine

app = typer.Typer(
    help="Git graph to Mermaid/Graphviz/D2/HTML converter.", no_args_is_help=True
)
console = Console()
error_console = Console(stderr=True)


@app.command(help="Initialize a default .git-graphable.toml configuration file.")
def init(
    output_path: str = typer.Option(
        ".git-graphable.toml", "--output", "-o", help="Path to create the config file"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing config file"
    ),
):
    if os.path.exists(output_path) and not force:
        error_console.print(
            f"[red]Error:[/red] File {output_path} already exists. Use --force to overwrite."
        )
        raise typer.Exit(1)

    try:
        # Read from the bundled default_config.toml
        ref = importlib.resources.files("git_graphable") / "default_config.toml"
        config_content = ref.read_text()
    except Exception as e:
        error_console.print(
            f"[red]Error:[/red] Could not load default configuration: {e}"
        )
        raise typer.Exit(1)

    with open(output_path, "w") as f:
        f.write(config_content)
    console.print(f"[green]Successfully initialized {output_path}[/green]")


@app.command(help="Analyze git history and generate a graph.")
def analyze(
    path: str = typer.Argument(..., help="Path to local directory or git URL"),
    config_path: Optional[str] = typer.Option(
        None, "--config", help="Path to TOML configuration file"
    ),
    production_branch: Optional[str] = typer.Option(
        None, "--production-branch", help="Production branch name (e.g. main, master)"
    ),
    development_branch: Optional[str] = typer.Option(
        None,
        "--development-branch",
        help="Development branch name (e.g. develop, main)",
    ),
    date_format: Optional[str] = typer.Option(
        None, "--date-format", help="Date format for commit labels"
    ),
    engine: str = typer.Option(
        "mermaid", "--engine", help="Visualization engine (mermaid, graphviz, d2, html)"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
    as_image: bool = typer.Option(
        False, "--image", help="Export as image even when output path is provided"
    ),
    simplify: bool = typer.Option(
        False, "--simplify", help="Pass --simplify-by-decoration to git log"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Limit the number of commits to process"
    ),
    highlight_critical: bool = typer.Option(
        False, "--highlight-critical", help="Highlight critical branches"
    ),
    critical_branch: List[str] = typer.Option(
        [], "--critical-branch", help="Branch name to treat as critical"
    ),
    highlight_authors: bool = typer.Option(
        False, "--highlight-authors", help="Assign colors to different authors"
    ),
    highlight_distance_from: Optional[str] = typer.Option(
        None, "--highlight-distance-from", help="Base branch/hash for distance"
    ),
    highlight_path: Optional[str] = typer.Option(
        None, "--highlight-path", help="Highlight path between two SHAs (START..END)"
    ),
    highlight_diverging_from: Optional[str] = typer.Option(
        None,
        "--highlight-diverging-from",
        help="Base branch/hash for divergence/behind analysis",
    ),
    highlight_orphans: bool = typer.Option(
        False, "--highlight-orphans", help="Highlight dangling/orphan commits"
    ),
    highlight_stale: bool = typer.Option(
        False, "--highlight-stale", help="Highlight stale branch tips"
    ),
    stale_days: Optional[int] = typer.Option(
        None, "--stale-days", help="Threshold in days for stale branches"
    ),
    highlight_long_running: bool = typer.Option(
        False, "--highlight-long-running", help="Highlight long-running branches"
    ),
    long_running_days: Optional[int] = typer.Option(
        None, "--long-running-days", help="Threshold in days for long-running branches"
    ),
    long_running_base: Optional[str] = typer.Option(
        None, "--long-running-base", help="Base branch for long-running analysis"
    ),
    highlight_pr_status: bool = typer.Option(
        False,
        "--highlight-pr-status",
        help="Highlight commits based on GitHub PR status",
    ),
    highlight_wip: bool = typer.Option(
        False, "--highlight-wip", help="Highlight WIP/TODO commits"
    ),
    wip_keyword: List[str] = typer.Option(
        [], "--wip-keyword", help="Additional keyword to trigger WIP highlighting"
    ),
    highlight_direct_pushes: bool = typer.Option(
        False,
        "--highlight-direct-pushes",
        help="Highlight non-merge commits on protected branches",
    ),
    highlight_squashed: bool = typer.Option(
        False,
        "--highlight-squashed",
        help="Highlight commits that appear to be squash-merged",
    ),
    highlight_back_merges: bool = typer.Option(
        False,
        "--highlight-back-merges",
        help="Highlight redundant back-merges from base branch",
    ),
    highlight_silos: bool = typer.Option(
        False,
        "--highlight-silos",
        help="Highlight branches dominated by too few authors",
    ),
    silo_threshold: Optional[int] = typer.Option(
        None, "--silo-threshold", help="Commit count threshold for silo detection"
    ),
    silo_author_count: Optional[int] = typer.Option(
        None, "--silo-author-count", help="Author count threshold for silo detection"
    ),
    highlight_issue_inconsistencies: bool = typer.Option(
        False,
        "--highlight-issue-inconsistencies",
        help="Highlight mismatches between Git and Issue Tracker",
    ),
    issue_pattern: Optional[str] = typer.Option(
        None, "--issue-pattern", help="Regex pattern to extract issue IDs"
    ),
    issue_engine: Optional[str] = typer.Option(
        None, "--issue-engine", help="Engine to fetch issue statuses"
    ),
    jira_url: Optional[str] = typer.Option(
        None, "--jira-url", help="Base URL for Jira instance"
    ),
    issue_script: Optional[str] = typer.Option(
        None,
        "--issue-script",
        help="Path to script for checking issue status (receives ID as arg)",
    ),
    highlight_release_inconsistencies: bool = typer.Option(
        False,
        "--highlight-release-inconsistencies",
        help="Highlight issues marked Released but missing a Git tag",
    ),
    released_statuses: List[str] = typer.Option(
        [], "--released-status", help="External status name that counts as Released"
    ),
    highlight_collaboration_gaps: bool = typer.Option(
        False,
        "--highlight-collaboration-gaps",
        help="Highlight when Git author doesn't match Ticket assignee",
    ),
    author_mapping: List[str] = typer.Option(
        [],
        "--author-mapping",
        help="Map Git author to Ticket assignee (format: git_name:ticket_name)",
    ),
    highlight_longevity_mismatch: bool = typer.Option(
        False,
        "--highlight-longevity-mismatch",
        help="Highlight large gap between issue creation and first commit",
    ),
    longevity_days: Optional[int] = typer.Option(
        None, "--longevity-days", help="Threshold in days for longevity mismatch"
    ),
    penalty: List[str] = typer.Option(
        [],
        "--penalty",
        help="Override hygiene penalty (format: metric:value, e.g. direct_push_penalty:20)",
    ),
    style: List[str] = typer.Option(
        [],
        "--style",
        help="Override visual style (format: key:property:value, e.g. critical:stroke:teal)",
    ),
    check: bool = typer.Option(
        False,
        "--check",
        help="Exit with non-zero if hygiene score is below threshold",
    ),
    min_score: Optional[int] = typer.Option(
        None, "--min-score", help="Minimum hygiene score required for --check"
    ),
    hygiene_output: Optional[str] = typer.Option(
        None, "--hygiene-output", help="Path to save hygiene summary as JSON"
    ),
):
    """Convert Git history to graph."""
    try:
        engine_enum = Engine[engine.upper()]

        # Validate conflicting highlights
        fill_highlights = [
            highlight_authors,
            highlight_pr_status,
            highlight_distance_from is not None,
            highlight_stale,
            highlight_wip,
        ]
        if sum(1 for h in fill_highlights if h) > 1:
            error_console.print(
                "[red]Error: Cannot use multiple fill-based highlights (Authors, PR Status, Distance, Stale, WIP)[/red]"
            )
            raise typer.Exit(1)

        overrides = {
            "engine": engine_enum,
            "production_branch": production_branch,
            "development_branch": development_branch,
            "date_format": date_format,
            "simplify": simplify,
            "limit": limit,
            "highlight_critical": highlight_critical if highlight_critical else None,
            "critical_branches": critical_branch,
            "highlight_authors": highlight_authors if highlight_authors else None,
            "highlight_distance_from": highlight_distance_from,
            "highlight_path": tuple(highlight_path.split("..", 1))
            if highlight_path and ".." in highlight_path
            else None,
            "highlight_diverging_from": highlight_diverging_from,
            "highlight_orphans": highlight_orphans if highlight_orphans else None,
            "highlight_stale": highlight_stale if highlight_stale else None,
            "stale_days": stale_days,
            "highlight_long_running": highlight_long_running
            if highlight_long_running
            else None,
            "long_running_days": long_running_days,
            "long_running_base": long_running_base,
            "highlight_pr_status": highlight_pr_status if highlight_pr_status else None,
            "highlight_wip": highlight_wip if highlight_wip else None,
            "wip_keywords": wip_keyword,
            "highlight_direct_pushes": highlight_direct_pushes
            if highlight_direct_pushes
            else None,
            "highlight_squashed": highlight_squashed if highlight_squashed else None,
            "highlight_back_merges": highlight_back_merges
            if highlight_back_merges
            else None,
            "highlight_silos": highlight_silos if highlight_silos else None,
            "silo_commit_threshold": silo_threshold,
            "silo_author_count": silo_author_count,
            "highlight_issue_inconsistencies": highlight_issue_inconsistencies
            if highlight_issue_inconsistencies
            else None,
            "issue_pattern": issue_pattern,
            "issue_engine": issue_engine,
            "jira_url": jira_url,
            "issue_script": issue_script,
            "highlight_release_inconsistencies": highlight_release_inconsistencies
            if highlight_release_inconsistencies
            else None,
            "released_statuses": released_statuses,
            "highlight_collaboration_gaps": highlight_collaboration_gaps
            if highlight_collaboration_gaps
            else None,
            "author_mapping": dict(m.split(":", 1) for m in author_mapping)
            if author_mapping
            else {},
            "highlight_longevity_mismatch": highlight_longevity_mismatch
            if highlight_longevity_mismatch
            else None,
            "longevity_threshold_days": longevity_days,
            "hygiene_weights": {
                p.split(":", 1)[0]: int(p.split(":", 1)[1]) for p in penalty
            }
            if penalty
            else {},
            "theme": parse_style_overrides(style) if style else {},
            "min_hygiene_score": min_score,
            "hygiene_output": hygiene_output,
        }

        results = convert_command(
            path, config_path, overrides, engine_enum, output, as_image, check
        )
        if output == "-":
            console.print(results["content"])

        if results.get("summary"):
            import json

            from rich.table import Table

            summary = results["summary"]
            hygiene = summary.get("Hygiene Score", {})

            if hygiene_output:
                with open(hygiene_output, "w") as f:
                    json.dump(hygiene, f, indent=2)

            table = Table(title="Git Hygiene Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            score = hygiene.get("score", 0)
            grade = hygiene.get("grade", "F")
            color = hygiene.get("color", "red")

            table.add_row("Overall Score", f"[{color}]{score}% ({grade})[/{color}]")

            for deduction in hygiene.get("deductions", []):
                table.add_row(
                    f"  - {deduction['message']}",
                    f"[red]-{deduction['amount']}%[/red]",
                )

            console.print(table)

            if check:
                min_s = min_score or 80
                if score < min_s:
                    console.print(
                        f"[red]Error: Hygiene score {score}% is below required {min_s}%[/red]"
                    )
                    raise typer.Exit(1)
                else:
                    console.print(
                        f"[green]Success: Hygiene score {score}% meets required {min_s}%[/green]"
                    )

    except Exception as e:
        error_console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

import argparse
import sys
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console

from .commands import convert_command
from .core import Engine

app = typer.Typer(help="Git graph to Mermaid/Graphviz/D2/HTML converter.")
console = Console()
error_console = Console(stderr=True)


def _parse_style_overrides(styles: List[str]) -> Dict[str, Any]:
    """Parse key:prop:val list into nested theme dict."""
    theme = {}
    for s in styles:
        parts = s.split(":", 2)
        if len(parts) == 3:
            key, prop, val = parts
            if key not in theme:
                theme[key] = {}
            # Try to convert to int if possible (for width)
            if val.isdigit():
                val = int(val)
            theme[key][prop] = val
    return theme


@app.command(help="Git graph to Mermaid/Graphviz/D2/HTML converter.")
def convert(
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
        "-", "--output", "-o", help="Output file path"
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
        help="Highlight squashed PRs and logically link them",
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
        None, "--issue-script", help="Shell command template for script engine"
    ),
    highlight_release_inconsistencies: bool = typer.Option(
        False,
        "--highlight-release-inconsistencies",
        help="Highlight issues marked Released but not tagged",
    ),
    released_statuses: List[str] = typer.Option(
        [], "--released-status", help="External status name that counts as Released"
    ),
    highlight_collaboration_gaps: bool = typer.Option(
        False,
        "--highlight-collaboration_gaps",
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
    bare: bool = typer.Option(False, "--bare", help="Force bare mode (no rich output)"),
):
    """Convert Git history to graph."""
    engine_enum = Engine(engine.lower())

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
        "theme": _parse_style_overrides(style) if style else {},
        "min_hygiene_score": min_score,
    }

    if bare:
        try:
            results = convert_command(
                path, config_path, overrides, engine_enum, output, as_image, check
            )
            if output == "-":
                console.print(results["content"])
            if results.get("summary"):
                hygiene = results["summary"].get("Hygiene Score", {})
                score = hygiene.get("score", 0)
                min_s = min_score or 80
                if check:
                    if score < min_s:
                        console.print(
                            f"Error: Hygiene score {score}% is below required {min_s}%"
                        )
                        raise typer.Exit(1)
                    else:
                        console.print(
                            f"Success: Hygiene score {score}% meets required {min_s}%"
                        )
        except Exception as e:
            error_console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    else:
        try:
            results = convert_command(
                path, config_path, overrides, engine_enum, output, as_image, check
            )
            if output == "-":
                console.print(results["content"])

            if results.get("summary"):
                from rich.table import Table

                summary = results["summary"]
                hygiene = summary.get("Hygiene Score", {})

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

                # CI Check
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


def run_bare_cli():
    """Fallback entry point for minimal environments without Typer/Rich."""
    parser = argparse.ArgumentParser(description="Git graph to Mermaid converter.")
    parser.add_argument("path", help="Path to local directory or git URL")
    parser.add_argument("--config", help="Path to TOML configuration file")
    parser.add_argument("--production-branch", help="Production branch name")
    parser.add_argument("--development-branch", help="Development branch name")
    parser.add_argument("--date-format", help="Date format for commit labels")
    parser.add_argument(
        "--engine",
        default="mermaid",
        help="Visualization engine (mermaid, graphviz, d2)",
    )
    parser.add_argument("-o", "--output", default="-", help="Output file path")
    parser.add_argument(
        "--image", action="store_true", help="Export as image even if output path given"
    )
    parser.add_argument(
        "--simplify", action="store_true", help="Simplify graph by decorations"
    )
    parser.add_argument("--limit", type=int, help="Limit number of commits")
    parser.add_argument(
        "--highlight-critical", action="store_true", help="Highlight critical branches"
    )
    parser.add_argument(
        "--critical-branch", action="append", default=[], help="Critical branch names"
    )
    parser.add_argument(
        "--highlight-authors", action="store_true", help="Assign colors per author"
    )
    parser.add_argument("--highlight-distance-from", help="Base hash for distance")
    parser.add_argument("--highlight-path", help="Path between two SHAs (START..END)")
    parser.add_argument(
        "--highlight-diverging-from", help="Base for divergence analysis"
    )
    parser.add_argument(
        "--highlight-orphans", action="store_true", help="Highlight orphan commits"
    )
    parser.add_argument(
        "--highlight-stale", action="store_true", help="Highlight stale branches"
    )
    parser.add_argument("--stale-days", type=int, help="Days until branch is stale")
    parser.add_argument(
        "--highlight-long-running", action="store_true", help="Highlight long branches"
    )
    parser.add_argument("--long-running-days", type=int, help="Long branch threshold")
    parser.add_argument("--long-running-base", help="Base for long branch check")
    parser.add_argument(
        "--highlight-pr-status", action="store_true", help="Highlight PR states"
    )
    parser.add_argument(
        "--highlight-wip", action="store_true", help="Highlight WIP commits"
    )
    parser.add_argument(
        "--wip-keyword", action="append", default=[], help="Additional WIP keywords"
    )
    parser.add_argument(
        "--highlight-direct-pushes", action="store_true", help="Highlight direct pushes"
    )
    parser.add_argument(
        "--highlight-squashed", action="store_true", help="Highlight squashed PRs"
    )
    parser.add_argument(
        "--highlight-back-merges", action="store_true", help="Highlight back-merges"
    )
    parser.add_argument(
        "--highlight-silos", action="store_true", help="Highlight author silos"
    )
    parser.add_argument("--silo-threshold", type=int, help="Silo commit threshold")
    parser.add_argument("--silo-author-count", type=int, help="Silo author threshold")
    parser.add_argument(
        "--highlight-issue-inconsistencies",
        action="store_true",
        help="Highlight desyncs",
    )
    parser.add_argument("--issue-pattern", help="Regex for issue IDs")
    parser.add_argument("--issue-engine", help="Engine (github, jira, script)")
    parser.add_argument("--jira-url", help="Base URL for Jira instance")
    parser.add_argument(
        "--issue-script", help="Shell command template for script engine"
    )
    parser.add_argument(
        "--highlight-release-inconsistencies",
        action="store_true",
        help="Highlight issues marked Released but not tagged",
    )
    parser.add_argument(
        "--released-status",
        action="append",
        dest="released_statuses",
        default=[],
        help="External status name that counts as Released",
    )
    parser.add_argument(
        "--highlight-collaboration-gaps",
        action="store_true",
        help="Highlight when Git author doesn't match Ticket assignee",
    )
    parser.add_argument(
        "--author-mapping",
        action="append",
        default=[],
        help="Map Git author to Ticket assignee (format: git_name:ticket_name)",
    )
    parser.add_argument(
        "--highlight-longevity-mismatch",
        action="store_true",
        help="Highlight large gap between issue creation and first commit",
    )
    parser.add_argument(
        "--longevity-days",
        type=int,
        help="Threshold in days for longevity mismatch detection",
    )
    parser.add_argument(
        "--penalty",
        action="append",
        default=[],
        help="Override hygiene penalty (format: metric:value, e.g. direct_push_penalty:20)",
    )
    parser.add_argument(
        "--style",
        action="append",
        default=[],
        help="Override visual style (format: key:property:value, e.g. critical:stroke:teal)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with non-zero if hygiene score is below threshold",
    )
    parser.add_argument("--min-score", type=int, help="Minimum score for --check")
    parser.add_argument("--bare", action="store_true", help="Force bare mode")

    args = parser.parse_args()

    # Validate conflicting highlights
    fill_highlights = [
        args.highlight_authors,
        args.highlight_pr_status,
        args.highlight_distance_from is not None,
        args.highlight_stale,
        args.highlight_wip,
    ]
    if sum(1 for h in fill_highlights if h) > 1:
        print(
            "Error: Cannot use multiple fill-based highlights (Authors, PR Status, Distance, Stale, WIP)",
            file=sys.stderr,
        )
        sys.exit(1)

    engine_enum = Engine(args.engine.lower())
    overrides = {
        "engine": engine_enum,
        "production_branch": args.production_branch,
        "development_branch": args.development_branch,
        "date_format": args.date_format,
        "simplify": args.simplify,
        "limit": args.limit,
        "highlight_critical": args.highlight_critical
        if args.highlight_critical
        else None,
        "critical_branches": args.critical_branch,
        "highlight_authors": args.highlight_authors if args.highlight_authors else None,
        "highlight_distance_from": args.highlight_distance_from,
        "highlight_path": tuple(args.highlight_path.split("..", 1))
        if args.highlight_path and ".." in args.highlight_path
        else None,
        "highlight_diverging_from": args.highlight_diverging_from,
        "highlight_orphans": args.highlight_orphans if args.highlight_orphans else None,
        "highlight_stale": args.highlight_stale if args.highlight_stale else None,
        "stale_days": args.stale_days,
        "highlight_long_running": args.highlight_long_running
        if args.highlight_long_running
        else None,
        "long_running_days": args.long_running_days,
        "long_running_base": args.long_running_base,
        "highlight_pr_status": args.highlight_pr_status
        if args.highlight_pr_status
        else None,
        "highlight_wip": args.highlight_wip if args.highlight_wip else None,
        "wip_keywords": args.wip_keyword,
        "highlight_direct_pushes": args.highlight_direct_pushes
        if args.highlight_direct_pushes
        else None,
        "highlight_squashed": args.highlight_squashed
        if args.highlight_squashed
        else None,
        "highlight_back_merges": args.highlight_back_merges
        if args.highlight_back_merges
        else None,
        "highlight_silos": args.highlight_silos if args.highlight_silos else None,
        "silo_commit_threshold": args.silo_threshold,
        "silo_author_count": args.silo_author_count,
        "highlight_issue_inconsistencies": args.highlight_issue_inconsistencies
        if args.highlight_issue_inconsistencies
        else None,
        "issue_pattern": args.issue_pattern,
        "issue_engine": args.issue_engine,
        "jira_url": args.jira_url,
        "issue_script": args.issue_script,
        "highlight_release_inconsistencies": args.highlight_release_inconsistencies
        if args.highlight_release_inconsistencies
        else None,
        "released_statuses": args.released_statuses,
        "highlight_collaboration_gaps": args.highlight_collaboration_gaps
        if args.highlight_collaboration_gaps
        else None,
        "author_mapping": dict(m.split(":", 1) for m in args.author_mapping)
        if args.author_mapping
        else {},
        "highlight_longevity_mismatch": args.highlight_longevity_mismatch
        if args.highlight_longevity_mismatch
        else None,
        "longevity_threshold_days": args.longevity_days,
        "hygiene_weights": {
            p.split(":", 1)[0]: int(p.split(":", 1)[1]) for p in args.penalty
        }
        if args.penalty
        else {},
        "theme": _parse_style_overrides(args.style) if args.style else {},
        "min_hygiene_score": args.min_score,
    }

    try:
        results = convert_command(
            args.path,
            args.config,
            overrides,
            engine_enum,
            args.output,
            args.image,
            args.check,
        )
        if args.output == "-":
            print(results["content"])

        if results.get("summary"):
            summary = results["summary"]
            hygiene = summary.get("Hygiene Score", {})
            print("\n--- Git Hygiene Summary ---")
            print(
                f"Overall Score: {hygiene.get('score', 0)}% ({hygiene.get('grade', 'F')})"
            )
            for deduction in hygiene.get("deductions", []):
                print(f"  - {deduction['message']} (-{deduction['amount']}%)")

            # Check logic
            if args.check:
                min_s = args.min_score or 80
                if hygiene.get("score", 0) < min_s:
                    print(
                        f"Error: Hygiene score {hygiene.get('score', 0)}% is below required {min_s}%",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                else:
                    print(
                        f"Success: Hygiene score {hygiene.get('score', 0)}% meets required {min_s}%"
                    )

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for console_scripts."""
    run_bare_cli()


if __name__ == "__main__":
    app()

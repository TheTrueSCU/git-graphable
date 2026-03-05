import argparse
import os
import sys
import tempfile
import webbrowser
from typing import Any, Dict, List, Optional

from graphable.enums import Engine

# Try to import rich
try:
    import typer
    from rich.console import Console

    HAS_CLI_EXTRAS = True
except ImportError:
    HAS_CLI_EXTRAS = False

from .core import GitLogConfig, generate_summary, process_repo
from .styler import export_graph


def get_extension(engine: Engine, as_image: bool) -> str:
    """Get file extension for the given engine and export type."""
    if as_image:
        return ".svg"  # Default to SVG for images

    extensions = {
        Engine.MERMAID: ".mmd",
        Engine.GRAPHVIZ: ".dot",
        Engine.D2: ".d2",
        Engine.PLANTUML: ".puml",
    }
    return extensions.get(engine, ".txt")


def handle_output(
    graph,
    engine: Engine,
    output: Optional[str],
    config: GitLogConfig,
    as_image: bool = False,
):
    """Handles exporting and optionally opening the graph."""
    if output:
        # If output path is provided, we use the specified as_image flag or infer from extension
        image_exts = [".png", ".svg", ".jpg", ".jpeg", ".pdf"]
        is_image = as_image or any(output.lower().endswith(ext) for ext in image_exts)
        export_graph(graph, output, config, engine, as_image=is_image)
        print(f"Exported to {output}")
    else:
        # Create temp file and open as image
        ext = get_extension(engine, as_image=True)
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
            temp_path = tf.name

        export_graph(graph, temp_path, config, engine, as_image=True)
        print(f"Opening temporary image: {temp_path}")
        webbrowser.open(f"file://{os.path.abspath(temp_path)}")


def display_summary(summary: Dict[str, Any], bare: bool = False):
    """Displays a summary of flagged commits and hygiene score."""
    if not summary:
        return

    score_info = summary.get("Hygiene Score", {})

    if not bare and HAS_CLI_EXTRAS:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        console = Console()

        # 1. Hygiene Score Panel
        score = score_info.get("score", 100)
        grade = score_info.get("grade", "A")
        color = score_info.get("color", "green")

        score_text = Text()
        score_text.append("Overall Hygiene Score: ", style="bold")
        score_text.append(f"{score}% ", style=f"bold {color}")
        score_text.append(f"({grade})", style=f"bold {color}")

        deductions = score_info.get("deductions", [])
        if deductions:
            score_text.append("\n\nDeductions:", style="dim")
            for d in deductions:
                score_text.append(
                    f"\n  • -{d['amount']}%: {d['message']}", style="red dim"
                )

        console.print(Panel(score_text, title="Git Health Report", expand=False))

        # 2. Issues Table
        table = Table(
            title="Git Hygiene Summary", show_header=True, header_style="bold magenta"
        )
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="magenta")
        table.add_column("Examples (SHA - Message)", style="green")

        for key, commits in summary.items():
            if key == "Hygiene Score" or not commits:
                continue

            # Limit examples
            examples = commits[:3]
            example_str = "\n".join(
                [
                    f"{c.reference.hash[:7]} - {c.reference.message[:50]}"
                    for c in examples
                ]
            )
            table.add_row(key, str(len(commits)), example_str)

        if table.row_count > 0:
            console.print(table)
    else:
        # Bare output
        print("\n--- Git Hygiene Summary ---")
        if score_info:
            print(
                f"Overall Score: {score_info.get('score')}% ({score_info.get('grade')})"
            )
            for d in score_info.get("deductions", []):
                print(f"  - {d['message']} (-{d['amount']}%)")
        print("")

        for key, commits in summary.items():
            if key == "Hygiene Score" or not commits:
                continue
            print(f"{key}: {len(commits)}")
            for c in commits[:3]:
                print(f"  {c.reference.hash[:7]} - {c.reference.message[:50]}")
        print("---------------------------")


def validate_highlights(
    highlight_authors: bool,
    highlight_distance_from: Optional[str],
    highlight_stale: Optional[int],
    highlight_pr_status: bool,
) -> Optional[str]:
    """Check for conflicting fill-based highlight options."""
    active = []
    if highlight_authors:
        active.append("--highlight-authors")
    if highlight_distance_from:
        active.append("--highlight-distance-from")
    if highlight_stale:
        active.append("--highlight-stale")
    if highlight_pr_status:
        active.append("--highlight-pr-status")

    if len(active) > 1:
        return f"Error: Cannot use multiple fill-based highlights at once: {', '.join(active)}"
    return None


def load_config(
    path: str, config_path: Optional[str], cli_overrides: Dict[str, Any]
) -> GitLogConfig:
    """Loads configuration from TOML and merges with CLI overrides."""
    # Priority:
    # 1. CLI flags (cli_overrides)
    # 2. Config file provided via --config
    # 3. .git-graphable.toml in the repo
    # 4. pyproject.toml in the repo

    # Try to find a config file if not explicitly provided
    if not config_path:
        possible_paths = [
            os.path.join(path, ".git-graphable.toml"),
            os.path.join(path, "pyproject.toml"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                config_path = p
                break

    base_config = GitLogConfig()
    if config_path and os.path.exists(config_path):
        base_config = GitLogConfig.from_toml(config_path)

    return base_config.merge(cli_overrides)


# --- Bare Argument Parser CLI ---
def run_bare_cli(argv: List[str]):
    parser = argparse.ArgumentParser(
        description="Git graph to Mermaid/Graphviz/D2/PlantUML converter"
    )
    parser.add_argument("path", help="Path to local directory or git URL")
    parser.add_argument("--config", help="Path to TOML configuration file")
    parser.add_argument(
        "--production-branch", help="Production branch name (e.g. main, master)"
    )
    parser.add_argument(
        "--development-branch", help="Development branch name (e.g. develop, main)"
    )
    parser.add_argument(
        "--date-format", default="%Y%m%d%H%M%S", help="Date format for commit labels"
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="mermaid",
        choices=[e.value for e in Engine],
        help="Visualization engine",
    )
    parser.add_argument(
        "-o", "--output", help="Output file path (default: create and open temp image)"
    )
    parser.add_argument(
        "--image",
        action="store_true",
        help="Export as image even when output path is provided",
    )
    parser.add_argument(
        "--simplify",
        action="store_true",
        help="Pass --simplify-by-decoration to git log",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit the number of commits to process"
    )
    parser.add_argument(
        "--highlight-critical",
        action="store_true",
        help="Highlight critical branches",
    )
    parser.add_argument(
        "--critical-branch",
        action="append",
        dest="critical_branches",
        default=[],
        help="Branch name to treat as critical",
    )
    parser.add_argument(
        "--highlight-authors",
        action="store_true",
        help="Assign colors to different authors",
    )
    parser.add_argument(
        "--highlight-distance-from", help="Base branch/hash for distance highlighting"
    )
    parser.add_argument(
        "--highlight-path", help="Highlight path between two SHAs (format: START..END)"
    )
    parser.add_argument(
        "--highlight-diverging-from",
        help="Base branch/hash for divergence/behind analysis",
    )
    parser.add_argument(
        "--highlight-orphans",
        action="store_true",
        help="Highlight dangling/orphan commits",
    )
    parser.add_argument(
        "--highlight-stale",
        action="store_true",
        help="Highlight stale branch tips",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        help="Threshold in days for stale branches",
    )
    parser.add_argument(
        "--highlight-long-running",
        action="store_true",
        help="Highlight long-running branches",
    )
    parser.add_argument(
        "--long-running-days",
        type=int,
        help="Threshold in days for long-running branches",
    )
    parser.add_argument(
        "--long-running-base",
        default="main",
        help="Base branch for long-running analysis",
    )
    parser.add_argument(
        "--highlight-pr-status",
        action="store_true",
        help="Highlight commits based on GitHub PR status",
    )
    parser.add_argument(
        "--highlight-wip",
        action="store_true",
        help="Highlight WIP/TODO commits",
    )
    parser.add_argument(
        "--wip-keyword",
        action="append",
        dest="wip_keywords",
        default=[],
        help="Additional keyword to trigger WIP highlighting",
    )
    parser.add_argument(
        "--highlight-direct-pushes",
        action="store_true",
        help="Highlight non-merge commits on protected branches",
    )
    parser.add_argument(
        "--highlight-squashed",
        action="store_true",
        help="Highlight squashed PRs and logically link them",
    )
    parser.add_argument(
        "--highlight-back-merges",
        action="store_true",
        help="Highlight redundant back-merges from base branch",
    )
    parser.add_argument(
        "--highlight-silos",
        action="store_true",
        help="Highlight branches dominated by too few authors",
    )
    parser.add_argument(
        "--silo-threshold",
        type=int,
        help="Commit count threshold for silo detection",
    )
    parser.add_argument(
        "--silo-author-count",
        type=int,
        help="Author count threshold for silo detection",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with non-zero if hygiene score is below threshold",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        help="Minimum hygiene score required for --check",
    )
    parser.add_argument(
        "--bare", action="store_true", help="Force bare mode (already active)"
    )

    args = parser.parse_args(argv)

    error = validate_highlights(
        args.highlight_authors,
        args.highlight_distance_from,
        args.highlight_stale,
        args.highlight_pr_status,
    )
    if error:
        print(error, file=sys.stderr)
        sys.exit(1)

    engine = Engine(args.engine)

    highlight_path = None
    if args.highlight_path and ".." in args.highlight_path:
        parts = args.highlight_path.split("..")
        highlight_path = (parts[0], parts[1])

    overrides = {
        "production_branch": args.production_branch,
        "development_branch": args.development_branch,
        "simplify": args.simplify if args.simplify else None,
        "limit": args.limit,
        "date_format": args.date_format if args.date_format != "%Y%m%d%H%M%S" else None,
        "highlight_critical": args.highlight_critical
        if args.highlight_critical
        else None,
        "critical_branches": args.critical_branches,
        "highlight_authors": args.highlight_authors if args.highlight_authors else None,
        "highlight_distance_from": args.highlight_distance_from,
        "highlight_path": highlight_path,
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
        "wip_keywords": args.wip_keywords,
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
        "min_hygiene_score": args.min_score,
    }

    config = load_config(args.path, args.config, overrides)

    try:
        graph = process_repo(args.path, config)

        # Safety check
        if engine == Engine.MERMAID and len(graph) > 500:
            print(
                f"Warning: Graph contains {len(graph)} nodes. Mermaid might exceed size limits.",
                file=sys.stderr,
            )

        if not args.check:
            handle_output(graph, engine, args.output, config, as_image=args.image)

        summary = generate_summary(graph, config)
        display_summary(summary, bare=True)

        if args.check:
            score = summary.get("Hygiene Score", {}).get("score", 100)
            if score < config.min_hygiene_score:
                print(
                    f"\nError: Hygiene score {score}% is below required {config.min_hygiene_score}%",
                    file=sys.stderr,
                )
                sys.exit(1)
            else:
                print(
                    f"\nSuccess: Hygiene score {score}% meets required {config.min_hygiene_score}%"
                )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# --- Typer CLI ---
if HAS_CLI_EXTRAS:
    app = typer.Typer(
        help="Git graph to Mermaid/Graphviz/D2/PlantUML converter",
        no_args_is_help=True,
    )

    @app.command()
    def convert(
        path: str = typer.Argument(..., help="Path to local directory or git URL"),
        config_path: Optional[str] = typer.Option(
            None, "--config", help="Path to TOML configuration file"
        ),
        production_branch: Optional[str] = typer.Option(
            None, "--production-branch", help="Production branch name"
        ),
        development_branch: Optional[str] = typer.Option(
            None, "--development-branch", help="Development branch name"
        ),
        date_format: str = typer.Option(
            "%Y%m%d%H%M%S", help="Date format for commit labels"
        ),
        engine: Engine = typer.Option(Engine.MERMAID, help="Visualization engine"),
        output: Optional[str] = typer.Option(
            None, "--output", "-o", help="Output file path"
        ),
        image: bool = typer.Option(
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
        critical_branches: List[str] = typer.Option(
            [], "--critical-branch", help="Branch name to treat as critical"
        ),
        highlight_authors: bool = typer.Option(
            False, "--highlight-authors", help="Assign colors to different authors"
        ),
        highlight_distance_from: Optional[str] = typer.Option(
            None,
            "--highlight-distance-from",
            help="Base branch/hash for distance highlighting",
        ),
        highlight_path: Optional[str] = typer.Option(
            None,
            "--highlight-path",
            help="Highlight path between two SHAs (START..END)",
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
            None,
            "--long-running-days",
            help="Threshold in days for long-running branches",
        ),
        long_running_base: str = typer.Option(
            "main", "--long-running-base", help="Base branch for long-running analysis"
        ),
        highlight_pr_status: bool = typer.Option(
            False,
            "--highlight-pr-status",
            help="Highlight commits based on GitHub PR status",
        ),
        highlight_wip: bool = typer.Option(
            False, "--highlight-wip", help="Highlight WIP/TODO commits"
        ),
        wip_keywords: List[str] = typer.Option(
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
            None,
            "--silo-author-count",
            help="Author count threshold for silo detection",
        ),
        check: bool = typer.Option(
            False,
            "--check",
            help="Exit with non-zero if hygiene score is below threshold",
        ),
        min_score: Optional[int] = typer.Option(
            None, "--min-score", help="Minimum hygiene score required for --check"
        ),
        bare: bool = typer.Option(
            False, "--bare", help="Force bare mode (no rich output)"
        ),
    ):
        """Git graph to Mermaid/Graphviz/D2/PlantUML converter."""
        error = validate_highlights(
            highlight_authors,
            highlight_distance_from,
            highlight_stale,
            highlight_pr_status,
        )
        if error:
            typer.secho(error, fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

        path_tuple = None
        if highlight_path and ".." in highlight_path:
            parts = highlight_path.split("..")
            path_tuple = (parts[0], parts[1])

        overrides = {
            "production_branch": production_branch,
            "development_branch": development_branch,
            "simplify": simplify if simplify else None,
            "limit": limit,
            "date_format": date_format if date_format != "%Y%m%d%H%M%S" else None,
            "highlight_critical": highlight_critical if highlight_critical else None,
            "critical_branches": critical_branches,
            "highlight_authors": highlight_authors if highlight_authors else None,
            "highlight_distance_from": highlight_distance_from,
            "highlight_path": path_tuple,
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
            "wip_keywords": wip_keywords,
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
            "min_hygiene_score": min_score,
        }

        config = load_config(path, config_path, overrides)

        if bare:
            try:
                graph = process_repo(path, config)
                if engine == Engine.MERMAID and len(graph) > 500:
                    print(
                        f"Warning: Graph contains {len(graph)} nodes. Mermaid might exceed size limits.",
                        file=sys.stderr,
                    )
                if not check:
                    handle_output(graph, engine, output, config, as_image=image)

                summary = generate_summary(graph, config)
                display_summary(summary, bare=True)

                if check:
                    score = summary.get("Hygiene Score", {}).get("score", 100)
                    if score < config.min_hygiene_score:
                        print(
                            f"\nError: Hygiene score {score}% is below required {config.min_hygiene_score}%",
                            file=sys.stderr,
                        )
                        sys.exit(1)
                    else:
                        print(
                            f"\nSuccess: Hygiene score {score}% meets required {config.min_hygiene_score}%"
                        )
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
            return

        console = Console()
        with console.status(
            f"[bold green]Processing repository using {engine.value} engine..."
        ):
            try:
                graph = process_repo(path, config)

                if engine == Engine.MERMAID and len(graph) > 500:
                    console.print(
                        f"[bold yellow]Warning:[/] Graph contains {len(graph)} nodes. Mermaid might exceed size limits."
                    )

                if not check:
                    handle_output(graph, engine, output, config, as_image=image)

                summary = generate_summary(graph, config)
                display_summary(summary, bare=False)

                if check:
                    score = summary.get("Hygiene Score", {}).get("score", 100)
                    if score < config.min_hygiene_score:
                        console.print(
                            f"\n[bold red]Error:[/] Hygiene score {score}% is below required {config.min_hygiene_score}%"
                        )
                        raise typer.Exit(code=1)
                    else:
                        console.print(
                            f"\n[bold green]Success:[/] Hygiene score {score}% meets required {config.min_hygiene_score}%"
                        )
            except Exception as e:
                console.print(f"[bold red]Error:[/] {e}")
                sys.exit(1)
else:
    app = None


def main():
    # If forced bare OR if typer/rich are missing, use bare CLI
    if "--bare" in sys.argv or not HAS_CLI_EXTRAS:
        # Just pass everything except --bare to let argparse handle it
        bare_argv = [a for a in sys.argv[1:] if a != "--bare"]
        run_bare_cli(bare_argv)
    else:
        # Default to Typer
        if app is not None:
            app()
        else:
            # Fallback if Typer is somehow missing but logic got here
            run_bare_cli(sys.argv[1:])


if __name__ == "__main__":
    main()

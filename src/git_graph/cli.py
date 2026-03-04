import argparse
import os
import sys
import tempfile
import webbrowser
from typing import Dict, List, Optional

from graphable.enums import Engine

# Try to import rich
try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    HAS_CLI_EXTRAS = True
except ImportError:
    HAS_CLI_EXTRAS = False

from .core import GitCommit, GitLogConfig, export_graph, generate_summary, process_repo


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


def display_summary(summary: Dict[str, List[GitCommit]], bare: bool = False):
    """Displays a summary of flagged commits."""
    if bare:
        print("\n--- Git Hygiene Summary ---")
        for category, commits in summary.items():
            if commits:
                print(f"{category}: {len(commits)} commits")
                for c in commits[:5]:  # Show first 5
                    branches = (
                        f" ({', '.join(c.reference.branches)})"
                        if c.reference.branches
                        else ""
                    )
                    print(
                        f"  - {c.reference.hash[:7]}{branches}: {c.reference.message}"
                    )
                if len(commits) > 5:
                    print(f"  ... and {len(commits) - 5} more")
    else:
        console = Console()
        table = Table(title="Git Hygiene Summary", box=None)
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Count", style="magenta")
        table.add_column("Examples (SHA - Message)", style="green")

        for category, commits in summary.items():
            if commits:
                examples = []
                for c in commits[:3]:
                    examples.append(
                        f"{c.reference.hash[:7]} - {c.reference.message[:50]}"
                    )
                example_str = "\n".join(examples)
                if len(commits) > 3:
                    example_str += f"\n... and {len(commits) - 3} more"
                table.add_row(category, str(len(commits)), example_str)

        if table.row_count > 0:
            console.print(Panel(table, border_style="blue"))
        else:
            console.print("[bold green]History looks clean! No issues flagged.[/]")


def validate_highlights(
    highlight_authors: bool,
    highlight_distance_from: Optional[str],
    highlight_stale: Optional[int],
) -> Optional[str]:
    """Check for conflicting fill-based highlight options."""
    active = []
    if highlight_authors:
        active.append("--highlight-authors")
    if highlight_distance_from:
        active.append("--highlight-distance-from")
    if highlight_stale is not None:
        active.append("--highlight-stale")

    if len(active) > 1:
        return f"Error: Cannot use multiple fill-based highlights at once: {', '.join(active)}"
    return None


# --- Bare Argument Parser CLI ---
def run_bare_cli(argv: List[str]):
    parser = argparse.ArgumentParser(
        description="Git graph to Mermaid/Graphviz/D2/PlantUML converter"
    )
    parser.add_argument("path", help="Path to local directory or git URL")
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
        action="append",
        default=[],
        help="Branch names to highlight as critical",
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
        type=int,
        help="Threshold in days to highlight stale branch tips",
    )
    parser.add_argument(
        "--highlight-long-running",
        type=int,
        help="Threshold in days to highlight long-running branches",
    )
    parser.add_argument(
        "--long-running-base",
        default="main",
        help="Base branch for long-running analysis",
    )
    parser.add_argument(
        "--bare", action="store_true", help="Force bare mode (already active)"
    )

    args = parser.parse_args(argv)

    error = validate_highlights(
        args.highlight_authors, args.highlight_distance_from, args.highlight_stale
    )
    if error:
        print(error, file=sys.stderr)
        sys.exit(1)

    engine = Engine(args.engine)

    highlight_path = None
    if args.highlight_path and ".." in args.highlight_path:
        parts = args.highlight_path.split("..")
        highlight_path = (parts[0], parts[1])

    config = GitLogConfig(
        simplify=args.simplify,
        limit=args.limit,
        date_format=args.date_format,
        highlight_critical=args.highlight_critical,
        highlight_authors=args.highlight_authors,
        highlight_distance_from=args.highlight_distance_from,
        highlight_path=highlight_path,
        highlight_diverging_from=args.highlight_diverging_from,
        highlight_orphans=args.highlight_orphans,
        highlight_stale=args.highlight_stale,
        highlight_long_running=args.highlight_long_running,
        long_running_base=args.long_running_base,
    )

    try:
        graph = process_repo(args.path, config)

        # Safety check
        if engine == Engine.MERMAID and len(graph) > 500:
            print(
                f"Warning: Graph contains {len(graph)} nodes. Mermaid might exceed size limits.",
                file=sys.stderr,
            )

        handle_output(graph, engine, args.output, config, as_image=args.image)
        display_summary(generate_summary(graph), bare=True)
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
        highlight_critical: List[str] = typer.Option(
            [], "--highlight-critical", help="Branch names to highlight as critical"
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
        highlight_stale: Optional[int] = typer.Option(
            None,
            "--highlight-stale",
            help="Threshold in days to highlight stale branch tips",
        ),
        highlight_long_running: Optional[int] = typer.Option(
            None,
            "--highlight-long-running",
            help="Threshold in days to highlight long-running branches",
        ),
        long_running_base: str = typer.Option(
            "main", "--long-running-base", help="Base branch for long-running analysis"
        ),
        bare: bool = typer.Option(
            False, "--bare", help="Force bare mode (no rich output)"
        ),
    ):
        """Git graph to Mermaid/Graphviz/D2/PlantUML converter."""
        error = validate_highlights(
            highlight_authors, highlight_distance_from, highlight_stale
        )
        if error:
            typer.secho(error, fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

        path_tuple = None
        if highlight_path and ".." in highlight_path:
            parts = highlight_path.split("..")
            path_tuple = (parts[0], parts[1])

        config = GitLogConfig(
            simplify=simplify,
            limit=limit,
            date_format=date_format,
            highlight_critical=highlight_critical,
            highlight_authors=highlight_authors,
            highlight_distance_from=highlight_distance_from,
            highlight_path=path_tuple,
            highlight_diverging_from=highlight_diverging_from,
            highlight_orphans=highlight_orphans,
            highlight_stale=highlight_stale,
            highlight_long_running=highlight_long_running,
            long_running_base=long_running_base,
        )

        if bare:
            try:
                graph = process_repo(path, config)
                if engine == Engine.MERMAID and len(graph) > 500:
                    print(
                        f"Warning: Graph contains {len(graph)} nodes. Mermaid might exceed size limits.",
                        file=sys.stderr,
                    )
                handle_output(graph, engine, output, config, as_image=image)
                display_summary(generate_summary(graph), bare=True)
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

                handle_output(graph, engine, output, config, as_image=image)
                display_summary(generate_summary(graph), bare=False)
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

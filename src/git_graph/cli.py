import argparse
import os
import sys
import tempfile
import webbrowser
from typing import List, Optional

from graphable.enums import Engine

# Try to import rich/typer
try:
    import typer
    from rich.console import Console

    HAS_CLI_EXTRAS = True
except ImportError:
    HAS_CLI_EXTRAS = False

from .core import GitLogConfig, export_graph, process_repo


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
        "--bare", action="store_true", help="Force bare mode (already active)"
    )

    args = parser.parse_args(argv)

    if args.highlight_authors and args.highlight_distance_from:
        print(
            "Error: Cannot use both --highlight-authors and --highlight-distance-from at the same time.",
            file=sys.stderr,
        )
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
        bare: bool = typer.Option(
            False, "--bare", help="Force bare mode (no rich output)"
        ),
    ):
        """Git graph to Mermaid/Graphviz/D2/PlantUML converter."""
        if highlight_authors and highlight_distance_from:
            typer.secho(
                "Error: Cannot use both --highlight-authors and --highlight-distance-from at the same time.",
                fg=typer.colors.RED,
                err=True,
            )
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

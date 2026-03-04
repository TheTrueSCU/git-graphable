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
        "--bare", action="store_true", help="Force bare mode (already active)"
    )

    args = parser.parse_args(argv)
    engine = Engine(args.engine)
    config = GitLogConfig(
        simplify=args.simplify, limit=args.limit, date_format=args.date_format
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
        bare: bool = typer.Option(
            False, "--bare", help="Force bare mode (no rich output)"
        ),
    ):
        """Git graph to Mermaid/Graphviz/D2/PlantUML converter."""
        config = GitLogConfig(simplify=simplify, limit=limit, date_format=date_format)

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

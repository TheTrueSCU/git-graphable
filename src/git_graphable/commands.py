import os
import tempfile
import webbrowser
from typing import Any, Dict, Optional

from graphable.enums import Engine

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


def convert_command(
    path: str,
    config_path: Optional[str],
    cli_overrides: Dict[str, Any],
    engine: Engine,
    output: Optional[str],
    as_image: bool = False,
    is_check: bool = False,
) -> Dict[str, Any]:
    """
    Core logic for the convert command.
    Returns the summary dictionary.
    """
    config = load_config(path, config_path, cli_overrides)
    graph = process_repo(path, config)

    # Note: We return the graph and config too if needed, but summary is usually enough
    if not is_check:
        handle_output(graph, engine, output, config, as_image=as_image)

    summary = generate_summary(graph, config)
    return {"summary": summary, "config": config, "graph_size": len(graph)}

import os
import subprocess
import tempfile
import webbrowser
from typing import Any, Dict, Optional

from .core import Engine, GitLogConfig, generate_summary, process_repo
from .styler import export_graph


def get_extension(engine: Engine, as_image: bool) -> str:
    """Get file extension for the given engine and export type."""
    if as_image:
        return ".svg"  # Default to SVG for images

    extensions = {
        Engine.MERMAID: ".mmd",
        Engine.GRAPHVIZ: ".dot",
        Engine.D2: ".d2",
        Engine.HTML: ".html",
    }
    return extensions.get(engine, ".txt")


def handle_output(
    graph,
    engine: Engine,
    output: Optional[str],
    config: GitLogConfig,
    as_image: bool = False,
) -> Optional[str]:
    """Handles exporting and optionally opening the graph. Returns content if output is '-'."""
    if output == "-":
        # Capture to string
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            export_graph(graph, "-", config, engine, as_image=False)
        return f.getvalue()

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


def ensure_local_repo(path: str) -> tuple[str, Optional[tempfile.TemporaryDirectory]]:
    """Ensures the path is a local repository. Clones if it's a URL."""
    if path.startswith(("http://", "https://", "git@", "ssh://")):
        temp_dir = tempfile.TemporaryDirectory()
        print(f"Cloning remote repository {path}...")
        try:
            # Clone bare repo for speed and less disk space
            subprocess.run(
                ["git", "clone", "--bare", path, temp_dir.name],
                check=True,
                capture_output=True,
            )
            return temp_dir.name, temp_dir
        except subprocess.CalledProcessError as e:
            temp_dir.cleanup()
            raise RuntimeError(f"Failed to clone repository: {e.stderr.decode()}")
    return path, None


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
    local_path, temp_repo = ensure_local_repo(path)
    try:
        config = load_config(local_path, config_path, cli_overrides)
        graph = process_repo(local_path, config)

        content = None
        if not is_check:
            content = handle_output(graph, engine, output, config, as_image=as_image)

        summary = generate_summary(graph, config)
        return {
            "summary": summary,
            "config": config,
            "graph_size": len(graph),
            "content": content,
        }
    finally:
        if temp_repo:
            temp_repo.cleanup()

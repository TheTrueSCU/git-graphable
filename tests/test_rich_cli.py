import os
import shutil
import subprocess
import tempfile

import pytest
from typer.testing import CliRunner

from git_graphable.rich_cli import app

runner = CliRunner()


@pytest.fixture
def test_repo():
    test_dir = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "init"], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=test_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=test_dir, check=True
        )
        with open(os.path.join(test_dir, "file1.txt"), "w") as f:
            f.write("v1")
        subprocess.run(["git", "add", "file1.txt"], cwd=test_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial commit"], cwd=test_dir, check=True
        )
        yield test_dir
    finally:
        shutil.rmtree(test_dir)


def test_rich_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "analyze" in result.stdout.lower() or "git graph" in result.stdout.lower()


def test_rich_cli_init():
    """Test the rich init command."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = os.path.join(tmp_dir, ".git-graphable.toml")
        result = runner.invoke(app, ["init", "--output", config_path])
        assert result.exit_code == 0
        assert os.path.exists(config_path)
        with open(config_path, "r") as f:
            content = f.read()
            assert "[git-graphable]" in content


def test_rich_cli_analyze_html(test_repo):
    output_file = os.path.join(test_repo, "test.html")
    result = runner.invoke(
        app, ["analyze", test_repo, "--engine", "html", "--output", output_file]
    )
    assert result.exit_code == 0
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        content = f.read()
        assert "Git Graph" in content


def test_rich_cli_engine_options(test_repo):
    for engine_val in ["mermaid", "d2"]:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            out_path = tf.name
        try:
            result = runner.invoke(
                app,
                ["analyze", test_repo, "--engine", engine_val, "--output", out_path],
            )
            assert result.exit_code == 0
            assert os.path.exists(out_path)
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)


def test_rich_cli_conflicting_highlights(test_repo):
    result = runner.invoke(
        app,
        [
            "analyze",
            test_repo,
            "--highlight-authors",
            "--highlight-distance-from",
            "main",
        ],
    )
    assert result.exit_code == 1
    assert (
        "Error: Cannot use multiple fill-based highlights" in result.stdout
        or "Error: Cannot use multiple fill-based highlights" in result.stderr
    )

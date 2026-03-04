import os
import shutil
import subprocess
import tempfile

import pytest
from typer.testing import CliRunner

from git_graphable.cli import app

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


def test_cli_help():
    if app is not None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "converter" in result.stdout


def test_cli_bare_output(test_repo):
    if app is not None:
        with tempfile.NamedTemporaryFile(suffix=".mmd", delete=False) as tf:
            out_path = tf.name
        try:
            result = runner.invoke(app, [test_repo, "--bare", "--output", out_path])
            assert result.exit_code == 0
            assert os.path.exists(out_path)
            with open(out_path, "r") as f:
                content = f.read()
                assert "flowchart TD" in content
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)


def test_cli_engine_options(test_repo):
    if app is not None:
        for engine_val in ["mermaid", "d2"]:
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
                out_path = tf.name
            try:
                result = runner.invoke(
                    app,
                    [test_repo, "--bare", "--engine", engine_val, "--output", out_path],
                )
                assert result.exit_code == 0
                assert os.path.exists(out_path)
            finally:
                if os.path.exists(out_path):
                    os.unlink(out_path)


def test_cli_simplify(test_repo):
    if app is not None:
        result = runner.invoke(
            app, [test_repo, "--bare", "--simplify", "--output", os.devnull]
        )
        assert result.exit_code == 0


def test_cli_highlight_critical(test_repo):
    if app is not None:
        result = runner.invoke(
            app,
            [
                test_repo,
                "--bare",
                "--highlight-critical",
                "main",
                "--output",
                os.devnull,
            ],
        )
        assert result.exit_code == 0


def test_cli_divergence(test_repo):
    if app is not None:
        result = runner.invoke(
            app,
            [
                test_repo,
                "--bare",
                "--highlight-diverging-from",
                "main",
                "--output",
                os.devnull,
            ],
        )
        assert result.exit_code == 0


def test_cli_conflicting_highlights(test_repo):
    if app is not None:
        result = runner.invoke(
            app, [test_repo, "--highlight-authors", "--highlight-distance-from", "main"]
        )
        assert result.exit_code == 1
        assert "Error: Cannot use multiple fill-based highlights" in result.stderr


def test_cli_image_flag(test_repo):
    if app is not None:
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tf:
            out_path = tf.name
        try:
            runner.invoke(app, [test_repo, "--bare", "--image", "--output", out_path])
            pass
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)

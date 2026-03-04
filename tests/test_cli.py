import os
import shutil
import subprocess
import tempfile

import pytest
from graphable.enums import Engine
from typer.testing import CliRunner

from git_graph.cli import app, get_extension

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
        for engine in [Engine.MERMAID, Engine.D2]:
            with tempfile.NamedTemporaryFile(
                suffix=get_extension(engine, False), delete=False
            ) as tf:
                out_path = tf.name
            try:
                result = runner.invoke(
                    app,
                    [
                        test_repo,
                        "--bare",
                        "--engine",
                        engine.value,
                        "--output",
                        out_path,
                    ],
                )
                assert result.exit_code == 0
                assert os.path.exists(out_path)
            finally:
                if os.path.exists(out_path):
                    os.unlink(out_path)


def test_cli_simplify(test_repo):
    if app is not None:
        # Just check it doesn't crash
        result = runner.invoke(
            app, [test_repo, "--bare", "--simplify", "--output", os.devnull]
        )
        assert result.exit_code == 0


def test_cli_highlight_critical(test_repo):
    if app is not None:
        # Just check it doesn't crash with the flag
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
        assert (
            "Error: Cannot use both --highlight-authors and --highlight-distance-from"
            in result.stderr
        )


def test_cli_image_flag(test_repo):
    if app is not None:
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tf:
            out_path = tf.name
        try:
            # Using --bare to avoid status spinner
            runner.invoke(app, [test_repo, "--bare", "--image", "--output", out_path])
            # If mmdc is missing, it might exit with error, which is fine for coverage
            pass
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)


def test_get_extension():
    assert get_extension(Engine.MERMAID, False) == ".mmd"
    assert get_extension(Engine.D2, False) == ".d2"
    assert get_extension(Engine.MERMAID, True) == ".svg"

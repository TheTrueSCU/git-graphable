import os
import shutil
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from git_graphable.bare_cli import run_bare_cli


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


def test_bare_cli_help():
    with patch("sys.argv", ["git-graphable", "--help"]):
        with pytest.raises(SystemExit) as e:
            run_bare_cli()
        assert e.value.code == 0


def test_bare_cli_init():
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = os.path.join(tmp_dir, ".git-graphable.toml")
        with patch("sys.argv", ["git-graphable", "init", "-o", config_path]):
            run_bare_cli()
        assert os.path.exists(config_path)


def test_bare_cli_analyze_basic(test_repo):
    with tempfile.NamedTemporaryFile(suffix=".mmd", delete=False) as tf:
        out_path = tf.name
    try:
        # Implicit analyze
        with patch("sys.argv", ["git-graphable", test_repo, "-o", out_path]):
            run_bare_cli()
        assert os.path.exists(out_path)
        with open(out_path, "r") as f:
            assert "flowchart TD" in f.read()
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_bare_cli_engine_options(test_repo):
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        out_path = tf.name
    try:
        with patch(
            "sys.argv",
            ["git-graphable", "analyze", test_repo, "--engine", "d2", "-o", out_path],
        ):
            run_bare_cli()
        assert os.path.exists(out_path)
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_bare_cli_conflicting_highlights(test_repo):
    with patch(
        "sys.argv",
        ["git-graphable", test_repo, "--highlight-authors", "--highlight-stale"],
    ):
        with pytest.raises(SystemExit) as e:
            run_bare_cli()
        assert e.value.code == 1

import os
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from git_graphable.bare_cli import run_bare_cli


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


def test_bare_cli_init_exists():
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = os.path.join(tmp_dir, ".git-graphable.toml")
        with open(config_path, "w") as f:
            f.write("exists")
        with patch("sys.argv", ["git-graphable", "init", "-o", config_path]):
            with pytest.raises(SystemExit) as e:
                run_bare_cli()
            assert e.value.code == 1


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


def test_bare_cli_invalid_engine(test_repo):
    with patch(
        "sys.argv",
        ["git-graphable", "analyze", test_repo, "--engine", "invalid"],
    ):
        with pytest.raises(SystemExit) as e:
            run_bare_cli()
        assert e.value.code == 1


def test_bare_cli_conflicting_highlights(test_repo):
    with patch(
        "sys.argv",
        ["git-graphable", test_repo, "--highlight-authors", "--highlight-stale"],
    ):
        with pytest.raises(SystemExit) as e:
            run_bare_cli()
        assert e.value.code == 1


def test_bare_cli_check_mode_success(test_repo):
    with patch(
        "sys.argv",
        ["git-graphable", "analyze", test_repo, "--check", "--min-score", "50"],
    ):
        # Should not exit(1) because initial commit has 100 score
        run_bare_cli()


def test_bare_cli_check_mode_failure(test_repo):
    # Create a WIP commit to lower score
    with open(os.path.join(test_repo, "wip.txt"), "w") as f:
        f.write("wip")
    subprocess.run(["git", "add", "wip.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "WIP: save"], cwd=test_repo, check=True)

    with patch(
        "sys.argv",
        [
            "git-graphable",
            "analyze",
            test_repo,
            "--check",
            "--min-score",
            "99",
            "--highlight-wip",
        ],
    ):
        with pytest.raises(SystemExit) as e:
            run_bare_cli()
        assert e.value.code == 1

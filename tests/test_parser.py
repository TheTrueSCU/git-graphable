import concurrent.futures
import os
import shutil
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from git_graphable.core import GitLogConfig
from git_graphable.parser import get_git_log


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


def test_get_git_log(test_repo):
    config = GitLogConfig()
    commits = get_git_log(test_repo, config)
    assert len(commits) == 1
    sha = list(commits.keys())[0]
    commit = commits[sha]
    assert commit.reference.author == "Test User"
    assert commit.reference.message == "initial commit"


def test_get_git_log_large_mock(test_repo):
    """Test parallel parsing with a mocked large log output."""
    # Generate 2500 lines of fake log data
    fake_lines = []
    for i in range(2500):
        # Format: hash|parents|refs|timestamp|author|message
        fake_lines.append(f"hash{i}|||123456789|Author{i}|Message{i}")

    fake_output = "\n".join(fake_lines)

    with patch("git_graphable.parser.run_git_command", return_value=fake_output):
        config = GitLogConfig()
        commits = get_git_log(test_repo, config)

        assert len(commits) == 2500
        assert "hash0" in commits
        assert "hash2499" in commits
        assert commits["hash1000"].reference.author == "Author1000"


@pytest.mark.slow
def test_get_git_log_parallel_trigger(test_repo):
    """Verify that parallel parsing is triggered when threshold is exceeded."""
    # Create 20 commits
    for i in range(20):
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", f"commit {i}"],
            cwd=test_repo,
            check=True,
            capture_output=True,
        )

    config = GitLogConfig()

    # 1. Mock threshold to 10 so 20 commits trigger it
    # 2. Mock ProcessPoolExecutor to verify it's used
    with patch("git_graphable.parser.PARALLEL_THRESHOLD", 10):
        with patch(
            "concurrent.futures.ProcessPoolExecutor",
            wraps=concurrent.futures.ProcessPoolExecutor,
        ) as mock_executor:
            commits = get_git_log(test_repo, config)

            assert len(commits) >= 21
            # Verify executor was actually instantiated and used
            assert mock_executor.called


def test_get_git_log_with_limit(test_repo):
    from git_graphable.core import GitLogConfig
    from git_graphable.parser import get_git_log

    config = GitLogConfig(limit=1)
    # This will fail if arguments are incorrectly passed
    commits = get_git_log(test_repo, config)
    assert len(commits) == 1

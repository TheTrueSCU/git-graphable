import os
import shutil
import subprocess
import tempfile

import pytest

from git_graph.core import GitLogConfig
from git_graph.parser import get_git_log


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

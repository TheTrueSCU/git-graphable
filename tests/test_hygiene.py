import os
import shutil
import subprocess
import tempfile

import pytest

from git_graphable.core import GitLogConfig, process_repo
from git_graphable.models import Tag


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


def test_wip_detection(test_repo):
    # Create a commit with WIP in message
    with open(os.path.join(test_repo, "wip.txt"), "w") as f:
        f.write("wip")
    subprocess.run(["git", "add", "wip.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "WIP: half baked"], cwd=test_repo, check=True
    )

    config = GitLogConfig(highlight_wip=True)
    graph = process_repo(test_repo, config)

    wip_commits = [c for c in graph if c.is_tagged(Tag.WIP.value)]
    assert len(wip_commits) >= 1
    assert "WIP: half baked" in str(wip_commits[0].reference.message)


def test_wip_custom_keywords(test_repo):
    # Create a commit with custom keyword
    with open(os.path.join(test_repo, "custom.txt"), "w") as f:
        f.write("custom")
    subprocess.run(["git", "add", "custom.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "experimental change"], cwd=test_repo, check=True
    )

    config = GitLogConfig(highlight_wip=True, wip_keywords=["experimental"])
    graph = process_repo(test_repo, config)

    wip_commits = [c for c in graph if c.is_tagged(Tag.WIP.value)]
    assert len(wip_commits) >= 1
    assert "experimental change" in str(wip_commits[0].reference.message)


def test_direct_push_detection(test_repo):
    # Initial commit is already there. Add one more on main.
    with open(os.path.join(test_repo, "direct.txt"), "w") as f:
        f.write("direct")
    subprocess.run(["git", "add", "direct.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "direct to main"], cwd=test_repo, check=True)

    config = GitLogConfig(highlight_direct_pushes=True, production_branch="master")
    graph = process_repo(test_repo, config)

    direct_pushes = [c for c in graph if c.is_tagged(Tag.DIRECT_PUSH.value)]
    # Note: in test_repo setup, branch is often 'master'
    assert len(direct_pushes) >= 1
    assert any("direct to main" in str(c.reference.message) for c in direct_pushes)

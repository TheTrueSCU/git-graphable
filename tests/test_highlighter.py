import os
import shutil
import subprocess
import tempfile

import pytest

from git_graph import GitLogConfig, process_repo
from git_graph.models import Tag


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


def test_author_highlighting(test_repo):
    config = GitLogConfig(highlight_authors=True)
    graph = process_repo(test_repo, config)
    commit = list(graph)[0]
    assert any(t.startswith(Tag.COLOR.value) for t in commit.tags)


def test_distance_highlighting(test_repo):
    res = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    branch = res.stdout.strip()
    config = GitLogConfig(highlight_distance_from=branch)
    graph = process_repo(test_repo, config)
    commit = list(graph)[0]
    assert any(t.startswith(Tag.DISTANCE_COLOR.value) for t in commit.tags)
    assert any(t.startswith(Tag.COLOR.value) for t in commit.tags)


def test_path_highlighting_edges(test_repo):
    with open(os.path.join(test_repo, "file2.txt"), "w") as f:
        f.write("v2")
    subprocess.run(["git", "add", "file2.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "second commit"], cwd=test_repo, check=True)
    res = subprocess.run(
        ["git", "log", "--format=%H"], cwd=test_repo, capture_output=True, text=True
    )
    shas = res.stdout.strip().split("\n")
    config = GitLogConfig(highlight_path=(shas[1], shas[0]))
    graph = process_repo(test_repo, config)
    nodes = {c.reference.hash: c for c in graph}
    child = nodes[shas[0]]
    parent = nodes[shas[1]]
    assert child.edge_attributes(parent).get(Tag.EDGE_PATH.value) is True


def test_divergence_highlighting(test_repo):
    res = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    base_branch = res.stdout.strip()
    with open(os.path.join(test_repo, "base_only.txt"), "w") as f:
        f.write("base only")
    subprocess.run(["git", "add", "base_only.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base only commit"], cwd=test_repo, check=True
    )
    subprocess.run(
        ["git", "checkout", "HEAD^"], cwd=test_repo, check=True, capture_output=True
    )
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=test_repo, check=True)
    with open(os.path.join(test_repo, "feature.txt"), "w") as f:
        f.write("feature")
    subprocess.run(["git", "add", "feature.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "feature commit"], cwd=test_repo, check=True)
    config = GitLogConfig(highlight_diverging_from=base_branch)
    graph = process_repo(test_repo, config)
    behind_commits = [c for c in graph if c.is_tagged(Tag.BEHIND.value)]
    assert len(behind_commits) >= 1
    assert any("base only commit" in str(c.reference.message) for c in behind_commits)


def test_orphan_highlighting(test_repo):
    subprocess.run(
        ["git", "checkout", "--detach"], cwd=test_repo, check=True, capture_output=True
    )
    with open(os.path.join(test_repo, "orphan.txt"), "w") as f:
        f.write("orphan")
    subprocess.run(["git", "add", "orphan.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "orphan commit"], cwd=test_repo, check=True)
    config = GitLogConfig(highlight_orphans=True)
    graph = process_repo(test_repo, config)
    orphans = [c for c in graph if c.is_tagged(Tag.ORPHAN.value)]
    assert len(orphans) >= 1
    assert any("orphan commit" in str(c.reference.message) for c in orphans)


def test_stale_branch_highlighting(test_repo):
    config = GitLogConfig(highlight_stale=30)
    graph = process_repo(test_repo, config)
    commit = list(graph)[0]
    assert any(t.startswith(Tag.STALE_COLOR.value) for t in commit.tags)
    assert any(t.startswith(Tag.COLOR.value) for t in commit.tags)


def test_long_running_branch_highlighting(test_repo):
    res = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    base_branch = res.stdout.strip()
    subprocess.run(["git", "checkout", "-b", "old_feature"], cwd=test_repo, check=True)
    with open(os.path.join(test_repo, "old.txt"), "w") as f:
        f.write("old")
    subprocess.run(["git", "add", "old.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "old commit"], cwd=test_repo, check=True)
    config = GitLogConfig(highlight_long_running=0, long_running_base=base_branch)
    graph = process_repo(test_repo, config)
    long_running = [c for c in graph if c.is_tagged(Tag.LONG_RUNNING.value)]
    assert len(long_running) >= 1
    assert any("old commit" in str(c.reference.message) for c in long_running)

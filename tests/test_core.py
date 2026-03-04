import os
import shutil
import subprocess
import tempfile

import pytest
from graphable.enums import Engine

from git_graph import (
    CommitMetadata,
    GitCommit,
    GitLogConfig,
    export_graph,
    process_repo,
)


@pytest.fixture
def test_repo():
    test_dir = tempfile.mkdtemp()
    try:
        # Initialize repo
        subprocess.run(["git", "init"], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=test_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=test_dir, check=True
        )

        # Commit 1
        with open(os.path.join(test_dir, "file1.txt"), "w") as f:
            f.write("v1")
        subprocess.run(["git", "add", "file1.txt"], cwd=test_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial commit"], cwd=test_dir, check=True
        )

        # Add a tag
        subprocess.run(["git", "tag", "v1.0"], cwd=test_dir, check=True)

        yield test_dir
    finally:
        shutil.rmtree(test_dir)


def test_process_repo_and_tags(test_repo):
    # Process
    config = GitLogConfig()
    graph = process_repo(test_repo, config)
    assert len(graph) == 1

    commit = list(graph)[0]
    assert commit.is_tagged("git_commit")
    assert commit.is_tagged("author:Test User")
    has_branch_tag = any(t.startswith("branch:") for t in commit.tags)
    assert has_branch_tag
    assert commit.is_tagged("tag:v1.0")


def test_critical_branches(test_repo):
    # Determine branch name
    res = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    branch = res.stdout.strip()

    config = GitLogConfig(highlight_critical=[branch])
    graph = process_repo(test_repo, config)
    commit = list(graph)[0]

    assert commit.is_tagged("critical")


def test_author_highlighting(test_repo):
    config = GitLogConfig(highlight_authors=True)
    graph = process_repo(test_repo, config)
    commit = list(graph)[0]

    # Author highlighting adds color tag
    assert any(t.startswith("color:") for t in commit.tags)


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

    assert any(t.startswith("distance_color:") for t in commit.tags)
    assert any(t.startswith("color:") for t in commit.tags)


def test_path_highlighting_edges(test_repo):
    # Create a second commit so we have an edge
    with open(os.path.join(test_repo, "file2.txt"), "w") as f:
        f.write("v2")
    subprocess.run(["git", "add", "file2.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "second commit"], cwd=test_repo, check=True)

    # Get SHAs
    res = subprocess.run(
        ["git", "log", "--format=%H"], cwd=test_repo, capture_output=True, text=True
    )
    shas = res.stdout.strip().split("\n")

    config = GitLogConfig(highlight_path=(shas[1], shas[0]))
    graph = process_repo(test_repo, config)

    # Find nodes
    nodes = {c.reference.hash: c for c in graph}
    child = nodes[shas[0]]
    parent = nodes[shas[1]]

    # Check edge attribute
    assert child.edge_attributes(parent).get("highlight") is True


def test_divergence_highlighting(test_repo):
    # Determine current branch (e.g. master)
    res = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    base_branch = res.stdout.strip()

    # Create a new commit on base branch
    with open(os.path.join(test_repo, "base_only.txt"), "w") as f:
        f.write("base only")
    subprocess.run(["git", "add", "base_only.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base only commit"], cwd=test_repo, check=True
    )

    # Create a feature branch from the PREVIOUS commit
    subprocess.run(
        ["git", "checkout", "HEAD^"], cwd=test_repo, check=True, capture_output=True
    )
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=test_repo, check=True)
    with open(os.path.join(test_repo, "feature.txt"), "w") as f:
        f.write("feature")
    subprocess.run(["git", "add", "feature.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "feature commit"], cwd=test_repo, check=True)

    # Analyze divergence from base_branch
    config = GitLogConfig(highlight_diverging_from=base_branch)
    graph = process_repo(test_repo, config)

    # The 'base only commit' should be tagged as 'behind'
    behind_commits = [c for c in graph if c.is_tagged("behind")]
    assert len(behind_commits) >= 1
    assert any("base only commit" in str(c.reference.message) for c in behind_commits)


def test_orphan_highlighting(test_repo):
    # Commit 1 (reachable from master)
    # Already exists in test_repo

    # Create an orphan commit by detached HEAD and committing
    subprocess.run(
        ["git", "checkout", "--detach"], cwd=test_repo, check=True, capture_output=True
    )
    with open(os.path.join(test_repo, "orphan.txt"), "w") as f:
        f.write("orphan")
    subprocess.run(["git", "add", "orphan.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "orphan commit"], cwd=test_repo, check=True)

    # Analyze orphans
    config = GitLogConfig(highlight_orphans=True)
    graph = process_repo(test_repo, config)

    # The 'orphan commit' should be tagged as 'orphan'
    orphans = [c for c in graph if c.is_tagged("orphan")]
    assert len(orphans) >= 1
    assert any("orphan commit" in str(c.reference.message) for c in orphans)


def test_export_formats(test_repo):
    config = GitLogConfig()
    graph = process_repo(test_repo, config)

    with tempfile.TemporaryDirectory() as tmp_out:
        # Test Mermaid export
        mermaid_file = os.path.join(tmp_out, "test.mmd")
        export_graph(graph, mermaid_file, config, engine=Engine.MERMAID)
        assert os.path.exists(mermaid_file)
        with open(mermaid_file, "r") as f:
            content = f.read()
            assert "flowchart TD" in content
            assert "Test User" in content

        # Test D2 export
        d2_file = os.path.join(tmp_out, "test.d2")
        export_graph(graph, d2_file, config, engine=Engine.D2)
        assert os.path.exists(d2_file)
        with open(d2_file, "r") as f:
            content = f.read()
            assert '"' in content
            assert "Test User" in content


def test_metadata_dataclass():
    meta = CommitMetadata(hash="abc", parents=["def"], author="User")
    assert meta.hash == "abc"
    assert meta.parents == ["def"]
    assert meta.author == "User"
    assert meta.branches == []
    assert meta.tags == []


def test_git_commit_init():
    config = GitLogConfig(highlight_critical=["main"])
    meta = CommitMetadata(
        hash="abc", parents=[], author="User", branches=["main"], tags=["v1"]
    )
    commit = GitCommit(meta, config)
    assert commit.reference == meta
    assert commit.is_tagged("author:User")
    assert commit.is_tagged("branch:main")
    assert commit.is_tagged("critical")
    assert commit.is_tagged("tag:v1")
    assert commit.is_tagged("git_commit")

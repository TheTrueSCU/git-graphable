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
    meta = CommitMetadata(
        hash="abc", parents=[], author="User", branches=["main"], tags=["v1"]
    )
    commit = GitCommit(meta)
    assert commit.reference == meta
    assert commit.is_tagged("author:User")
    assert commit.is_tagged("branch:main")
    assert commit.is_tagged("tag:v1")
    assert commit.is_tagged("git_commit")

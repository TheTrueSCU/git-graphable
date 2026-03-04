import os
import shutil
import subprocess
import tempfile

import pytest

from git_graph.core import (
    CommitMetadata,
    GitCommit,
    GitLogConfig,
    generate_summary,
    process_repo,
)
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


def test_process_repo_and_tags(test_repo):
    config = GitLogConfig()
    graph = process_repo(test_repo, config)
    assert len(graph) == 1
    commit = list(graph)[0]
    assert commit.is_tagged(Tag.GIT_COMMIT.value)
    assert commit.is_tagged(f"{Tag.AUTHOR.value}Test User")


def test_metadata_dataclass():
    meta = CommitMetadata(hash="abc", parents=["def"], author="User", message="msg")
    assert meta.hash == "abc"
    assert meta.parents == ["def"]
    assert meta.author == "User"
    assert meta.message == "msg"


def test_git_commit_init():
    config = GitLogConfig(highlight_critical=["main"])
    meta = CommitMetadata(
        hash="abc", parents=[], author="User", branches=["main"], tags=["v1"]
    )
    commit = GitCommit(meta, config)
    assert commit.reference == meta
    assert commit.is_tagged(f"{Tag.AUTHOR.value}User")
    assert commit.is_tagged(f"{Tag.BRANCH.value}main")
    assert commit.is_tagged(Tag.CRITICAL.value)


def test_generate_summary(test_repo):
    config = GitLogConfig(highlight_critical=["master", "main"])
    graph = process_repo(test_repo, config)
    summary = generate_summary(graph)
    assert "Critical" in summary
    assert len(summary["Critical"]) >= 1

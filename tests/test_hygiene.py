import os
import shutil
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from git_graphable.core import GitLogConfig, process_repo
from git_graphable.github import PullRequestInfo
from git_graphable.hygiene import HygieneScorer
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
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"], cwd=test_dir, check=True
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


def test_squash_merge_detection(test_repo):
    # Get current SHA
    res = subprocess.run(
        ["git", "log", "--format=%H", "-n", "1"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    main_sha = res.stdout.strip()

    # Create a feature branch and a commit
    subprocess.run(
        ["git", "checkout", "-b", "feature/squash-me"], cwd=test_repo, check=True
    )
    with open(os.path.join(test_repo, "squash.txt"), "w") as f:
        f.write("squash")
    subprocess.run(["git", "add", "squash.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "feature commit"], cwd=test_repo, check=True)

    res = subprocess.run(
        ["git", "log", "--format=%H", "-n", "1"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    feature_sha = res.stdout.strip()

    # Now we simulate that feature_sha was squashed into main_sha
    pr = PullRequestInfo(
        number=123,
        title="Squash PR",
        state="MERGED",
        is_draft=False,
        head_ref_name="feature/squash-me",
        head_ref_oid=feature_sha,
        merge_commit_oid=main_sha,
        mergeable="MERGEABLE",
    )

    with patch("git_graphable.github.get_repo_prs") as mock_get_prs:
        mock_get_prs.return_value = [pr]

        config = GitLogConfig(highlight_squashed=True)
        graph = process_repo(test_repo, config)

        nodes = {c.reference.hash: c for c in graph}
        main_node = nodes[main_sha]
        feature_node = nodes[feature_sha]

        assert Tag.SQUASH_COMMIT.value in main_node.tags
        assert Tag.SQUASHED.value in feature_node.tags
        assert (
            main_node.edge_attributes(feature_node).get(Tag.EDGE_LOGICAL_MERGE.value)
            is True
        )


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


def test_back_merge_detection(test_repo):
    # 1. Create a baseline on master
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=test_repo, check=True
    )

    # 2. Create a feature branch from current master
    subprocess.run(
        ["git", "checkout", "-b", "feature/back-merge"], cwd=test_repo, check=True
    )
    with open(os.path.join(test_repo, "feat_work.txt"), "w") as f:
        f.write("feat")
    subprocess.run(["git", "add", "feat_work.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "work on feature"], cwd=test_repo, check=True
    )

    # 3. Go back to master and add a commit
    subprocess.run(["git", "checkout", "master"], cwd=test_repo, check=True)
    with open(os.path.join(test_repo, "master_work.txt"), "w") as f:
        f.write("master")
    subprocess.run(["git", "add", "master_work.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "work on master"], cwd=test_repo, check=True)

    # 4. Merge master INTO feature
    subprocess.run(["git", "checkout", "feature/back-merge"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "merge", "master", "-m", "Merge master into feature"],
        cwd=test_repo,
        check=True,
    )

    config = GitLogConfig(highlight_back_merges=True, development_branch="master")
    graph = process_repo(test_repo, config)

    back_merges = [c for c in graph if c.is_tagged(Tag.BACK_MERGE.value)]
    assert len(back_merges) >= 1
    assert any(
        "Merge master into feature" in str(c.reference.message) for c in back_merges
    )


def test_contributor_silo_detection(test_repo):
    # 1. Baseline on master
    subprocess.run(["git", "checkout", "master"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=test_repo, check=True
    )

    # 2. Create a silo branch (3 commits from same user)
    subprocess.run(["git", "checkout", "-b", "feature/silo"], cwd=test_repo, check=True)
    for i in range(3):
        with open(os.path.join(test_repo, f"silo_{i}.txt"), "w") as f:
            f.write(f"work {i}")
        subprocess.run(["git", "add", f"silo_{i}.txt"], cwd=test_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"silo work {i}"], cwd=test_repo, check=True
        )

    config = GitLogConfig(
        highlight_silos=True,
        silo_commit_threshold=3,
        silo_author_count=1,
        development_branch="master",
    )
    graph = process_repo(test_repo, config)

    silo_tips = [c for c in graph if c.is_tagged(Tag.CONTRIBUTOR_SILO.value)]
    assert len(silo_tips) >= 1
    assert any("silo work 2" in str(c.reference.message) for c in silo_tips)


def test_hygiene_scorer_logic(test_repo):
    # 1. Create a direct push
    with open(os.path.join(test_repo, "direct_push.txt"), "w") as f:
        f.write("direct")
    subprocess.run(["git", "add", "direct_push.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=test_repo, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "direct push commit"], cwd=test_repo, check=True
    )

    # 2. Create a WIP commit
    with open(os.path.join(test_repo, "wip_file.txt"), "w") as f:
        f.write("wip")
    subprocess.run(["git", "add", "wip_file.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "WIP: baked"], cwd=test_repo, check=True)

    config = GitLogConfig(
        highlight_direct_pushes=True, highlight_wip=True, production_branch="master"
    )
    graph = process_repo(test_repo, config)

    scorer = HygieneScorer(graph, config)
    report = scorer.calculate()

    # Score should be < 100
    assert report["score"] < 100
    # Should have at least 2 deductions (Direct push and WIP)
    assert len(report["deductions"]) >= 2
    assert any("Direct pushes" in d["message"] for d in report["deductions"])
    assert any("WIP/Fixup" in d["message"] for d in report["deductions"])

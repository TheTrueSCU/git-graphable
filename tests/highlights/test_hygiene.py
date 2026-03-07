import os
import subprocess

from git_graphable.core import GitLogConfig, process_repo
from git_graphable.models import Tag


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
    # Now the FEATURE branch tip should be tagged as behind
    assert any("feature commit" in str(c.reference.message) for c in behind_commits)


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
    config = GitLogConfig(highlight_stale=True, stale_days=30)
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
    config = GitLogConfig(
        highlight_long_running=True, long_running_days=0, long_running_base=base_branch
    )
    graph = process_repo(test_repo, config)
    long_running = [c for c in graph if c.is_tagged(Tag.LONG_RUNNING.value)]
    assert len(long_running) >= 1
    assert any("old commit" in str(c.reference.message) for c in long_running)

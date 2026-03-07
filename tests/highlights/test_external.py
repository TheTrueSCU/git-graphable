import os
import subprocess
from unittest.mock import MagicMock, patch

from git_graphable.core import GitLogConfig, process_repo
from git_graphable.github import PullRequestInfo
from git_graphable.models import Tag


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

    with patch("git_graphable.highlights.external.get_repo_prs") as mock_get_prs:
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


def test_issue_inconsistency_detection(test_repo):
    import os

    # 1. Create a commit with issue ID in message
    with open(os.path.join(test_repo, "issue.txt"), "w") as f:
        f.write("fix")
    subprocess.run(["git", "add", "issue.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=test_repo, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "fix: JIRA-123 working"], cwd=test_repo, check=True
    )

    # 2. Mock PR as OPEN
    from git_graphable.github import PullRequestInfo

    pr = PullRequestInfo(
        number=1,
        title="PR 1",
        state="OPEN",
        is_draft=False,
        head_ref_name="main",
        head_ref_oid="dummy",
        merge_commit_oid=None,
        mergeable="MERGEABLE",
    )

    # 3. Mock Issue as CLOSED
    from git_graphable.issues import IssueInfo, IssueStatus

    with (
        patch("git_graphable.highlights.external.get_repo_prs") as mock_get_prs,
        patch("git_graphable.highlights.external.get_issue_engine") as mock_get_engine,
    ):
        mock_get_prs.return_value = [pr]
        mock_engine = MagicMock()
        mock_engine.get_issue_info.return_value = {
            "JIRA-123": IssueInfo(id="JIRA-123", status=IssueStatus.CLOSED)
        }
        mock_get_engine.return_value = mock_engine

        config = GitLogConfig(
            highlight_issue_inconsistencies=True,
            issue_pattern=r"JIRA-[0-9]+",
            issue_engine="jira",
        )
        # We need to make sure the commit has the PR tag
        graph = process_repo(test_repo, config)
        for commit in graph:
            if "JIRA-123" in str(commit.reference.message):
                commit.add_tag("pr:open")

        # Re-run highlights manually since we added tag after process_repo
        from git_graphable.highlighter import apply_highlights

        apply_highlights(graph, config, repo_path=test_repo)

        inconsistent = [c for c in graph if c.is_tagged(Tag.ISSUE_INCONSISTENCY.value)]
        assert len(inconsistent) >= 1
        assert any("JIRA-123" in str(c.reference.message) for c in inconsistent)


def test_release_inconsistency_detection(test_repo):
    import os

    # 1. Create a commit with issue ID
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=test_repo, check=True
    )
    with open(os.path.join(test_repo, "release.txt"), "w") as f:
        f.write("release")
    subprocess.run(["git", "add", "release.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "fix: PROJ-789 release candidate"],
        cwd=test_repo,
        check=True,
    )

    # 2. Mock Issue as CLOSED (Released)
    from git_graphable.issues import IssueInfo, IssueStatus

    with patch("git_graphable.highlights.external.get_issue_engine") as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.get_issue_info.return_value = {
            "PROJ-789": IssueInfo(id="PROJ-789", status=IssueStatus.CLOSED)
        }
        mock_get_engine.return_value = mock_engine

        config = GitLogConfig(
            highlight_release_inconsistencies=True,
            issue_pattern=r"PROJ-[0-9]+",
            issue_engine="jira",
        )

        # We need to make sure the commit is in the graph
        graph = process_repo(test_repo, config)

        # Verify it's tagged as RELEASE_INCONSISTENCY because it's not reachable from any tag
        inconsistent = [
            c for c in graph if c.is_tagged(Tag.RELEASE_INCONSISTENCY.value)
        ]
        assert len(inconsistent) >= 1
        assert any("PROJ-789" in str(c.reference.message) for c in inconsistent)


def test_collaboration_gap_detection(test_repo):
    import os

    # 1. Create a baseline on master
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=test_repo, check=True
    )
    # Add a commit to master so feature branch is 'ahead'
    with open(os.path.join(test_repo, "base.txt"), "w") as f:
        f.write("base")
    subprocess.run(["git", "add", "base.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "base commit"], cwd=test_repo, check=True)

    # 2. Create feature branch and commit with specific author
    subprocess.run(
        ["git", "checkout", "-b", "feature/PROJ-999"], cwd=test_repo, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Git Author"], cwd=test_repo, check=True
    )
    with open(os.path.join(test_repo, "collab.txt"), "w") as f:
        f.write("collab")
    subprocess.run(["git", "add", "collab.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "fix: PROJ-999 help"], cwd=test_repo, check=True
    )

    # 3. Mock Issue assignee as 'Different Person' (Mismatch with 'Git Author')
    from git_graphable.issues import IssueInfo, IssueStatus

    with patch("git_graphable.highlights.external.get_issue_engine") as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.get_issue_info.return_value = {
            "PROJ-999": IssueInfo(
                id="PROJ-999", status=IssueStatus.OPEN, assignee="Different Person"
            )
        }
        mock_get_engine.return_value = mock_engine

        config = GitLogConfig(
            highlight_collaboration_gaps=True,
            issue_pattern=r"PROJ-[0-9]+",
            issue_engine="jira",
            development_branch="master",
        )

        graph = process_repo(test_repo, config)

        # Explicitly apply highlights
        from git_graphable.highlighter import apply_highlights

        apply_highlights(graph, config, repo_path=test_repo)

        gaps = [c for c in graph if c.is_tagged(Tag.COLLABORATION_GAP.value)]
        assert len(gaps) >= 1


def test_longevity_mismatch_detection(test_repo):
    import os

    # 1. Create a commit now
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=test_repo, check=True
    )
    with open(os.path.join(test_repo, "late.txt"), "w") as f:
        f.write("late")
    subprocess.run(["git", "add", "late.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: PROJ-OLD finally started"],
        cwd=test_repo,
        check=True,
    )

    # 2. Mock Issue created 30 days ago
    from datetime import datetime, timedelta, timezone

    old_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    from git_graphable.issues import IssueInfo, IssueStatus

    with patch("git_graphable.highlights.external.get_issue_engine") as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.get_issue_info.return_value = {
            "PROJ-OLD": IssueInfo(
                id="PROJ-OLD", status=IssueStatus.OPEN, created_at=old_date
            )
        }
        mock_get_engine.return_value = mock_engine

        config = GitLogConfig(
            highlight_longevity_mismatch=True,
            issue_pattern=r"PROJ-[A-Z]+",
            issue_engine="jira",
            longevity_threshold_days=14,
        )

        graph = process_repo(test_repo, config)

        # Explicitly apply highlights
        from git_graphable.highlighter import apply_highlights

        apply_highlights(graph, config, repo_path=test_repo)

        mismatches = [c for c in graph if c.is_tagged(Tag.LONGEVITY_MISMATCH.value)]
        assert len(mismatches) >= 1
        assert any("PROJ-OLD" in str(c.reference.message) for c in mismatches)


def test_pr_status_highlighting(test_repo):
    res = subprocess.run(
        ["git", "log", "--format=%H", "-n", "1"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    sha = res.stdout.strip()

    pr = PullRequestInfo(
        number=1,
        title="PR 1",
        state="OPEN",
        is_draft=False,
        head_ref_name="feature",
        head_ref_oid=sha,
        merge_commit_oid=None,
        mergeable="MERGEABLE",
    )

    with patch("git_graphable.highlights.external.get_repo_prs") as mock_get_prs:
        mock_get_prs.return_value = [pr]

        config = GitLogConfig(highlight_pr_status=True)
        graph = process_repo(test_repo, config)

        commit = next(c for c in graph if c.reference.hash == sha)
        assert Tag.PR_STATUS.value in commit.tags
        assert Tag.PR_OPEN.value in commit.tags

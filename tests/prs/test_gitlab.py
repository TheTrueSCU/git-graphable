"""
Tests for GitLab PR provider.
"""

import json
from unittest.mock import MagicMock, patch

from git_graphable.prs.gitlab import GitLabPullRequestProvider


def test_gitlab_pr_provider_success():
    mock_stdout = json.dumps(
        [
            {
                "iid": 42,
                "title": "GitLab MR",
                "state": "opened",
                "draft": True,
                "source_branch": "feat/gitlab",
                "sha": "sha123",
                "merge_commit_sha": "sha456",
                "merge_status": "can_be_merged",
            }
        ]
    )
    with patch("subprocess.run") as mock_run:
        # First call for glab version check, second for mr list
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(stdout=mock_stdout, returncode=0),
        ]
        provider = GitLabPullRequestProvider()
        prs = provider.get_repo_prs(".")
        assert len(prs) == 1
        assert prs[0].number == 42
        assert prs[0].state == "OPEN"
        assert prs[0].is_draft is True
        assert prs[0].merge_commit_oid == "sha456"

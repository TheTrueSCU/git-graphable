"""
Tests for GitLab issue tracker.
"""

import json
from unittest.mock import MagicMock, patch

from git_graphable.issues.base import IssueStatus
from git_graphable.issues.gitlab import GitLabIssueEngine


def test_gitlab_issue_engine_success():
    mock_data = {
        "state": "opened",
        "assignees": [{"username": "gitlab_user"}],
        "created_at": "2023-01-01T00:00:00Z",
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=json.dumps(mock_data), returncode=0)
        engine = GitLabIssueEngine()
        info_map = engine.get_issue_info(["101"])
        info = info_map["101"]
        assert info.status == IssueStatus.OPEN
        assert info.assignee == "gitlab_user"
        assert info.created_at == "2023-01-01T00:00:00Z"

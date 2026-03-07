import json
from unittest.mock import MagicMock, patch

from git_graphable.issues.base import IssueStatus
from git_graphable.issues.github import GitHubIssueEngine


def test_github_engine_success():
    mock_stdout = json.dumps({"state": "OPEN"})
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout, returncode=0)
        engine = GitHubIssueEngine()
        statuses = engine.get_statuses(["123"])
        assert statuses["123"] == IssueStatus.OPEN

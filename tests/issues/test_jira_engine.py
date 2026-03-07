import json
from unittest.mock import MagicMock, patch

from git_graphable.issues.base import IssueStatus
from git_graphable.issues.jira import JiraIssueEngine


def test_jira_engine_success():
    mock_data = {"fields": {"status": {"name": "Done"}}}
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with patch.dict("os.environ", {"JIRA_TOKEN": "secret"}):
            engine = JiraIssueEngine(
                url="http://jira", token_env="JIRA_TOKEN", closed_statuses=["Done"]
            )
            statuses = engine.get_statuses(["PROJ-123"])
            assert statuses["PROJ-123"] == IssueStatus.CLOSED

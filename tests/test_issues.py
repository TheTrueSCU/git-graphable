import json
from unittest.mock import MagicMock, patch

from git_graphable.issues import (
    GitHubIssueEngine,
    IssueStatus,
    JiraIssueEngine,
    ScriptIssueEngine,
)


def test_github_engine_success():
    mock_stdout = json.dumps({"state": "OPEN"})
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout, returncode=0)
        engine = GitHubIssueEngine()
        statuses = engine.get_statuses(["123"])
        assert statuses["123"] == IssueStatus.OPEN


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


def test_script_engine_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="CLOSED", returncode=0)
        engine = ScriptIssueEngine(script_template="check {id}")
        statuses = engine.get_statuses(["123"])
        assert statuses["123"] == IssueStatus.CLOSED


def test_script_engine_escaping():
    """Verify that ScriptIssueEngine safely escapes malicious IDs."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="OPEN", returncode=0)
        engine = ScriptIssueEngine(script_template="echo {id}")
        malicious_id = "123; touch injected.txt"
        engine.get_issue_info([malicious_id])

        # Check the command string that was actually executed
        # It should contain the quoted malicious_id
        args, kwargs = mock_run.call_args
        cmd_str = args[0]
        assert "'123; touch injected.txt'" in cmd_str


def test_script_engine_full_info():
    """Test full info parsing (STATUS,ASSIGNEE,CREATED_AT)."""
    with patch("subprocess.run") as mock_run:
        # Format: STATUS,ASSIGNEE,CREATED_AT
        mock_run.return_value = MagicMock(
            stdout="CLOSED,Alice,2023-01-01T12:00:00Z", returncode=0
        )
        engine = ScriptIssueEngine(script_template="check {id}")
        info_map = engine.get_issue_info(["123"])
        info = info_map["123"]
        assert info.status == IssueStatus.CLOSED
        assert info.assignee == "Alice"
        assert info.created_at == "2023-01-01T12:00:00Z"


def test_script_engine_failure():
    """Verify handling of script failures."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("execution failed")
        engine = ScriptIssueEngine(script_template="check {id}")
        info_map = engine.get_issue_info(["123"])
        assert info_map["123"].status == IssueStatus.UNKNOWN

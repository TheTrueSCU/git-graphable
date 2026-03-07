from unittest.mock import MagicMock, patch

from git_graphable.issues.base import IssueStatus
from git_graphable.issues.script import ScriptIssueEngine


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
        args, _ = mock_run.call_args
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


def test_script_engine_json_success():
    """Test JSON info parsing."""
    import json

    with patch("subprocess.run") as mock_run:
        mock_data = {
            "status": "OPEN",
            "assignee": "Bob",
            "created_at": "2023-02-02T10:00:00Z",
        }
        mock_run.return_value = MagicMock(stdout=json.dumps(mock_data), returncode=0)
        engine = ScriptIssueEngine(script_template="check {id}")
        info_map = engine.get_issue_info(["456"])
        info = info_map["456"]
        assert info.status == IssueStatus.OPEN
        assert info.assignee == "Bob"
        assert info.created_at == "2023-02-02T10:00:00Z"


def test_script_engine_failure():
    """Verify handling of script failures."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("execution failed")
        engine = ScriptIssueEngine(script_template="check {id}")
        info_map = engine.get_issue_info(["123"])
        assert info_map["123"].status == IssueStatus.UNKNOWN

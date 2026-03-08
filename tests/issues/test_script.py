from unittest.mock import MagicMock, patch

from git_graphable.issues.base import IssueStatus
from git_graphable.issues.script import ScriptIssueEngine


def test_script_engine_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="CLOSED", returncode=0)
        engine = ScriptIssueEngine(script_template="check {id}", trusted=True)
        statuses = engine.get_statuses(["123"])
        assert statuses["123"] == IssueStatus.CLOSED


def test_script_engine_escaping():
    """Verify that ScriptIssueEngine safely escapes malicious IDs."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="OPEN", returncode=0)
        engine = ScriptIssueEngine(script_template="echo {id}", trusted=True)
        malicious_id = "123; touch injected.txt"
        engine.get_issue_info([malicious_id])

        # Check the command args
        args, _ = mock_run.call_args
        cmd_list = args[0]
        assert "sh" in cmd_list
        assert "-c" in cmd_list
        assert malicious_id in cmd_list


def test_script_engine_full_info():
    """Test full info parsing (STATUS,ASSIGNEE,CREATED_AT)."""
    with patch("subprocess.run") as mock_run:
        # Format: STATUS,ASSIGNEE,CREATED_AT
        mock_run.return_value = MagicMock(
            stdout="CLOSED,Alice,2023-01-01T12:00:00Z", returncode=0
        )
        engine = ScriptIssueEngine(script_template="check {id}", trusted=True)
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
        engine = ScriptIssueEngine(script_template="check {id}", trusted=True)
        info_map = engine.get_issue_info(["456"])
        info = info_map["456"]
        assert info.status == IssueStatus.OPEN
        assert info.assignee == "Bob"
        assert info.created_at == "2023-02-02T10:00:00Z"


def test_script_engine_failure():
    """Verify handling of script failures."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("execution failed")
        engine = ScriptIssueEngine(script_template="check {id}", trusted=True)
        info_map = engine.get_issue_info(["123"])
        assert info_map["123"].status == IssueStatus.UNKNOWN


def test_script_engine_trust_warning():
    """Verify that an error is printed when executing an untrusted script."""
    import io
    from contextlib import redirect_stdout

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="OPEN", returncode=0)
        # Default is trusted=False
        engine = ScriptIssueEngine(script_template="echo {id}", trusted=False)

        f = io.StringIO()
        with redirect_stdout(f):
            engine.get_issue_info(["123"])

        output = f.getvalue()
        assert "ERROR" in output
        assert "untrusted configuration" in output


def test_script_engine_no_warning_if_trusted():
    """Verify that no warning is printed when executing a trusted script."""
    import io
    from contextlib import redirect_stdout

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="OPEN", returncode=0)
        engine = ScriptIssueEngine(script_template="echo {id}", trusted=True)

        f = io.StringIO()
        with redirect_stdout(f):
            engine.get_issue_info(["123"])

        output = f.getvalue()
        assert "ERROR" not in output

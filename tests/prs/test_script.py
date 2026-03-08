import io
import json
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from git_graphable.prs.script import ScriptPullRequestProvider


def test_script_pr_provider_success():
    mock_stdout = json.dumps(
        [
            {
                "number": 123,
                "title": "Script PR",
                "state": "MERGED",
                "is_draft": False,
                "head_ref_name": "feat",
                "head_ref_oid": "sha1",
                "merge_commit_oid": "sha2",
                "mergeable": "CONFLICTING",
            }
        ]
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_stdout, returncode=0)
        provider = ScriptPullRequestProvider(script_path="./my-script.sh", trusted=True)
        prs = provider.get_repo_prs(".")
        assert len(prs) == 1

        assert prs[0].number == 123
        assert prs[0].state == "MERGED"
        assert prs[0].mergeable == "CONFLICTING"


def test_script_pr_provider_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("script failed")
        # Added trusted=True so it actually tries to run and then fails
        provider = ScriptPullRequestProvider(script_path="./my-script.sh", trusted=True)
        prs = provider.get_repo_prs(".")
        assert prs == []


def test_script_pr_provider_trust_warning():
    """Verify that an error is printed when executing an untrusted PR script."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)
        provider = ScriptPullRequestProvider(
            script_path="./my-script.sh", trusted=False
        )

        f = io.StringIO()
        with redirect_stdout(f):
            provider.get_repo_prs(".")

        output = f.getvalue()
        assert "ERROR" in output


def test_script_pr_provider_no_warning_if_trusted():
    """Verify that no error is printed when executing a trusted PR script."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)
        provider = ScriptPullRequestProvider(script_path="./my-script.sh", trusted=True)

        f = io.StringIO()
        with redirect_stdout(f):
            provider.get_repo_prs(".")

        output = f.getvalue()
        assert "ERROR" not in output

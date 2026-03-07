import json
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
        provider = ScriptPullRequestProvider(script_path="./my-script.sh")
        prs = provider.get_repo_prs(".")
        assert len(prs) == 1
        assert prs[0].number == 123
        assert prs[0].state == "MERGED"
        assert prs[0].mergeable == "CONFLICTING"


def test_script_pr_provider_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("script failed")
        provider = ScriptPullRequestProvider(script_path="./my-script.sh")
        prs = provider.get_repo_prs(".")
        assert prs == []

import json
from unittest.mock import MagicMock, patch

from git_graphable.prs.github import GitHubPullRequestProvider


def test_github_pr_provider_success():
    mock_stdout = json.dumps(
        [
            {
                "number": 1,
                "title": "PR 1",
                "state": "OPEN",
                "isDraft": False,
                "headRefName": "feat",
                "headRefOid": "sha1",
                "mergeCommit": {"oid": "sha2"},
                "mergeable": "MERGEABLE",
            }
        ]
    )
    with patch("subprocess.run") as mock_run:
        # First call for gh version check, second for pr list
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(stdout=mock_stdout, returncode=0),
        ]
        provider = GitHubPullRequestProvider()
        prs = provider.get_repo_prs(".")
        assert len(prs) == 1
        assert prs[0].number == 1
        assert prs[0].merge_commit_oid == "sha2"

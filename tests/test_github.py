import json
from unittest.mock import MagicMock, patch

from git_graphable.github import PullRequestInfo, get_repo_prs, map_prs_to_commits


def test_get_repo_prs_success():
    mock_data = [
        {
            "number": 1,
            "title": "PR 1",
            "state": "OPEN",
            "isDraft": False,
            "headRefOid": "sha1",
            "mergeCommit": {"oid": "sha2"},
            "mergeable": "MERGEABLE",
        }
    ]

    with patch("subprocess.run") as mock_run:
        # Mock gh --version
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0, stdout=json.dumps(mock_data)),
        ]

        prs = get_repo_prs("/tmp/repo")
        assert len(prs) == 1
        assert prs[0].number == 1
        assert prs[0].head_ref_oid == "sha1"
        assert prs[0].merge_commit_oid == "sha2"
        assert prs[0].state == "OPEN"


def test_get_repo_prs_no_gh():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        prs = get_repo_prs("/tmp/repo")
        assert prs == []


def test_map_prs_to_commits():
    pr = PullRequestInfo(
        number=1,
        title="PR 1",
        state="OPEN",
        is_draft=False,
        head_ref_oid="sha1",
        merge_commit_oid="sha2",
        mergeable="MERGEABLE",
    )
    mapping = map_prs_to_commits([pr])
    assert mapping["sha1"] == pr
    assert mapping["sha2"] == pr

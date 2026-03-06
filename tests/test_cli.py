import sys
from unittest.mock import patch

from git_graphable.cli import main


def test_main_bare_explicit():
    """Verify that --bare triggers run_bare_cli and is removed from argv."""
    with patch("sys.argv", ["git-graphable", "--bare", "init"]):
        with patch("git_graphable.bare_cli.run_bare_cli") as mock_bare:
            main()
            mock_bare.assert_called_once()
            assert "--bare" not in sys.argv


def test_main_rich_default():
    """Verify that rich CLI is preferred by default."""
    with patch("sys.argv", ["git-graphable", "init"]):
        with patch("git_graphable.rich_cli.app") as mock_rich:
            main()
            mock_rich.assert_called_once()


def test_main_fallback_on_error():
    """Verify fallback to bare CLI if rich CLI fails."""
    with patch("sys.argv", ["git-graphable", "init"]):
        with patch("git_graphable.rich_cli.app", side_effect=Exception("Missing deps")):
            with patch("git_graphable.bare_cli.run_bare_cli") as mock_bare:
                main()
                mock_bare.assert_called_once()

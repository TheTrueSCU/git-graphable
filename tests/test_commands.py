import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from git_graphable.commands import ensure_local_repo, get_extension, handle_output
from git_graphable.core import Engine, GitLogConfig, process_repo


def test_get_extension():
    assert get_extension(Engine.MERMAID, False) == ".mmd"
    assert get_extension(Engine.D2, False) == ".d2"
    assert get_extension(Engine.MERMAID, True) == ".png"


def test_handle_output_stdout(test_repo):
    """Test output to stdout ('-')."""
    config = GitLogConfig()
    graph = process_repo(test_repo, config)
    content = handle_output(graph, Engine.MERMAID, "-", config)
    assert content is not None
    assert "flowchart TD" in content


def test_handle_output_image_inference(test_repo):
    """Test inference of image format from file extension."""
    config = GitLogConfig()
    graph = process_repo(test_repo, config)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = os.path.join(tmp_dir, "graph.png")
        with patch("git_graphable.commands.export_graph") as mock_export:
            handle_output(graph, Engine.MERMAID, out_path, config)
            mock_export.assert_called_once()
            # Verify as_image was inferred as True
            kwargs = mock_export.call_args[1]
            assert kwargs.get("as_image") is True


def test_ensure_local_repo_remote():
    """Test cloning of remote repository."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        path, temp_repo = ensure_local_repo("https://github.com/user/repo")
        assert temp_repo is not None
        mock_run.assert_called_once()
        assert "clone" in mock_run.call_args[0][0]
        temp_repo.cleanup()


def test_ensure_local_repo_failure():
    """Test handling of failed clone."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "clone", stderr=b"auth failed"
        )
        with pytest.raises(RuntimeError, match="Failed to clone repository"):
            ensure_local_repo("https://github.com/user/repo")

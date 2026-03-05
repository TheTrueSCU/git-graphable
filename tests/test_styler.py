import os
import shutil
import subprocess
import tempfile

import pytest
from graphable.enums import Engine

from git_graphable.commands import get_extension
from git_graphable.core import GitLogConfig, process_repo
from git_graphable.styler import export_graph


@pytest.fixture
def test_repo():
    test_dir = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "init"], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=test_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=test_dir, check=True
        )
        with open(os.path.join(test_dir, "file1.txt"), "w") as f:
            f.write("v1")
        subprocess.run(["git", "add", "file1.txt"], cwd=test_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial commit"], cwd=test_dir, check=True
        )
        yield test_dir
    finally:
        shutil.rmtree(test_dir)


def test_export_formats(test_repo):
    config = GitLogConfig()
    graph = process_repo(test_repo, config)

    with tempfile.TemporaryDirectory() as tmp_out:
        # Test Mermaid export
        mermaid_file = os.path.join(tmp_out, "test.mmd")
        export_graph(graph, mermaid_file, config, engine=Engine.MERMAID)
        assert os.path.exists(mermaid_file)
        with open(mermaid_file, "r") as f:
            content = f.read()
            assert "flowchart TD" in content
            assert "Test User" in content

        # Test D2 export
        d2_file = os.path.join(tmp_out, "test.d2")
        export_graph(graph, d2_file, config, engine=Engine.D2)
        assert os.path.exists(d2_file)
        with open(d2_file, "r") as f:
            content = f.read()
            assert '"' in content
            assert "Test User" in content


def test_get_extension():
    assert get_extension(Engine.MERMAID, False) == ".mmd"
    assert get_extension(Engine.D2, False) == ".d2"
    assert get_extension(Engine.MERMAID, True) == ".svg"

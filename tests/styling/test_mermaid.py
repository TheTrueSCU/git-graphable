import os
import subprocess
import tempfile

from git_graphable.core import Engine, GitLogConfig, process_repo
from git_graphable.styler import export_graph


def test_mermaid_export(test_repo):
    config = GitLogConfig()
    graph = process_repo(test_repo, config)

    with tempfile.TemporaryDirectory() as tmp_out:
        mermaid_file = os.path.join(tmp_out, "test.mmd")
        export_graph(graph, mermaid_file, config, engine=Engine.MERMAID)
        assert os.path.exists(mermaid_file)
        with open(mermaid_file, "r") as f:
            content = f.read()
            assert "flowchart TD" in content
            assert "Test User" in content


def test_mermaid_styling_variations(test_repo):
    """Verify various tags produce correct Mermaid styling output."""
    from git_graphable.models import Tag

    config = GitLogConfig()
    # Create multiple commits
    for i in range(2):
        with open(os.path.join(test_repo, f"file_mmd_{i}.txt"), "w") as f:
            f.write(str(i))
        subprocess.run(["git", "add", f"file_mmd_{i}.txt"], cwd=test_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"mmd commit {i}"], cwd=test_repo, check=True
        )

    graph = process_repo(test_repo, config)
    nodes = list(graph)

    # 1. Color tag
    nodes[0].add_tag(f"{Tag.COLOR.value}#ff0000")
    # 2. WIP tag
    nodes[1].add_tag(Tag.WIP.value)
    # 3. Critical tag
    nodes[2].add_tag(Tag.CRITICAL.value)

    with tempfile.TemporaryDirectory() as tmp_out:
        mermaid_file = os.path.join(tmp_out, "styled.mmd")
        export_graph(graph, mermaid_file, config, engine=Engine.MERMAID)

        with open(mermaid_file, "r") as f:
            content = f.read()
            assert f"style {nodes[0].reference.hash} " in content
            assert "fill:#ff0000" in content
            assert "fill:#ffff00" in content  # WIP
            # For critical, it should have a stroke
            assert "stroke:" in content
            assert "stroke-width:" in content

import os
import subprocess
import tempfile

from git_graphable.core import Engine, GitLogConfig, process_repo
from git_graphable.styler import export_graph


def test_d2_export(test_repo):
    config = GitLogConfig()
    graph = process_repo(test_repo, config)

    with tempfile.TemporaryDirectory() as tmp_out:
        d2_file = os.path.join(tmp_out, "test.d2")
        export_graph(graph, d2_file, config, engine=Engine.D2)
        assert os.path.exists(d2_file)
        with open(d2_file, "r") as f:
            content = f.read()
            assert '"' in content
            assert "Test User" in content


def test_graphviz_export(test_repo):
    config = GitLogConfig()
    graph = process_repo(test_repo, config)

    with tempfile.TemporaryDirectory() as tmp_out:
        gv_file = os.path.join(tmp_out, "test.dot")
        export_graph(graph, gv_file, config, engine=Engine.GRAPHVIZ)
        assert os.path.exists(gv_file)
        with open(gv_file, "r") as f:
            content = f.read()
            assert "digraph" in content
            assert "Test User" in content


def test_d2_styling_variations(test_repo):
    """Verify various tags produce correct D2 styling output."""
    from git_graphable.models import Tag

    config = GitLogConfig()
    # Create multiple commits
    for i in range(2):
        with open(os.path.join(test_repo, f"file_{i}.txt"), "w") as f:
            f.write(str(i))
        subprocess.run(["git", "add", f"file_{i}.txt"], cwd=test_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"commit {i}"], cwd=test_repo, check=True
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
        d2_file = os.path.join(tmp_out, "styled.d2")
        export_graph(graph, d2_file, config, engine=Engine.D2)

        with open(d2_file, "r") as f:
            content = f.read()
            # Find the style block for node 0
            assert f"{nodes[0].reference.hash}:" in content
            # D2 might not quote the hex
            assert "fill: #ff0000" in content
            # WIP stroke
            assert "fill: #ffff00" in content
            # Critical
            assert "double-border: true" in content


def test_graphviz_styling_variations(test_repo):
    """Verify various tags produce correct Graphviz styling output."""
    from git_graphable.models import Tag

    config = GitLogConfig()
    # Create multiple commits
    for i in range(2):
        with open(os.path.join(test_repo, f"file_gv_{i}.txt"), "w") as f:
            f.write(str(i))
        subprocess.run(["git", "add", f"file_gv_{i}.txt"], cwd=test_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"gv commit {i}"], cwd=test_repo, check=True
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
        gv_file = os.path.join(tmp_out, "styled.dot")
        export_graph(graph, gv_file, config, engine=Engine.GRAPHVIZ)

        with open(gv_file, "r") as f:
            content = f.read()
            assert 'fillcolor="#ff0000"' in content
            assert 'fillcolor="#ffff00"' in content  # WIP
            # style might contain multiple values
            assert 'style="filled' in content
            assert "bold" in content

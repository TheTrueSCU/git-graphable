import os
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

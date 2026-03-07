import os
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

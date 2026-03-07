import os
import tempfile

from git_graphable.core import Engine, GitLogConfig, process_repo
from git_graphable.styler import export_graph


def test_export_graph_entry_point(test_repo):
    config = GitLogConfig()
    graph = process_repo(test_repo, config)

    with tempfile.TemporaryDirectory() as tmp_out:
        out_file = os.path.join(tmp_out, "test.mmd")
        export_graph(graph, out_file, config, engine=Engine.MERMAID)
        assert os.path.exists(out_file)

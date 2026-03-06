import json
import re
from pathlib import Path

import pytest

from git_graphable.core import Engine, GitLogConfig, process_repo
from git_graphable.styler import export_graph

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
REPOS_DIR = EXAMPLES_DIR / "repos"


@pytest.mark.skipif(not REPOS_DIR.exists(), reason="Example repos not generated")
@pytest.mark.parametrize(
    "repo_name",
    ["repo-messy", "repo-features", "repo-risk-silo", "repo-complex-hygiene"],
)
def test_example_repo_html(repo_name):
    repo_path = str(REPOS_DIR / repo_name)
    config = GitLogConfig(engine=Engine.HTML)
    graph = process_repo(repo_path, config)

    html_file = Path(repo_path + "_graph.html")
    try:
        export_graph(graph, str(html_file), config, engine=Engine.HTML)

        assert html_file.exists()
        content = html_file.read_text()

        # Extract elements and styles
        elements_match = re.search(r"elements: (\[.*\]),\s+style:", content, re.DOTALL)
        assert elements_match
        elements = json.loads(elements_match.group(1))

        styles_match = re.search(
            r"var tagStyles = (\{.*?\});\s+var", content, re.DOTALL
        )
        assert styles_match
        tag_styles = json.loads(styles_match.group(1))

        nodes = [e for e in elements if "source" not in e["data"]]

        if repo_name == "repo-messy":
            assert any("wip" in n["data"].get("tags", []) for n in nodes)
            assert "wip" in tag_styles

        elif repo_name == "repo-features":
            assert any("orphan" in n["data"].get("tags", []) for n in nodes)
            assert "orphan" in tag_styles

        elif repo_name == "repo-risk-silo":
            assert any("contributor_silo" in n["data"].get("tags", []) for n in nodes)
            assert "contributor_silo" in tag_styles

        elif repo_name == "repo-complex-hygiene":
            assert any("back_merge" in n["data"].get("tags", []) for n in nodes)
            assert "back_merge" in tag_styles

    finally:
        if html_file.exists():
            html_file.unlink()

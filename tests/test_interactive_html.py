import json
import os
import re
import shutil
import subprocess
import tempfile

import pytest

from git_graphable.core import Engine, GitLogConfig, process_repo
from git_graphable.styler import export_graph


@pytest.fixture
def messy_repo():
    """Create a repository with various hygiene issues (WIP, direct push, stale)."""
    test_dir = tempfile.mkdtemp()

    def run_git(args):
        subprocess.run(["git"] + args, cwd=test_dir, check=True, capture_output=True)

    try:
        run_git(["init", "-b", "main"])
        run_git(["config", "user.email", "test@example.com"])
        run_git(["config", "user.name", "Test User"])
        run_git(["config", "commit.gpgsign", "false"])

        # 1. Initial commit (Critical)
        with open(os.path.join(test_dir, "README.md"), "w") as f:
            f.write("# Test Repo")
        run_git(["add", "README.md"])
        run_git(["commit", "-m", "initial commit"])

        # 2. Direct push to main (Critical + Direct Push)
        with open(os.path.join(test_dir, "fix.txt"), "w") as f:
            f.write("fix")
        run_git(["add", "fix.txt"])
        run_git(["commit", "-m", "urgent fix"])

        # 3. WIP commit on feature branch
        run_git(["checkout", "-b", "feature/wip"])
        with open(os.path.join(test_dir, "wip.txt"), "w") as f:
            f.write("wip")
        run_git(["add", "wip.txt"])
        run_git(["commit", "-m", "WIP: saving work"])

        yield test_dir
    finally:
        shutil.rmtree(test_dir)


def test_interactive_html_metadata(messy_repo):
    """Verify that the generated HTML contains the correct metadata for interactivity."""
    config = GitLogConfig(engine=Engine.HTML)
    graph = process_repo(messy_repo, config)

    with tempfile.TemporaryDirectory() as tmp_out:
        html_file = os.path.join(tmp_out, "graph.html")
        export_graph(graph, html_file, config, engine=Engine.HTML)

        assert os.path.exists(html_file)
        with open(html_file, "r") as f:
            content = f.read()

        # 1. Check for injected scripts
        assert "cytoscape-dagre.js" in content
        assert "dagre.js" in content

        # 2. Extract elements JSON
        # We use a more robust regex that looks for the end of the array before 'style:'
        elements_match = re.search(r"elements: (\[.*\]),\s+style:", content, re.DOTALL)
        assert elements_match, "Could not find elements array in HTML"
        elements = json.loads(elements_match.group(1))

        # 3. Verify node tags
        nodes = [e for e in elements if "source" not in e["data"]]

        # At least the tip of 'main' should be critical
        critical_nodes = [n for n in nodes if "critical" in n["data"].get("tags", [])]
        assert len(critical_nodes) >= 1

        # Direct push should be tagged (the 'urgent fix' commit)
        direct_nodes = [n for n in nodes if "direct_push" in n["data"].get("tags", [])]
        assert len(direct_nodes) >= 1

        # WIP commit should be tagged (on feature branch)
        wip_nodes = [n for n in nodes if "wip" in n["data"].get("tags", [])]
        assert len(wip_nodes) >= 1
        assert any("WIP: saving work" in n["data"]["message"] for n in wip_nodes)

        # 4. Extract tagStyles JSON
        # Looking for 'var tagStyles = { ... };'
        styles_match = re.search(
            r"var tagStyles = (\{.*?\});\s+var", content, re.DOTALL
        )
        assert styles_match, "Could not find tagStyles object in HTML"
        tag_styles = json.loads(styles_match.group(1))

        # Verify essential styles are present
        assert "critical" in tag_styles
        assert "wip" in tag_styles
        assert "direct_push" in tag_styles
        assert tag_styles["wip"]["background-color"] == "#ffff00"
        assert tag_styles["critical"]["shape"] == "diamond"

        # 5. Check for interactive functions
        assert "function setMode" in content
        assert "function toggleOverlay" in content
        assert "function applyStyles" in content


def test_html_always_tags_critical(messy_repo):
    """Verify that HTML engine always tags critical branches even if not requested via flag."""
    # Note: highlight_critical defaults to False
    config = GitLogConfig(engine=Engine.HTML, highlight_critical=False)
    graph = process_repo(messy_repo, config)

    # Check if 'critical' tag was added by the highlighter because it's HTML engine
    main_commits = [n for n in graph if "main" in n.reference.branches]
    assert all(n.is_tagged("critical") for n in main_commits)

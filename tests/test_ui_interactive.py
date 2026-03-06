import os
import shutil
import subprocess
import tempfile

import pytest

from git_graphable.core import Engine, GitLogConfig, process_repo
from git_graphable.styler import export_graph


@pytest.fixture
def messy_repo():
    """Create a repository with various hygiene issues."""
    test_dir = tempfile.mkdtemp()

    def run_git(args):
        subprocess.run(["git"] + args, cwd=test_dir, check=True, capture_output=True)

    try:
        run_git(["init", "-b", "main"])
        run_git(["config", "user.email", "test@example.com"])
        run_git(["config", "user.name", "Test User"])
        run_git(["config", "commit.gpgsign", "false"])

        # 1. Root commit
        with open(os.path.join(test_dir, "README.md"), "w") as f:
            f.write("# Test Repo")
        run_git(["add", "README.md"])
        run_git(["commit", "-m", "initial commit"])

        # 2. WIP commit
        run_git(["checkout", "-b", "feature/wip"])
        with open(os.path.join(test_dir, "wip.txt"), "w") as f:
            f.write("wip")
        run_git(["add", "wip.txt"])
        run_git(["commit", "-m", "WIP: work in progress"])

        yield test_dir
    finally:
        shutil.rmtree(test_dir)


@pytest.mark.ui
def test_interactivity_toggling(messy_repo, page):
    """Test that clicking legend items updates the Cytoscape visuals using Playwright."""
    config = GitLogConfig(engine=Engine.HTML)
    graph = process_repo(messy_repo, config)

    with tempfile.TemporaryDirectory() as tmp_out:
        html_path = os.path.join(tmp_out, "interactive.html")
        export_graph(graph, html_path, config, engine=Engine.HTML)

        # Load the file in the browser
        page.goto(f"file://{os.path.abspath(html_path)}")

        # Wait for Cytoscape to initialize (checking window.cyGraph)
        page.wait_for_function("typeof window.cyGraph !== 'undefined'")

        # Helper to get node colors
        def get_node_colors():
            return page.evaluate(
                "window.cyGraph.nodes().map(n => n.style('background-color'))"
            )

        def normalize_rgb(c):
            return c.replace(" ", "")

        # 1. Verify initial state (all blue #007bff -> rgb(0, 123, 255))
        initial_colors = get_node_colors()
        assert all("rgb(0,123,255)" in normalize_rgb(c) for c in initial_colors)

        # 2. Toggle 'Authors' mode
        # Clicking the radio button
        page.click("#mode-authors")

        # Verify colors changed
        page.wait_for_timeout(300)  # Small wait for style application
        author_colors = get_node_colors()
        assert any("rgb(0,123,255)" not in normalize_rgb(c) for c in author_colors)

        # 3. Toggle 'WIP' overlay
        # First verify it's OFF by default (not yellow)
        def get_wip_colors():
            return page.evaluate(
                "window.cyGraph.nodes().filter(n => (n.data('tags') || []).includes('wip')).map(n => n.style('background-color'))"
            )

        # Initially they should be the mode color (Authors mode is active)
        assert all("rgb(255,255,0)" not in normalize_rgb(c) for c in get_wip_colors())

        # Toggle it ON
        page.click("#overlay-wip")

        # Verify color is now yellow
        page.wait_for_timeout(300)
        assert any("rgb(255,255,0)" in normalize_rgb(c) for c in get_wip_colors())

        # 4. Switch back to Default mode
        page.click("#mode-none")
        page.wait_for_timeout(300)

        # Non-WIP nodes should be blue, WIP nodes should stay yellow
        def get_all_node_data():
            return page.evaluate("""
                window.cyGraph.nodes().map(n => ({
                    is_wip: (n.data('tags') || []).includes('wip'),
                    color: n.style('background-color')
                }))
            """)

        final_data = get_all_node_data()
        for item in final_data:
            color = normalize_rgb(item["color"])
            if item["is_wip"]:
                assert "rgb(255,255,0)" in color
            else:
                assert "rgb(0,123,255)" in color

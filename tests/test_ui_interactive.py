import os
import subprocess
import tempfile
import shutil
import pytest
from pathlib import Path
from git_graphable.core import Engine, GitLogConfig, process_repo
from git_graphable.styler import export_graph

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
REPOS_DIR = EXAMPLES_DIR / "repos"

def normalize_rgb(c):
    return c.replace(" ", "")

@pytest.mark.ui
@pytest.mark.parametrize("repo_name, mode_id, expected_tag", [
    ("repo-pristine", "mode-authors", "author_highlight:"),
    ("repo-messy", "overlay-wip", "wip"),
    ("repo-risk-silo", "overlay-contributor_silo", "contributor_silo"),
])
def test_example_repo_interactivity(repo_name, mode_id, expected_tag, page):
    """Test interactivity for specific modes across multiple example repositories."""
    repo_path = str(REPOS_DIR / repo_name)
    if not os.path.exists(repo_path):
        pytest.skip(f"Example repo {repo_name} not found")

    config = GitLogConfig(engine=Engine.HTML)
    graph = process_repo(repo_path, config)
    
    with tempfile.TemporaryDirectory() as tmp_out:
        html_path = os.path.join(tmp_out, f"{repo_name}_interactive.html")
        export_graph(graph, html_path, config, engine=Engine.HTML)
        
        page.goto(f"file://{os.path.abspath(html_path)}")
        page.wait_for_function("typeof window.cyGraph !== 'undefined'")
        
        # 1. Test Color Mode (Authors)
        if mode_id == "mode-authors":
            # Initial state: Default blue
            colors = page.evaluate("window.cyGraph.nodes().map(n => n.style('background-color'))")
            assert all("rgb(0,123,255)" in normalize_rgb(c) for c in colors)
            
            # Switch to Authors
            page.click(f"#{mode_id}")
            page.wait_for_timeout(300)
            
            # Verify diversity in colors
            author_colors = page.evaluate("window.cyGraph.nodes().map(n => n.style('background-color'))")
            assert any("rgb(0,123,255)" not in normalize_rgb(c) for c in author_colors)

        # 2. Test Overlays (WIP / Silo)
        elif mode_id.startswith("overlay-"):
            tag = mode_id.replace("overlay-", "")
            
            # Initial state: Style should be default (e.g., no border or non-yellow background)
            def get_tagged_styles():
                return page.evaluate(f"""
                    window.cyGraph.nodes().filter(n => (n.data('tags') || []).includes('{tag}'))
                        .map(n => ({{ bg: n.style('background-color'), border: n.style('border-width') }}))
                """)
            
            initial_styles = get_tagged_styles()
            assert len(initial_styles) > 0, f"No nodes tagged with {tag} found in {repo_name}"
            
            # Verify style is NOT applied yet
            for s in initial_styles:
                if tag == "wip":
                    assert "rgb(255,255,0)" not in normalize_rgb(s["bg"])
                else:
                    assert s["border"] == "0px"
            
            # Toggle overlay ON
            page.click(f"#{mode_id}")
            page.wait_for_timeout(300)
            
            # Verify style IS applied
            updated_styles = get_tagged_styles()
            for s in updated_styles:
                if tag == "wip":
                    assert "rgb(255,255,0)" in normalize_rgb(s["bg"])
                else:
                    assert int(s["border"].replace("px", "")) > 0

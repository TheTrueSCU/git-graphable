import os
import re
import json
import pytest
from pathlib import Path
from git_graphable.core import Engine, GitLogConfig, process_repo
from git_graphable.styler import export_graph
from git_graphable.models import Tag

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
REPOS_DIR = EXAMPLES_DIR / "repos"

@pytest.mark.skipif(not REPOS_DIR.exists(), reason="Example repos not generated")
@pytest.mark.parametrize("repo_name", [
    "repo-pristine",
    "repo-messy",
    "repo-features",
    "repo-risk-silo",
    "repo-complex-hygiene",
    "repo-issue-desync",
    "repo-release-desync",
    "repo-collab-gap"
])
def test_example_repo_html_metadata(repo_name):
    """Exhaustively verify HTML metadata for every example repository."""
    repo_path = str(REPOS_DIR / repo_name)
    
    # Configure engine-aware config
    config = GitLogConfig(
        engine=Engine.HTML,
        issue_pattern=r"PROJ-[0-9]+" if "issue" in repo_name or "release" in repo_name or "collab" in repo_name else None,
        issue_engine="script" if "issue" in repo_name or "release" in repo_name or "collab" in repo_name else None,
        issue_script="echo CLOSED,WrongUser"
    )
    
    graph = process_repo(repo_path, config)
    html_file = Path(repo_path + "_metadata_test.html")
    
    try:
        export_graph(graph, str(html_file), config, engine=Engine.HTML)
        assert html_file.exists()
        content = html_file.read_text()
        
        # 1. Extract and validate elements
        elements_match = re.search(r"elements: (\[.*\]),\s+style:", content, re.DOTALL)
        assert elements_match
        elements = json.loads(elements_match.group(1))
        nodes = [e for e in elements if "source" not in e["data"]]
        
        # 2. Extract and validate tag styles
        styles_match = re.search(r"var tagStyles = (\{.*?\});\s+var", content, re.DOTALL)
        assert styles_match
        tag_styles = json.loads(styles_match.group(1))
        
        # 3. Repo-specific content verification
        if repo_name == "repo-pristine":
            # Pristine should only have standard git tags
            for n in nodes:
                tags = n["data"].get("tags", [])
                # Filter out auto-added tags
                hygiene_tags = [t for t in tags if t in [Tag.WIP.value, Tag.ORPHAN.value, Tag.DIRECT_PUSH.value]]
                assert not hygiene_tags
                
        elif repo_name == "repo-messy":
            assert any("wip" in n["data"].get("tags", []) for n in nodes)
            assert any("direct_push" in n["data"].get("tags", []) for n in nodes)
            assert "wip" in tag_styles
            
        elif repo_name == "repo-features":
            assert any("orphan" in n["data"].get("tags", []) for n in nodes)
            assert "orphan" in tag_styles
            
        elif repo_name == "repo-risk-silo":
            assert any("contributor_silo" in n["data"].get("tags", []) for n in nodes)
            assert "contributor_silo" in tag_styles
            
        elif repo_name == "repo-issue-desync":
            assert any("issue_inconsistency" in n["data"].get("tags", []) for n in nodes)
            assert "issue_inconsistency" in tag_styles
            
        elif repo_name == "repo-release-desync":
            assert any("release_inconsistency" in n["data"].get("tags", []) for n in nodes)
            assert "release_inconsistency" in tag_styles
            
        elif repo_name == "repo-collab-gap":
            assert any("collaboration_gap" in n["data"].get("tags", []) for n in nodes)
            assert "collaboration_gap" in tag_styles

    finally:
        if html_file.exists():
            html_file.unlink()

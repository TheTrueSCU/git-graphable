from git_graphable import GitLogConfig, process_repo
from git_graphable.highlighter import apply_highlights


def test_apply_highlights_entry_point(test_repo):
    config = GitLogConfig()
    graph = process_repo(test_repo, config)
    # Just verify it runs without error
    apply_highlights(graph, config, repo_path=test_repo)

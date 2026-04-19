from hypothesis import given
from hypothesis import strategies as st

from git_graphable.core import CommitMetadata, GitCommit, AcyclicGraph
from git_graphable.models import Tag
from git_graphable.parser import GitLogConfig

# Strategies for generating commit-like objects
commit_metadata_strategy = st.builds(
    CommitMetadata,
    hash=st.text(min_size=7, max_size=40),
    author=st.text(),
    message=st.text(),
    tags=st.lists(st.sampled_from([t.value for t in Tag])),
)

# Mock config


@given(st.lists(commit_metadata_strategy, min_size=1))
def test_graph_invariants(metadata_list):
    """
    Property: AcyclicGraph construction should at least contain the provided commits
    and maintain basic structure.
    """
    config = GitLogConfig()
    commits = [GitCommit(meta, config) for meta in metadata_list]
    graph = AcyclicGraph(commits)
    assert len(graph) == len(commits)
    for commit in commits:
        assert commit in graph


@given(st.lists(commit_metadata_strategy, min_size=1))
def test_hygiene_score_range(metadata_list):
    """
    Property: Hygiene score should always be within [0, 100].
    """
    from git_graphable.hygiene import HygieneScorer

    config = GitLogConfig()
    commits = [GitCommit(meta, config) for meta in metadata_list]
    graph = AcyclicGraph(commits)
    scorer = HygieneScorer(graph, config)
    score = scorer.calculate()

    # Check score structure based on implementation
    if isinstance(score, dict) and "score" in score:
        assert 0 <= score["score"] <= 100
    elif isinstance(score, (int, float)):
        assert 0 <= score <= 100

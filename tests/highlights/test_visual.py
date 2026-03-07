import subprocess

from git_graphable import GitLogConfig, process_repo
from git_graphable.models import Tag


def test_author_highlighting(test_repo):
    config = GitLogConfig(highlight_authors=True)
    graph = process_repo(test_repo, config)
    commit = list(graph)[0]
    assert any(t.startswith(Tag.COLOR.value) for t in commit.tags)


def test_distance_highlighting(test_repo):
    res = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    branch = res.stdout.strip()
    config = GitLogConfig(highlight_distance_from=branch)
    graph = process_repo(test_repo, config)
    commit = list(graph)[0]
    assert any(t.startswith(Tag.DISTANCE_COLOR.value) for t in commit.tags)
    assert any(t.startswith(Tag.COLOR.value) for t in commit.tags)


def test_critical_branch_highlighting(test_repo):
    res = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=test_repo,
        capture_output=True,
        text=True,
    )
    branch = res.stdout.strip()
    config = GitLogConfig(highlight_critical=True, critical_branches=[branch])
    graph = process_repo(test_repo, config)
    commit = list(graph)[0]
    assert Tag.CRITICAL.value in commit.tags


def test_path_highlighting_edges(test_repo):
    import os

    with open(os.path.join(test_repo, "file2.txt"), "w") as f:
        f.write("v2")
    subprocess.run(["git", "add", "file2.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "second commit"], cwd=test_repo, check=True)
    res = subprocess.run(
        ["git", "log", "--format=%H"], cwd=test_repo, capture_output=True, text=True
    )
    shas = res.stdout.strip().split("\n")
    config = GitLogConfig(highlight_path=(shas[1], shas[0]))
    graph = process_repo(test_repo, config)
    nodes = {c.reference.hash: c for c in graph}
    child = nodes[shas[0]]
    parent = nodes[shas[1]]
    assert child.edge_attributes(parent).get(Tag.EDGE_PATH.value) is True

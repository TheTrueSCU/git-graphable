import subprocess

from git_graphable.core import GitLogConfig, process_repo
from git_graphable.hygiene import HygieneScorer


def test_hygiene_scorer_logic(test_repo):
    import os

    # 1. Create a direct push
    with open(os.path.join(test_repo, "direct_push.txt"), "w") as f:
        f.write("direct")
    subprocess.run(["git", "add", "direct_push.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=test_repo, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "direct push commit"], cwd=test_repo, check=True
    )

    # 2. Create a WIP commit
    with open(os.path.join(test_repo, "wip_file.txt"), "w") as f:
        f.write("wip")
    subprocess.run(["git", "add", "wip_file.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "WIP: baked"], cwd=test_repo, check=True)

    config = GitLogConfig(
        highlight_direct_pushes=True, highlight_wip=True, production_branch="master"
    )
    graph = process_repo(test_repo, config)

    scorer = HygieneScorer(graph, config)
    report = scorer.calculate()

    # Score should be < 100
    assert report["score"] < 100
    # Should have at least 2 deductions (Direct push and WIP)
    assert len(report["deductions"]) >= 2
    assert any("Direct pushes" in d["message"] for d in report["deductions"])
    assert any("WIP/Fixup" in d["message"] for d in report["deductions"])


def test_configurable_hygiene_weights(test_repo):
    import os

    # 1. Create a direct push and a WIP commit
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=test_repo, check=True
    )
    with open(os.path.join(test_repo, "weight.txt"), "w") as f:
        f.write("weight")
    subprocess.run(["git", "add", "weight.txt"], cwd=test_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "direct to master"], cwd=test_repo, check=True
    )

    with open(os.path.join(test_repo, "wip_file.txt"), "w") as f:
        f.write("wip")
    subprocess.run(["git", "add", "wip_file.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "WIP: saving"], cwd=test_repo, check=True)

    # 2. Scorer with default weights
    config_default = GitLogConfig(
        highlight_direct_pushes=True, highlight_wip=True, production_branch="master"
    )
    graph = process_repo(test_repo, config_default)
    scorer_default = HygieneScorer(graph, config_default)
    report_default = scorer_default.calculate()
    # Defaults: Direct push -15, WIP -3 => 100 - 18 = 82
    assert report_default["score"] == 82

    # 3. Scorer with custom weights
    from git_graphable.core import HygieneWeights

    custom_weights = HygieneWeights(
        direct_push_penalty=50, direct_push_cap=100, wip_commit_penalty=0
    )
    config_custom = GitLogConfig(
        highlight_direct_pushes=True,
        highlight_wip=True,
        production_branch="master",
        hygiene_weights=custom_weights,
    )
    graph_custom = process_repo(test_repo, config_custom)
    scorer_custom = HygieneScorer(graph_custom, config_custom)
    report_custom = scorer_custom.calculate()
    # Custom: Direct push -50, WIP -0 => 100 - 50 = 50
    assert report_custom["score"] == 50
    assert any(d["amount"] == 50 for d in report_custom["deductions"])
    # WIP deduction should be 0 and excluded from report
    assert not any("WIP" in d["message"] for d in report_custom["deductions"])

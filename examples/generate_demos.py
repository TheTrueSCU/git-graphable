import os
import shutil
import subprocess
import time
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent
REPOS_DIR = EXAMPLES_DIR / "repos"
ASSETS_DIR = EXAMPLES_DIR / "assets"


def run_git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True)


def create_base_repo(name):
    path = REPOS_DIR / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)

    run_git(["init", "-b", "main"], path)
    run_git(["config", "user.email", "demo@example.com"], path)
    run_git(["config", "user.name", "Demo User"], path)
    run_git(["config", "commit.gpgsign", "false"], path)

    # Root commit
    (path / "README.md").write_text(f"# {name}")
    run_git(["add", "README.md"], path)
    run_git(["commit", "-m", "initial commit"], path)
    return path


def generate_pristine():
    print("Generating repo-pristine...")
    path = create_base_repo("repo-pristine")

    # Clean history
    for i in range(3):
        (path / f"file_{i}.txt").write_text(f"content {i}")
        run_git(["add", f"file_{i}.txt"], path)
        run_git(["commit", "-m", f"feat: add component {i}"], path)

    # Merge a feature branch
    run_git(["checkout", "-b", "feature/login"], path)
    (path / "login.py").write_text("def login(): pass")
    run_git(["add", "login.py"], path)
    run_git(["commit", "-m", "feat: implement login logic"], path)

    run_git(["checkout", "main"], path)
    run_git(
        [
            "merge",
            "--no-ff",
            "feature/login",
            "-m",
            "Merge pull request #1 from feature/login",
        ],
        path,
    )


def generate_messy():
    print("Generating repo-messy...")
    path = create_base_repo("repo-messy")

    # 1. Direct pushes to main
    for i in range(2):
        (path / f"hotfix_{i}.txt").write_text("fix")
        run_git(["add", f"hotfix_{i}.txt"], path)
        run_git(["commit", "-m", f"urgent fix {i}"], path)

    # 2. WIP commits
    run_git(["checkout", "-b", "feature/draft"], path)
    for i in range(3):
        (path / f"draft_{i}.txt").write_text("draft")
        run_git(["add", f"draft_{i}.txt"], path)
        run_git(["commit", "-m", f"WIP: saving work {i}"], path)

    # 3. Stale branch (backdated commit)
    run_git(["checkout", "-b", "stale-branch"], path)
    (path / "stale.txt").write_text("old")
    run_git(["add", "stale.txt"], path)
    # Set date to 60 days ago
    old_date = int(time.time()) - (60 * 24 * 60 * 60)
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = f"{old_date} +0000"
    env["GIT_COMMITTER_DATE"] = f"{old_date} +0000"
    subprocess.run(
        ["git", "commit", "-m", "feat: ancient work"], cwd=path, env=env, check=True
    )


def generate_features():
    print("Generating repo-features...")
    path = create_base_repo("repo-features")

    # 1. Divergence
    run_git(["checkout", "-b", "feature/diverged"], path)
    (path / "feature.txt").write_text("feat")
    run_git(["add", "feature.txt"], path)
    run_git(["commit", "-m", "feat: divergence start"], path)

    run_git(["checkout", "main"], path)
    (path / "main_update.txt").write_text("update")
    run_git(["add", "main_update.txt"], path)
    run_git(["commit", "-m", "chore: update base with critical fix"], path)

    # 2. Orphan commit
    run_git(["checkout", "--orphan", "detached-work"], path)
    (path / "orphan.txt").write_text("orphan")
    run_git(["add", "orphan.txt"], path)
    run_git(["commit", "-m", "feat: some experimental work"], path)
    run_git(["checkout", "main"], path)


def main():
    REPOS_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)

    generate_pristine()
    generate_messy()
    generate_features()

    print("\nDone! Demo repositories created in examples/repos/")


if __name__ == "__main__":
    main()

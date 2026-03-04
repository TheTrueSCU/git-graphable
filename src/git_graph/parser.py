import subprocess
import sys
from typing import Dict, List, Optional

from .core import CommitMetadata, GitCommit, GitLogConfig


def run_git_command(args: List[str], cwd: Optional[str] = None) -> str:
    """Run a git command and return its output."""
    try:
        return subprocess.check_output(
            ["git"] + args, cwd=cwd, text=True, stderr=subprocess.PIPE
        ).strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e.stderr}", file=sys.stderr)
        raise


def parse_ref_names(ref_names: str) -> tuple[List[str], List[str]]:
    """Parse git log ref names (%D) into branches and tags."""
    branches = []
    tags = []
    if not ref_names:
        return branches, tags

    parts = [p.strip() for p in ref_names.split(",")]
    for part in parts:
        if part.startswith("tag: "):
            tags.append(part[len("tag: ") :])
        elif "->" in part:
            branches.append(part.split("->")[-1].strip())
        elif part == "HEAD":
            continue
        else:
            branches.append(part)
    return branches, tags


def get_git_log(repo_path: str, config: GitLogConfig) -> Dict[str, GitCommit]:
    """Retrieve git log and parse into GitCommit objects."""
    # Format: hash|parents|refs|timestamp|author|message
    format_str = "%H|%P|%D|%at|%an|%s"
    args = ["log", "--all", f"--format={format_str}"]
    if config.simplify:
        args.append("--simplify-by-decoration")
    if config.limit:
        args.append(f"-n {config.limit}")

    output = run_git_command(args, cwd=repo_path)

    commits: Dict[str, GitCommit] = {}
    for line in output.split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) < 6:
            continue

        sha = parts[0]
        parents = parts[1].split() if parts[1] else []
        refs = parts[2]
        timestamp = parts[3]
        author = parts[4]
        message = parts[5]

        branches, tags = parse_ref_names(refs)

        metadata = CommitMetadata(
            hash=sha,
            parents=parents,
            branches=branches,
            tags=tags,
            timestamp=int(timestamp) if timestamp.isdigit() else 0,
            author=author,
            message=message,
        )
        commits[sha] = GitCommit(metadata, config)

    return commits

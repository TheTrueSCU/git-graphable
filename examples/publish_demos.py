import shutil
import subprocess
from pathlib import Path
from string import Template

EXAMPLES_DIR = Path(__file__).parent
REPOS_DIR = EXAMPLES_DIR / "repos"
OUTPUT_DIR = Path("demo-site")


def run_command(cmd):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    # 1. Generate the repo data
    import generate_demos

    generate_demos.main()

    # 2. Prepare output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()

    # 3. Analyze each repo and generate HTML
    repos = [d for d in REPOS_DIR.iterdir() if d.is_dir()]

    html_links = []

    for repo in sorted(repos):
        repo_name = repo.name
        output_file = f"{repo_name}.html"
        print(f"Analyzing {repo_name}...")

        # Build command with relevant flags for the specific demo
        cmd = [
            "uv",
            "run",
            "git-graphable",
            "analyze",
            "--bare",
            str(repo),
            "--engine",
            "html",
            "-o",
            str(OUTPUT_DIR / output_file),
        ]

        # Add flags based on the demo type
        if repo_name == "repo-pristine":
            cmd.extend(["--highlight-authors", "--highlight-critical"])
        elif repo_name == "repo-messy":
            cmd.extend(["--highlight-direct-pushes", "--highlight-stale"])
        elif repo_name == "repo-risk-silo":
            cmd.extend(["--highlight-silos", "--silo-threshold", "20"])
        elif repo_name == "repo-complex-hygiene":
            cmd.extend(["--highlight-back-merges", "--highlight-squashed"])
        elif repo_name == "repo-features":
            cmd.extend(["--highlight-orphans", "--highlight-diverging-from", "main"])
        elif repo_name == "repo-issue-desync":
            cmd.extend(
                [
                    "--highlight-issue-inconsistencies",
                    "--issue-engine",
                    "script",
                    "--issue-script",
                    "echo CLOSED",
                ]
            )
        elif repo_name == "repo-release-desync":
            cmd.extend(
                [
                    "--highlight-release-inconsistencies",
                    "--issue-engine",
                    "script",
                    "--issue-script",
                    "echo CLOSED",
                ]
            )
        elif repo_name == "repo-collab-gap":
            cmd.extend(
                [
                    "--highlight-collaboration-gaps",
                    "--issue-engine",
                    "script",
                    "--issue-script",
                    "echo OPEN,Bob",
                ]
            )

        run_command(cmd)
        label = repo_name.replace("repo-", "").replace("-", " ").title()
        html_links.append(f'<li><a href="{output_file}">{label}</a></li>')

    # 4. Create index.html from template
    template_path = EXAMPLES_DIR / "index_template.html"
    if template_path.exists():
        template_str = template_path.read_text()
        t = Template(template_str)
        index_content = t.substitute(html_links="\n        ".join(html_links))
        (OUTPUT_DIR / "index.html").write_text(index_content)
        print(f"\nDone! Demo site generated in {OUTPUT_DIR}/")
    else:
        print(f"Error: Template not found at {template_path}")


if __name__ == "__main__":
    main()

import argparse
import importlib.resources
import os
import sys

from .cli_utils import parse_style_overrides
from .commands import convert_command
from .core import Engine


def run_bare_cli():
    """Fallback entry point for minimal environments without Typer/Rich."""
    parser = argparse.ArgumentParser(
        description="Git graph to Mermaid/Graphviz/D2/HTML converter."
    )
    subparsers = parser.add_subparsers(dest="command")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize configuration")
    init_parser.add_argument(
        "-o", "--output", default=".git-graphable.toml", help="Path to create config"
    )
    init_parser.add_argument("-f", "--force", action="store_true", help="Overwrite")

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze git history and generate graph"
    )

    def add_analyze_args(p):
        p.add_argument("path", help="Path to local directory or git URL")
        p.add_argument("--config", help="Path to TOML configuration file")
        p.add_argument("--production-branch", help="Production branch name")
        p.add_argument("--development-branch", help="Development branch name")
        p.add_argument("--date-format", help="Date format for commit labels")
        p.add_argument(
            "--engine",
            default="mermaid",
            help="Visualization engine (mermaid, graphviz, d2, html)",
        )
        p.add_argument("-o", "--output", default=None, help="Output file path")
        p.add_argument(
            "--image",
            action="store_true",
            help="Export as image even if output path given",
        )
        p.add_argument(
            "--simplify", action="store_true", help="Simplify graph by decorations"
        )
        p.add_argument("--limit", type=int, help="Limit number of commits")
        p.add_argument(
            "--highlight-critical",
            action="store_true",
            help="Highlight critical branches",
        )
        p.add_argument(
            "--critical-branch",
            action="append",
            default=[],
            help="Critical branch names",
        )
        p.add_argument(
            "--highlight-authors", action="store_true", help="Assign colors per author"
        )
        p.add_argument("--highlight-distance-from", help="Base hash for distance")
        p.add_argument("--highlight-path", help="Path between two SHAs (START..END)")
        p.add_argument(
            "--highlight-diverging-from", help="Base for divergence analysis"
        )
        p.add_argument(
            "--highlight-orphans", action="store_true", help="Highlight orphan commits"
        )
        p.add_argument(
            "--highlight-stale", action="store_true", help="Highlight stale branches"
        )
        p.add_argument("--stale-days", type=int, help="Days until branch is stale")
        p.add_argument(
            "--highlight-long-running",
            action="store_true",
            help="Highlight long branches",
        )
        p.add_argument("--long-running-days", type=int, help="Long branch threshold")
        p.add_argument("--long-running-base", help="Base for long branch check")
        p.add_argument(
            "--highlight-pr-status", action="store_true", help="Highlight PR states"
        )
        p.add_argument(
            "--highlight-wip", action="store_true", help="Highlight WIP commits"
        )
        p.add_argument(
            "--wip-keyword", action="append", default=[], help="Additional WIP keywords"
        )
        p.add_argument(
            "--highlight-direct-pushes",
            action="store_true",
            help="Highlight direct pushes",
        )
        p.add_argument(
            "--highlight-squashed", action="store_true", help="Highlight squashed PRs"
        )
        p.add_argument(
            "--highlight-back-merges", action="store_true", help="Highlight back-merges"
        )
        p.add_argument(
            "--highlight-silos", action="store_true", help="Highlight author silos"
        )
        p.add_argument("--silo-threshold", type=int, help="Silo commit threshold")
        p.add_argument("--silo-author-count", type=int, help="Silo author threshold")
        p.add_argument(
            "--highlight-issue-inconsistencies",
            action="store_true",
            help="Highlight desyncs",
        )
        p.add_argument("--issue-pattern", help="Regex for issue IDs")
        p.add_argument("--issue-engine", help="Engine (github, jira, script)")
        p.add_argument("--jira-url", help="Base URL for Jira instance")
        p.add_argument(
            "--issue-script", help="Shell command template for script engine"
        )
        p.add_argument(
            "--highlight-release-inconsistencies",
            action="store_true",
            help="Highlight issues marked Released but not tagged",
        )
        p.add_argument(
            "--released-status",
            action="append",
            dest="released_statuses",
            default=[],
            help="External status name that counts as Released",
        )
        p.add_argument(
            "--highlight-collaboration-gaps",
            action="store_true",
            help="Highlight when Git author doesn't match Ticket assignee",
        )
        p.add_argument(
            "--author-mapping",
            action="append",
            default=[],
            help="Map Git author to Ticket assignee (format: git_name:ticket_name)",
        )
        p.add_argument(
            "--highlight-longevity-mismatch",
            action="store_true",
            help="Highlight large gap between issue creation and first commit",
        )
        p.add_argument(
            "--longevity-days",
            type=int,
            help="Threshold in days for longevity mismatch detection",
        )
        p.add_argument(
            "--check",
            action="store_true",
            help="Exit with non-zero if hygiene score is below threshold",
        )
        p.add_argument("--min-score", type=int, help="Minimum score for --check")
        p.add_argument(
            "--hygiene-output",
            help="Path to save hygiene summary as JSON",
        )
        p.add_argument(
            "--trust",
            action="store_true",
            help="Trust configuration files found in the repository",
        )
        p.add_argument(
            "--penalty",
            action="append",
            default=[],
            help="Override hygiene penalty (format: metric:value, e.g. direct_push_penalty:20)",
        )
        p.add_argument(
            "--style",
            action="append",
            default=[],
            help="Override visual style (format: key:property:value, e.g. critical:stroke:teal)",
        )

    add_analyze_args(analyze_parser)

    # Implicit analyze behavior: if 1st arg isn't a command, insert 'analyze'
    if len(sys.argv) > 1 and sys.argv[1] not in ["init", "analyze", "-h", "--help"]:
        sys.argv.insert(1, "analyze")

    args = parser.parse_args()

    if args.command == "init":
        if os.path.exists(args.output) and not args.force:
            print(f"Error: File {args.output} already exists. Use --force.")
            sys.exit(1)
        try:
            ref = importlib.resources.files("git_graphable") / "default_config.toml"
            content = ref.read_text()
            with open(args.output, "w") as f:
                f.write(content)
            print(f"Successfully initialized {args.output}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    if args.command != "analyze":
        parser.print_help()
        return

    # Validate conflicting highlights
    fill_highlights = [
        args.highlight_authors,
        args.highlight_pr_status,
        args.highlight_distance_from is not None,
        args.highlight_stale,
        args.highlight_wip,
    ]
    if sum(1 for h in fill_highlights if h) > 1:
        print(
            "Error: Cannot use multiple fill-based highlights (Authors, PR Status, Distance, Stale, WIP)",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        engine_enum = Engine[args.engine.upper()]
    except (ValueError, KeyError):
        print(f"Error: Invalid engine '{args.engine}'")
        sys.exit(1)

    overrides = {
        "engine": engine_enum,
        "production_branch": args.production_branch,
        "development_branch": args.development_branch,
        "date_format": args.date_format,
        "simplify": args.simplify,
        "limit": args.limit,
        "highlight_critical": args.highlight_critical
        if args.highlight_critical
        else None,
        "critical_branches": args.critical_branch,
        "highlight_authors": args.highlight_authors if args.highlight_authors else None,
        "highlight_distance_from": args.highlight_distance_from,
        "highlight_path": tuple(args.highlight_path.split("..", 1))
        if args.highlight_path and ".." in args.highlight_path
        else None,
        "highlight_diverging_from": args.highlight_diverging_from,
        "highlight_orphans": args.highlight_orphans if args.highlight_orphans else None,
        "highlight_stale": args.highlight_stale if args.highlight_stale else None,
        "stale_days": args.stale_days,
        "highlight_long_running": args.highlight_long_running
        if args.highlight_long_running
        else None,
        "long_running_days": args.long_running_days,
        "long_running_base": args.long_running_base,
        "highlight_pr_status": args.highlight_pr_status
        if args.highlight_pr_status
        else None,
        "highlight_wip": args.highlight_wip if args.highlight_wip else None,
        "wip_keywords": args.wip_keyword,
        "highlight_direct_pushes": args.highlight_direct_pushes
        if args.highlight_direct_pushes
        else None,
        "highlight_squashed": args.highlight_squashed
        if args.highlight_squashed
        else None,
        "highlight_back_merges": args.highlight_back_merges
        if args.highlight_back_merges
        else None,
        "highlight_silos": args.highlight_silos if args.highlight_silos else None,
        "silo_commit_threshold": args.silo_threshold,
        "silo_author_count": args.silo_author_count,
        "highlight_issue_inconsistencies": args.highlight_issue_inconsistencies
        if args.highlight_issue_inconsistencies
        else None,
        "issue_pattern": args.issue_pattern,
        "issue_engine": args.issue_engine,
        "jira_url": args.jira_url,
        "issue_script": args.issue_script,
        "highlight_release_inconsistencies": args.highlight_release_inconsistencies
        if args.highlight_release_inconsistencies
        else None,
        "released_statuses": args.released_statuses,
        "highlight_collaboration_gaps": args.highlight_collaboration_gaps
        if args.highlight_collaboration_gaps
        else None,
        "author_mapping": dict(m.split(":", 1) for m in args.author_mapping)
        if args.author_mapping
        else {},
        "highlight_longevity_mismatch": args.highlight_longevity_mismatch
        if args.highlight_longevity_mismatch
        else None,
        "longevity_threshold_days": args.longevity_days,
        "hygiene_weights": {
            p.split(":", 1)[0]: int(p.split(":", 1)[1]) for p in args.penalty
        }
        if args.penalty
        else {},
        "theme": parse_style_overrides(args.style) if args.style else {},
        "min_hygiene_score": args.min_score,
        "hygiene_output": args.hygiene_output,
        "trust": args.trust,
    }

    try:
        results = convert_command(
            args.path,
            args.config,
            overrides,
            engine_enum,
            args.output,
            args.image,
            args.check,
        )
        if args.output == "-":
            print(results["content"])

        if results.get("summary"):
            import json

            hygiene = results["summary"].get("Hygiene Score", {})

            if args.hygiene_output:
                with open(args.hygiene_output, "w") as f:
                    json.dump(hygiene, f, indent=2)

            print("\n--- Git Hygiene Summary ---")
            print(
                f"Overall Score: {hygiene.get('score', 0)}% ({hygiene.get('grade', 'F')})"
            )
            for deduction in hygiene.get("deductions", []):
                print(f"  - {deduction['message']} (-{deduction['amount']}%)")
                for item in deduction.get("items", []):
                    print(f"    * {item}")

            if args.check:
                min_s = args.min_score or 80
                if hygiene.get("score", 0) < min_s:
                    print(
                        f"Error: Hygiene score {hygiene.get('score', 0)}% is below required {min_s}%",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                else:
                    print(
                        f"Success: Hygiene score {hygiene.get('score', 0)}% meets required {min_s}%"
                    )

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

import sys


def main():
    """Main entry point for console_scripts switcher."""
    # Handle implicit 'analyze' behavior
    if len(sys.argv) > 1 and sys.argv[1] not in ["init", "analyze", "--help", "-h"]:
        # If first arg doesn't look like a command or flag, assume it's a path for 'analyze'
        if not sys.argv[1].startswith("-"):
            sys.argv.insert(1, "analyze")

    if "--bare" in sys.argv:
        sys.argv.remove("--bare")
        from .bare_cli import run_bare_cli

        run_bare_cli()
    else:
        try:
            from .rich_cli import app

            app()
        except (ImportError, Exception):
            from .bare_cli import run_bare_cli

            run_bare_cli()


if __name__ == "__main__":
    main()

import sys


def main():
    """Main entry point for console_scripts switcher."""
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

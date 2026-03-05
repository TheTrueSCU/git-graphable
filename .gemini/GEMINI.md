# Gemini Instructions
- Always execute `just test` instead of `pytest` for running tests. Any arguments you specify will be passed through to the wrapped `pytest` command. For example, you may wish to pass `-n 0 -p no:sugar` to disable the xdist and sugar plugins.
- Always execute `just coverage` instead of `pytest` for coverage.
- When adding, removing, or modifying code, adhere to the code ordering guidelines in @./code-ordering.md
- Always execute `just check` before committing any changes to ensure linting, typing, and coverage standards are met.
- Always execute `just lint` after finishing code changes and address any issues flagged.
- Do not use `pip` or `venv` directly; use `uv` for all environment management.
- Do not stage or commit any changes unless explicitly instructed. When instructed to commit or push changes, you MUST first create a new feature branch and then execute `just pr <title> [body]` to prepare the pull request. If a pull request already exists for the current feature branch, push your updates to the same branch instead of creating a new pull request.

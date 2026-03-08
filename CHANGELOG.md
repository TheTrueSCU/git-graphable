# Changelog

All notable changes to this project will be documented in this file.

## [0.7.0] - Unreleased

### Added
- **Security Trust Enforcement**: Custom scripts (`issue_script`, `pr_script`) and sensitive API integrations (Jira) are now disabled by default for untrusted local configurations. Users must explicitly use `--trust` to enable these features for repository-local configs.

### Fixed
- **Critical Command Injection Mitigation**: Fixed a vulnerability in `ScriptIssueEngine` where malicious `issue_id` strings could inject shell commands. Switched to `sh -c` with positional arguments for safe execution.
- **Credential Theft Prevention**: Prevented potential Jira token exposure to untrusted URLs by enforcing the trust model for Jira configurations.
- **XSS Mitigation**: Fixed a medium-severity XSS vulnerability in interactive HTML export legend generation by properly escaping repository-derived data.

## [0.6.0] - 2026-03-06

### Added
- **Native GitLab Support**: Added support for GitLab Merge Requests and Issues using the `glab` CLI.
- **Pull Request Provider Abstraction**: Introduced a new `PullRequestProvider` interface, decoupling PR status logic from GitHub.
    - Added `GitHubPullRequestProvider` (default) using the `gh` CLI.
    - Added `ScriptPullRequestProvider` for custom script-based PR status lookups.
- **Configuration Trust Mechanism**: Introduced a security layer for local repository configurations.
    - Added `--trust` CLI flag to explicitly trust automatically loaded `.git-graphable.toml` or `pyproject.toml` files.
    - Users are now warned when executing custom scripts from untrusted configurations.
- **Dynamic Project Badges**:
    - Added automated generation of Shields.io-compatible JSON badges for **Git Hygiene** and **Code Coverage**.
    - Updated `README.md` to display live status from GitHub Pages.
    - Added `--hygiene-output <path>` to CLI for machine-readable (JSON) hygiene summaries.
- **Improved Automatic Visualization**:
    - Restored the behavior of automatically opening a graph if no output path is provided.
    - Changed default automatic visualization export format from SVG to **PNG** for broader compatibility.
- **Modular Architecture Refactor**: Substantially reorganized the codebase into specialized sub-packages for better maintainability:
    - `src/git_graphable/prs/`: Modular PR providers.
    - `src/git_graphable/issues/`: Modular issue tracker engines.
    - `src/git_graphable/highlights/`: Specialized highlighting logic (visual, hygiene, external).
    - `src/git_graphable/styling/`: Specialized styling logic per visualization engine.
- **Enhanced Issue Scripting**: `ScriptIssueEngine` now supports robust JSON output from scripts (with legacy CSV fallback).
- **Project Governance**: Added official **MIT License** to the repository.
- **Reorganized Test Suite**: Refactored tests into a modular structure mirroring the source code, including a global `conftest.py` for shared fixtures.

### Fixed
- **Comprehensive Security Hardening**: 
    - Protected against argument injection in `git clone`, `glab`, `gh`, and `git rev-list` commands using the `--` separator.
    - Resolved potential path traversal and SSRF risks in Jira issue lookups by properly URL-encoding IDs.
    - Corrected argument passing logic for `git log` limits.
- **Mermaid Parser Reliability**: Fixed parsing errors in Mermaid graphs by substituting sensitive characters (brackets and parentheses) with visually similar full-width Unicode characters.
- **CI Stability**: Fixed CI failures in GitHub Pages deployment by preventing automatic visualization triggers during badge generation.
- **Naming Collisions**: Resolved pytest module collision issues by adding `__init__.py` files to test directories.
- **Code Maintenance**: Updated `.gitignore` to prevent tracking of build artifacts and coverage data.


## [0.5.0] - 2026-03-06

### Added
- **Interactive Demos**: Implemented `examples/publish_demos.py` to generate and host live HTML demos via GitHub Pages.
- **Marketplace Preparation**: Moved `action.yml` to the root directory for GitHub Marketplace publishing and updated related documentation and CI workflows.

### Fixed
- **Squash Merge Detection**: Resolved a `KeyError` and `CycleError` in the logical merge visualization for squashed pull requests when local branch tips were present.

## [0.4.0] - 2026-03-05

### Added
- **Interactive HTML Viewer**: New `--engine html` output that generates a self-contained interactive graph using Cytoscape.js.
    - Includes searchable nodes and a details sidebar with live highlight toggling.
    - Preserves all visual themes and highlighting styles.
    - Lightweight and portable with zero local dependencies.
- **Performance Optimizations**:
    - **Parallel Log Parsing**: Parallelized `GitCommit` instantiation using `ProcessPoolExecutor` for large repositories.
    - **Parallel Hygiene Scoring**: Concurrent execution of hygiene checks using `ThreadPoolExecutor` for faster report generation.
- **Modular CLI Architecture**: 
    - Split into `rich_cli` (Typer/Rich) and `bare_cli` (Argparse) for better environment support.
    - Intelligent switcher logic in `cli.py` handles optional dependencies and fallbacks.
- **New `init` Command**: Easily initialize a default `.git-graphable.toml` configuration file.
- **Reusable GitHub Action**: Added a composite action in `.github/actions/git-graphable/` for automated reporting.
- **Robust Distance/Divergence Highlights**: Enhanced visualization of branch distance and divergence with clearer legend labels.
- **Remote URL Support**: Restored and improved ability to pass remote Git URLs (HTTPS/SSH) as the repository path.
- **Comprehensive UI Testing**: Integrated Playwright for automated browser-based UI testing of the interactive graph.

### Changed
- **Command Renamed**: Renamed the primary command from `convert` to `analyze` for better semantic alignment.
- **Decoupled Hygiene Scoring**: Scoring logic is now independent of visual highlighting options, allowing for more granular configuration.
- **Template System Refactor**: Extracted large HTML/JS blocks into `src/git_graphable/templates.py` for improved maintainability.
- **Removed PlantUML Support**: Support for PlantUML has been removed in favor of more customizable engines (Mermaid, D2, HTML).

## [0.3.0] - 2026-03-05

### Added
- **Customizable Visual Styling**: Full override of node and edge styles (colors, widths, dash patterns) via CLI (`--style`) and TOML (`[git-graphable.theme]`).
- **Configurable Hygiene Scoring**: Customization of hygiene penalties and caps via TOML (`[git-graphable.hygiene_weights]`).
- **Advanced Issue Tracker Integration**:
    - **Longevity Mismatch**: Detection of large time gaps between ticket creation and the first commit.
    - **Collaboration Gaps**: Highlighting when the Git author doesn't match the Issue Tracker assignee.
    - **Release Validation**: Verification that "Released" tickets are tagged in Git.
- **New Documentation**: Added `STYLING.md` guide for visual customization.
- **Engine Consistency**: Unified styling logic across Mermaid, D2, and Graphviz engines.

### Changed
- **CLI Refactor**: Migrated to a more robust Typer/Rich implementation with enhanced command-line options.
- **Issue Engine**: Refactored `IssueTracker` to support richer metadata (assignees, timestamps).

### Fixed
- Fixed inconsistent color application in Mermaid graphs.
- Improved cleanup of temporary files during image export.

## [0.2.0] - 2026-03-04
- Initial functional release with basic Git hygiene scoring and GitHub/Jira integration.

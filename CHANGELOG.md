# Changelog

All notable changes to this project will be documented in this file.

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

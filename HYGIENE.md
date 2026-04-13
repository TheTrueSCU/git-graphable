# Git Hygiene Guidelines

This document explains the hygiene metrics analyzed by `git-graphable` and provides actionable steps to remediate common issues.

## 1. Process Integrity

### Direct Pushes to Protected Branches
**Detection:** Commits made directly to `production_branch` or `development_branch` without a merge commit.
**Why it matters:** Bypassing the Pull Request process avoids code review and CI checks, increasing the risk of bugs.
**Remediation:**
1.  **Stop**: Do not push directly to main/master/develop.
2.  **Fix History** (if not yet shared/stable):
    ```bash
    # Move the commit to a new branch
    git checkout -b feature/my-fix

    # Reset main back to before the direct push
    git checkout main
    git reset --hard <commit-before-push>

    # Push the new branch and open a PR
    git push -u origin feature/my-fix
    ```
3.  **Protection**: Enable "Branch Protection Rules" in GitHub/GitLab settings to physically prevent direct pushes.

### Conflicting Pull Requests
**Detection:** Open PRs marked as `CONFLICTING` by the VCS provider.
**Why it matters:** Conflicts block merging and indicate divergent development paths that get harder to resolve over time.
**Remediation:**
```bash
git checkout feature/my-branch
git pull origin main
# Resolve conflicts in editor
git add .
git commit -m "Merge branch 'main' into feature/my-branch"
git push
```

### Orphan/Dangling Commits
**Detection:** Commits that are not reachable from any branch or tag.
**Why it matters:** These are often lost code or mistakes.
**Remediation:**
- **Garbage Collect**: `git gc --prune=now`
- **Recover**: If valuable, checkout the SHA and create a branch: `git checkout -b recover-work <sha>`

## 2. Cleanliness

### WIP / Fixup Commits
**Detection:** Commit messages containing "wip", "todo", "fixup", "temp".
**Why it matters:** messy history makes debugging and `git bisect` difficult.
**Remediation:**
- **Interactive Rebase**: Squash WIP commits into meaningful units.
    ```bash
    git rebase -i HEAD~n  # where n is number of commits back
    # Change 'pick' to 'squash' or 'fixup' for the WIP commits
    ```

### Stale Branches
**Detection:** Feature branches with no activity for `stale_days` (default: 30).
**Why it matters:** Clutters the repository and indicates abandoned work.
**Remediation:**
- **Delete Local**: `git branch -d branch-name`
- **Delete Remote**: `git push origin --delete branch-name`
- **Archive**: Tag it if you need to keep it: `git tag archive/branch-name branch-name`

## 3. Connectivity & Flow

### Long-Running Branches
**Detection:** Feature branches that have diverged from the base for more than `long_running_days` (default: 14).
**Why it matters:** Increases the risk of massive merge conflicts (The "Merge Hell").
**Remediation:**
- **Merge Often**: Merge `main` into your feature branch frequently.
- **Ship Smaller**: Break large features into smaller, mergeable PRs.

### Divergence (Behind Base)
**Detection:** Feature branches that are missing commits from the base branch (`main`).
**Why it matters:** You are testing against outdated code.
**Remediation:**
```bash
git checkout feature/my-feature
git pull origin main
git push
```

### Redundant Back-Merges
**Detection:** Merging `main` into a feature branch, but doing it recursively or unnecessarily often creates a "railroad track" history.
**Why it matters:** Makes history hard to read.
**Remediation:**
- Use `git rebase main` instead of `git merge main` for feature branches (if your team policy allows rewriting feature branch history).

## 4. Collaboration

### Contributor Silos
**Detection:** Long sequences of commits on a branch by a single author without interaction from others.
**Why it matters:** Risk of "Bus Factor". No code review or shared knowledge.
**Remediation:**
- **Pair Program**: Involve others earlier.
- **Early PRs**: Open a Draft PR to get feedback before the feature is done.

### Collaboration Gaps
**Detection:** The Git commit author does not match the assignee of the linked Issue Tracker ticket.
**Remediation:**
- Update the Issue Tracker ticket to assign it to the actual developer.
- Configure `author_mapping` in `.git-graphable.toml` if names just don't match (e.g., "John Doe" vs "jdoe").

## 5. Consistency (Issue Tracking)

### Issue / Git Desync
**Detection:**
- Ticket is `OPEN` but PR is `MERGED`.
- Ticket is `CLOSED` but PR is `OPEN`.
**Remediation:**
- **Sync Status**: Manually update the ticket status.
- **Automation**: Configure GitHub/Jira to auto-close issues when PRs are merged.

### Release Inconsistencies
**Detection:** Ticket is marked `RELEASED` but the commit is not included in any Git Tag.
**Remediation:**
- **Cut a Release**: Create a Git tag for the deployment.
    ```bash
    git tag v1.0.0
    git push --tags
    ```

### Longevity Mismatch
**Detection:** A large time gap (>14 days) exists between when a ticket was created and when work (commits) started.
**Why it matters:** Planning failure or stale requirements.
**Remediation:**
- **Review Backlog**: Don't open tickets until work is ready to start.
- **Re-evaluate**: If a ticket sits for 2 weeks, check if requirements have changed before starting code.

## 6. Ignoring Hygiene Rules

Sometimes a commit or branch is flagged for a reason that is acceptable or intended. You can selectively ignore these rules.

### Via Configuration (`.git-graphable.toml`)

Add an `[git-graphable.ignore]` section to your configuration:

```toml
[git-graphable.ignore]
# Ignore specific rules for specific SHAs (prefix or full SHA)
"9bd5377" = ["wip", "direct_push"]
"abc1234" = ["all"]  # Ignore all hygiene rules for this commit
```

### Via CLI

Use the `--ignore` flag:

```bash
# Ignore WIP rule for a specific SHA
uv run git-graphable analyze . --ignore 9bd5377:wip

# Ignore multiple items
uv run git-graphable analyze . --ignore 9bd5377:wip --ignore abc1234:all
```

### Supported Rule Names
- `wip`
- `direct_push`
- `divergence`
- `orphan`
- `stale`
- `long_running`
- `back_merge`
- `silo`
- `all` (ignores everything for that SHA)

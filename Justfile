set dotenv-load

GIT_BRANCH:=`git branch --show-current | xargs echo -n | grep . || echo "unknown"`
GIT_COMMIT:=`git rev-parse HEAD | xargs echo -n | grep . || echo "unknown"`

@_:
    just --list

_browser *args:
    @uv run -m webbrowser -t {{ args }}

_cleandir name:
    @rm -rf {{ name }}

_cleanfiles type:
    @find . -type f -name "*.{{ type }}" -delete

[group('docs')]
usage:
    PYTHONPATH=src uv run typer git_graphable.cli utils docs --name git-graphable --output USAGE.md

[group('env')]
@clean:
    just _cleandir build
    just _cleandir __pycache__
    just _cleandir .coverage
    just _cleandir .pytest_cache
    just _cleandir .ruff_cache
    just _cleandir htmlcov
    just _cleandir htmlrep
    just _cleandir _minted
    just _cleandir svg-inkscape
    just _cleandir docs/_build
    just _cleandir docs/_extra

[group('env')]
fresh: nuke install

[group('env')]
install:
    uv sync

[group('env')]
nuke: clean
    just _cleandir .venv

[group('env')]
update:
    uv sync --upgrade

[group('package')]
build:
    uv build

[group('package')]
publish: build
    uv publish

[group('qa')]
check: lint typing coverage
    uv run git-graphable . --check --min-score 75 --bare --highlight-wip --highlight-direct-pushes

[group('qa')]
@coverage *args:
    just test --cov=. --cov-report html --cov-report term-missing {{ args }}

[group('qa')]
[group('view')]
covrep:
    just _browser htmlcov/index.html

[group('qa')]
lint:
    uv run isort .
    uv run ruff format
    uv run ruff check --fix

[group('qa')]
@test *args:
    uv run -m pytest --git-branch {{ GIT_BRANCH }} --git-commit {{ GIT_COMMIT }} --html-output htmlrep -n auto --should-open-report never -m "not ui" {{ args }}

[group('qa')]
install-ui:
    uv run --group ui playwright install chromium

[group('qa')]
@test-ui *args:
    uv run --group ui -m pytest --git-branch {{ GIT_BRANCH }} --git-commit {{ GIT_COMMIT }} --html-output htmlrep -n 1 --should-open-report never -m "ui" {{ args }}

[group('qa')]
[group('view')]
testrep:
    just _browser htmlrep/report.html

[group('qa')]
typing:
    uv run ty check

[group('run')]
pr title body="":
    #!/usr/bin/env bash
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" == "main" ]; then
        echo "Error: You are on the 'main' branch. Please create a feature branch first!"
        exit 1
    fi
    just check
    git push -u origin "$CURRENT_BRANCH"
    gh pr create --repo TheTrueSCU/git-graphable --head "$CURRENT_BRANCH" --title "{{ title }}" --body "{{ body }}"

[group('run')]
@run *args:
    uv run git-graphable {{ args }}

[group('demo')]
generate-examples:
    uv run python examples/generate_demos.py
    uv run git-graphable examples/repos/repo-pristine --engine mermaid -o examples/assets/pristine.mmd --highlight-critical --critical-branch main --highlight-authors --bare
    uv run git-graphable examples/repos/repo-messy --engine mermaid -o examples/assets/messy.mmd --highlight-wip --highlight-direct-pushes --highlight-stale --bare
    uv run git-graphable examples/repos/repo-features --engine mermaid -o examples/assets/features.mmd --highlight-orphans --highlight-diverging-from main --bare
    uv run git-graphable examples/repos/repo-risk-silo --engine mermaid -o examples/assets/silo.mmd --highlight-silos --silo-threshold 20 --bare
    uv run git-graphable examples/repos/repo-complex-hygiene --engine mermaid -o examples/assets/complex.mmd --highlight-back-merges --bare
    uv run git-graphable examples/repos/repo-issue-desync --engine mermaid -o examples/assets/issue_desync.mmd --highlight-issue-inconsistencies --issue-pattern "PROJ-[0-9]+" --issue-engine script --issue-script "echo CLOSED" --bare
    uv run git-graphable examples/repos/repo-release-desync --engine mermaid -o examples/assets/release_desync.mmd --highlight-release-inconsistencies --issue-pattern "PROJ-[0-9]+" --issue-engine script --issue-script "echo CLOSED" --bare
    uv run git-graphable examples/repos/repo-collab-gap --engine mermaid -o examples/assets/collab_gap.mmd --highlight-collaboration-gaps --issue-pattern "PROJ-[0-9]+" --issue-engine script --issue-script "echo OPEN,Bob" --bare

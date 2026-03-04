set dotenv-load

GIT_BRANCH:=`git branch --show-current`
GIT_COMMIT:=`git rev-parse HEAD`

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
    PYTHONPATH=src uv run typer git_graph.cli utils docs --name git-graph --output USAGE.md

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
    uv run -m pytest --git-branch {{ GIT_BRANCH }} --git-commit {{ GIT_COMMIT }} --html-output htmlrep -n auto --should-open-report never {{ args }}

[group('qa')]
[group('view')]
testrep:
    just _browser htmlrep/report.html

[group('qa')]
typing:
    uv run ty check

[group('run')]
@run *args:
    uv run git-graph {{ args }}

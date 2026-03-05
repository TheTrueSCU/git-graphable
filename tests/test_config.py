import os
import tempfile

from git_graphable.core import GitLogConfig


def test_config_from_toml():
    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write("""
[git-graphable]
simplify = true
limit = 50
highlight_critical = ["main", "prod"]
highlight_path = ["v1", "v2"]
""")
        config_path = f.name

    try:
        config = GitLogConfig.from_toml(config_path)
        assert config.simplify is True
        assert config.limit == 50
        assert config.highlight_critical == ["main", "prod"]
        assert config.highlight_path == ("v1", "v2")
    finally:
        os.unlink(config_path)


def test_config_from_pyproject_toml():
    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write("""
[tool.git-graphable]
simplify = true
""")
        config_path = f.name

    try:
        config = GitLogConfig.from_toml(config_path)
        assert config.simplify is True
    finally:
        os.unlink(config_path)


def test_config_branch_roles():
    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write("""
[git-graphable]
production_branch = "master"
development_branch = "dev"
""")
        config_path = f.name

    try:
        config = GitLogConfig.from_toml(config_path)
        assert config.production_branch == "master"
        assert config.development_branch == "dev"
    finally:
        os.unlink(config_path)


def test_config_merge():
    base = GitLogConfig(limit=100, simplify=False)
    overrides = {"limit": 50}  # Non-default override

    merged = base.merge(overrides)
    assert merged.limit == 50
    assert merged.simplify is False


def test_config_merge_default_priority():
    base = GitLogConfig(simplify=True)
    overrides = {"simplify": False}  # Default value

    merged = base.merge(overrides)
    # Since 'False' is the default for simplify, we need to decide if an explicit False in overrides should win.
    # In current implementation, we only override if value is not None.
    # If a user passes --no-simplify (if we had it), we'd want False to win.
    assert merged.simplify is False


def test_config_decoupled_threshold():
    # Test that we can set stale_days in config without turning on highlighting
    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write("""
[git-graphable]
stale_days = 45
highlight_stale = false
""")
        config_path = f.name

    try:
        config = GitLogConfig.from_toml(config_path)
        assert config.stale_days == 45
        assert config.highlight_stale is False

        # Now merge with a CLI toggle
        merged = config.merge({"highlight_stale": True})
        assert merged.highlight_stale is True
        assert merged.stale_days == 45

        # Or override everything
        overridden = config.merge({"highlight_stale": True, "stale_days": 15})
        assert overridden.highlight_stale is True
        assert overridden.stale_days == 15
    finally:
        os.unlink(config_path)

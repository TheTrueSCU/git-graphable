from git_graphable.cli_utils import parse_style_overrides


def test_parse_style_overrides():
    styles = ["critical:stroke:teal", "direct_push:dash:dotted", "orphan:width:5"]
    expected = {
        "critical": {"stroke": "teal"},
        "direct_push": {"dash": "dotted"},
        "orphan": {"width": 5},
    }
    assert parse_style_overrides(styles) == expected


def test_parse_style_overrides_invalid():
    styles = ["invalid", "partially:valid"]
    assert parse_style_overrides(styles) == {}

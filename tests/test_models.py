from git_graph.models import Tag


def test_tag_enum_values():
    assert Tag.GIT_COMMIT.value == "git_commit"
    assert Tag.AUTHOR.value == "author:"
    assert Tag.COLOR.value == "color:"
    assert Tag.EDGE_PATH.value == "highlight"

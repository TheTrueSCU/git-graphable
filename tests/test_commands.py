from git_graphable.commands import get_extension
from git_graphable.core import Engine


def test_get_extension():
    assert get_extension(Engine.MERMAID, False) == ".mmd"
    assert get_extension(Engine.D2, False) == ".d2"
    assert get_extension(Engine.MERMAID, True) == ".svg"

from enum import Enum


class Tag(str, Enum):
    GIT_COMMIT = "git_commit"
    CRITICAL = "critical"
    BEHIND = "behind"
    ORPHAN = "orphan"
    LONG_RUNNING = "long_running"
    PATH_HIGHLIGHT = "path_highlight"

    # Prefix tags
    AUTHOR = "author:"
    BRANCH = "branch:"
    TAG = "tag:"
    COLOR = "color:"
    DISTANCE_COLOR = "distance_color:"
    STALE_COLOR = "stale_color:"
    AUTHOR_HIGHLIGHT = "author_highlight:"

    # Edge attributes
    EDGE_PATH = "highlight"
    EDGE_LONG_RUNNING = "long_running_edge"

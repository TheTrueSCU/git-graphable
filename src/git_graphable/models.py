from enum import Enum


class Tag(str, Enum):
    GIT_COMMIT = "git_commit"
    CRITICAL = "critical"
    BEHIND = "behind"
    ORPHAN = "orphan"
    LONG_RUNNING = "long_running"
    PATH_HIGHLIGHT = "path_highlight"
    PR_STATUS = "pr_status"
    WIP = "wip"
    DIRECT_PUSH = "direct_push"

    # Specific PR states
    PR_OPEN = "pr:open"
    PR_CLOSED = "pr:closed"
    PR_MERGED = "pr:merged"
    PR_DRAFT = "pr:draft"
    PR_CONFLICT = "pr:conflict"

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

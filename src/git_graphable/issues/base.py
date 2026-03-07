"""
Base models and ABC for issue trackers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


class IssueStatus:
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


@dataclass
class IssueInfo:
    id: str
    status: str
    assignee: Optional[str] = None
    created_at: Optional[str] = None  # ISO 8601 timestamp


class IssueTracker(ABC):
    """Base class for issue tracker integrations."""

    @abstractmethod
    def get_issue_info(self, issue_ids: List[str]) -> Dict[str, IssueInfo]:
        """Fetch info for a list of issue IDs. Returns ID -> IssueInfo map."""
        pass

    def get_statuses(self, issue_ids: List[str]) -> Dict[str, str]:
        """Backward compatible helper."""
        info = self.get_issue_info(issue_ids)
        return {iid: item.status for iid, item in info.items()}

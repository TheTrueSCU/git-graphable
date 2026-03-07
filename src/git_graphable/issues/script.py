"""
Script-based issue tracker integration.
"""

import json
import shlex
import subprocess
from typing import Dict, List

from .base import IssueInfo, IssueStatus, IssueTracker


class ScriptIssueEngine(IssueTracker):
    """Integration using a custom shell script."""

    def __init__(self, script_template: str, trusted: bool = False):
        self.template = script_template
        self.trusted = trusted
        self._warned = False

    def get_issue_info(self, issue_ids: List[str]) -> Dict[str, IssueInfo]:
        if not self.template:
            return {}

        if not self.trusted and not self._warned:
            print(
                "\n[bold yellow]WARNING:[/bold yellow] Executing issue script from an untrusted configuration."
            )
            print("Review your configuration if this was unexpected.\n")
            self._warned = True

        results = {}
        for issue_id in issue_ids:
            try:
                # Use shlex.quote to prevent command injection if the issue_id
                # contains malicious characters.
                safe_id = shlex.quote(issue_id)
                cmd_str = self.template.replace("{id}", safe_id)
                result = subprocess.run(
                    cmd_str, shell=True, capture_output=True, text=True, check=True
                )
                output = result.stdout.strip()

                # Try JSON parsing first
                try:
                    data = json.loads(output)
                    raw_status = data.get("status", "").upper()
                    assignee = data.get("assignee")
                    created_at = data.get("created_at")
                except json.JSONDecodeError:
                    # Fallback to simple parsing logic: "STATUS,ASSIGNEE,CREATED_AT"
                    parts = output.split(",")
                    raw_status = parts[0].upper()
                    assignee = parts[1].strip() if len(parts) > 1 else None
                    created_at = parts[2].strip() if len(parts) > 2 else None

                status = IssueStatus.UNKNOWN
                if "OPEN" in raw_status:
                    status = IssueStatus.OPEN
                elif "CLOSED" in raw_status or "DONE" in raw_status:
                    status = IssueStatus.CLOSED

                results[issue_id] = IssueInfo(
                    id=issue_id, status=status, assignee=assignee, created_at=created_at
                )
            except Exception:
                results[issue_id] = IssueInfo(id=issue_id, status=IssueStatus.UNKNOWN)
        return results

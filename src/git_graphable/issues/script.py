"""
Script-based issue tracker integration.
"""

import json
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

        if not self.trusted:
            print(
                "\n[bold red]ERROR:[/bold red] Executing issue script from an untrusted configuration is disabled."
            )
            print("To enable this script, use --config or --trust.\n")
            return {}

        results = {}
        for issue_id in issue_ids:
            try:
                # Use positional arguments to prevent command injection.
                # We replace {id} with "$1" and pass issue_id as the first argument to sh -c.
                cmd_template = self.template.replace("{id}", '"$1"')
                result = subprocess.run(
                    ["sh", "-c", cmd_template, "--", issue_id],
                    capture_output=True,
                    text=True,
                    check=True,
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

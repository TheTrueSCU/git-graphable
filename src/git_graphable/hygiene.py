from typing import Any, Dict

from graphable import Graph

from .core import GitCommit, GitLogConfig
from .models import Tag


class HygieneScorer:
    def __init__(self, graph: Graph[GitCommit], config: GitLogConfig):
        self.graph = graph
        self.config = config
        self.score = 100
        self.deductions = []

    def calculate(self) -> Dict[str, Any]:
        """Calculate hygiene score and return report."""
        self._check_process_integrity()
        self._check_cleanliness()
        self._check_connectivity()
        self._check_back_merges()
        self._check_contributor_silos()

        # Ensure score doesn't go below 0
        final_score = max(0, self.score)

        grade = "F"
        color = "red"
        if final_score >= 90:
            grade = "A"
            color = "green"
        elif final_score >= 80:
            grade = "B"
            color = "blue"
        elif final_score >= 70:
            grade = "C"
            color = "yellow"
        elif final_score >= 60:
            grade = "D"
            color = "orange"

        return {
            "score": final_score,
            "grade": grade,
            "color": color,
            "deductions": self.deductions,
        }

    def _add_deduction(self, amount: int, message: str):
        self.score -= amount
        self.deductions.append({"amount": amount, "message": message})

    def _check_process_integrity(self):
        # Direct Pushes
        direct_pushes = [c for c in self.graph if c.is_tagged(Tag.DIRECT_PUSH.value)]
        if direct_pushes:
            # -15% per commit, capped at 45%
            deduction = min(45, len(direct_pushes) * 15)
            self._add_deduction(
                deduction, f"Direct pushes to protected branches ({len(direct_pushes)})"
            )

        # Conflicting PRs
        conflicts = [c for c in self.graph if c.is_tagged(Tag.PR_CONFLICT.value)]
        if conflicts:
            # -10% per PR, capped at 30%
            deduction = min(30, len(conflicts) * 10)
            self._add_deduction(
                deduction, f"Conflicting pull requests ({len(conflicts)})"
            )

        # Orphan Commits
        orphans = [c for c in self.graph if c.is_tagged(Tag.ORPHAN.value)]
        if orphans:
            # -2% per instance, capped at 10%
            deduction = min(10, len(orphans) * 2)
            self._add_deduction(
                deduction, f"Orphan/Dangling commits found ({len(orphans)})"
            )

    def _check_cleanliness(self):
        # WIP Commits
        wip_commits = [c for c in self.graph if c.is_tagged(Tag.WIP.value)]
        if wip_commits:
            # -3% per commit, capped at 15%
            deduction = min(15, len(wip_commits) * 3)
            self._add_deduction(
                deduction, f"WIP/Fixup commits in history ({len(wip_commits)})"
            )

        # Stale Branches
        stale = [c for c in self.graph if c.is_tagged(Tag.STALE_COLOR.value)]
        if stale:
            # -5% per branch, capped at 20%
            deduction = min(20, len(stale) * 5)
            self._add_deduction(deduction, f"Stale branch tips found ({len(stale)})")

    def _check_connectivity(self):
        # Long-Running Branches
        long_running = [
            c
            for c in self.graph
            if c.is_tagged(Tag.LONG_RUNNING.value) and c.reference.branches
        ]
        if long_running:
            # -10% per branch, capped at 30%
            deduction = min(30, len(long_running) * 10)
            self._add_deduction(
                deduction, f"Long-running unmerged branches ({len(long_running)})"
            )

        # Behind Base (Divergence)
        behind = [c for c in self.graph if c.is_tagged(Tag.BEHIND.value)]
        if behind:
            # -5% flat deduction if any divergence exists
            self._add_deduction(
                5, "Repository has commits missing from feature branches (divergence)"
            )

    def _check_back_merges(self):
        # Redundant Merges (Back-merges from main into feature)
        back_merges = [c for c in self.graph if c.is_tagged(Tag.BACK_MERGE.value)]
        if back_merges:
            # -5% per instance, capped at 25%
            deduction = min(25, len(back_merges) * 5)
            self._add_deduction(
                deduction,
                f"Redundant back-merges from base branch ({len(back_merges)})",
            )

    def _check_contributor_silos(self):
        # Contributor Silos
        silos = [c for c in self.graph if c.is_tagged(Tag.CONTRIBUTOR_SILO.value)]
        if silos:
            # -10% per siloed branch, capped at 30%
            deduction = min(30, len(silos) * 10)
            self._add_deduction(
                deduction, f"Branches dominated by too few authors ({len(silos)})"
            )

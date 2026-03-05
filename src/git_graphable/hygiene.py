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
        self.weights = config.hygiene_weights

    def calculate(self) -> Dict[str, Any]:
        """Calculate hygiene score and return report."""
        self._check_process_integrity()
        self._check_cleanliness()
        self._check_connectivity()
        self._check_back_merges()
        self._check_contributor_silos()
        self._check_issue_inconsistencies()
        self._check_release_inconsistencies()
        self._check_collaboration_gaps()
        self._check_longevity_mismatches()

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
        if amount <= 0:
            return
        self.score -= amount
        self.deductions.append({"amount": amount, "message": message})

    def _check_process_integrity(self):
        # Direct Pushes
        direct_pushes = [c for c in self.graph if c.is_tagged(Tag.DIRECT_PUSH.value)]
        if direct_pushes:
            deduction = min(
                self.weights.direct_push_cap,
                len(direct_pushes) * self.weights.direct_push_penalty,
            )
            self._add_deduction(
                deduction, f"Direct pushes to protected branches ({len(direct_pushes)})"
            )

        # Conflicting PRs
        conflicts = [c for c in self.graph if c.is_tagged(Tag.PR_CONFLICT.value)]
        if conflicts:
            deduction = min(
                self.weights.pr_conflict_cap,
                len(conflicts) * self.weights.pr_conflict_penalty,
            )
            self._add_deduction(
                deduction, f"Conflicting pull requests ({len(conflicts)})"
            )

        # Orphan Commits
        orphans = [c for c in self.graph if c.is_tagged(Tag.ORPHAN.value)]
        if orphans:
            deduction = min(
                self.weights.orphan_commit_cap,
                len(orphans) * self.weights.orphan_commit_penalty,
            )
            self._add_deduction(
                deduction, f"Orphan/Dangling commits found ({len(orphans)})"
            )

    def _check_cleanliness(self):
        # WIP Commits
        wip_commits = [c for c in self.graph if c.is_tagged(Tag.WIP.value)]
        if wip_commits:
            deduction = min(
                self.weights.wip_commit_cap,
                len(wip_commits) * self.weights.wip_commit_penalty,
            )
            self._add_deduction(
                deduction, f"WIP/Fixup commits in history ({len(wip_commits)})"
            )

        # Stale Branches
        stale = [c for c in self.graph if c.is_tagged(Tag.STALE_COLOR.value)]
        if stale:
            deduction = min(
                self.weights.stale_branch_cap,
                len(stale) * self.weights.stale_branch_penalty,
            )
            self._add_deduction(deduction, f"Stale branch tips found ({len(stale)})")

    def _check_connectivity(self):
        # Long-Running Branches
        long_running = [
            c
            for c in self.graph
            if c.is_tagged(Tag.LONG_RUNNING.value) and c.reference.branches
        ]
        if long_running:
            deduction = min(
                self.weights.long_running_branch_cap,
                len(long_running) * self.weights.long_running_branch_penalty,
            )
            self._add_deduction(
                deduction, f"Long-running unmerged branches ({len(long_running)})"
            )

        # Behind Base (Divergence)
        behind = [c for c in self.graph if c.is_tagged(Tag.BEHIND.value)]
        if behind:
            self._add_deduction(
                self.weights.divergence_penalty,
                "Repository has commits missing from feature branches (divergence)",
            )

    def _check_back_merges(self):
        # Redundant Merges (Back-merges from main into feature)
        back_merges = [c for c in self.graph if c.is_tagged(Tag.BACK_MERGE.value)]
        if back_merges:
            deduction = min(
                self.weights.back_merge_cap,
                len(back_merges) * self.weights.back_merge_penalty,
            )
            self._add_deduction(
                deduction,
                f"Redundant back-merges from base branch ({len(back_merges)})",
            )

    def _check_contributor_silos(self):
        # Contributor Silos
        silos = [c for c in self.graph if c.is_tagged(Tag.CONTRIBUTOR_SILO.value)]
        if silos:
            deduction = min(
                self.weights.contributor_silo_cap,
                len(silos) * self.weights.contributor_silo_penalty,
            )
            self._add_deduction(
                deduction, f"Branches dominated by too few authors ({len(silos)})"
            )

    def _check_issue_inconsistencies(self):
        # Issue Inconsistencies
        inconsistencies = [
            c for c in self.graph if c.is_tagged(Tag.ISSUE_INCONSISTENCY.value)
        ]
        if inconsistencies:
            deduction = min(
                self.weights.issue_inconsistency_cap,
                len(inconsistencies) * self.weights.issue_inconsistency_penalty,
            )
            self._add_deduction(
                deduction,
                f"Inconsistencies between Git and Issue Tracker ({len(inconsistencies)})",
            )

    def _check_release_inconsistencies(self):
        # Release Inconsistencies
        inconsistencies = [
            c for c in self.graph if c.is_tagged(Tag.RELEASE_INCONSISTENCY.value)
        ]
        if inconsistencies:
            deduction = min(
                self.weights.release_inconsistency_cap,
                len(inconsistencies) * self.weights.release_inconsistency_penalty,
            )
            self._add_deduction(
                deduction,
                f"Issues marked 'Released' but not tagged in Git ({len(inconsistencies)})",
            )

    def _check_collaboration_gaps(self):
        # Collaboration Gaps
        gaps = [c for c in self.graph if c.is_tagged(Tag.COLLABORATION_GAP.value)]
        if gaps:
            deduction = min(
                self.weights.collaboration_gap_cap,
                len(gaps) * self.weights.collaboration_gap_penalty,
            )
            self._add_deduction(
                deduction, f"Git author doesn't match issue assignee ({len(gaps)})"
            )

    def _check_longevity_mismatches(self):
        # Longevity Mismatches
        mismatches = [
            c for c in self.graph if c.is_tagged(Tag.LONGEVITY_MISMATCH.value)
        ]
        if mismatches:
            deduction = min(
                self.weights.longevity_mismatch_cap,
                len(mismatches) * self.weights.longevity_mismatch_penalty,
            )
            self._add_deduction(
                deduction,
                f"Significant gap between issue creation and code commit ({len(mismatches)})",
            )

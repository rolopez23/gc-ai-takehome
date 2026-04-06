"""Tests for the deterministic synthesis function."""

import os

import pytest

from services.synthesis import (
    ESCALATION_THRESHOLD,
    compute_overall_fairness,
    synthesize,
)
from services.agents.headline import HeadlineResult

# --- Cycle 3: synthesis-worst-clause-wins ---


class TestWorstClauseWins:
    def test_synthesis_all_fair(self):
        """All clauses fairness='fair' -> overall_fairness='fair'."""
        clauses = [
            {"fairness": "fair", "status": "evaluated"},
            {"fairness": "fair", "status": "evaluated"},
            {"fairness": "fair", "status": "evaluated"},
        ]
        assert compute_overall_fairness(clauses) == "fair"

    def test_synthesis_one_dealbreaker(self):
        """One dealbreaker clause -> overall_fairness='dealbreaker'."""
        clauses = [
            {"fairness": "fair", "status": "evaluated"},
            {"fairness": "dealbreaker", "status": "evaluated"},
            {"fairness": "fair", "status": "evaluated"},
        ]
        assert compute_overall_fairness(clauses) == "dealbreaker"

    def test_synthesis_one_nonstandard(self):
        """One non-standard, rest fair -> overall_fairness='non-standard' (below escalation threshold)."""
        # 1 of 10 = 10%, below the 20% escalation threshold
        clauses = [{"fairness": "fair", "status": "evaluated"}] * 9 + [
            {"fairness": "non-standard", "status": "evaluated"}
        ]
        assert compute_overall_fairness(clauses) == "non-standard"

    def test_synthesis_worst_wins(self):
        """Mix with dealbreaker -> overall_fairness='dealbreaker' regardless of counts."""
        clauses = [
            {"fairness": "fair", "status": "evaluated"},
            {"fairness": "non-standard", "status": "evaluated"},
            {"fairness": "dealbreaker", "status": "evaluated"},
        ] + [{"fairness": "fair", "status": "evaluated"}] * 7
        assert compute_overall_fairness(clauses) == "dealbreaker"


# --- Cycle 4: synthesis-escalation-rule ---


class TestEscalationRule:
    def test_escalation_20_percent(self):
        """2 of 10 clauses non-standard (20%) -> overall_fairness='dealbreaker'."""
        clauses = [{"fairness": "fair", "status": "evaluated"}] * 8 + [
            {"fairness": "non-standard", "status": "evaluated"}
        ] * 2
        assert compute_overall_fairness(clauses) == "dealbreaker"

    def test_no_escalation_below_threshold(self):
        """1 of 10 clauses non-standard (10%) -> overall_fairness='non-standard' (no escalation)."""
        clauses = [{"fairness": "fair", "status": "evaluated"}] * 9 + [
            {"fairness": "non-standard", "status": "evaluated"}
        ]
        assert compute_overall_fairness(clauses) == "non-standard"

    def test_escalation_threshold_configurable(self, monkeypatch):
        """With ESCALATION_THRESHOLD=0.3, 2 of 10 non-standard does not escalate."""
        monkeypatch.setenv("ESCALATION_THRESHOLD", "0.3")
        # Need to re-import to pick up new env var
        import importlib
        import services.synthesis

        importlib.reload(services.synthesis)
        from services.synthesis import compute_overall_fairness as reloaded_fn

        clauses = [{"fairness": "fair", "status": "evaluated"}] * 8 + [
            {"fairness": "non-standard", "status": "evaluated"}
        ] * 2
        assert reloaded_fn(clauses) == "non-standard"

        # Restore default
        monkeypatch.delenv("ESCALATION_THRESHOLD", raising=False)
        importlib.reload(services.synthesis)


# --- Cycle 5: synthesis-excludes-errored ---


class TestExcludesErrored:
    def test_synthesis_excludes_errored_clauses(self):
        """Errored clauses are excluded from fairness computation."""
        # 2 errored (would be dealbreaker if counted), 8 fair
        clauses = [
            {"fairness": "dealbreaker", "status": "error"},
            {"fairness": "dealbreaker", "status": "error"},
        ] + [{"fairness": "fair", "status": "evaluated"}] * 8
        # synthesize should exclude errored, so all remaining are fair
        headline = HeadlineResult(summary="Test summary", call_to_action=["Action 1"])
        result = synthesize(
            agreement_type="SaaS MSA",
            clause_results=clauses,
            headline=headline,
        )
        assert result["overall_fairness"] == "fair"

    def test_synthesis_assembles_full_result(self):
        """synthesize() returns a dict with all required fields."""
        # 1 of 10 non-standard = 10%, below escalation threshold
        clauses = [{"fairness": "fair", "status": "evaluated"}] * 9 + [
            {"fairness": "non-standard", "status": "evaluated"},
        ]
        headline = HeadlineResult(
            summary="Contract looks fair overall.",
            call_to_action=["Review indemnification clause"],
        )
        result = synthesize(
            agreement_type="NDA",
            clause_results=clauses,
            headline=headline,
        )
        assert result["overall_fairness"] == "non-standard"
        assert result["agreement_type"] == "NDA"
        assert result["summary"] == "Contract looks fair overall."
        assert result["call_to_action"] == ["Review indemnification clause"]
        assert result["clauses"] == clauses

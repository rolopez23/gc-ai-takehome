"""Deterministic synthesis: overall fairness computation and result assembly."""

import os

from services.agents.headline import HeadlineResult

FAIRNESS_RANK = {"fair": 0, "non-standard": 1, "dealbreaker": 2}
RANK_TO_FAIRNESS = {v: k for k, v in FAIRNESS_RANK.items()}

ESCALATION_THRESHOLD = float(os.getenv("ESCALATION_THRESHOLD", "0.2"))


def compute_overall_fairness(clauses: list[dict]) -> str:
    """Compute overall fairness using worst-clause-wins + escalation rule.

    Excludes clauses with status='error' from computation.
    """
    evaluated = [
        c
        for c in clauses
        if c.get("status") != "error" and c.get("fairness") in FAIRNESS_RANK
    ]
    if not evaluated:
        return "fair"

    worst = max(FAIRNESS_RANK[c["fairness"]] for c in evaluated)

    # Escalation: if >= threshold of clauses are non-standard, escalate to dealbreaker
    nonstandard_count = sum(1 for c in evaluated if c["fairness"] == "non-standard")
    if nonstandard_count / len(evaluated) >= ESCALATION_THRESHOLD:
        worst = max(worst, FAIRNESS_RANK["dealbreaker"])

    return RANK_TO_FAIRNESS[worst]


def synthesize(
    agreement_type: str,
    clause_results: list[dict],
    headline: HeadlineResult,
) -> dict:
    """Assemble the final result dict from clause evaluations and headline."""
    return {
        "overall_fairness": compute_overall_fairness(clause_results),
        "agreement_type": agreement_type,
        "summary": headline.summary,
        "call_to_action": headline.call_to_action,
        "clauses": clause_results,
    }

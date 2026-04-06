"""Clause evaluator agent: evaluates a single clause against playbook checks."""

import json
from dataclasses import dataclass

from services.agents.base import AgentConfig, AgentRunner
from services.playbook import get_playbook

GET_PLAYBOOK_TOOL = {
    "name": "get_playbook",
    "description": "Retrieve playbook checks for the given agreement type and check names.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "agreement_type": {
                "type": "string",
                "description": "The agreement type to look up checks for.",
            },
            "check_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of playbook check names to retrieve.",
            },
        },
        "required": ["agreement_type", "check_names"],
        "additionalProperties": False,
    },
}

REPORT_EVALUATION_TOOL = {
    "name": "report_evaluation",
    "description": "Report the evaluation of a single contract clause.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "section_number": {
                "type": "string",
                "description": "Section number of the clause.",
            },
            "clause_type": {
                "type": "string",
                "description": "Type of the clause (e.g. Limitation of Liability).",
            },
            "severity": {
                "type": "integer",
                "description": "Severity score from 1 (minor) to 10 (critical).",
            },
            "playbook_status": {
                "type": ["string", "null"],
                "enum": ["TRIGGERED", "PASS", "ABSENT", "PARTIAL", None],
                "description": "Playbook check status, or null if no playbook grounding.",
            },
            "playbook_position": {
                "type": ["string", "null"],
                "description": "The playbook's recommended position, or null.",
            },
            "contract_language": {
                "type": ["string", "null"],
                "description": "Relevant contract language, or null.",
            },
            "finding": {
                "type": "string",
                "description": "Key finding from the evaluation.",
            },
            "recommended_redline": {
                "type": ["string", "null"],
                "description": "Suggested contract modification, or null.",
            },
            "fairness": {
                "type": "string",
                "enum": ["fair", "non-standard", "dealbreaker"],
                "description": "User-facing fairness tier.",
            },
            "purpose": {
                "type": "string",
                "description": "What this clause is meant to accomplish.",
            },
            "market_standard": {
                "type": "string",
                "description": "What is typical in the market for this clause.",
            },
            "explanation": {
                "type": "string",
                "description": "Detailed explanation of the evaluation.",
            },
        },
        "required": [
            "section_number",
            "clause_type",
            "severity",
            "playbook_status",
            "playbook_position",
            "contract_language",
            "finding",
            "recommended_redline",
            "fairness",
            "purpose",
            "market_standard",
            "explanation",
        ],
        "additionalProperties": False,
    },
}


def build_evaluator_prompt(instructions: str | None = None) -> str:
    """Build the system prompt for the clause evaluator agent."""
    prompt = (
        "You are a contract clause evaluator. You will receive a single clause from a contract "
        "along with its section number, clause type, and any cross-referenced clause text.\n\n"
        "Your job is to:\n"
        "1. Call the get_playbook tool to retrieve the relevant playbook checks for this clause.\n"
        "2. Evaluate the clause against the playbook checks.\n"
        "3. Call the report_evaluation tool with your assessment, including both the playbook "
        "status (TRIGGERED/PASS/ABSENT/PARTIAL) and the user-facing fairness tier "
        "(fair/non-standard/dealbreaker), plus a severity score from 1-10.\n\n"
        "Evaluate carefully and ground your assessment in the playbook checks retrieved."
    )
    if instructions:
        prompt += (
            f'\n\nAdditional instructions from the user:\n"{instructions}"\n'
            "(Source: user-provided review instructions)\n"
            "These instructions may not be relevant for this clause; if irrelevant, ignore."
        )
    return prompt


async def handle_get_playbook(input_data: dict) -> dict:
    """Tool handler for get_playbook: calls playbook parser lookup."""
    try:
        checks = get_playbook(input_data["agreement_type"], input_data["check_names"])
        return {
            "checks": [
                {
                    "number": c.number,
                    "name": c.name,
                    "importance": c.importance,
                    "description": c.description,
                }
                for c in checks
            ]
        }
    except (KeyError, ValueError) as e:
        return {"error": str(e)}


@dataclass
class EvaluatorResult:
    section_number: str
    clause_type: str
    severity: int
    playbook_status: str | None
    playbook_position: str | None
    contract_language: str | None
    finding: str
    recommended_redline: str | None
    fairness: str
    purpose: str
    market_standard: str
    explanation: str


class EvaluatorAgent:
    def __init__(
        self,
        agreement_type: str,
        instructions: str | None = None,
    ):
        self.agreement_type = agreement_type
        self.instructions = instructions
        self.config = AgentConfig("evaluator")

    async def run(
        self,
        clause: dict,
        cross_ref_text: dict[str, str] | None = None,
    ) -> EvaluatorResult:
        system = build_evaluator_prompt(self.instructions)

        # Build user message with clause data
        msg_parts = [
            f"Section: {clause['section_number']}",
            f"Clause type: {clause['clause_type']}",
            f"Agreement type: {self.agreement_type}",
            f"Relevant checks: {json.dumps(clause.get('relevant_checks', []))}",
            f"\nClause text:\n{clause['text']}",
        ]

        # Add cross-reference text if provided
        if cross_ref_text:
            msg_parts.append("\nCross-referenced clauses:")
            for ref_section, ref_text in cross_ref_text.items():
                msg_parts.append(f"  Section {ref_section}: {ref_text}")

        # Note unresolvable references
        refs = clause.get("cross_references", [])
        if refs and cross_ref_text:
            missing = [r for r in refs if r not in cross_ref_text]
            if missing:
                msg_parts.append(
                    f"\nNote: Referenced section(s) {', '.join(missing)} not found in contract."
                )

        user_message = "\n".join(msg_parts)

        runner = AgentRunner(
            config=self.config,
            tools=[GET_PLAYBOOK_TOOL, REPORT_EVALUATION_TOOL],
            tool_handlers={
                "get_playbook": handle_get_playbook,
                "report_evaluation": self._handle_report_evaluation,
            },
        )

        result = await runner.run(
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )

        tool_input = result.tool_results.get("report_evaluation", {})
        return EvaluatorResult(
            section_number=tool_input.get("section_number", ""),
            clause_type=tool_input.get("clause_type", ""),
            severity=tool_input.get("severity", 0),
            playbook_status=tool_input.get("playbook_status"),
            playbook_position=tool_input.get("playbook_position"),
            contract_language=tool_input.get("contract_language"),
            finding=tool_input.get("finding", ""),
            recommended_redline=tool_input.get("recommended_redline"),
            fairness=tool_input.get("fairness", ""),
            purpose=tool_input.get("purpose", ""),
            market_standard=tool_input.get("market_standard", ""),
            explanation=tool_input.get("explanation", ""),
        )

    async def _handle_report_evaluation(self, input_data: dict) -> str:
        return "Evaluation recorded."

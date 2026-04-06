"""Headline generator agent: executive summary and call-to-action from clause evaluations."""

import json
from dataclasses import dataclass

from services.agents.base import AgentConfig, AgentRunner

HEADLINE_TOOL = {
    "name": "report_headline",
    "description": "Produce an executive summary and prioritized action items.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Concise executive summary"},
            "call_to_action": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Prioritized next steps",
            },
        },
        "required": ["summary", "call_to_action"],
        "additionalProperties": False,
    },
}


def build_headline_prompt(instructions: str | None = None) -> str:
    """Build the system prompt for the headline agent."""
    prompt = (
        "You are a contract evaluation summarizer. You will receive clause evaluation data "
        "from a contract review. Your job is to produce a concise executive summary and "
        "prioritized action items based on the evaluation results.\n\n"
        "Analyze all clause evaluations provided and:\n"
        "1. Write a clear, concise executive summary highlighting the key findings.\n"
        "2. Produce a prioritized list of specific next steps the user should take.\n\n"
        "Focus on the most significant issues first (dealbreaker > non-standard > fair).\n"
        "Use the report_headline tool to submit your results."
    )
    if instructions:
        prompt += (
            f'\n\nAdditional instructions from the user:\n"{instructions}"\n'
            "(Source: user-provided review instructions)"
        )
    return prompt


@dataclass
class HeadlineResult:
    summary: str
    call_to_action: list[str]


class HeadlineAgent:
    def __init__(self, instructions: str | None = None):
        self.config = AgentConfig("headline")
        self.instructions = instructions

    async def run(
        self,
        agreement_type: str,
        clauses: list[dict],
        failed_clause_count: int,
        absent_clause_count: int,
    ) -> HeadlineResult:
        system = build_headline_prompt(self.instructions)

        user_message = json.dumps(
            {
                "agreement_type": agreement_type,
                "clauses": clauses,
                "failed_clause_count": failed_clause_count,
                "absent_clause_count": absent_clause_count,
            },
            indent=2,
        )

        async def handle_report_headline(input_data: dict) -> str:
            return "Headline recorded."

        runner = AgentRunner(
            config=self.config,
            tools=[HEADLINE_TOOL],
            tool_handlers={"report_headline": handle_report_headline},
        )

        result = await runner.run(
            system=system,
            messages=[{"role": "user", "content": user_message}],
            force_tool="report_headline",
        )

        tool_input = result.tool_results.get("report_headline", {})
        return HeadlineResult(
            summary=tool_input.get("summary", ""),
            call_to_action=tool_input.get("call_to_action", []),
        )

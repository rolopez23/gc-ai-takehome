"""Clause splitter agent: reads contract, determines agreement type, splits into clauses."""

import base64
import logging
from dataclasses import dataclass

from services.agents.base import AgentConfig, AgentRunner
from services.playbook import (
    _cached_playbook,
    get_all_check_names,
    get_check_names_with_descriptions,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

SPLITTER_TOOL = {
    "name": "report_clauses",
    "description": "Report the agreement type and all clauses found in the contract.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "agreement_type": {
                "type": "string",
                "enum": ["SaaS MSA", "NDA", "Commercial MSA", "DPA", "General"],
            },
            "clauses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "section_number": {"type": "string"},
                        "clause_type": {"type": "string"},
                        "text": {"type": "string"},
                        "relevant_checks": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "cross_references": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "is_cycle": {"type": "boolean"},
                    },
                    "required": [
                        "section_number",
                        "clause_type",
                        "text",
                        "relevant_checks",
                        "cross_references",
                        "is_cycle",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["agreement_type", "clauses"],
        "additionalProperties": False,
    },
}

# ---------------------------------------------------------------------------
# Agreement type to playbook name mapping
# ---------------------------------------------------------------------------

AGREEMENT_TYPE_TO_PLAYBOOK = {
    "SaaS MSA": "SaaS Master Service Agreement",
    "NDA": "Mutual Non-Disclosure Agreement",
    "Commercial MSA": "Commercial Master Services Agreement \u2014 Non-SaaS",
    "DPA": "Data Processing Agreement",
}

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def build_splitter_prompt(instructions: str | None) -> str:
    """Build the system prompt for the clause splitter agent.

    Includes the full playbook check name enum with one-sentence descriptions
    for all 4 agreement types, plus user instructions if provided.
    """
    check_sections = []
    for short_name, playbook_name in AGREEMENT_TYPE_TO_PLAYBOOK.items():
        try:
            descriptions = get_check_names_with_descriptions(playbook_name)
            checks = [f"  - {d}" for d in descriptions]
            check_sections.append(f"### {short_name}\n" + "\n".join(checks))
        except KeyError:
            pass

    check_enum_text = "\n\n".join(check_sections)

    instructions_block = ""
    if instructions:
        instructions_block = (
            f"\n\n## User Instructions\n"
            f"The user who uploaded this contract provided the following instructions. "
            f"Source: user-provided review instructions.\n\n"
            f"{instructions}\n\n"
            f"These instructions may provide context for how to split or tag clauses. "
            f"If they are not relevant to splitting, ignore them."
        )

    return f"""You are a contract clause splitter. Your job is to:

1. Read the contract document carefully.
2. Determine the agreement type (one of: SaaS MSA, NDA, Commercial MSA, DPA, General).
3. Split the contract into individual clauses.
4. Tag each clause with relevant playbook check names from the enum below.
5. Detect cross-references between sections and flag cycles.
6. Generate synthetic section numbers (clause-1, clause-2, ...) for unnumbered contracts.

## Playbook Check Names

You MUST only use check names from this list when tagging clauses. Each clause should be
tagged with the check names that are relevant to evaluating that clause. Use check names
from the detected agreement type only. If the agreement type is "General", leave
relevant_checks as an empty list for all clauses.

{check_enum_text}

## Cross-References

For each clause, identify any references to other sections (e.g., "as defined in Section 3.1",
"subject to the terms in Section 8"). List the referenced section numbers in cross_references.
If a clause is part of a circular reference chain, set is_cycle to true.

## Section Numbering

If the contract has section numbers (e.g., "4.2", "Section 8"), use them as-is.
If the contract lacks numbering, assign synthetic sequential identifiers: clause-1, clause-2, etc.

## Output

Call the report_clauses tool with the agreement type and all clauses found.{instructions_block}"""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SplitterClause:
    section_number: str
    clause_type: str
    text: str
    relevant_checks: list[str]
    cross_references: list[str]
    is_cycle: bool


@dataclass
class SplitterResult:
    agreement_type: str
    clauses: list[SplitterClause]


# ---------------------------------------------------------------------------
# Absent check detection
# ---------------------------------------------------------------------------

ABSENT_IMPORTANCE_MAP = {
    "High": {"severity": 8, "fairness": "dealbreaker"},
    "Medium": {"severity": 5, "fairness": "non-standard"},
    "Low": {"severity": 2, "fairness": "fair"},
}


@dataclass
class AbsentClause:
    section_number: str
    clause_type: str
    text: str
    relevant_checks: list[str]
    cross_references: list[str]
    is_cycle: bool
    is_synthetic: bool
    severity: int
    fairness: str


def detect_absent_checks(
    agreement_type: str,
    tagged_checks: set[str],
) -> list[AbsentClause]:
    """Detect playbook checks not covered by any clause and return synthetic ABSENT clauses.

    This is deterministic -- no LLM call. Returns empty list for "General" agreement type.
    """
    if agreement_type == "General":
        return []

    playbook_name = AGREEMENT_TYPE_TO_PLAYBOOK.get(agreement_type)
    if not playbook_name:
        return []

    playbook = _cached_playbook()
    all_checks_list = playbook.get(playbook_name, [])

    # Build ordered list of uncovered checks (preserve playbook order for determinism)
    uncovered = [c for c in all_checks_list if c.name not in tagged_checks]

    result = []
    for i, check in enumerate(uncovered, start=1):
        rating = ABSENT_IMPORTANCE_MAP.get(
            check.importance, {"severity": 5, "fairness": "non-standard"}
        )
        result.append(
            AbsentClause(
                section_number=f"absent-{i}",
                clause_type=check.name,
                text="",
                relevant_checks=[check.name],
                cross_references=[],
                is_cycle=False,
                is_synthetic=True,
                severity=rating["severity"],
                fairness=rating["fairness"],
            )
        )

    return result


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------


class SplitterAgent:
    """Agent that splits a contract into clauses using the Anthropic API."""

    def __init__(self):
        config = AgentConfig("splitter")
        self.runner = AgentRunner(
            config=config,
            tools=[SPLITTER_TOOL],
            tool_handlers={"report_clauses": self._handle_report_clauses},
        )
        self._last_tool_input: dict | None = None

    async def _handle_report_clauses(self, input_dict: dict) -> str:
        """Store the tool input for later extraction."""
        self._last_tool_input = input_dict
        return "Clauses received."

    async def run(
        self,
        pdf_blob: bytes | None = None,
        text: str | None = None,
        instructions: str | None = None,
    ) -> SplitterResult:
        """Run the splitter agent on a contract document."""
        system = build_splitter_prompt(instructions)

        # Build the user message content
        content: list[dict] = []
        if pdf_blob:
            content.append(
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.standard_b64encode(pdf_blob).decode(),
                    },
                }
            )
        if text:
            content.append({"type": "text", "text": text})

        if not content:
            raise ValueError("Either pdf_blob or text must be provided")

        messages = [{"role": "user", "content": content}]

        await self.runner.run(
            system=system,
            messages=messages,
            force_tool="report_clauses",
        )

        if not self._last_tool_input:
            raise RuntimeError("Splitter did not produce report_clauses tool output")

        tool_data = self._last_tool_input
        clauses = [
            SplitterClause(
                section_number=c["section_number"],
                clause_type=c["clause_type"],
                text=c["text"],
                relevant_checks=c["relevant_checks"],
                cross_references=c["cross_references"],
                is_cycle=c["is_cycle"],
            )
            for c in tool_data["clauses"]
        ]

        return SplitterResult(
            agreement_type=tool_data["agreement_type"],
            clauses=clauses,
        )

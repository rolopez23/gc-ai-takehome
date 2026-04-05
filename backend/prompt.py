import json
from typing import Literal

from pydantic import BaseModel


class EvalClauseResponse(BaseModel):
    section_number: str
    clause_type: str
    purpose: str
    fairness: Literal["fair", "non-standard", "dealbreaker"]
    market_standard: str
    explanation: str


class EvalSuccessResponse(BaseModel):
    error: None
    overall_fairness: Literal["fair", "non-standard", "dealbreaker"]
    summary: str
    call_to_action: list[str]
    clauses: list[EvalClauseResponse]


class EvalErrorResponse(BaseModel):
    error: Literal[True]
    reason: str


def build_system_prompt(instructions: str | None = None) -> str:
    success_schema = json.dumps(EvalSuccessResponse.model_json_schema(), indent=2)
    error_schema = json.dumps(EvalErrorResponse.model_json_schema(), indent=2)

    prompt = f"""You are a senior in-house commercial lawyer reviewing a vendor contract on behalf of the customer. Your job is to evaluate the contract against market standards and flag every clause that deviates.

## Step 1: Determine if this is a contract

Before analyzing, determine if the input text is a contract or legal agreement. If it is clearly not a contract (e.g., a recipe, article, resume, code, or other non-legal document), return the error JSON schema below instead of the success schema.

When in doubt, treat the input as a contract and proceed with analysis. Bias toward accepting borderline input.

## Step 2: Analyze each clause

For each material clause in the contract, produce an analysis object. Write the "purpose" field in plain English from the customer's perspective — describe what the clause means for the customer, not what it legally governs. For example, write "Determines whether you can get your data back after termination" instead of "Governs vendor data handling obligations."

## Step 3: Assign fairness tiers

For each clause, assign one of three fairness tiers:

- **fair**: Market standard or better for this type of agreement. No action needed.
- **non-standard**: Deviates from market standard in a way that disadvantages the customer, but is not a showstopper on its own. Worth negotiating. Examples: shorter-than-typical notice periods, above-market late fees, narrow warranty scope.
- **dealbreaker**: A clause that creates unacceptable risk or fundamentally shifts the balance of power. Do not sign without resolving. Examples: vendor can unilaterally amend terms, no IP indemnification, liability cap under 6 months of fees, no data export on termination, linking to external terms that can change without consent. A non-standard clause can also be a dealbreaker if it heightens structural risk — e.g., incorporating terms by URL reference even if the referenced terms are currently fair.

## Step 4: Compute the topline

The overall_fairness is determined by the worst clause. One dealbreaker clause makes the entire contract a dealbreaker. Never average across clauses.

Death by paper cuts: if more than 30% of material clauses are non-standard, escalate the overall rating to dealbreaker even if no single clause qualifies on its own — the cumulative risk is too high.

Write a summary sentence describing the clause breakdown (e.g., "1 dealbreaker, 2 negotiating points, 4 acceptable clauses.").

Write a call_to_action array with prioritized, opinionated recommendations. Lead with dealbreakers, then negotiating points, then acceptable items. Each entry should reference the section number and clause type.

## Output format

Return only valid JSON matching one of the two schemas below. No text, no markdown fences — just the raw JSON object.

### Success schema
{success_schema}

### Error schema (non-contract input)
{error_schema}"""

    if instructions is not None:
        prompt += f"\n\n## Additional instructions from reviewer\n{instructions}"

    return prompt

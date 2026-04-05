# Step: system-prompt

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

The system prompt ported from TypeScript (`frontend/prompt/system-prompt.ts`) to Python
(`backend/prompt.py`). JSON schema is generated from Pydantic models via `model_json_schema()`
instead of Zod's `toJSONSchema()`. The prompt includes an injection point for optional
`review_instructions`. After this step, the evaluation service has a ready-to-use prompt builder.

## Done When

- `backend/prompt.py` exports a `build_system_prompt(instructions: str | None) -> str` function
- The generated prompt contains the same analysis rules as the TypeScript version
- JSON schemas in the prompt match the Pydantic `EvalSuccessResponse` and `EvalErrorResponse` models
- When `instructions` is provided, they are appended to the prompt
- When `instructions` is None, the prompt is identical to the base version

## Cycles

### eval-response-pydantic-models

**Test** — write these tests and confirm they fail:
- **test_eval_success_schema_has_required_fields**: Call `EvalSuccessResponse.model_json_schema()`. Assert it contains `overall_fairness`, `summary`, `call_to_action`, `clauses`, and `error` (literal null).
- **test_eval_error_schema_has_required_fields**: Call `EvalErrorResponse.model_json_schema()`. Assert it contains `error` (literal true) and `reason`.
- **test_eval_clause_schema_fields**: Call `EvalClauseResponse.model_json_schema()`. Assert it contains `section_number`, `clause_type`, `purpose`, `fairness`, `market_standard`, `explanation`.

**Code** — Create Pydantic models in `backend/prompt.py` (or a separate `backend/eval_schemas.py` if cleaner) that mirror the LLM output shape:
- `EvalClauseResponse`: `section_number: str`, `clause_type: str`, `purpose: str`, `fairness: Literal["fair", "non-standard", "dealbreaker"]`, `market_standard: str`, `explanation: str`
- `EvalSuccessResponse`: `error: None`, `overall_fairness: Literal["fair", "non-standard", "dealbreaker"]`, `summary: str`, `call_to_action: list[str]`, `clauses: list[EvalClauseResponse]`
- `EvalErrorResponse`: `error: Literal[True]`, `reason: str`

**Refactor** — none

**Commit**: `Add Pydantic models for LLM response schema generation`

---

### build-system-prompt

**Test** — write these tests and confirm they fail:
- **test_prompt_contains_analysis_rules**: Call `build_system_prompt(None)`. Assert the prompt contains key phrases: "senior in-house commercial lawyer", "fairness tiers", "dealbreaker", "non-standard", "fair", "death by paper cuts", "30%".
- **test_prompt_contains_json_schemas**: Call `build_system_prompt(None)`. Assert prompt contains `"overall_fairness"` and `"reason"` (from the JSON schemas).
- **test_prompt_without_instructions**: Call `build_system_prompt(None)`. Assert prompt does NOT contain "Additional instructions".
- **test_prompt_with_instructions**: Call `build_system_prompt("Focus on IP clauses")`. Assert prompt contains "Additional instructions" and "Focus on IP clauses".

**Code** — Implement `build_system_prompt(instructions: str | None) -> str` in `backend/prompt.py`. Port the full prompt text from the TypeScript version. Replace `z.toJSONSchema()` calls with `EvalSuccessResponse.model_json_schema()` and `EvalErrorResponse.model_json_schema()`. If `instructions` is provided, append a section: `\n\n## Additional instructions from reviewer\n{instructions}`.

**Refactor** — none

**Commit**: `Port system prompt to Python with Pydantic schema generation`

---

## Verification

```python
# Run in Python REPL from backend/:
from prompt import build_system_prompt

# Without instructions:
prompt = build_system_prompt(None)
assert "senior in-house commercial lawyer" in prompt
assert "fairness tiers" in prompt
assert "death by paper cuts" in prompt
assert "overall_fairness" in prompt  # from JSON schema
assert "Additional instructions" not in prompt
print("Base prompt: OK")
print(f"Length: {len(prompt)} chars")

# With instructions:
prompt_with = build_system_prompt("Focus on IP clauses")
assert "Additional instructions" in prompt_with
assert "Focus on IP clauses" in prompt_with
print("Instructions injection: OK")

# Verify JSON schemas are present and valid JSON:
import json
# Find the schema blocks in the prompt and verify they're parseable
idx = prompt.index('"overall_fairness"')
print(f"JSON schema contains overall_fairness at char {idx}: OK")
```

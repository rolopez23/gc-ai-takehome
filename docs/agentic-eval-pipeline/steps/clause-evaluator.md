# Step: clause-evaluator

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)
>
> Depends on: agent-core, playbook-parser

## What This Step Delivers

An agent that evaluates a single clause against playbook checks. The evaluator uses two tools:
`get_playbook` (to retrieve relevant checks) and `report_evaluation` (to return the dual-tier
rating). Receives depth-1 cross-referenced clause text when available. Flags unresolvable
references as findings.

## Done When

- `EvaluatorAgent.run(clause, cross_ref_text)` executes the get_playbook → report_evaluation
  tool sequence with mocked LLM responses
- The `get_playbook` tool handler calls the real playbook parser lookup
- The `report_evaluation` tool returns structured output with both rating schemes + severity
- User instructions are included with relevance guardrail

## Cycles

### evaluator-tool-definitions

**Test** — write these tests and confirm they fail:
- **test_evaluator_tools_count**: evaluator has 2 tools: `get_playbook` and `report_evaluation`
- **test_get_playbook_tool_schema**: `GET_PLAYBOOK_TOOL` has correct input_schema
  (agreement_type, check_names)
- **test_report_evaluation_tool_schema**: `REPORT_EVALUATION_TOOL` has correct input_schema
  with all fields (severity, playbook_status, fairness, purpose, etc.)
- **test_evaluator_prompt_includes_guardrail**: prompt contains "instructions may not be
  relevant for this clause"

**Code** — create `backend/services/agents/evaluator.py` with tool definitions and prompt builder.
Both tools use `"strict": True` and `"additionalProperties": False` for guaranteed schema
adherence. The evaluator uses `tool_choice: "auto"` (not forced) since it needs to call
`get_playbook` first, then `report_evaluation`. The agent runner's tool loop handles the
multi-tool sequence naturally.

**Refactor** — none

**Commit**: `add evaluator tool definitions and prompt with instruction guardrail`

---

### get-playbook-tool-handler

**Test** — write these tests and confirm they fail:
- **test_playbook_handler_returns_checks**: handler called with
  `{"agreement_type": "SaaS MSA", "check_names": ["Payment Terms"]}` returns a dict with
  `checks` list containing the matching check
- **test_playbook_handler_error_on_zero_match**: handler called with unknown check name
  returns an error result (not an exception — tool results should be JSON-serializable)

**Code** — implement the `get_playbook` tool handler that calls `playbook.get_playbook()`:

```python
def handle_get_playbook(input: dict) -> dict:
    try:
        checks = get_playbook(input["agreement_type"], input["check_names"])
        return {"checks": [asdict(c) for c in checks]}
    except PlaybookLookupError as e:
        return {"error": str(e)}
```

**Refactor** — none

**Commit**: `add get_playbook tool handler backed by playbook parser`

---

### evaluator-agent-class

**Test** — write these tests and confirm they fail:
- **test_evaluator_runs_tool_sequence**: mock AgentRunner to first call `get_playbook`, receive
  checks, then call `report_evaluation`. Assert `EvaluatorResult` has all fields.
- **test_evaluator_result_has_dual_tier**: result has both `playbook_status` and `fairness`
- **test_evaluator_result_has_severity**: result has `severity` (1-10)
- **test_evaluator_receives_cross_ref_text**: when cross-reference text is provided, it appears
  in the user message sent to the agent

**Code** — add `EvaluatorAgent` class:

```python
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
    def __init__(self, agreement_type: str, instructions: str | None = None):
        self.agreement_type = agreement_type
        self.instructions = instructions

    async def run(
        self,
        clause: SplitterClause,
        cross_ref_text: dict[str, str] | None = None,
    ) -> EvaluatorResult:
        ...
```

The user message includes the clause text, section number, clause type, and any depth-1
cross-referenced clause text. If cross-references point to sections not found in the clause
list, the message notes "Referenced section X.Y not found in contract."

**Refactor** — none

**Commit**: `add EvaluatorAgent with get_playbook → report_evaluation tool sequence`

---

## Verification

```bash
cd backend && uv run pytest tests/test_evaluator.py -v
```

Expected: all tests pass. The evaluator correctly executes the two-tool sequence and returns
structured results with both rating schemes.

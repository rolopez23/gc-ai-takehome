# Step: headline-synthesis

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)
>
> Depends on: agent-core

## What This Step Delivers

Two components: (1) the headline generator agent that produces summary + call_to_action from
clause evaluation results, and (2) the deterministic synthesis function that computes
`overall_fairness` and assembles the final result.

## Done When

- `HeadlineAgent.run(clause_results, metadata)` returns `HeadlineResult` with summary and
  call_to_action via tool call
- `synthesize()` computes `overall_fairness` using worst-clause-wins + 20% escalation
- `synthesize()` excludes errored clauses from computation
- `synthesize()` assembles the complete result object

## Cycles

### headline-tool-and-prompt

**Test** — write these tests and confirm they fail:
- **test_headline_tool_schema**: `HEADLINE_TOOL` has name "report_headline" with summary
  (string) and call_to_action (array of strings)
- **test_headline_prompt_includes_context**: prompt references that it will receive clause
  evaluation data
- **test_headline_prompt_includes_instructions**: when instructions provided, they appear
  in the prompt with source attribution

**Code** — create `backend/services/agents/headline.py`:

```python
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

# Agent calls with force_tool="report_headline" to guarantee the tool is called
```

**Refactor** — none

**Commit**: `add headline tool definition and prompt`

---

### headline-agent-class

**Test** — write these tests and confirm they fail:
- **test_headline_returns_summary**: mock AgentRunner to return `report_headline` with
  summary text. Assert `HeadlineResult.summary` matches.
- **test_headline_returns_call_to_action**: assert `HeadlineResult.call_to_action` is a list
  of strings
- **test_headline_input_includes_clauses**: the user message sent to the agent includes
  the clause evaluation data
- **test_headline_input_includes_metadata**: user message includes agreement_type,
  failed_clause_count, absent_clause_count

**Code** — add `HeadlineAgent` class:

```python
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
        clauses: list[EvaluatorResult],
        failed_clause_count: int,
        absent_clause_count: int,
    ) -> HeadlineResult:
        # Build user message with full clause data as JSON
        ...
```

**Refactor** — none

**Commit**: `add HeadlineAgent with structured input and tool-call output`

---

### synthesis-worst-clause-wins

**Test** — write these tests and confirm they fail:
- **test_synthesis_all_fair**: all clauses `fairness="fair"` → `overall_fairness="fair"`
- **test_synthesis_one_dealbreaker**: one dealbreaker clause → `overall_fairness="dealbreaker"`
- **test_synthesis_one_nonstandard**: one non-standard, rest fair →
  `overall_fairness="non-standard"`
- **test_synthesis_worst_wins**: mix of fair and non-standard → `overall_fairness="non-standard"`

**Code** — create `backend/services/synthesis.py`:

```python
FAIRNESS_RANK = {"fair": 0, "non-standard": 1, "dealbreaker": 2}
RANK_TO_FAIRNESS = {v: k for k, v in FAIRNESS_RANK.items()}

def compute_overall_fairness(clauses: list[dict]) -> str:
    worst = max(FAIRNESS_RANK[c["fairness"]] for c in clauses)
    return RANK_TO_FAIRNESS[worst]
```

**Refactor** — none

**Commit**: `add worst-clause-wins overall fairness computation`

---

### synthesis-escalation-rule

**Test** — write these tests and confirm they fail:
- **test_escalation_20_percent**: 2 of 10 clauses non-standard (20%) →
  `overall_fairness="dealbreaker"`
- **test_no_escalation_below_threshold**: 1 of 10 clauses non-standard (10%) →
  `overall_fairness="non-standard"` (no escalation)
- **test_escalation_threshold_configurable**: with `ESCALATION_THRESHOLD=0.3`, 2 of 10
  non-standard does not escalate

**Code** — add escalation logic:

```python
ESCALATION_THRESHOLD = float(os.getenv("ESCALATION_THRESHOLD", "0.2"))

def compute_overall_fairness(clauses: list[dict]) -> str:
    worst = max(FAIRNESS_RANK[c["fairness"]] for c in clauses)
    # Escalation: if >20% non-standard, escalate to dealbreaker
    nonstandard_count = sum(1 for c in clauses if c["fairness"] == "non-standard")
    if len(clauses) > 0 and nonstandard_count / len(clauses) >= ESCALATION_THRESHOLD:
        worst = max(worst, FAIRNESS_RANK["dealbreaker"])
    return RANK_TO_FAIRNESS[worst]
```

**Refactor** — none

**Commit**: `add 20% escalation rule to overall fairness computation`

---

### synthesis-excludes-errored

**Test** — write these tests and confirm they fail:
- **test_synthesis_excludes_errored_clauses**: 2 clauses with `status="error"`, 8 with
  `status="evaluated"`. Errored clauses are excluded from fairness computation.
- **test_synthesis_assembles_full_result**: `synthesize()` returns a dict with
  `overall_fairness`, `agreement_type`, `summary`, `call_to_action`, `clauses`

**Code** — add `synthesize()` function:

```python
def synthesize(
    agreement_type: str,
    clause_results: list[dict],
    headline: HeadlineResult,
) -> dict:
    evaluated = [c for c in clause_results if c.get("status") != "error"]
    return {
        "overall_fairness": compute_overall_fairness(evaluated),
        "agreement_type": agreement_type,
        "summary": headline.summary,
        "call_to_action": headline.call_to_action,
        "clauses": clause_results,  # include all, even errored
    }
```

**Refactor** — none

**Commit**: `add synthesize function that excludes errored clauses from fairness`

---

## Verification

```bash
cd backend && uv run pytest tests/test_headline.py tests/test_synthesis.py -v
```

Expected: all tests pass. Synthesis correctly computes overall_fairness with worst-clause-wins,
20% escalation, and errored clause exclusion.

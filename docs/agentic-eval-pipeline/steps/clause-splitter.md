# Step: clause-splitter

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)
>
> Depends on: agent-core, playbook-parser

## What This Step Delivers

An agent that reads the full contract, determines the agreement type, and splits it into
individual clauses. Each clause is tagged with relevant playbook check names (from the known
enum), cross-references, and cycle flags. Handles both PDF and plain text input. Generates
synthetic section numbers for unnumbered contracts.

After the LLM returns, the orchestrator (deterministic code) detects uncovered playbook checks
and generates synthetic ABSENT clauses. This step includes that logic.

## Done When

- `SplitterAgent.run(document)` returns `SplitterResult` with agreement_type and clauses
- Each clause has section_number, clause_type, text, relevant_checks, cross_references, is_cycle
- The splitter prompt includes the full playbook check enum with descriptions
- `detect_absent_checks()` returns synthetic clauses for uncovered checks
- User instructions are included in the system prompt

## Cycles

### splitter-tool-definition

**Test** — write these tests and confirm they fail:
- **test_splitter_tool_schema**: `SPLITTER_TOOL` has name "report_clauses" with correct
  input_schema (agreement_type, clauses array with all fields)
- **test_splitter_prompt_contains_check_enum**: `build_splitter_prompt("SaaS MSA check enum...")`
  contains the check names

**Code** — create `backend/services/agents/splitter.py`:

```python
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
                        "relevant_checks": {"type": "array", "items": {"type": "string"}},
                        "cross_references": {"type": "array", "items": {"type": "string"}},
                        "is_cycle": {"type": "boolean"},
                    },
                    "required": ["section_number", "clause_type", "text", "relevant_checks",
                                 "cross_references", "is_cycle"],
                },
            },
        },
        "required": ["agreement_type", "clauses"],
        "additionalProperties": False,
    },
}

# Agent calls with force_tool="report_clauses" to guarantee the tool is called
```

Build the system prompt dynamically using `get_check_names_with_descriptions()` from the
playbook parser.

**Refactor** — none

**Commit**: `add splitter tool definition and prompt with check enum`

---

### splitter-agent-class

**Test** — write these tests and confirm they fail:
- **test_splitter_returns_agreement_type**: mock AgentRunner to return `report_clauses` tool
  result with `agreement_type="SaaS MSA"`. Assert `SplitterResult.agreement_type == "SaaS MSA"`.
- **test_splitter_returns_clauses**: mock response with 3 clauses. Assert
  `len(result.clauses) == 3` and each has all required fields.
- **test_splitter_clause_shape**: each clause in result has `section_number`, `clause_type`,
  `text`, `relevant_checks`, `cross_references`, `is_cycle`.
- **test_splitter_uses_correct_config**: `SplitterAgent` uses `AgentConfig("splitter")`
  (32768 max tokens).

**Code** — add `SplitterAgent` class:

```python
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

class SplitterAgent:
    async def run(self, pdf_blob=None, text=None, instructions=None) -> SplitterResult:
        ...
```

**Refactor** — none

**Commit**: `add SplitterAgent with structured clause output`

---

### absent-check-detection

**Test** — write these tests and confirm they fail:
- **test_detect_absent_checks_finds_uncovered**: given agreement_type="SaaS MSA" and clauses
  that tag 15 of 21 checks, `detect_absent_checks()` returns 6 synthetic clauses
- **test_absent_clause_shape**: each synthetic clause has `is_synthetic=True`, empty `text`,
  `relevant_checks` with the uncovered check name, `clause_type` matching the check name
- **test_absent_clause_deterministic_rating**: a High-importance absent check gets
  `severity=8, fairness="dealbreaker"`. Medium gets `severity=5, fairness="non-standard"`.
  Low gets `severity=2, fairness="fair"`.
- **test_absent_detection_general_returns_empty**: agreement_type="General" returns no
  absent clauses
- **test_absent_clause_section_numbering**: synthetic clauses get sequential section numbers
  starting after the last real clause (e.g., "absent-1", "absent-2")

**Code** — add `detect_absent_checks()` function:

```python
ABSENT_IMPORTANCE_MAP = {
    "High": {"severity": 8, "fairness": "dealbreaker"},
    "Medium": {"severity": 5, "fairness": "non-standard"},
    "Low": {"severity": 2, "fairness": "fair"},
}

def detect_absent_checks(
    agreement_type: str,
    tagged_checks: set[str],
) -> list[AbsentClause]:
    if agreement_type == "General":
        return []
    all_checks = get_all_check_names(agreement_type)
    uncovered = all_checks - tagged_checks
    # Build synthetic clauses with deterministic ratings
    ...
```

**Refactor** — none

**Commit**: `add deterministic absent check detection`

---

## Verification

```bash
cd backend && uv run pytest tests/test_splitter.py -v
```

Expected: all tests pass. The splitter produces structured clause output with check tags,
and absent check detection finds uncovered checks with correct deterministic ratings.

# Step: contract-verifier

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

A lightweight agent that confirms the uploaded document is a contract. Uses a cheap model with
1024 max tokens. Returns `{is_contract: bool, reason: str | null}` via the `verify_contract`
tool call. This gates the pipeline — non-contracts are rejected before spending tokens on splitting.

## Done When

- `VerifierAgent.run(document)` returns `VerifierResult(is_contract=True)` for contracts
- `VerifierAgent.run(document)` returns `VerifierResult(is_contract=False, reason="...")` for non-contracts
- The agent uses the `verify_contract` tool definition
- User instructions are included in the system prompt when provided

## Cycles

### verifier-tool-definition

**Test** — write these tests and confirm they fail:
- **test_verifier_tool_schema**: `VERIFIER_TOOL` has name "verify_contract", input_schema
  with `is_contract` (bool) and `reason` (string, nullable)
- **test_verifier_system_prompt**: `build_verifier_prompt()` contains "determine if this
  document is a contract"
- **test_verifier_prompt_includes_instructions**: `build_verifier_prompt("Check for NDA")`
  includes "Check for NDA" with the source attribution

**Code** — create `backend/services/agents/verifier.py`:

```python
VERIFIER_TOOL = {
    "name": "verify_contract",
    "description": "Report whether the document is a contract or legal agreement.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "is_contract": {"type": "boolean", "description": "True if the document is a contract"},
            "reason": {"type": ["string", "null"], "description": "Explanation if not a contract"},
        },
        "required": ["is_contract", "reason"],
        "additionalProperties": False,
    },
}

# Agent calls with force_tool="verify_contract" to guarantee the tool is called

def build_verifier_prompt(instructions: str | None = None) -> str:
    prompt = """You are a document classifier. Your only job is to determine if the provided
document is a contract or legal agreement. Do not analyze its contents deeply.

Call the verify_contract tool with your determination."""
    if instructions:
        prompt += f"\n\n## Additional instructions from reviewer\n{instructions}"
    return prompt
```

**Refactor** — none

**Commit**: `add verifier tool definition and prompt`

---

### verifier-agent-class

**Test** — write these tests and confirm they fail:
- **test_verifier_returns_is_contract_true**: mock AgentRunner to return tool result
  `{"is_contract": true, "reason": null}`. `VerifierAgent.run(...)` returns
  `VerifierResult(is_contract=True, reason=None)`.
- **test_verifier_returns_rejection**: mock AgentRunner to return tool result
  `{"is_contract": false, "reason": "This is a recipe"}`. Returns
  `VerifierResult(is_contract=False, reason="This is a recipe")`.
- **test_verifier_uses_correct_config**: `VerifierAgent` uses `AgentConfig("verifier")`
  (1024 max tokens, cheap model).

**Code** — add `VerifierAgent` class that wraps `AgentRunner`:

```python
@dataclass
class VerifierResult:
    is_contract: bool
    reason: str | None

class VerifierAgent:
    def __init__(self, instructions: str | None = None):
        self.config = AgentConfig("verifier")
        self.instructions = instructions

    async def run(self, pdf_blob: bytes | None = None, text: str | None = None) -> VerifierResult:
        runner = AgentRunner(
            config=self.config,
            tools=[VERIFIER_TOOL],
            tool_handlers={"verify_contract": lambda input: input},  # pass-through
        )
        messages = _build_user_message(pdf_blob, text)
        result = await runner.run(build_verifier_prompt(self.instructions), messages,
                                force_tool="verify_contract")
        tool_data = result.tool_results["verify_contract"]
        return VerifierResult(is_contract=tool_data["is_contract"], reason=tool_data.get("reason"))
```

**Refactor** — extract `_build_user_message(pdf_blob, text)` helper into a shared location
(it's the same pattern as `build_messages` in the current evaluation.py)

**Commit**: `add VerifierAgent with tool-call-enforced output`

---

## Verification

```bash
cd backend && uv run pytest tests/test_verifier.py -v
```

Expected: all tests pass. The verifier correctly classifies documents via tool call.

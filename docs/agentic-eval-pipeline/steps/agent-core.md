# Step: agent-core

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

A base agent runner that wraps the Anthropic SDK. Handles the tool-use loop (send message →
check for tool_use blocks → execute registered tool handlers → send results back → repeat
until end_turn), retries up to 2x on API failure, respects per-agent model config and token
budgets, and tracks `max_tokens` stop reasons. All tool definitions use strict mode
(`"strict": true`) for guaranteed schema adherence, and agents that must call a specific tool
use `tool_choice: {"type": "tool", "name": "..."}` to force the call.

## Done When

- `AgentRunner` can execute a simple tool-using conversation with mocked Anthropic responses
- Retry logic fires on API errors (up to 2x)
- `max_tokens` stop reason is detected and tracked
- Per-agent model and token budget configuration works
- Tool handler registration and dispatch works

## Cycles

### agent-config

**Test** — write these tests and confirm they fail:
- **test_agent_config_defaults**: `AgentConfig("evaluator")` uses the default model and token
  budget from `AGENT_MODELS` and `AGENT_MAX_TOKENS`
- **test_agent_config_env_override**: with `EVALUATOR_MODEL=claude-sonnet-4-6` in env,
  `AgentConfig("evaluator")` uses sonnet
- **test_agent_config_custom_values**: `AgentConfig("evaluator", model="custom", max_tokens=4096)`
  overrides defaults

**Code** — create `backend/services/agents/base.py` with:

```python
AGENT_MODELS = {
    "verifier": os.getenv("VERIFIER_MODEL", "claude-haiku-4-5-20251001"),
    "splitter": os.getenv("SPLITTER_MODEL", "claude-haiku-4-5-20251001"),
    "evaluator": os.getenv("EVALUATOR_MODEL", "claude-haiku-4-5-20251001"),
    "headline": os.getenv("HEADLINE_MODEL", "claude-haiku-4-5-20251001"),
}

AGENT_MAX_TOKENS = {
    "verifier": 1024,
    "splitter": 32768,
    "evaluator": 8192,
    "headline": 8192,
}

@dataclass
class AgentConfig:
    agent_type: str
    model: str = None
    max_tokens: int = None

    def __post_init__(self):
        if self.model is None:
            self.model = AGENT_MODELS.get(self.agent_type, "claude-haiku-4-5-20251001")
        if self.max_tokens is None:
            self.max_tokens = AGENT_MAX_TOKENS.get(self.agent_type, 8192)
```

Create `backend/services/agents/__init__.py` (empty).

**Refactor** — none

**Commit**: `add AgentConfig with per-agent model and token budget`

---

### tool-loop-happy-path

**Test** — write these tests and confirm they fail:
- **test_agent_runner_text_response**: mock Anthropic to return a text response with
  `stop_reason="end_turn"`. Runner returns the text content.
- **test_agent_runner_tool_use_loop**: mock Anthropic to return a `tool_use` block on first
  call, then `end_turn` on second call (after receiving tool result). Runner executes the
  registered tool handler and returns the final text.
- **test_tool_handler_receives_input**: registered tool handler receives the `input` dict
  from the tool_use block. Assert handler was called with correct args.

**Code** — add `AgentRunner` class:

```python
class AgentRunner:
    def __init__(self, config: AgentConfig, tools: list[dict], tool_handlers: dict[str, Callable]):
        self.config = config
        self.tools = tools
        self.tool_handlers = tool_handlers
        self.client = anthropic.AsyncAnthropic(api_key=_get_api_key())

    async def run(self, system: str, messages: list[dict],
                  force_tool: str | None = None) -> AgentResult:
        tool_choice = ({"type": "tool", "name": force_tool} if force_tool
                       else {"type": "auto"})
        # Loop: send message, check for tool_use, execute, repeat
        while True:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=system,
                messages=messages,
                tools=self.tools,
                tool_choice=tool_choice,
            )
            # Check stop reason
            if response.stop_reason == "end_turn":
                return AgentResult(content=response.content, stop_reason="end_turn")
            if response.stop_reason == "tool_use":
                # Find tool_use blocks, execute handlers, append results
                ...
```

```python
@dataclass
class AgentResult:
    content: list  # content blocks from final response
    stop_reason: str
    tool_results: dict  # collected tool call results by tool name
    max_tokens_hit: bool = False
```

**Refactor** — none

**Commit**: `add AgentRunner with tool-use loop`

---

### retry-on-failure

**Test** — write these tests and confirm they fail:
- **test_retry_on_api_error**: mock Anthropic to raise `APIError` on first call, succeed on
  second. Runner retries and returns success.
- **test_retry_exhausted_raises**: mock Anthropic to raise `APIError` 3 times. Runner raises
  after 2 retries (3 total attempts).
- **test_retry_on_timeout**: mock Anthropic to raise `APITimeoutError` on first call, succeed
  on second. Runner retries.
- **test_no_retry_on_non_api_error**: mock Anthropic to raise `ValueError`. Runner raises
  immediately (no retry).

**Code** — wrap the `client.messages.create` call in a retry loop:

```python
MAX_RETRIES = 2

for attempt in range(MAX_RETRIES + 1):
    try:
        response = await self.client.messages.create(...)
        break
    except (anthropic.APIError, anthropic.APITimeoutError):
        if attempt == MAX_RETRIES:
            raise
```

**Refactor** — none

**Commit**: `add 2x retry on API errors in AgentRunner`

---

### max-tokens-tracking

**Test** — write these tests and confirm they fail:
- **test_max_tokens_detected**: mock Anthropic to return `stop_reason="max_tokens"`. Runner
  returns `AgentResult` with `max_tokens_hit=True`.
- **test_max_tokens_logged**: when max_tokens is hit, a warning is logged with the agent type.

**Code** — check `response.stop_reason == "max_tokens"` and set the flag. Add logging.

**Refactor** — none

**Commit**: `track max_tokens stop reason for observability`

---

## Verification

```bash
cd backend && uv run pytest tests/test_agent_base.py -v
```

Expected: all tests pass. The agent runner correctly handles tool loops, retries, and token tracking.

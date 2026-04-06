"""Base agent runner: config, tool-use loop, retry, and token tracking."""

import os
from dataclasses import dataclass, field

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
    model: str | None = None
    max_tokens: int | None = None

    def __post_init__(self):
        if self.model is None:
            self.model = AGENT_MODELS.get(self.agent_type, "claude-haiku-4-5-20251001")
        if self.max_tokens is None:
            self.max_tokens = AGENT_MAX_TOKENS.get(self.agent_type, 8192)

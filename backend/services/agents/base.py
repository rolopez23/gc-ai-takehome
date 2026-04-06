"""Base agent runner: config, tool-use loop, retry, and token tracking."""

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

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


def _get_api_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "")


@dataclass
class AgentResult:
    content: list
    stop_reason: str
    tool_results: dict = field(default_factory=dict)
    max_tokens_hit: bool = False


class AgentRunner:
    def __init__(
        self,
        config: AgentConfig,
        tools: list[dict],
        tool_handlers: dict[str, Callable],
    ):
        self.config = config
        self.tools = tools
        self.tool_handlers = tool_handlers
        self.client = anthropic.AsyncAnthropic(api_key=_get_api_key())

    async def run(
        self,
        system: str,
        messages: list[dict],
        force_tool: str | None = None,
    ) -> AgentResult:
        tool_choice: dict[str, str] = (
            {"type": "tool", "name": force_tool}
            if force_tool
            else {"type": "auto"}
        )
        tool_results: dict[str, Any] = {}

        # Copy messages so we don't mutate the caller's list
        messages = list(messages)

        while True:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=system,
                messages=messages,
                tools=self.tools,
                tool_choice=tool_choice,
            )

            if response.stop_reason == "end_turn":
                return AgentResult(
                    content=response.content,
                    stop_reason="end_turn",
                    tool_results=tool_results,
                )

            if response.stop_reason == "tool_use":
                # Process all tool_use blocks in the response
                tool_result_blocks = []
                for block in response.content:
                    if block.type == "tool_use":
                        handler = self.tool_handlers.get(block.name)
                        if handler:
                            result = await handler(block.input)
                        else:
                            result = f"Unknown tool: {block.name}"
                        tool_results[block.name] = block.input
                        tool_result_blocks.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result),
                            }
                        )

                # Append assistant response + tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_result_blocks})

                # After first forced tool call, switch to auto
                if force_tool:
                    tool_choice = {"type": "auto"}
                continue

            # Unexpected stop reason -- return what we have
            return AgentResult(
                content=response.content,
                stop_reason=response.stop_reason,
                tool_results=tool_results,
            )

"""Tests for the base agent runner (AgentConfig, AgentRunner, retry, max_tokens)."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

# ---------------------------------------------------------------------------
# Cycle 1: AgentConfig
# ---------------------------------------------------------------------------


class TestAgentConfig:
    def test_agent_config_defaults(self):
        """AgentConfig('evaluator') uses default model and token budget."""
        from services.agents.base import AGENT_MAX_TOKENS, AGENT_MODELS, AgentConfig

        config = AgentConfig("evaluator")
        assert config.model == AGENT_MODELS["evaluator"]
        assert config.max_tokens == AGENT_MAX_TOKENS["evaluator"]

    def test_agent_config_env_override(self, monkeypatch):
        """With EVALUATOR_MODEL env var set, AgentConfig picks it up."""
        monkeypatch.setenv("EVALUATOR_MODEL", "claude-sonnet-4-6")

        # Force reimport so module-level os.getenv sees the new env
        import importlib

        import services.agents.base as mod

        importlib.reload(mod)

        config = mod.AgentConfig("evaluator")
        assert config.model == "claude-sonnet-4-6"

    def test_agent_config_custom_values(self):
        """Explicit model/max_tokens override defaults."""
        from services.agents.base import AgentConfig

        config = AgentConfig("evaluator", model="custom-model", max_tokens=4096)
        assert config.model == "custom-model"
        assert config.max_tokens == 4096


# ---------------------------------------------------------------------------
# Helpers for mocking Anthropic responses
# ---------------------------------------------------------------------------


def _make_text_block(text: str):
    """Create a mock TextBlock content block."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_tool_use_block(tool_id: str, name: str, input_dict: dict):
    """Create a mock ToolUseBlock content block."""
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = input_dict
    return block


def _make_response(content: list, stop_reason: str):
    """Create a mock Anthropic Message response."""
    resp = MagicMock()
    resp.content = content
    resp.stop_reason = stop_reason
    return resp


# ---------------------------------------------------------------------------
# Cycle 2: tool-loop-happy-path
# ---------------------------------------------------------------------------


class TestAgentRunnerHappyPath:
    @pytest.mark.asyncio
    async def test_agent_runner_text_response(self):
        """Runner returns text content on end_turn with no tool use."""
        from services.agents.base import AgentConfig, AgentResult, AgentRunner

        config = AgentConfig("evaluator")
        text_block = _make_text_block("Hello world")
        mock_response = _make_response([text_block], "end_turn")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        runner = AgentRunner(config=config, tools=[], tool_handlers={})
        runner.client = mock_client

        result = await runner.run(
            system="test", messages=[{"role": "user", "content": "hi"}]
        )

        assert isinstance(result, AgentResult)
        assert result.content == [text_block]
        assert result.stop_reason == "end_turn"
        assert result.tool_results == {}
        assert result.max_tokens_hit is False

    @pytest.mark.asyncio
    async def test_agent_runner_tool_use_loop(self):
        """Runner executes tool handler and loops back until end_turn."""
        from services.agents.base import AgentConfig, AgentResult, AgentRunner

        config = AgentConfig("evaluator")

        # First response: tool_use block
        tool_block = _make_tool_use_block("tool_1", "my_tool", {"key": "value"})
        first_response = _make_response([tool_block], "tool_use")

        # Second response: text with end_turn
        text_block = _make_text_block("Done")
        second_response = _make_response([text_block], "end_turn")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[first_response, second_response]
        )

        handler = AsyncMock(return_value="tool output")
        runner = AgentRunner(
            config=config,
            tools=[{"name": "my_tool", "description": "test", "input_schema": {}}],
            tool_handlers={"my_tool": handler},
        )
        runner.client = mock_client

        result = await runner.run(
            system="test", messages=[{"role": "user", "content": "go"}]
        )

        assert result.content == [text_block]
        assert result.stop_reason == "end_turn"
        assert "my_tool" in result.tool_results
        assert result.tool_results["my_tool"] == {"key": "value"}
        handler.assert_called_once_with({"key": "value"})

    @pytest.mark.asyncio
    async def test_tool_handler_receives_input(self):
        """Tool handler is called with the exact input dict from the tool_use block."""
        from services.agents.base import AgentConfig, AgentRunner

        config = AgentConfig("evaluator")

        tool_input = {"name": "Alice", "count": 3}
        tool_block = _make_tool_use_block("t1", "greet", tool_input)
        first_response = _make_response([tool_block], "tool_use")

        text_block = _make_text_block("ok")
        second_response = _make_response([text_block], "end_turn")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[first_response, second_response]
        )

        handler = AsyncMock(return_value="greeted")
        runner = AgentRunner(
            config=config,
            tools=[{"name": "greet", "description": "greet", "input_schema": {}}],
            tool_handlers={"greet": handler},
        )
        runner.client = mock_client

        await runner.run(system="test", messages=[{"role": "user", "content": "greet"}])

        handler.assert_called_once_with(tool_input)


# ---------------------------------------------------------------------------
# Cycle 3: retry-on-failure
# ---------------------------------------------------------------------------


class TestAgentRunnerRetry:
    @pytest.mark.asyncio
    async def test_retry_on_api_error(self):
        """Runner retries on APIError and returns success on second attempt."""
        from services.agents.base import AgentConfig, AgentRunner

        config = AgentConfig("evaluator")
        text_block = _make_text_block("ok")
        success_response = _make_response([text_block], "end_turn")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[
                anthropic.APIError(
                    message="server error",
                    request=MagicMock(),
                    body=None,
                ),
                success_response,
            ]
        )

        runner = AgentRunner(config=config, tools=[], tool_handlers={})
        runner.client = mock_client

        result = await runner.run(
            system="test", messages=[{"role": "user", "content": "hi"}]
        )
        assert result.stop_reason == "end_turn"
        assert mock_client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self):
        """Runner raises after 3 total attempts (2 retries)."""
        from services.agents.base import AgentConfig, AgentRunner

        config = AgentConfig("evaluator")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=anthropic.APIError(
                message="server error",
                request=MagicMock(),
                body=None,
            )
        )

        runner = AgentRunner(config=config, tools=[], tool_handlers={})
        runner.client = mock_client

        with pytest.raises(anthropic.APIError):
            await runner.run(
                system="test", messages=[{"role": "user", "content": "hi"}]
            )

        assert mock_client.messages.create.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Runner retries on APITimeoutError and returns success on second attempt."""
        from services.agents.base import AgentConfig, AgentRunner

        config = AgentConfig("evaluator")
        text_block = _make_text_block("ok")
        success_response = _make_response([text_block], "end_turn")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[
                anthropic.APITimeoutError(request=MagicMock()),
                success_response,
            ]
        )

        runner = AgentRunner(config=config, tools=[], tool_handlers={})
        runner.client = mock_client

        result = await runner.run(
            system="test", messages=[{"role": "user", "content": "hi"}]
        )
        assert result.stop_reason == "end_turn"
        assert mock_client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_non_api_error(self):
        """Runner raises immediately on non-API errors (no retry)."""
        from services.agents.base import AgentConfig, AgentRunner

        config = AgentConfig("evaluator")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=ValueError("bad input"))

        runner = AgentRunner(config=config, tools=[], tool_handlers={})
        runner.client = mock_client

        with pytest.raises(ValueError, match="bad input"):
            await runner.run(
                system="test", messages=[{"role": "user", "content": "hi"}]
            )

        assert mock_client.messages.create.call_count == 1


# ---------------------------------------------------------------------------
# Cycle 4: max-tokens-tracking
# ---------------------------------------------------------------------------


class TestMaxTokensTracking:
    @pytest.mark.asyncio
    async def test_max_tokens_detected(self):
        """Runner sets max_tokens_hit=True when stop_reason is 'max_tokens'."""
        from services.agents.base import AgentConfig, AgentRunner

        config = AgentConfig("evaluator")
        text_block = _make_text_block("truncated output")
        response = _make_response([text_block], "max_tokens")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=response)

        runner = AgentRunner(config=config, tools=[], tool_handlers={})
        runner.client = mock_client

        result = await runner.run(
            system="test", messages=[{"role": "user", "content": "hi"}]
        )
        assert result.max_tokens_hit is True
        assert result.stop_reason == "max_tokens"
        assert result.content == [text_block]

    @pytest.mark.asyncio
    async def test_max_tokens_logged(self, caplog):
        """A warning is logged when max_tokens is hit."""
        import logging

        from services.agents.base import AgentConfig, AgentRunner

        config = AgentConfig("evaluator")
        text_block = _make_text_block("truncated")
        response = _make_response([text_block], "max_tokens")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=response)

        runner = AgentRunner(config=config, tools=[], tool_handlers={})
        runner.client = mock_client

        with caplog.at_level(logging.WARNING, logger="services.agents.base"):
            await runner.run(
                system="test", messages=[{"role": "user", "content": "hi"}]
            )

        assert any("max_tokens" in record.message for record in caplog.records)
        assert any("evaluator" in record.message for record in caplog.records)

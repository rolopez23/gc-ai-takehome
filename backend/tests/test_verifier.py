"""Tests for the contract verifier agent."""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.agents.verifier import (
    VERIFIER_TOOL,
    VerifierAgent,
    VerifierResult,
    build_verifier_prompt,
)
from services.agents.messages import build_user_message

# --- Cycle 1: verifier-tool-definition ---


class TestVerifierTool:
    def test_verifier_tool_schema(self):
        """VERIFIER_TOOL has name 'verify_contract', is_contract (bool) and reason (string, nullable)."""
        assert VERIFIER_TOOL["name"] == "verify_contract"
        assert VERIFIER_TOOL["strict"] is True
        schema = VERIFIER_TOOL["input_schema"]
        assert schema["additionalProperties"] is False
        assert schema["properties"]["is_contract"]["type"] == "boolean"
        # reason must be nullable string
        assert schema["properties"]["reason"]["type"] == ["string", "null"]
        assert "is_contract" in schema["required"]
        assert "reason" in schema["required"]


class TestVerifierPrompt:
    def test_verifier_system_prompt(self):
        """build_verifier_prompt() contains 'determine if this document is a contract'."""
        prompt = build_verifier_prompt()
        assert "determine" in prompt.lower()
        assert "contract" in prompt.lower()

    def test_verifier_prompt_includes_instructions(self):
        """When instructions provided, they appear in the prompt with source attribution."""
        prompt = build_verifier_prompt("Check for NDA")
        assert "Check for NDA" in prompt
        # Should have some attribution about where instructions come from
        assert (
            "reviewer" in prompt.lower()
            or "instruction" in prompt.lower()
            or "user" in prompt.lower()
        )

    def test_verifier_prompt_without_instructions(self):
        """When no instructions, prompt still works without errors."""
        prompt = build_verifier_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0


# --- Cycle 1: _build_user_message helper ---


class TestBuildUserMessage:
    def test_build_user_message_with_pdf(self):
        """PDF blob produces a document content block."""
        pdf_blob = b"%PDF-fake-content"
        messages = build_user_message(pdf_blob=pdf_blob, text=None)
        assert len(messages) == 1
        msg = messages[0]
        assert msg["role"] == "user"
        content = msg["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "document"
        assert content[0]["source"]["media_type"] == "application/pdf"
        expected_b64 = base64.standard_b64encode(pdf_blob).decode("ascii")
        assert content[0]["source"]["data"] == expected_b64

    def test_build_user_message_with_text(self):
        """Text-only produces a simple string message."""
        messages = build_user_message(pdf_blob=None, text="This is a contract.")
        assert len(messages) == 1
        msg = messages[0]
        assert msg["role"] == "user"
        assert msg["content"] == "This is a contract."

    def test_build_user_message_requires_input(self):
        """Must provide either pdf_blob or text."""
        with pytest.raises(ValueError):
            build_user_message(pdf_blob=None, text=None)

    def test_build_user_message_pdf_takes_precedence(self):
        """When both provided, pdf_blob is used (not text)."""
        pdf_blob = b"%PDF-test"
        messages = build_user_message(pdf_blob=pdf_blob, text="fallback text")
        content = messages[0]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "document"


# --- Cycle 2: verifier-agent-class ---


class TestVerifierAgent:
    @pytest.fixture
    def mock_agent_result_contract(self):
        """AgentResult where the tool says it IS a contract."""
        result = MagicMock()
        result.tool_results = {"verify_contract": {"is_contract": True, "reason": None}}
        result.stop_reason = "tool_use"
        return result

    @pytest.fixture
    def mock_agent_result_not_contract(self):
        """AgentResult where the tool says it is NOT a contract."""
        result = MagicMock()
        result.tool_results = {
            "verify_contract": {"is_contract": False, "reason": "This is a recipe"}
        }
        result.stop_reason = "tool_use"
        return result

    @pytest.mark.asyncio
    async def test_verifier_returns_is_contract_true(self, mock_agent_result_contract):
        """VerifierAgent.run() returns VerifierResult(is_contract=True) for contracts."""
        with patch("services.agents.verifier.AgentRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run = AsyncMock(return_value=mock_agent_result_contract)

            agent = VerifierAgent()
            result = await agent.run(pdf_blob=None, text="This is a binding agreement.")

            assert isinstance(result, VerifierResult)
            assert result.is_contract is True
            assert result.reason is None

    @pytest.mark.asyncio
    async def test_verifier_returns_rejection(self, mock_agent_result_not_contract):
        """VerifierAgent.run() returns VerifierResult(is_contract=False, reason=...) for non-contracts."""
        with patch("services.agents.verifier.AgentRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run = AsyncMock(return_value=mock_agent_result_not_contract)

            agent = VerifierAgent()
            result = await agent.run(pdf_blob=None, text="Mix flour and sugar.")

            assert isinstance(result, VerifierResult)
            assert result.is_contract is False
            assert result.reason == "This is a recipe"

    def test_verifier_uses_correct_config(self):
        """VerifierAgent uses AgentConfig('verifier') — 1024 max tokens, cheap model."""
        agent = VerifierAgent()
        assert agent.config.agent_type == "verifier"
        assert agent.config.max_tokens == 1024

    @pytest.mark.asyncio
    async def test_verifier_passes_force_tool(self, mock_agent_result_contract):
        """VerifierAgent passes force_tool='verify_contract' to AgentRunner.run()."""
        with patch("services.agents.verifier.AgentRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run = AsyncMock(return_value=mock_agent_result_contract)

            agent = VerifierAgent()
            await agent.run(pdf_blob=None, text="Contract text")

            instance.run.assert_called_once()
            call_kwargs = instance.run.call_args
            assert call_kwargs.kwargs.get("force_tool") == "verify_contract" or (
                len(call_kwargs.args) >= 3 and call_kwargs.args[2] == "verify_contract"
            )

    @pytest.mark.asyncio
    async def test_verifier_passes_instructions_to_prompt(
        self, mock_agent_result_contract
    ):
        """When instructions provided, they are included in the system prompt."""
        with patch("services.agents.verifier.AgentRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run = AsyncMock(return_value=mock_agent_result_contract)

            agent = VerifierAgent(instructions="Check for NDA")
            await agent.run(pdf_blob=None, text="Contract text")

            call_args = instance.run.call_args
            system_prompt = (
                call_args.args[0]
                if call_args.args
                else call_args.kwargs.get("system", "")
            )
            assert "Check for NDA" in system_prompt

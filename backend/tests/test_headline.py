"""Tests for the headline generator agent."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.agents.headline import (
    HEADLINE_TOOL,
    HeadlineAgent,
    HeadlineResult,
    build_headline_prompt,
)

# --- Cycle 1: headline-tool-and-prompt ---


class TestHeadlineTool:
    def test_headline_tool_schema(self):
        """HEADLINE_TOOL has name 'report_headline' with summary (string) and call_to_action (array of strings)."""
        assert HEADLINE_TOOL["name"] == "report_headline"
        assert HEADLINE_TOOL["strict"] is True
        schema = HEADLINE_TOOL["input_schema"]
        assert schema["additionalProperties"] is False
        assert schema["properties"]["summary"]["type"] == "string"
        assert schema["properties"]["call_to_action"]["type"] == "array"
        assert schema["properties"]["call_to_action"]["items"]["type"] == "string"
        assert "summary" in schema["required"]
        assert "call_to_action" in schema["required"]


class TestHeadlinePrompt:
    def test_headline_prompt_includes_context(self):
        """Prompt references that it will receive clause evaluation data."""
        prompt = build_headline_prompt(instructions=None)
        assert "clause" in prompt.lower()
        assert "evaluation" in prompt.lower() or "evaluat" in prompt.lower()

    def test_headline_prompt_includes_instructions(self):
        """When instructions provided, they appear in the prompt with source attribution."""
        prompt = build_headline_prompt(instructions="Focus on IP clauses")
        assert "Focus on IP clauses" in prompt
        # Should have some source attribution
        assert "user" in prompt.lower() or "instruction" in prompt.lower()

    def test_headline_prompt_without_instructions(self):
        """When no instructions, prompt still works without errors."""
        prompt = build_headline_prompt(instructions=None)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_headline_prompt_includes_brevity(self):
        """Prompt contains brevity instructions for summary and call_to_action."""
        prompt = build_headline_prompt(instructions=None)
        assert "1-2 sentences" in prompt
        assert "5-10 words" in prompt


# --- Cycle 2: headline-agent-class ---


class TestHeadlineAgent:
    @pytest.fixture
    def mock_clause_data(self):
        return [
            {
                "section_number": "1.1",
                "clause_type": "Limitation of Liability",
                "severity": 7,
                "fairness": "non-standard",
                "finding": "Cap is too low",
                "explanation": "The liability cap is below market standard.",
                "purpose": "Limits total liability",
                "market_standard": "Usually 12 months fees",
            },
            {
                "section_number": "2.1",
                "clause_type": "Indemnification",
                "severity": 3,
                "fairness": "fair",
                "finding": "Standard mutual indemnification",
                "explanation": "Both parties indemnify each other.",
                "purpose": "Mutual protection",
                "market_standard": "Standard",
            },
        ]

    @pytest.mark.asyncio
    async def test_headline_returns_summary(self, mock_clause_data):
        """Mock AgentRunner to return report_headline with summary text."""
        summary_text = "This contract has some concerning liability provisions."
        cta = ["Negotiate liability cap", "Review indemnification"]

        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "report_headline"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {
            "summary": summary_text,
            "call_to_action": cta,
        }

        with patch("services.agents.headline.AgentRunner") as MockRunner:
            mock_runner_instance = AsyncMock()
            MockRunner.return_value = mock_runner_instance
            mock_runner_instance.run.return_value = MagicMock(
                tool_results={"report_headline": mock_tool_block.input},
                stop_reason="tool_use",
            )

            agent = HeadlineAgent()
            result = await agent.run(
                agreement_type="SaaS MSA",
                clauses=mock_clause_data,
                failed_clause_count=0,
                absent_clause_count=1,
            )

            assert result.summary == summary_text

    @pytest.mark.asyncio
    async def test_headline_returns_call_to_action(self, mock_clause_data):
        """Assert HeadlineResult.call_to_action is a list of strings."""
        cta = ["Negotiate liability cap", "Review indemnification"]

        with patch("services.agents.headline.AgentRunner") as MockRunner:
            mock_runner_instance = AsyncMock()
            MockRunner.return_value = mock_runner_instance
            mock_runner_instance.run.return_value = MagicMock(
                tool_results={
                    "report_headline": {
                        "summary": "Summary text",
                        "call_to_action": cta,
                    }
                },
                stop_reason="tool_use",
            )

            agent = HeadlineAgent()
            result = await agent.run(
                agreement_type="SaaS MSA",
                clauses=mock_clause_data,
                failed_clause_count=0,
                absent_clause_count=1,
            )

            assert isinstance(result.call_to_action, list)
            assert all(isinstance(item, str) for item in result.call_to_action)
            assert result.call_to_action == cta

    @pytest.mark.asyncio
    async def test_headline_input_includes_clauses(self, mock_clause_data):
        """The user message sent to the agent includes the clause evaluation data."""
        with patch("services.agents.headline.AgentRunner") as MockRunner:
            mock_runner_instance = AsyncMock()
            MockRunner.return_value = mock_runner_instance
            mock_runner_instance.run.return_value = MagicMock(
                tool_results={
                    "report_headline": {
                        "summary": "Summary",
                        "call_to_action": ["Action"],
                    }
                },
                stop_reason="tool_use",
            )

            agent = HeadlineAgent()
            await agent.run(
                agreement_type="SaaS MSA",
                clauses=mock_clause_data,
                failed_clause_count=0,
                absent_clause_count=1,
            )

            # Check the messages passed to runner.run
            call_args = mock_runner_instance.run.call_args
            messages = call_args.kwargs.get("messages") or call_args[1].get(
                "messages", call_args[0][1] if len(call_args[0]) > 1 else None
            )
            user_msg = messages[0]["content"]
            assert "1.1" in user_msg
            assert "Limitation of Liability" in user_msg

    @pytest.mark.asyncio
    async def test_headline_input_includes_metadata(self, mock_clause_data):
        """User message includes agreement_type, failed_clause_count, absent_clause_count."""
        with patch("services.agents.headline.AgentRunner") as MockRunner:
            mock_runner_instance = AsyncMock()
            MockRunner.return_value = mock_runner_instance
            mock_runner_instance.run.return_value = MagicMock(
                tool_results={
                    "report_headline": {
                        "summary": "Summary",
                        "call_to_action": ["Action"],
                    }
                },
                stop_reason="tool_use",
            )

            agent = HeadlineAgent()
            await agent.run(
                agreement_type="SaaS MSA",
                clauses=mock_clause_data,
                failed_clause_count=2,
                absent_clause_count=3,
            )

            call_args = mock_runner_instance.run.call_args
            messages = call_args.kwargs.get("messages") or call_args[1].get(
                "messages", call_args[0][1] if len(call_args[0]) > 1 else None
            )
            user_msg = messages[0]["content"]
            assert "SaaS MSA" in user_msg
            assert "2" in user_msg  # failed_clause_count
            assert "3" in user_msg  # absent_clause_count

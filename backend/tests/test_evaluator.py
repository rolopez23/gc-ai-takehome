"""Tests for the clause evaluator agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.agents.evaluator import (
    GET_PLAYBOOK_TOOL,
    REPORT_EVALUATION_TOOL,
    EvaluatorAgent,
    EvaluatorResult,
    build_evaluator_prompt,
    handle_get_playbook,
)

# --- Cycle 1: evaluator-tool-definitions ---


class TestEvaluatorToolDefinitions:
    def test_evaluator_tools_count(self):
        """Evaluator agent registers exactly 2 tools: get_playbook and report_evaluation."""
        agent = EvaluatorAgent(agreement_type="SaaS Master Service Agreement")
        # The agent should use both tools
        assert GET_PLAYBOOK_TOOL["name"] == "get_playbook"
        assert REPORT_EVALUATION_TOOL["name"] == "report_evaluation"

    def test_get_playbook_tool_schema(self):
        """GET_PLAYBOOK_TOOL has strict mode, agreement_type (str) and check_names (array of str)."""
        assert GET_PLAYBOOK_TOOL["strict"] is True
        schema = GET_PLAYBOOK_TOOL["input_schema"]
        assert schema["additionalProperties"] is False
        assert schema["properties"]["agreement_type"]["type"] == "string"
        assert schema["properties"]["check_names"]["type"] == "array"
        assert schema["properties"]["check_names"]["items"]["type"] == "string"
        assert "agreement_type" in schema["required"]
        assert "check_names" in schema["required"]

    def test_report_evaluation_tool_schema(self):
        """REPORT_EVALUATION_TOOL has strict mode and all required fields from spec."""
        assert REPORT_EVALUATION_TOOL["strict"] is True
        schema = REPORT_EVALUATION_TOOL["input_schema"]
        assert schema["additionalProperties"] is False

        # All fields from the spec
        expected_fields = [
            "section_number",
            "clause_type",
            "severity",
            "playbook_status",
            "playbook_position",
            "contract_language",
            "finding",
            "recommended_redline",
            "fairness",
            "purpose",
            "market_standard",
            "explanation",
        ]
        for field in expected_fields:
            assert field in schema["properties"], f"Missing field: {field}"

        # severity should be integer
        assert schema["properties"]["severity"]["type"] == "integer"
        # fairness should have enum
        assert set(schema["properties"]["fairness"]["enum"]) == {
            "fair",
            "non-standard",
            "dealbreaker",
        }

    def test_evaluator_prompt_includes_guardrail(self):
        """Prompt contains the relevance guardrail for user instructions."""
        prompt = build_evaluator_prompt(instructions="Focus on IP terms")
        assert "instructions may not be relevant for this clause" in prompt.lower()

    def test_evaluator_prompt_includes_instructions(self):
        """User instructions appear in the prompt when provided."""
        prompt = build_evaluator_prompt(instructions="Focus on IP terms")
        assert "Focus on IP terms" in prompt

    def test_evaluator_prompt_without_instructions(self):
        """Prompt works without instructions."""
        prompt = build_evaluator_prompt(instructions=None)
        assert isinstance(prompt, str)
        assert len(prompt) > 0


# --- Cycle 2: get-playbook-tool-handler ---


class TestGetPlaybookHandler:
    @pytest.mark.asyncio
    async def test_playbook_handler_returns_checks(self):
        """Handler called with valid agreement_type and check_names returns checks list."""
        result = await handle_get_playbook(
            {
                "agreement_type": "SaaS Master Service Agreement",
                "check_names": ["Payment Terms"],
            }
        )
        assert "checks" in result
        assert len(result["checks"]) > 0
        check = result["checks"][0]
        assert "name" in check
        assert check["name"] == "Payment Terms"

    @pytest.mark.asyncio
    async def test_playbook_handler_error_on_zero_match(self):
        """Handler with unknown check name returns error dict, not an exception."""
        result = await handle_get_playbook(
            {
                "agreement_type": "SaaS Master Service Agreement",
                "check_names": ["Nonexistent Check XYZ"],
            }
        )
        assert "error" in result


# --- Cycle 3: evaluator-agent-class ---


class TestEvaluatorAgent:
    @pytest.mark.asyncio
    async def test_evaluator_runs_tool_sequence(self):
        """Mock AgentRunner: first calls get_playbook, then report_evaluation. Returns EvaluatorResult."""
        eval_output = {
            "section_number": "4.2",
            "clause_type": "Limitation of Liability",
            "severity": 7,
            "playbook_status": "TRIGGERED",
            "playbook_position": "Cap should be at least 12 months fees",
            "contract_language": "Total liability shall not exceed $10,000",
            "finding": "Liability cap is below market standard.",
            "recommended_redline": "Increase cap to 12 months of fees.",
            "fairness": "non-standard",
            "purpose": "Limits total liability exposure",
            "market_standard": "Typically 12 months of fees",
            "explanation": "The liability cap is significantly below market standard.",
        }

        with patch("services.agents.evaluator.AgentRunner") as MockRunner:
            mock_runner_instance = AsyncMock()
            MockRunner.return_value = mock_runner_instance
            mock_runner_instance.run.return_value = MagicMock(
                tool_results={
                    "get_playbook": {
                        "agreement_type": "SaaS Master Service Agreement",
                        "check_names": ["Limitation of Liability"],
                    },
                    "report_evaluation": eval_output,
                },
                stop_reason="end_turn",
            )

            agent = EvaluatorAgent(agreement_type="SaaS Master Service Agreement")
            result = await agent.run(
                clause={
                    "section_number": "4.2",
                    "clause_type": "Limitation of Liability",
                    "text": "Total liability shall not exceed $10,000.",
                    "relevant_checks": ["Limitation of Liability"],
                    "cross_references": [],
                    "is_cycle": False,
                },
            )

            assert isinstance(result, EvaluatorResult)
            assert result.section_number == "4.2"
            assert result.finding == "Liability cap is below market standard."

    @pytest.mark.asyncio
    async def test_evaluator_result_has_dual_tier(self):
        """Result has both playbook_status and fairness."""
        eval_output = {
            "section_number": "4.2",
            "clause_type": "Limitation of Liability",
            "severity": 7,
            "playbook_status": "TRIGGERED",
            "playbook_position": "Cap should be at least 12 months fees",
            "contract_language": "Total liability shall not exceed $10,000",
            "finding": "Liability cap is below market standard.",
            "recommended_redline": "Increase cap to 12 months of fees.",
            "fairness": "non-standard",
            "purpose": "Limits total liability exposure",
            "market_standard": "Typically 12 months of fees",
            "explanation": "The liability cap is significantly below market standard.",
        }

        with patch("services.agents.evaluator.AgentRunner") as MockRunner:
            mock_runner_instance = AsyncMock()
            MockRunner.return_value = mock_runner_instance
            mock_runner_instance.run.return_value = MagicMock(
                tool_results={
                    "get_playbook": {
                        "agreement_type": "SaaS Master Service Agreement",
                        "check_names": ["Limitation of Liability"],
                    },
                    "report_evaluation": eval_output,
                },
                stop_reason="end_turn",
            )

            agent = EvaluatorAgent(agreement_type="SaaS Master Service Agreement")
            result = await agent.run(
                clause={
                    "section_number": "4.2",
                    "clause_type": "Limitation of Liability",
                    "text": "Total liability shall not exceed $10,000.",
                    "relevant_checks": ["Limitation of Liability"],
                    "cross_references": [],
                    "is_cycle": False,
                },
            )

            assert result.playbook_status == "TRIGGERED"
            assert result.fairness == "non-standard"

    @pytest.mark.asyncio
    async def test_evaluator_result_has_severity(self):
        """Result has severity (int 1-10)."""
        eval_output = {
            "section_number": "4.2",
            "clause_type": "Limitation of Liability",
            "severity": 7,
            "playbook_status": "TRIGGERED",
            "playbook_position": "Cap position",
            "contract_language": "Contract text",
            "finding": "Finding text",
            "recommended_redline": "Redline text",
            "fairness": "non-standard",
            "purpose": "Purpose text",
            "market_standard": "Market text",
            "explanation": "Explanation text",
        }

        with patch("services.agents.evaluator.AgentRunner") as MockRunner:
            mock_runner_instance = AsyncMock()
            MockRunner.return_value = mock_runner_instance
            mock_runner_instance.run.return_value = MagicMock(
                tool_results={
                    "get_playbook": {
                        "agreement_type": "SaaS Master Service Agreement",
                        "check_names": ["Limitation of Liability"],
                    },
                    "report_evaluation": eval_output,
                },
                stop_reason="end_turn",
            )

            agent = EvaluatorAgent(agreement_type="SaaS Master Service Agreement")
            result = await agent.run(
                clause={
                    "section_number": "4.2",
                    "clause_type": "Limitation of Liability",
                    "text": "Contract text.",
                    "relevant_checks": ["Limitation of Liability"],
                    "cross_references": [],
                    "is_cycle": False,
                },
            )

            assert isinstance(result.severity, int)
            assert result.severity == 7

    @pytest.mark.asyncio
    async def test_evaluator_receives_cross_ref_text(self):
        """When cross-reference text is provided, it appears in the user message."""
        eval_output = {
            "section_number": "4.2",
            "clause_type": "Limitation of Liability",
            "severity": 5,
            "playbook_status": "PASS",
            "playbook_position": None,
            "contract_language": None,
            "finding": "Standard clause",
            "recommended_redline": None,
            "fairness": "fair",
            "purpose": "Purpose",
            "market_standard": "Standard",
            "explanation": "Explanation",
        }

        with patch("services.agents.evaluator.AgentRunner") as MockRunner:
            mock_runner_instance = AsyncMock()
            MockRunner.return_value = mock_runner_instance
            mock_runner_instance.run.return_value = MagicMock(
                tool_results={
                    "get_playbook": {
                        "agreement_type": "SaaS Master Service Agreement",
                        "check_names": ["Limitation of Liability"],
                    },
                    "report_evaluation": eval_output,
                },
                stop_reason="end_turn",
            )

            agent = EvaluatorAgent(agreement_type="SaaS Master Service Agreement")
            cross_ref_text = {
                "8.2": "Termination for cause requires 30 days notice.",
            }
            await agent.run(
                clause={
                    "section_number": "4.2",
                    "clause_type": "Limitation of Liability",
                    "text": "Subject to Section 8.2, total liability shall not exceed $10,000.",
                    "relevant_checks": ["Limitation of Liability"],
                    "cross_references": ["8.2"],
                    "is_cycle": False,
                },
                cross_ref_text=cross_ref_text,
            )

            # Check the messages passed to runner.run
            call_args = mock_runner_instance.run.call_args
            messages = call_args.kwargs.get(
                "messages", call_args[0][1] if len(call_args[0]) > 1 else None
            )
            user_msg = messages[0]["content"]
            assert "8.2" in user_msg
            assert "Termination for cause requires 30 days notice" in user_msg

"""Tests for the clause splitter agent (tool definition, prompt, agent class, absent detection)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers for mocking Anthropic responses
# ---------------------------------------------------------------------------


def _make_tool_use_block(tool_id: str, name: str, input_dict: dict):
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = input_dict
    return block


def _make_text_block(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_response(content: list, stop_reason: str):
    resp = MagicMock()
    resp.content = content
    resp.stop_reason = stop_reason
    return resp


# ---------------------------------------------------------------------------
# Cycle 1: splitter-tool-definition
# ---------------------------------------------------------------------------


class TestSplitterToolSchema:
    def test_splitter_tool_schema(self):
        """SPLITTER_TOOL has name 'report_clauses' with correct input_schema."""
        from services.agents.splitter import SPLITTER_TOOL

        assert SPLITTER_TOOL["name"] == "report_clauses"
        assert SPLITTER_TOOL["strict"] is True

        schema = SPLITTER_TOOL["input_schema"]
        assert schema["additionalProperties"] is False
        assert "agreement_type" in schema["properties"]
        assert "clauses" in schema["properties"]

        # agreement_type enum
        at_prop = schema["properties"]["agreement_type"]
        assert set(at_prop["enum"]) == {
            "SaaS MSA",
            "NDA",
            "Commercial MSA",
            "DPA",
            "General",
        }

        # clause items schema
        clause_schema = schema["properties"]["clauses"]["items"]
        required_fields = {
            "section_number",
            "clause_type",
            "text",
            "relevant_checks",
            "cross_references",
            "is_cycle",
        }
        assert set(clause_schema["required"]) == required_fields
        assert clause_schema["additionalProperties"] is False

    def test_splitter_prompt_contains_check_enum(self):
        """build_splitter_prompt includes playbook check names with descriptions."""
        from services.agents.splitter import build_splitter_prompt

        prompt = build_splitter_prompt("Please focus on liability clauses.")
        # Should contain check names from the playbook
        assert "Payment Terms" in prompt
        assert "Auto-Renewal" in prompt
        assert "Limitation of Liability" in prompt
        # Should contain user instructions
        assert "Please focus on liability clauses." in prompt

    def test_splitter_prompt_contains_all_agreement_types(self):
        """build_splitter_prompt includes check enums for all 4 agreement types."""
        from services.agents.splitter import build_splitter_prompt

        prompt = build_splitter_prompt(None)
        # SaaS MSA checks
        assert "Price Increase Cap" in prompt
        # NDA checks
        assert "Definition of Confidential Information" in prompt
        # DPA checks
        assert "Data Processing Agreement" in prompt or "Data Subject Rights" in prompt
        # Commercial MSA checks
        assert "Limitation of Liability" in prompt

    def test_splitter_prompt_no_instructions(self):
        """build_splitter_prompt with None instructions omits instructions section."""
        from services.agents.splitter import build_splitter_prompt

        prompt = build_splitter_prompt(None)
        assert (
            "User instructions" not in prompt
            or "no additional instructions" in prompt.lower()
        )


# ---------------------------------------------------------------------------
# Cycle 2: splitter-agent-class
# ---------------------------------------------------------------------------


class TestSplitterAgentClass:
    @pytest.mark.asyncio
    async def test_splitter_returns_agreement_type(self):
        """SplitterAgent.run returns SplitterResult with correct agreement_type."""
        from services.agents.splitter import SplitterAgent, SplitterResult

        tool_input = {
            "agreement_type": "SaaS MSA",
            "clauses": [
                {
                    "section_number": "1.1",
                    "clause_type": "Payment Terms",
                    "text": "Payment is due within 30 days.",
                    "relevant_checks": ["Payment Terms"],
                    "cross_references": [],
                    "is_cycle": False,
                },
            ],
        }

        tool_block = _make_tool_use_block("tool_1", "report_clauses", tool_input)
        mock_response = _make_response([tool_block], "tool_use")
        # After tool use, the runner loops; second call ends turn
        end_response = _make_response([_make_text_block("done")], "end_turn")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[mock_response, end_response]
        )

        agent = SplitterAgent()
        agent.runner.client = mock_client

        result = await agent.run(text="Some contract text")
        assert isinstance(result, SplitterResult)
        assert result.agreement_type == "SaaS MSA"

    @pytest.mark.asyncio
    async def test_splitter_returns_clauses(self):
        """SplitterAgent.run returns correct number of clauses with all fields."""
        from services.agents.splitter import SplitterAgent, SplitterClause

        clauses_data = [
            {
                "section_number": f"clause-{i}",
                "clause_type": f"Type {i}",
                "text": f"Clause text {i}",
                "relevant_checks": ["Payment Terms"] if i == 1 else [],
                "cross_references": ["clause-1"] if i == 2 else [],
                "is_cycle": False,
            }
            for i in range(1, 4)
        ]

        tool_input = {"agreement_type": "NDA", "clauses": clauses_data}
        tool_block = _make_tool_use_block("tool_1", "report_clauses", tool_input)
        mock_response = _make_response([tool_block], "tool_use")
        end_response = _make_response([_make_text_block("done")], "end_turn")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[mock_response, end_response]
        )

        agent = SplitterAgent()
        agent.runner.client = mock_client

        result = await agent.run(text="NDA contract text")
        assert len(result.clauses) == 3
        for clause in result.clauses:
            assert isinstance(clause, SplitterClause)

    @pytest.mark.asyncio
    async def test_splitter_clause_shape(self):
        """Each clause has all required fields with correct types."""
        from services.agents.splitter import SplitterAgent

        tool_input = {
            "agreement_type": "SaaS MSA",
            "clauses": [
                {
                    "section_number": "4.2",
                    "clause_type": "Limitation of Liability",
                    "text": "Liability is limited to 12 months fees.",
                    "relevant_checks": ["Limitation of Liability"],
                    "cross_references": ["3.1"],
                    "is_cycle": True,
                },
            ],
        }

        tool_block = _make_tool_use_block("tool_1", "report_clauses", tool_input)
        mock_response = _make_response([tool_block], "tool_use")
        end_response = _make_response([_make_text_block("done")], "end_turn")

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[mock_response, end_response]
        )

        agent = SplitterAgent()
        agent.runner.client = mock_client

        result = await agent.run(text="Contract text")
        clause = result.clauses[0]
        assert clause.section_number == "4.2"
        assert clause.clause_type == "Limitation of Liability"
        assert clause.text == "Liability is limited to 12 months fees."
        assert clause.relevant_checks == ["Limitation of Liability"]
        assert clause.cross_references == ["3.1"]
        assert clause.is_cycle is True

    def test_splitter_uses_correct_config(self):
        """SplitterAgent uses AgentConfig('splitter') with 32768 max tokens."""
        from services.agents.splitter import SplitterAgent

        agent = SplitterAgent()
        assert agent.runner.config.agent_type == "splitter"
        assert agent.runner.config.max_tokens == 32768


# ---------------------------------------------------------------------------
# Cycle 3: absent-check-detection
# ---------------------------------------------------------------------------


class TestAbsentCheckDetection:
    def test_detect_absent_checks_finds_uncovered(self):
        """Absent detection returns synthetic clauses for uncovered checks."""
        from services.agents.splitter import detect_absent_checks

        # Tag only a subset of SaaS MSA checks (21 total)
        tagged = {
            "Payment Terms",
            "Auto-Renewal",
            "Price Increase Cap",
            "Termination for Convenience",
            "Limitation of Liability",
            "Indemnification",
            "IP Ownership",
            "Data Security",
            "Uptime SLA",
            "Support SLA",
            "Data Portability",
            "Audit Rights",
            "Insurance",
            "Governing Law",
            "Dispute Resolution",
        }
        # 21 - 15 = 6 uncovered
        result = detect_absent_checks("SaaS MSA", tagged)
        assert len(result) == 6

    def test_absent_clause_shape(self):
        """Synthetic absent clauses have correct shape."""
        from services.agents.splitter import AbsentClause, detect_absent_checks

        tagged = set()  # Tag nothing -- all checks are absent
        result = detect_absent_checks("SaaS MSA", tagged)
        assert len(result) > 0

        for clause in result:
            assert isinstance(clause, AbsentClause)
            assert clause.is_synthetic is True
            assert clause.text == ""
            assert len(clause.relevant_checks) == 1
            assert clause.clause_type == clause.relevant_checks[0]

    def test_absent_clause_deterministic_rating(self):
        """Absent checks get deterministic severity and fairness by importance."""
        from services.agents.splitter import detect_absent_checks

        # Only tag checks that are NOT the ones we want to test
        # We want to see: High -> severity 8, dealbreaker
        #                  Medium -> severity 5, non-standard
        #                  Low -> severity 2, fair
        tagged = set()  # Tag nothing
        result = detect_absent_checks("SaaS MSA", tagged)

        by_name = {c.clause_type: c for c in result}

        # High importance: e.g., "Price Increase Cap"
        assert by_name["Price Increase Cap"].severity == 8
        assert by_name["Price Increase Cap"].fairness == "dealbreaker"

        # Medium importance: e.g., "Payment Terms"
        assert by_name["Payment Terms"].severity == 5
        assert by_name["Payment Terms"].fairness == "non-standard"

        # Low importance: e.g., "Insurance"
        assert by_name["Insurance"].severity == 2
        assert by_name["Insurance"].fairness == "fair"

    def test_absent_detection_general_returns_empty(self):
        """agreement_type='General' returns no absent clauses."""
        from services.agents.splitter import detect_absent_checks

        result = detect_absent_checks("General", set())
        assert result == []

    def test_absent_clause_section_numbering(self):
        """Synthetic clauses get sequential 'absent-N' section numbers."""
        from services.agents.splitter import detect_absent_checks

        tagged = set()
        result = detect_absent_checks("SaaS MSA", tagged)

        section_numbers = [c.section_number for c in result]
        for i, sn in enumerate(section_numbers, start=1):
            assert sn == f"absent-{i}"

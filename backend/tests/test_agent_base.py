"""Tests for the base agent runner (AgentConfig, AgentRunner, retry, max_tokens)."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

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

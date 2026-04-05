from prompt import EvalErrorResponse, EvalSuccessResponse, build_system_prompt


class TestPromptContainsAnalysisRules:
    def test_prompt_contains_analysis_rules(self):
        prompt = build_system_prompt()
        assert "senior in-house commercial lawyer" in prompt
        assert "fairness tiers" in prompt
        assert "dealbreaker" in prompt
        assert "non-standard" in prompt
        assert "Death by paper cuts" in prompt
        assert "30%" in prompt


class TestPromptContainsJsonSchemas:
    def test_prompt_contains_json_schemas(self):
        prompt = build_system_prompt()
        assert "overall_fairness" in prompt
        assert "reason" in prompt


class TestPromptWithoutInstructions:
    def test_prompt_without_instructions(self):
        prompt = build_system_prompt()
        assert "Additional instructions" not in prompt


class TestPromptWithInstructions:
    def test_prompt_with_instructions(self):
        prompt = build_system_prompt("Focus on IP clauses")
        assert "Additional instructions" in prompt
        assert "Focus on IP clauses" in prompt


class TestEvalSuccessSchemaFields:
    def test_eval_success_schema_fields(self):
        schema = EvalSuccessResponse.model_json_schema()
        props = schema["properties"]
        assert "error" in props
        assert "overall_fairness" in props
        assert "summary" in props
        assert "call_to_action" in props
        assert "clauses" in props


class TestEvalErrorSchemaFields:
    def test_eval_error_schema_fields(self):
        schema = EvalErrorResponse.model_json_schema()
        props = schema["properties"]
        assert "error" in props
        assert "reason" in props

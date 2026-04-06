"""Contract verifier agent: confirms the uploaded document is a contract."""

from dataclasses import dataclass

from services.agents.base import AgentConfig, AgentRunner
from services.agents.messages import append_instructions, build_user_message

VERIFIER_TOOL = {
    "name": "verify_contract",
    "description": "Report whether the document is a contract or legal agreement.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "is_contract": {
                "type": "boolean",
                "description": "True if the document is a contract",
            },
            "reason": {
                "type": ["string", "null"],
                "description": "Explanation if not a contract",
            },
        },
        "required": ["is_contract", "reason"],
        "additionalProperties": False,
    },
}


def build_verifier_prompt(instructions: str | None = None) -> str:
    """Build the system prompt for the verifier agent."""
    prompt = (
        "You are a document classifier. Your only job is to determine if the provided "
        "document is a contract or legal agreement. Do not analyze its contents deeply.\n\n"
        "Call the verify_contract tool with your determination."
    )
    return append_instructions(prompt, instructions)


@dataclass
class VerifierResult:
    is_contract: bool
    reason: str | None


class VerifierAgent:
    def __init__(self, instructions: str | None = None):
        self.config = AgentConfig("verifier")
        self.instructions = instructions

    async def run(
        self, pdf_blob: bytes | None = None, text: str | None = None
    ) -> VerifierResult:
        async def handle_verify(input_data: dict) -> str:
            return "Verification recorded."

        runner = AgentRunner(
            config=self.config,
            tools=[VERIFIER_TOOL],
            tool_handlers={"verify_contract": handle_verify},
        )

        messages = build_user_message(pdf_blob, text)
        result = await runner.run(
            system=build_verifier_prompt(self.instructions),
            messages=messages,
            force_tool="verify_contract",
        )

        if "verify_contract" not in result.tool_results:
            raise RuntimeError(
                f"Verifier did not call verify_contract. "
                f"Stop reason: {result.stop_reason}, max_tokens_hit: {result.max_tokens_hit}"
            )

        tool_data = result.tool_results["verify_contract"]
        return VerifierResult(
            is_contract=tool_data["is_contract"],
            reason=tool_data.get("reason"),
        )

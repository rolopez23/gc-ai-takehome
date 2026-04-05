import base64
import json
import os
import re

from prompt import EvalErrorResponse, EvalSuccessResponse, build_system_prompt

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))


def _strip_fences(text: str) -> str:
    """Remove leading ```json and trailing ``` markdown fences."""
    stripped = text.strip()
    stripped = re.sub(r"^```json\s*", "", stripped)
    stripped = re.sub(r"```\s*$", "", stripped)
    return stripped.strip()


def build_messages(
    pdf_blob: bytes | None = None,
    text: str | None = None,
    instructions: str | None = None,
) -> dict:
    """Build the params dict for client.messages.create."""
    if pdf_blob is None and text is None:
        raise ValueError("Either pdf_blob or text must be provided")

    base: dict = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": ANTHROPIC_MAX_TOKENS,
        "system": build_system_prompt(instructions),
    }

    if pdf_blob is not None:
        base["messages"] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": base64.standard_b64encode(pdf_blob).decode(
                                "ascii"
                            ),
                        },
                    }
                ],
            }
        ]
    else:
        base["messages"] = [{"role": "user", "content": text}]

    return base


def parse_response(raw_text: str) -> tuple[str, dict]:
    """Parse Claude's raw text response into a typed result tuple."""
    cleaned = _strip_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        return ("parse_error", {"message": str(e)})

    # Try success schema first
    try:
        validated = EvalSuccessResponse.model_validate(data)
        return ("success", validated.model_dump())
    except Exception:
        pass

    # Try error schema
    try:
        validated = EvalErrorResponse.model_validate(data)
        return ("not_a_contract", {"reason": validated.reason})
    except Exception as e:
        return ("parse_error", {"message": str(e)})

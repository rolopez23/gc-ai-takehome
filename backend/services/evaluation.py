import base64
import json
import os
import re
from datetime import UTC, datetime

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from models import Contract, ContractReview, ReviewClause
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


EVAL_TIMEOUT = 90  # seconds


async def run_evaluation(review_id, contract: Contract, db: AsyncSession):
    """Run evaluation: call Anthropic, parse, persist results."""
    review = await db.get(ContractReview, review_id)
    review.status = "evaluating"
    await db.flush()

    try:
        # Eagerly load deferred blob columns to avoid sync-context greenlet errors
        await db.refresh(contract, attribute_names=["pdf_blob", "text"])
        params = build_messages(
            pdf_blob=contract.pdf_blob,
            text=contract.text,
            instructions=review.review_instructions,
        )

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(**params, timeout=EVAL_TIMEOUT)

        if message.stop_reason == "max_tokens":
            review.status = "failed"
            review.failure_message = "Contract too large to evaluate"
            review.completed_at = datetime.now(UTC)
            await db.commit()
            return

        content = message.content[0]
        if not content or content.type != "text":
            review.status = "failed"
            review.failure_message = "Unexpected response type from Claude"
            review.completed_at = datetime.now(UTC)
            await db.commit()
            return

        kind, data = parse_response(content.text)

        if kind == "success":
            review.status = "completed"
            review.overall_fairness = data["overall_fairness"]
            review.summary = data["summary"]
            review.call_to_action = data["call_to_action"]
            review.completed_at = datetime.now(UTC)
            for clause_data in data["clauses"]:
                clause = ReviewClause(
                    review_id=review_id,
                    section_number=clause_data["section_number"],
                    clause_type=clause_data["clause_type"],
                    purpose=clause_data["purpose"],
                    fairness=clause_data["fairness"],
                    market_standard=clause_data["market_standard"],
                    explanation=clause_data["explanation"],
                )
                db.add(clause)
            await db.commit()
            return

        if kind == "not_a_contract":
            review.status = "completed"
            review.overall_fairness = None
            review.summary = data["reason"]
            review.completed_at = datetime.now(UTC)
            await db.commit()
            return

        # parse_error
        review.status = "failed"
        review.failure_message = f"Invalid response from Claude: {data['message']}"
        review.completed_at = datetime.now(UTC)
        await db.commit()

    except anthropic.APITimeoutError:
        review.status = "failed"
        review.failure_message = "Evaluation timed out (90s)"
        review.completed_at = datetime.now(UTC)
        await db.commit()
    except anthropic.APIError as e:
        review.status = "failed"
        review.failure_message = f"Anthropic API error: {e}"
        review.completed_at = datetime.now(UTC)
        await db.commit()
    except Exception as e:
        review.status = "failed"
        review.failure_message = f"Evaluation failed: {e}"
        review.completed_at = datetime.now(UTC)
        await db.commit()

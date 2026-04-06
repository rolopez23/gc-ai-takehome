import base64
import json
import os
import re
import uuid
from datetime import UTC, datetime

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from database import AsyncSessionLocal
from models import Contract, ContractReview, ReviewClause
from prompt import EvalErrorResponse, EvalSuccessResponse, build_system_prompt

def _get_api_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "")

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))
EVAL_TIMEOUT = 90


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    stripped = re.sub(r"^```json\s*", "", stripped)
    stripped = re.sub(r"```\s*$", "", stripped)
    return stripped.strip()


def build_messages(
    pdf_blob: bytes | None = None,
    text: str | None = None,
    instructions: str | None = None,
) -> dict:
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
                            "data": base64.standard_b64encode(pdf_blob).decode("ascii"),
                        },
                    }
                ],
            }
        ]
    else:
        base["messages"] = [{"role": "user", "content": text}]

    return base


def parse_response(raw_text: str) -> tuple[str, dict]:
    cleaned = _strip_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        return ("parse_error", {"message": str(e)})

    try:
        validated = EvalSuccessResponse.model_validate(data)
        return ("success", validated.model_dump())
    except Exception:
        pass

    try:
        validated = EvalErrorResponse.model_validate(data)
        return ("not_a_contract", {"reason": validated.reason})
    except Exception as e:
        return ("parse_error", {"message": str(e)})


async def _fail_review(review: ContractReview, message: str, db: AsyncSession):
    review.status = "failed"
    review.failure_message = message
    review.completed_at = datetime.now(UTC)
    await db.commit()


async def run_evaluation(review_id, contract: Contract, db: AsyncSession):
    review = await db.get(ContractReview, review_id)
    if not review:
        return
    review.status = "evaluating"
    await db.commit()

    try:
        await db.refresh(contract, attribute_names=["pdf_blob", "text"])
        params = build_messages(
            pdf_blob=contract.pdf_blob,
            text=contract.text,
            instructions=review.review_instructions,
        )

        client = anthropic.AsyncAnthropic(api_key=_get_api_key())
        message = await client.messages.create(**params, timeout=EVAL_TIMEOUT)

        if message.stop_reason == "max_tokens":
            await _fail_review(review, "Contract too large to evaluate", db)
            return

        if not message.content:
            await _fail_review(review, "Empty response from Claude", db)
            return

        content = message.content[0]
        if content.type != "text":
            await _fail_review(review, "Unexpected response type from Claude", db)
            return

        kind, data = parse_response(content.text)

        if kind == "success":
            review.status = "completed"
            review.overall_fairness = data["overall_fairness"]
            review.summary = data["summary"]
            review.call_to_action = data["call_to_action"]
            review.completed_at = datetime.now(UTC)
            for clause_data in data["clauses"]:
                db.add(ReviewClause(
                    review_id=review_id,
                    section_number=clause_data["section_number"],
                    clause_type=clause_data["clause_type"],
                    purpose=clause_data["purpose"],
                    fairness=clause_data["fairness"],
                    market_standard=clause_data["market_standard"],
                    explanation=clause_data["explanation"],
                ))
            await db.commit()
            return

        if kind == "not_a_contract":
            review.status = "completed"
            review.overall_fairness = None
            review.summary = data["reason"]
            review.completed_at = datetime.now(UTC)
            await db.commit()
            return

        await _fail_review(review, f"Invalid response from Claude: {data['message']}", db)

    except anthropic.APITimeoutError:
        await _fail_review(review, "Evaluation timed out (90s)", db)
    except anthropic.APIError as e:
        await _fail_review(review, f"Anthropic API error: {e}", db)
    except Exception as e:
        await _fail_review(review, f"Evaluation failed: {e}", db)


async def evaluate_contract_task(review_id: uuid.UUID, contract_id: uuid.UUID):
    """Background task: set status, then evaluate. Conversion already done at upload."""
    async with AsyncSessionLocal() as db:
        try:
            # Only load blobs needed for evaluation (pdf_blob for PDF/DOC/DOCX, text for TXT)
            contract = await db.get(
                Contract,
                contract_id,
                options=[undefer(Contract.pdf_blob)],
            )
            review = await db.get(ContractReview, review_id)

            if not contract or not review:
                return

            await run_evaluation(review.id, contract, db)

        except Exception as e:
            review = await db.get(ContractReview, review_id)
            if review and review.status != "failed":
                await _fail_review(review, f"Pipeline error: {e}", db)

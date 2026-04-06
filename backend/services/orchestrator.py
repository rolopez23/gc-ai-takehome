"""Pipeline orchestrator: verify -> split -> persist -> evaluate -> headline -> synthesize."""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from dataclasses import asdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import undefer

from database import AsyncSessionLocal
from models import Contract, ContractReview, ReviewClause
from services.agents.evaluator import EvaluatorAgent, EvaluatorResult
from services.agents.headline import HeadlineAgent
from services.agents.splitter import SplitterAgent, detect_absent_checks
from services.agents.verifier import VerifierAgent
from services.streaming import EventEmitter
from services.synthesis import synthesize

logger = logging.getLogger(__name__)

MAX_CONCURRENT_EVALUATORS = 7
FAILURE_THRESHOLD = 0.10


class PipelineOrchestrator:
    def __init__(
        self,
        review_id: uuid.UUID,
        contract_id: uuid.UUID,
        instructions: str | None = None,
    ):
        self.review_id = review_id
        self.contract_id = contract_id
        self.instructions = instructions
        self.emitter = EventEmitter()

    async def _set_review_status(self, status: str, **kwargs) -> None:
        """Update review status and optional fields."""
        async with AsyncSessionLocal() as db:
            review = await db.get(ContractReview, self.review_id)
            if review is None:
                logger.error("Review %s not found during status update", self.review_id)
                return
            review.status = status
            for key, value in kwargs.items():
                setattr(review, key, value)
            await db.commit()

    async def _load_contract(self) -> tuple[bytes | None, str | None]:
        """Load contract data (pdf_blob and text) from DB."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Contract)
                .where(Contract.id == self.contract_id)
                .options(undefer(Contract.pdf_blob))
            )
            contract = result.scalar_one_or_none()
            if contract is None:
                raise RuntimeError(f"Contract {self.contract_id} not found")
            return contract.pdf_blob, contract.text

    async def run(self) -> AsyncGenerator[str, None]:
        """Run the full pipeline, yielding NDJSON event strings."""
        yield self.emitter.started(str(self.review_id))

        try:
            # Load contract data
            pdf_blob, text = await self._load_contract()

            # --- Stage 1: Verify ---
            yield self.emitter.token("status", "Verifying document...")
            await self._set_review_status("verifying")

            verifier = VerifierAgent(instructions=self.instructions)
            verify_result = await verifier.run(pdf_blob=pdf_blob, text=text)
            yield self.emitter.verifying(verify_result.is_contract)

            if not verify_result.is_contract:
                await self._set_review_status(
                    "rejected",
                    summary=verify_result.reason,
                    completed_at=datetime.now(UTC),
                )
                yield self.emitter.rejected(verify_result.reason)
                return

            # --- Stage 2: Split ---
            yield self.emitter.token("status", "Splitting clauses...")

            splitter = SplitterAgent()
            split_result = await splitter.run(
                pdf_blob=pdf_blob, text=text, instructions=self.instructions
            )
            agreement_type = split_result.agreement_type

            await self._set_review_status("splitting", agreement_type=agreement_type)

            # Detect absent checks
            tagged_checks: set[str] = set()
            for clause in split_result.clauses:
                tagged_checks.update(clause.relevant_checks)
            absent_clauses = detect_absent_checks(agreement_type, tagged_checks)

            # Build section_number -> text map for cross-reference resolution
            section_text_map: dict[str, str] = {}
            for clause in split_result.clauses:
                if clause.section_number in section_text_map:
                    logger.warning(
                        "Duplicate section_number '%s' in splitter output — "
                        "cross-reference resolution will use the last occurrence",
                        clause.section_number,
                    )
                section_text_map[clause.section_number] = clause.text

            # Persist all clauses (real + synthetic) to DB
            clause_rows: list[ReviewClause] = []
            real_clause_data: list[tuple[ReviewClause, dict]] = []

            async with AsyncSessionLocal() as db:
                # Real clauses
                for clause in split_result.clauses:
                    row = ReviewClause(
                        review_id=self.review_id,
                        section_number=clause.section_number,
                        clause_type=clause.clause_type,
                        contract_language=clause.text,
                        relevant_checks=clause.relevant_checks,
                        cross_references=clause.cross_references,
                        is_cycle=clause.is_cycle,
                        is_synthetic=False,
                        status="pending",
                    )
                    db.add(row)
                    clause_rows.append(row)

                    real_clause_data.append((row, asdict(clause)))

                # Synthetic absent clauses
                synthetic_rows: list[ReviewClause] = []
                for ac in absent_clauses:
                    row = ReviewClause(
                        review_id=self.review_id,
                        section_number=ac.section_number,
                        clause_type=ac.clause_type,
                        contract_language=ac.text,
                        relevant_checks=ac.relevant_checks,
                        cross_references=ac.cross_references,
                        is_cycle=ac.is_cycle,
                        is_synthetic=True,
                        status="evaluated",
                        severity=ac.severity,
                        fairness=ac.fairness,
                        playbook_status="ABSENT",
                    )
                    db.add(row)
                    clause_rows.append(row)
                    synthetic_rows.append(row)

                await db.commit()

            total_clause_count = len(split_result.clauses) + len(absent_clauses)
            yield self.emitter.splitting(agreement_type, total_clause_count)

            # --- Stage 3: Evaluate ---
            yield self.emitter.token("status", "Evaluating clauses...")
            await self._set_review_status("evaluating")

            semaphore = asyncio.Semaphore(MAX_CONCURRENT_EVALUATORS)

            async def evaluate_clause(
                clause_row: ReviewClause,
                clause_data: dict,
                cross_ref_text: dict[str, str] | None,
            ) -> tuple[str, uuid.UUID, EvaluatorResult | str]:
                async with semaphore:
                    evaluator = EvaluatorAgent(agreement_type, self.instructions)
                    try:
                        result = await evaluator.run(clause_data, cross_ref_text)
                        async with AsyncSessionLocal() as db:
                            row = await db.get(ReviewClause, clause_row.id)
                            row.status = "evaluated"
                            row.severity = result.severity
                            row.fairness = result.fairness
                            row.playbook_status = result.playbook_status
                            row.playbook_position = result.playbook_position
                            row.contract_language = result.contract_language
                            row.finding = result.finding
                            row.recommended_redline = result.recommended_redline
                            row.purpose = result.purpose
                            row.market_standard = result.market_standard
                            row.explanation = result.explanation
                            await db.commit()
                        return ("ok", clause_row.id, result)
                    except Exception as e:
                        async with AsyncSessionLocal() as db:
                            row = await db.get(ReviewClause, clause_row.id)
                            row.status = "error"
                            await db.commit()
                        return ("error", clause_row.id, str(e))

            # Build tasks for real (non-synthetic) clauses only
            tasks = []
            for clause_row, clause_data in real_clause_data:
                # Resolve depth-1 cross-references
                cross_refs = clause_data.get("cross_references", [])
                cross_ref_text = None
                if cross_refs:
                    resolved = {}
                    for ref in cross_refs:
                        if ref in section_text_map:
                            resolved[ref] = section_text_map[ref]
                    if resolved:
                        cross_ref_text = resolved

                tasks.append(evaluate_clause(clause_row, clause_data, cross_ref_text))

            # Run evaluators and stream results as they complete
            failed_count = 0
            evaluated_count = 0
            real_count = len(real_clause_data)
            all_clause_results: list[dict] = []
            row_id_to_clause = {cr.id: cd for cr, cd in real_clause_data}

            for coro in asyncio.as_completed(tasks):
                status, row_id, result_or_error = await coro
                evaluated_count += 1
                yield self.emitter.token(
                    "status", f"Evaluated clause {evaluated_count} of {real_count}..."
                )
                if status == "ok":
                    result_dict = asdict(result_or_error)
                    result_dict["status"] = "evaluated"
                    all_clause_results.append(result_dict)
                    yield self.emitter.clause_evaluated(result_dict)
                else:
                    failed_count += 1
                    cd = row_id_to_clause[row_id]
                    yield self.emitter.clause_error(
                        cd["section_number"],
                        cd["clause_type"],
                        str(result_or_error),
                    )
                    all_clause_results.append(
                        {
                            "section_number": cd["section_number"],
                            "clause_type": cd["clause_type"],
                            "status": "error",
                        }
                    )

            # Emit clause_evaluated for synthetic absent clauses (already rated)
            for srow in synthetic_rows:
                synthetic_dict = {
                    "section_number": srow.section_number,
                    "clause_type": srow.clause_type,
                    "status": "evaluated",
                    "severity": srow.severity,
                    "fairness": srow.fairness,
                    "playbook_status": "ABSENT",
                    "is_synthetic": True,
                }
                all_clause_results.append(synthetic_dict)
                yield self.emitter.clause_evaluated(synthetic_dict)

            # --- Stage 4: Failure check ---
            real_clause_count = len(real_clause_data)
            if (
                real_clause_count > 0
                and failed_count / real_clause_count > FAILURE_THRESHOLD
            ):
                fail_msg = f"evaluators failed ({failed_count}/{real_clause_count} clauses, >{FAILURE_THRESHOLD:.0%} threshold)"
                await self._set_review_status(
                    "failed",
                    failure_message=fail_msg,
                    completed_at=datetime.now(UTC),
                )
                yield self.emitter.failed(fail_msg)
                return

            # --- Stage 5: Headline ---
            yield self.emitter.token("status", "Generating summary...")

            headline_agent = HeadlineAgent(instructions=self.instructions)
            # Filter to only successfully evaluated clauses for headline
            evaluated_clauses = [
                c for c in all_clause_results if c.get("status") == "evaluated"
            ]
            absent_count = len(absent_clauses)

            headline = await headline_agent.run(
                agreement_type=agreement_type,
                clauses=evaluated_clauses,
                failed_clause_count=failed_count,
                absent_clause_count=absent_count,
            )

            yield self.emitter.replace("summary", headline.summary)
            yield self.emitter.replace("call_to_action", headline.call_to_action)

            # --- Stage 6: Synthesize ---
            final = synthesize(agreement_type, all_clause_results, headline)
            yield self.emitter.completed(final)

            # Persist final result
            await self._set_review_status(
                "completed",
                overall_fairness=final["overall_fairness"],
                summary=final["summary"],
                call_to_action=final["call_to_action"],
                completed_at=datetime.now(UTC),
            )

        except Exception as e:
            logger.exception("Pipeline failed with unexpected error")
            # Store full error for debugging; send sanitized message to client
            error_detail = str(e)
            client_message = (
                "An error occurred during contract evaluation. Please try again."
            )
            try:
                await self._set_review_status(
                    "failed",
                    failure_message=error_detail,
                    completed_at=datetime.now(UTC),
                )
            except Exception:
                logger.exception("Failed to update review status after error")
            yield self.emitter.failed(client_message)

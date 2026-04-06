"""Tests for NDJSON event emitter and pipeline orchestrator."""

import asyncio
import json
import uuid
from dataclasses import asdict
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import Base
from models import Contract, ContractReview, ReviewClause
from services.agents.evaluator import EvaluatorResult
from services.agents.headline import HeadlineResult
from services.agents.splitter import AbsentClause, SplitterClause, SplitterResult
from services.agents.verifier import VerifierResult

# ---------------------------------------------------------------------------
# Test DB setup (separate from conftest to avoid coupling)
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite://"  # in-memory
_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSession = async_sessionmaker(_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def _orch_db():
    """Create/drop tables for each test."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_splitter_clauses(n: int) -> list[SplitterClause]:
    return [
        SplitterClause(
            section_number=f"{i + 1}.0",
            clause_type=f"Clause Type {i + 1}",
            text=f"Text of clause {i + 1}.",
            relevant_checks=[f"Check {i + 1}"],
            cross_references=[],
            is_cycle=False,
        )
        for i in range(n)
    ]


def _make_evaluator_result(section_number: str, clause_type: str) -> EvaluatorResult:
    return EvaluatorResult(
        section_number=section_number,
        clause_type=clause_type,
        severity=5,
        playbook_status="TRIGGERED",
        playbook_position="Some position",
        contract_language="Some language",
        finding="Finding text",
        recommended_redline="Redline text",
        fairness="fair",
        purpose="Purpose text",
        market_standard="Standard text",
        explanation="Explanation text",
    )


def _make_headline_result() -> HeadlineResult:
    return HeadlineResult(
        summary="Executive summary text.",
        call_to_action=["Negotiate LoL cap", "Review IP clauses"],
    )


async def _seed_contract_and_review(
    instructions: str | None = None,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Insert a Contract and ContractReview, return (contract_id, review_id)."""
    contract_id = uuid.uuid4()
    review_id = uuid.uuid4()
    async with _TestSession() as db:
        contract = Contract(
            id=contract_id,
            name="test.pdf",
            upload_type="pdf",
            original_blob=b"original",
            pdf_blob=b"fakepdf",
            text="Contract text here.",
        )
        db.add(contract)
        review = ContractReview(
            id=review_id,
            contract_id=contract_id,
            status="pending",
            review_instructions=instructions,
        )
        db.add(review)
        await db.commit()
    return contract_id, review_id


async def _collect_events(orchestrator) -> list[dict]:
    """Run the orchestrator and collect all emitted NDJSON events."""
    events = []
    async for line in orchestrator.run():
        events.append(json.loads(line))
    return events


def _find_event(events: list[dict], event_type: str) -> dict | None:
    for e in events:
        if e["event"] == event_type:
            return e
    return None


def _find_events(events: list[dict], event_type: str) -> list[dict]:
    return [e for e in events if e["event"] == event_type]


# ---------------------------------------------------------------------------
# Cycle 1: NDJSON Event Emitter tests
# ---------------------------------------------------------------------------


class TestEventEmitter:
    """Tests for the EventEmitter class."""

    def _make_emitter(self):
        from services.streaming import EventEmitter

        return EventEmitter()

    def test_emitter_started_event(self):
        emitter = self._make_emitter()
        review_id = str(uuid.uuid4())
        line = emitter.started(review_id)
        data = json.loads(line)
        assert data["event"] == "started"
        assert data["review_id"] == review_id
        assert data["summary"] == ""
        assert data["call_to_action"] == []

    def test_emitter_token_event(self):
        emitter = self._make_emitter()
        line = emitter.token("status", "Reading...")
        data = json.loads(line)
        assert data == {"event": "token", "field": "status", "text": "Reading..."}

    def test_emitter_verifying_event(self):
        emitter = self._make_emitter()
        line = emitter.verifying(True)
        data = json.loads(line)
        assert data == {"event": "verifying", "is_contract": True}

    def test_emitter_splitting_event(self):
        emitter = self._make_emitter()
        line = emitter.splitting("SaaS MSA", 14)
        data = json.loads(line)
        assert data == {
            "event": "splitting",
            "agreement_type": "SaaS MSA",
            "clause_count": 14,
        }

    def test_emitter_clause_evaluated_event(self):
        emitter = self._make_emitter()
        clause_data = {"section_number": "4.2", "fairness": "fair"}
        line = emitter.clause_evaluated(clause_data)
        data = json.loads(line)
        assert data["event"] == "clause_evaluated"
        assert data["clause"] == clause_data

    def test_emitter_clause_error_event(self):
        emitter = self._make_emitter()
        line = emitter.clause_error("4.2", "LoL", "timeout")
        data = json.loads(line)
        assert data == {
            "event": "clause_error",
            "section_number": "4.2",
            "clause_type": "LoL",
            "error": "timeout",
        }

    def test_emitter_replace_event_string(self):
        emitter = self._make_emitter()
        line = emitter.replace("summary", "Final text")
        data = json.loads(line)
        assert data == {"event": "replace", "field": "summary", "text": "Final text"}

    def test_emitter_replace_event_list(self):
        emitter = self._make_emitter()
        line = emitter.replace("call_to_action", ["Step 1", "Step 2"])
        data = json.loads(line)
        assert data == {
            "event": "replace",
            "field": "call_to_action",
            "value": ["Step 1", "Step 2"],
        }

    def test_emitter_rejected_event(self):
        emitter = self._make_emitter()
        line = emitter.rejected("Not a contract")
        data = json.loads(line)
        assert data == {"event": "rejected", "reason": "Not a contract"}

    def test_emitter_failed_event(self):
        emitter = self._make_emitter()
        line = emitter.failed("evaluators failed")
        data = json.loads(line)
        assert data == {"event": "failed", "reason": "evaluators failed"}

    def test_emitter_completed_event(self):
        emitter = self._make_emitter()
        result = {"overall_fairness": "fair", "clauses": []}
        line = emitter.completed(result)
        data = json.loads(line)
        assert data == {"event": "completed", "result": result}

    def test_emitter_outputs_ndjson(self):
        """Each event is a single JSON line ending with newline."""
        emitter = self._make_emitter()
        lines = [
            emitter.started(str(uuid.uuid4())),
            emitter.token("status", "test"),
            emitter.verifying(True),
            emitter.splitting("NDA", 3),
            emitter.clause_evaluated({"section_number": "1"}),
            emitter.rejected("nope"),
            emitter.failed("oops"),
            emitter.completed({"result": True}),
        ]
        for line in lines:
            assert line.endswith("\n"), f"Line does not end with newline: {line!r}"
            assert line.count("\n") == 1, f"Line has multiple newlines: {line!r}"
            json.loads(line)  # Must be valid JSON

    def test_emitter_returns_valid_json(self):
        """Emitter returns valid JSON strings."""
        emitter = self._make_emitter()
        line = emitter.started(str(uuid.uuid4()))
        import json

        parsed = json.loads(line.strip())
        assert parsed["event"] == "started"


# ---------------------------------------------------------------------------
# Cycle 2: Orchestrator verify stage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestOrchestratorVerifyStage:
    """Tests for the orchestrator verification stage."""

    async def _make_orchestrator(self, review_id, contract_id, instructions=None):
        from services.orchestrator import PipelineOrchestrator

        return PipelineOrchestrator(review_id, contract_id, instructions)

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    async def test_orchestrator_rejects_non_contract(
        self, mock_headline, mock_evaluator, mock_splitter, mock_verifier
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=False, reason="This is a recipe")
        )

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        rejected = _find_event(events, "rejected")
        assert rejected is not None
        assert rejected["reason"] == "This is a recipe"

        # Review status should be "rejected"
        async with _TestSession() as db:
            review = await db.get(ContractReview, review_id)
            assert review.status == "rejected"

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_passes_contract(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="SaaS MSA", clauses=_make_splitter_clauses(2)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "SaaS MSA",
            "summary": "Summary",
            "call_to_action": ["Step 1"],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        # Should not have rejected event
        assert _find_event(events, "rejected") is None
        # Should have completed event
        assert _find_event(events, "completed") is not None

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    async def test_orchestrator_emits_verifying_event(
        self, mock_headline, mock_evaluator, mock_splitter, mock_verifier
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=False, reason="Not a contract")
        )

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        verifying = _find_event(events, "verifying")
        assert verifying is not None
        assert verifying["is_contract"] is False

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    async def test_orchestrator_sets_status_verifying(
        self, mock_headline, mock_evaluator, mock_splitter, mock_verifier
    ):
        """review.status transitions to 'verifying' before the verifier runs."""
        statuses_seen = []

        original_run = AsyncMock(
            return_value=VerifierResult(is_contract=False, reason="Nope")
        )

        async def capture_status(*args, **kwargs):
            async with _TestSession() as db:
                review = await db.get(ContractReview, review_id)
                statuses_seen.append(review.status)
            return await original_run(*args, **kwargs)

        mock_verifier.return_value.run = capture_status

        contract_id, review_id = await _seed_contract_and_review()
        orch = await self._make_orchestrator(review_id, contract_id)
        await _collect_events(orch)

        assert "verifying" in statuses_seen


# ---------------------------------------------------------------------------
# Cycle 3: Orchestrator split and persist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestOrchestratorSplitAndPersist:
    async def _make_orchestrator(self, review_id, contract_id, instructions=None):
        from services.orchestrator import PipelineOrchestrator

        return PipelineOrchestrator(review_id, contract_id, instructions)

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_splits_contract(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        clauses = _make_splitter_clauses(5)
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(agreement_type="NDA", clauses=clauses)
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        splitting = _find_event(events, "splitting")
        assert splitting is not None
        assert splitting["agreement_type"] == "NDA"
        assert splitting["clause_count"] == 5

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_persists_clauses(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        clauses = _make_splitter_clauses(5)
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(agreement_type="NDA", clauses=clauses)
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        await _collect_events(orch)

        async with _TestSession() as db:
            result = await db.execute(
                select(ReviewClause).where(ReviewClause.review_id == review_id)
            )
            rows = result.scalars().all()
            assert len(rows) == 5
            for row in rows:
                assert row.is_synthetic is False

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_persists_agreement_type(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="DPA", clauses=_make_splitter_clauses(1)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "DPA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        await _collect_events(orch)

        async with _TestSession() as db:
            review = await db.get(ContractReview, review_id)
            assert review.agreement_type == "DPA"

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_sets_status_splitting(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )

        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(1)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        # Verify splitting event was emitted with agreement_type
        split_event = _find_event(events, "splitting")
        assert split_event is not None
        assert split_event["agreement_type"] == "NDA"

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    async def test_orchestrator_persists_absent_clauses(
        self,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="SaaS MSA", clauses=_make_splitter_clauses(3)
            )
        )
        # 2 absent clauses
        absent = [
            AbsentClause(
                section_number="absent-1",
                clause_type="Missing Check A",
                text="",
                relevant_checks=["Missing Check A"],
                cross_references=[],
                is_cycle=False,
                is_synthetic=True,
                severity=8,
                fairness="dealbreaker",
            ),
            AbsentClause(
                section_number="absent-2",
                clause_type="Missing Check B",
                text="",
                relevant_checks=["Missing Check B"],
                cross_references=[],
                is_cycle=False,
                is_synthetic=True,
                severity=5,
                fairness="non-standard",
            ),
        ]

        with patch("services.orchestrator.detect_absent_checks", return_value=absent):
            mock_evaluator.return_value.run = AsyncMock(
                side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                    clause["section_number"], clause["clause_type"]
                )
            )
            mock_headline.return_value.run = AsyncMock(
                return_value=_make_headline_result()
            )
            mock_synthesize.return_value = {
                "overall_fairness": "fair",
                "agreement_type": "SaaS MSA",
                "summary": "S",
                "call_to_action": [],
                "clauses": [],
            }

            orch = await self._make_orchestrator(review_id, contract_id)
            await _collect_events(orch)

        async with _TestSession() as db:
            result = await db.execute(
                select(ReviewClause).where(ReviewClause.review_id == review_id)
            )
            rows = result.scalars().all()
            assert len(rows) == 5  # 3 real + 2 synthetic
            synthetic = [r for r in rows if r.is_synthetic]
            assert len(synthetic) == 2
            assert synthetic[0].severity == 8
            assert synthetic[0].fairness == "dealbreaker"


# ---------------------------------------------------------------------------
# Cycle 4: Orchestrator parallel evaluation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestOrchestratorParallelEvaluation:
    async def _make_orchestrator(self, review_id, contract_id, instructions=None):
        from services.orchestrator import PipelineOrchestrator

        return PipelineOrchestrator(review_id, contract_id, instructions)

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_evaluates_clauses_parallel(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(5)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        await _collect_events(orch)

        async with _TestSession() as db:
            result = await db.execute(
                select(ReviewClause).where(ReviewClause.review_id == review_id)
            )
            rows = result.scalars().all()
            evaluated = [r for r in rows if r.status == "evaluated"]
            assert len(evaluated) == 5

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_max_7_concurrency(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(10)
            )
        )

        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def tracked_eval(clause, cross_ref_text=None):
            nonlocal max_concurrent, current_concurrent
            async with lock:
                current_concurrent += 1
                if current_concurrent > max_concurrent:
                    max_concurrent = current_concurrent
            await asyncio.sleep(0.01)
            async with lock:
                current_concurrent -= 1
            return _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )

        mock_evaluator.return_value.run = tracked_eval
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        await _collect_events(orch)

        assert max_concurrent <= 7

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_emits_clause_evaluated(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(3)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        clause_events = _find_events(events, "clause_evaluated")
        assert len(clause_events) == 3

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_handles_evaluator_failure(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(5)
            )
        )

        call_count = 0

        async def sometimes_fail(clause, cross_ref_text=None):
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                raise RuntimeError("Evaluator exploded")
            return _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )

        mock_evaluator.return_value.run = sometimes_fail
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        # 1 failure, 4 successes
        clause_errors = _find_events(events, "clause_error")
        assert len(clause_errors) == 1
        clause_evals = _find_events(events, "clause_evaluated")
        assert len(clause_evals) == 4

        # Error clause in DB
        async with _TestSession() as db:
            result = await db.execute(
                select(ReviewClause).where(
                    ReviewClause.review_id == review_id,
                    ReviewClause.status == "error",
                )
            )
            error_rows = result.scalars().all()
            assert len(error_rows) == 1

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    async def test_orchestrator_skips_synthetic_clauses(
        self,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(2)
            )
        )
        absent = [
            AbsentClause(
                section_number="absent-1",
                clause_type="Missing",
                text="",
                relevant_checks=["Missing"],
                cross_references=[],
                is_cycle=False,
                is_synthetic=True,
                severity=5,
                fairness="non-standard",
            )
        ]
        with patch("services.orchestrator.detect_absent_checks", return_value=absent):
            eval_calls = []

            async def track_eval(clause, cross_ref_text=None):
                eval_calls.append(clause["section_number"])
                return _make_evaluator_result(
                    clause["section_number"], clause["clause_type"]
                )

            mock_evaluator.return_value.run = track_eval
            mock_headline.return_value.run = AsyncMock(
                return_value=_make_headline_result()
            )
            mock_synthesize.return_value = {
                "overall_fairness": "fair",
                "agreement_type": "NDA",
                "summary": "S",
                "call_to_action": [],
                "clauses": [],
            }

            orch = await self._make_orchestrator(review_id, contract_id)
            events = await _collect_events(orch)

        # Evaluator called for 2 real clauses, NOT the synthetic one
        assert len(eval_calls) == 2
        assert "absent-1" not in eval_calls

        # Synthetic clauses are NOT emitted as clause_evaluated events —
        # they are included in the completed result's absent_clauses list
        clause_events = _find_events(events, "clause_evaluated")
        synthetic_events = [
            e for e in clause_events if e["clause"].get("section_number") == "absent-1"
        ]
        assert len(synthetic_events) == 0

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_passes_cross_ref_text(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        # Clause 2 references clause 1
        clauses = [
            SplitterClause(
                section_number="1.0",
                clause_type="Definitions",
                text="Definitions text.",
                relevant_checks=["Check 1"],
                cross_references=[],
                is_cycle=False,
            ),
            SplitterClause(
                section_number="2.0",
                clause_type="Liability",
                text="Liability text.",
                relevant_checks=["Check 2"],
                cross_references=["1.0"],
                is_cycle=False,
            ),
        ]
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(agreement_type="NDA", clauses=clauses)
        )

        cross_ref_received = {}

        async def capture_xref(clause, cross_ref_text=None):
            cross_ref_received[clause["section_number"]] = cross_ref_text
            return _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )

        mock_evaluator.return_value.run = capture_xref
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        await _collect_events(orch)

        # Clause 2.0 should have received cross-ref text for 1.0
        assert cross_ref_received.get("2.0") == {"1.0": "Definitions text."}
        # Clause 1.0 should have no cross-refs
        assert cross_ref_received.get("1.0") is None


# ---------------------------------------------------------------------------
# Cycle 5: Failure threshold
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestOrchestratorFailureThreshold:
    async def _make_orchestrator(self, review_id, contract_id, instructions=None):
        from services.orchestrator import PipelineOrchestrator

        return PipelineOrchestrator(review_id, contract_id, instructions)

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_fails_on_10_percent(
        self,
        mock_absent,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(10)
            )
        )

        call_count = 0

        async def fail_two(clause, cross_ref_text=None):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("Boom")
            return _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )

        mock_evaluator.return_value.run = fail_two
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        failed = _find_event(events, "failed")
        assert failed is not None
        assert "10%" in failed["reason"] or "failure rate" in failed["reason"]

        async with _TestSession() as db:
            review = await db.get(ContractReview, review_id)
            assert review.status == "failed"

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_succeeds_under_threshold(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(10)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        assert _find_event(events, "failed") is None
        assert _find_event(events, "completed") is not None

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    async def test_orchestrator_threshold_ignores_synthetic(
        self,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(5)
            )
        )
        absent = [
            AbsentClause(
                section_number=f"absent-{i}",
                clause_type=f"Missing {i}",
                text="",
                relevant_checks=[],
                cross_references=[],
                is_cycle=False,
                is_synthetic=True,
                severity=5,
                fairness="non-standard",
            )
            for i in range(5)
        ]
        with patch("services.orchestrator.detect_absent_checks", return_value=absent):
            mock_evaluator.return_value.run = AsyncMock(
                side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                    clause["section_number"], clause["clause_type"]
                )
            )
            mock_headline.return_value.run = AsyncMock(
                return_value=_make_headline_result()
            )
            mock_synthesize.return_value = {
                "overall_fairness": "fair",
                "agreement_type": "NDA",
                "summary": "S",
                "call_to_action": [],
                "clauses": [],
            }

            orch = await self._make_orchestrator(review_id, contract_id)
            events = await _collect_events(orch)

        # 5 real + 5 synthetic, 0 failures -> should succeed
        assert _find_event(events, "failed") is None
        assert _find_event(events, "completed") is not None

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_emits_failed_event(
        self,
        mock_absent,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(5)
            )
        )

        async def always_fail(clause, cross_ref_text=None):
            raise RuntimeError("All fail")

        mock_evaluator.return_value.run = always_fail

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        failed = _find_event(events, "failed")
        assert failed is not None


# ---------------------------------------------------------------------------
# Cycle 6: Headline and synthesis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestOrchestratorHeadlineAndSynthesis:
    async def _make_orchestrator(self, review_id, contract_id, instructions=None):
        from services.orchestrator import PipelineOrchestrator

        return PipelineOrchestrator(review_id, contract_id, instructions)

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_runs_headline(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(2)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "Executive summary text.",
            "call_to_action": ["Negotiate LoL cap", "Review IP clauses"],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        replace_events = _find_events(events, "replace")
        summary_replace = [e for e in replace_events if e["field"] == "summary"]
        cta_replace = [e for e in replace_events if e["field"] == "call_to_action"]
        assert len(summary_replace) == 1
        assert summary_replace[0]["text"] == "Executive summary text."
        assert len(cta_replace) == 1
        assert cta_replace[0]["value"] == ["Negotiate LoL cap", "Review IP clauses"]

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_emits_status_during_headline(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(1)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "NDA",
            "summary": "S",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        token_events = _find_events(events, "token")
        generating = [e for e in token_events if "Generating summary" in e["text"]]
        assert len(generating) >= 1

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_runs_synthesis(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(1)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        synth_result = {
            "overall_fairness": "non-standard",
            "agreement_type": "NDA",
            "summary": "Summary",
            "call_to_action": ["Step 1"],
            "clauses": [],
        }
        mock_synthesize.return_value = synth_result

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        completed = _find_event(events, "completed")
        assert completed is not None
        assert completed["result"]["overall_fairness"] == "non-standard"

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_orchestrator_persists_final_result(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="NDA", clauses=_make_splitter_clauses(1)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "dealbreaker",
            "agreement_type": "NDA",
            "summary": "Final summary",
            "call_to_action": ["Action 1"],
            "clauses": [],
        }

        orch = await self._make_orchestrator(review_id, contract_id)
        await _collect_events(orch)

        async with _TestSession() as db:
            review = await db.get(ContractReview, review_id)
            assert review.status == "completed"
            assert review.overall_fairness == "dealbreaker"
            assert review.summary == "Final summary"
            assert review.call_to_action == ["Action 1"]
            assert review.completed_at is not None


# ---------------------------------------------------------------------------
# Full happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestOrchestratorFullPipeline:
    async def _make_orchestrator(self, review_id, contract_id, instructions=None):
        from services.orchestrator import PipelineOrchestrator

        return PipelineOrchestrator(review_id, contract_id, instructions)

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    @patch("services.orchestrator.synthesize")
    @patch("services.orchestrator.detect_absent_checks", return_value=[])
    async def test_full_happy_path(
        self,
        mock_absent,
        mock_synthesize,
        mock_headline,
        mock_evaluator,
        mock_splitter,
        mock_verifier,
    ):
        """Full pipeline: verify -> split -> evaluate -> headline -> synthesis -> completed."""
        contract_id, review_id = await _seed_contract_and_review(
            instructions="Focus on IP clauses"
        )
        mock_verifier.return_value.run = AsyncMock(
            return_value=VerifierResult(is_contract=True, reason=None)
        )
        mock_splitter.return_value.run = AsyncMock(
            return_value=SplitterResult(
                agreement_type="SaaS MSA", clauses=_make_splitter_clauses(3)
            )
        )
        mock_evaluator.return_value.run = AsyncMock(
            side_effect=lambda clause, cross_ref_text=None: _make_evaluator_result(
                clause["section_number"], clause["clause_type"]
            )
        )
        mock_headline.return_value.run = AsyncMock(return_value=_make_headline_result())
        mock_synthesize.return_value = {
            "overall_fairness": "fair",
            "agreement_type": "SaaS MSA",
            "summary": "All good",
            "call_to_action": [],
            "clauses": [],
        }

        orch = await self._make_orchestrator(
            review_id, contract_id, instructions="Focus on IP clauses"
        )
        events = await _collect_events(orch)

        event_types = [e["event"] for e in events]
        assert "started" in event_types
        assert "verifying" in event_types
        assert "splitting" in event_types
        assert "clause_evaluated" in event_types
        assert "completed" in event_types

        # DB state
        async with _TestSession() as db:
            review = await db.get(ContractReview, review_id)
            assert review.status == "completed"
            result = await db.execute(
                select(ReviewClause).where(ReviewClause.review_id == review_id)
            )
            rows = result.scalars().all()
            assert len(rows) == 3

    @patch("services.orchestrator.AsyncSessionLocal", _TestSession)
    @patch("services.orchestrator.VerifierAgent")
    @patch("services.orchestrator.SplitterAgent")
    @patch("services.orchestrator.EvaluatorAgent")
    @patch("services.orchestrator.HeadlineAgent")
    async def test_orchestrator_handles_unexpected_error(
        self, mock_headline, mock_evaluator, mock_splitter, mock_verifier
    ):
        """Unhandled exceptions set status=failed and emit failed event."""
        contract_id, review_id = await _seed_contract_and_review()
        mock_verifier.return_value.run = AsyncMock(
            side_effect=RuntimeError("Unexpected boom")
        )

        orch = await self._make_orchestrator(review_id, contract_id)
        events = await _collect_events(orch)

        failed = _find_event(events, "failed")
        assert failed is not None

        async with _TestSession() as db:
            review = await db.get(ContractReview, review_id)
            assert review.status == "failed"

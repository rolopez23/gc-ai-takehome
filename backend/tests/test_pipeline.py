import json

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch


def _mock_anthropic_success():
    """Mock Anthropic response with a valid EvalSuccess JSON."""
    mock_msg = MagicMock()
    mock_msg.stop_reason = "end_turn"
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = json.dumps({
        "error": None,
        "overall_fairness": "fair",
        "summary": "Looks good",
        "call_to_action": [],
        "clauses": [
            {
                "section_number": "1",
                "clause_type": "Term",
                "purpose": "Sets duration",
                "fairness": "fair",
                "market_standard": "Standard",
                "explanation": "Normal",
            }
        ],
    })
    mock_msg.content = [mock_content]
    return mock_msg


@pytest.mark.asyncio
async def test_upload_triggers_evaluation(client: AsyncClient):
    """POST a .txt file with mocked Anthropic. Background task runs synchronously
    in the test client, so GET should see completed status immediately."""
    with patch("services.evaluation.anthropic.Anthropic") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.messages.create.return_value = _mock_anthropic_success()

        resp = await client.post(
            "/api/contracts/upload",
            files={"file": ("test.txt", b"Contract text here", "text/plain")},
        )
        assert resp.status_code == 201
        review_id = resp.json()["review_id"]

        review_resp = await client.get(f"/api/reviews/{review_id}")
        data = review_resp.json()
        assert data["status"] == "completed"
        assert data["overall_fairness"] == "fair"
        assert len(data["clauses"]) == 1


@pytest.mark.asyncio
async def test_upload_and_poll_completed(client: AsyncClient):
    """POST .txt, then GET review. Assert final status is completed with
    overall_fairness and clauses populated."""
    with patch("services.evaluation.anthropic.Anthropic") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.messages.create.return_value = _mock_anthropic_success()

        resp = await client.post(
            "/api/contracts/upload",
            files={"file": ("poll.txt", b"Some contract terms", "text/plain")},
        )
        assert resp.status_code == 201
        review_id = resp.json()["review_id"]

        review_resp = await client.get(f"/api/reviews/{review_id}")
        assert review_resp.status_code == 200
        data = review_resp.json()

        assert data["status"] == "completed"
        assert data["overall_fairness"] == "fair"
        assert data["summary"] == "Looks good"
        assert data["call_to_action"] == []
        assert len(data["clauses"]) == 1
        clause = data["clauses"][0]
        assert clause["section_number"] == "1"
        assert clause["clause_type"] == "Term"


@pytest.mark.asyncio
async def test_pipeline_conversion_error(client: AsyncClient):
    """POST a .docx where process_upload raises ValueError during the background
    task conversion step. The review should end up failed with a failure_message."""
    from services.conversion import ConversionResult

    # The router calls process_upload on upload; let that succeed with a docx result.
    # The background task re-calls process_upload for doc/docx conversion; make that fail.
    router_result = ConversionResult(
        upload_type="docx",
        original_blob=b"fake docx bytes",
        pdf_blob=None,
        text=None,
    )

    with patch("routers.contracts.process_upload", return_value=router_result), \
         patch("services.evaluation.process_upload", side_effect=ValueError("corrupt file")):
        resp = await client.post(
            "/api/contracts/upload",
            files={"file": ("test.docx", b"fake docx bytes", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 201
        review_id = resp.json()["review_id"]

        review_resp = await client.get(f"/api/reviews/{review_id}")
        data = review_resp.json()
        assert data["status"] == "failed"
        assert "corrupt file" in data["failure_message"]

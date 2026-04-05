import base64
import json

import pytest

from services.evaluation import build_messages, parse_response


def test_build_messages_pdf():
    result = build_messages(pdf_blob=b"fake", text=None, instructions=None)
    msg = result["messages"][0]
    assert msg["role"] == "user"
    block = msg["content"][0]
    assert block["type"] == "document"
    assert block["source"]["media_type"] == "application/pdf"
    assert block["source"]["data"] == base64.standard_b64encode(b"fake").decode("ascii")
    assert "system" in result


def test_build_messages_pdf_with_instructions():
    result = build_messages(pdf_blob=b"fake", text=None, instructions="Focus on IP")
    assert "Additional instructions" in result["system"]
    assert "Focus on IP" in result["system"]


def test_build_messages_text():
    result = build_messages(pdf_blob=None, text="Contract text", instructions=None)
    msg = result["messages"][0]
    assert msg["content"] == "Contract text"


def test_build_messages_requires_one():
    with pytest.raises(ValueError, match="Either pdf_blob or text must be provided"):
        build_messages(pdf_blob=None, text=None, instructions=None)


def _make_success_json(**overrides):
    data = {
        "error": None,
        "overall_fairness": "fair",
        "summary": "All clauses are market standard.",
        "call_to_action": ["No action needed."],
        "clauses": [
            {
                "section_number": "1.1",
                "clause_type": "Term",
                "purpose": "Sets the contract duration.",
                "fairness": "fair",
                "market_standard": "Standard 12-month term.",
                "explanation": "This is a typical term clause.",
            }
        ],
    }
    data.update(overrides)
    return json.dumps(data)


def test_parse_success():
    raw = _make_success_json()
    status, data = parse_response(raw)
    assert status == "success"
    assert data["overall_fairness"] == "fair"
    assert data["summary"] == "All clauses are market standard."
    assert len(data["clauses"]) == 1
    assert data["clauses"][0]["section_number"] == "1.1"


def test_parse_strips_fences():
    raw = "```json\n" + _make_success_json() + "\n```"
    status, data = parse_response(raw)
    assert status == "success"
    assert data["overall_fairness"] == "fair"


def test_parse_eval_error():
    raw = json.dumps({"error": True, "reason": "Not a contract"})
    status, data = parse_response(raw)
    assert status == "not_a_contract"
    assert data == {"reason": "Not a contract"}


def test_parse_invalid_json():
    status, data = parse_response("this is not json {{{")
    assert status == "parse_error"
    assert "message" in data


def test_parse_wrong_schema():
    raw = json.dumps({"unexpected": "shape", "no_match": True})
    status, data = parse_response(raw)
    assert status == "parse_error"
    assert "message" in data

"""NDJSON event emitter for the pipeline orchestrator stream."""

import json


class EventEmitter:
    def _emit(self, event: dict) -> str:
        return json.dumps(event) + "\n"

    def started(self, review_id: str) -> str:
        return self._emit(
            {
                "event": "started",
                "review_id": review_id,
                "summary": "",
                "call_to_action": [],
            }
        )

    def token(self, field: str, text: str) -> str:
        return self._emit({"event": "token", "field": field, "text": text})

    def verifying(self, is_contract: bool) -> str:
        return self._emit({"event": "verifying", "is_contract": is_contract})

    def splitting(self, agreement_type: str, clause_count: int) -> str:
        return self._emit(
            {
                "event": "splitting",
                "agreement_type": agreement_type,
                "clause_count": clause_count,
            }
        )

    def clause_evaluated(self, clause: dict) -> str:
        return self._emit({"event": "clause_evaluated", "clause": clause})

    def clause_error(self, section_number: str, clause_type: str, error: str) -> str:
        return self._emit(
            {
                "event": "clause_error",
                "section_number": section_number,
                "clause_type": clause_type,
                "error": error,
            }
        )

    def replace(self, field: str, value) -> str:
        if isinstance(value, str):
            return self._emit({"event": "replace", "field": field, "text": value})
        return self._emit({"event": "replace", "field": field, "value": value})

    def rejected(self, reason: str) -> str:
        return self._emit({"event": "rejected", "reason": reason})

    def failed(self, reason: str) -> str:
        return self._emit({"event": "failed", "reason": reason})

    def completed(self, result: dict) -> str:
        return self._emit({"event": "completed", "result": result})

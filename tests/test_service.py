from datetime import datetime, timezone

from groundtrace_memory.models import MemoryCandidate
from groundtrace_memory.service import MemoryService


class FakeEmbedder:
    def embed(self, _text):
        return [0.0] * 1024


class FakeRepository:
    def __init__(self, *, outcome_success: bool = True, verified: bool = True):
        self._outcome_success = outcome_success
        self._verified = verified

    def find_similar(self, **_kwargs):
        return [
            MemoryCandidate(
                memory_id="m-1",
                incident_text="latency alarm",
                action_text="inspect connection saturation",
                outcome_success=self._outcome_success,
                verified=self._verified,
                occurred_at=datetime.now(timezone.utc),
                similarity=0.95,
                provenance={"source": "resolved_incident"},
            )
        ]

    def record_decision_trace(self, **_kwargs):
        return "trace-1"


def test_recall_returns_action_from_relied_memory():
    service = MemoryService(FakeRepository(), FakeEmbedder())
    result = service.recall({"tenant_id": "demo", "incident_text": "database latency"})
    assert result["trace_id"] == "trace-1"
    assert result["status"] == "recommended"
    assert result["recommendation"] == "inspect connection saturation"
    assert result["candidates"][0]["admission"] == "RELY"


def test_recall_reports_rejected_when_all_candidates_are_rejected():
    service = MemoryService(FakeRepository(outcome_success=False), FakeEmbedder())
    result = service.recall({"tenant_id": "demo", "incident_text": "database latency"})
    assert result["trace_id"] == "trace-1"
    assert result["status"] == "rejected"
    assert result["recommendation"] is None
    assert result["candidates"][0]["admission"] == "REJECT"
    assert result["candidates"][0]["reasons"] == ["outcome_not_successful"]

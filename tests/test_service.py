from datetime import datetime, timezone

from groundtrace_memory.models import MemoryCandidate
from groundtrace_memory.service import MemoryService


class FakeEmbedder:
    def embed(self, _text):
        return [0.0] * 1024


class FakeRepository:
    def find_similar(self, **_kwargs):
        return [
            MemoryCandidate(
                memory_id="m-1",
                incident_text="latency alarm",
                action_text="inspect connection saturation",
                outcome_success=True,
                verified=True,
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

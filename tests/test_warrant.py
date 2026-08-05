from datetime import datetime, timedelta, timezone

from groundtrace_memory.models import Admission, MemoryCandidate
from groundtrace_memory.warrant import admit_memory


def candidate(**overrides):
    values = {
        "memory_id": "m-1",
        "incident_text": "database latency alarm",
        "action_text": "inspect connection saturation",
        "outcome_success": True,
        "verified": True,
        "occurred_at": datetime.now(timezone.utc) - timedelta(days=7),
        "similarity": 0.91,
        "provenance": {"source": "resolved_incident"},
    }
    values.update(overrides)
    return MemoryCandidate(**values)


def test_verified_successful_fresh_similar_memory_is_relied_on():
    decision = admit_memory(candidate())
    assert decision.admission == Admission.RELY
    assert decision.reasons == ()


def test_unverified_memory_is_held():
    decision = admit_memory(candidate(verified=False))
    assert decision.admission == Admission.HOLD
    assert "memory_not_verified" in decision.reasons


def test_failed_outcome_is_rejected():
    decision = admit_memory(candidate(outcome_success=False))
    assert decision.admission == Admission.REJECT
    assert "outcome_not_successful" in decision.reasons


def test_missing_provenance_is_rejected():
    decision = admit_memory(candidate(provenance={}))
    assert decision.admission == Admission.REJECT
    assert "provenance_missing" in decision.reasons

from __future__ import annotations

from .models import Admission, AdmissionDecision, MemoryCandidate


def admit_memory(candidate: MemoryCandidate, *, max_age_days: int = 180) -> AdmissionDecision:
    reasons: list[str] = []

    if not candidate.verified:
        reasons.append("memory_not_verified")
    if not candidate.outcome_success:
        reasons.append("outcome_not_successful")
    if candidate.age_days > max_age_days:
        reasons.append("memory_stale")
    if candidate.similarity < 0.70:
        reasons.append("similarity_below_floor")
    if not candidate.provenance:
        reasons.append("provenance_missing")

    hard_reject = {"outcome_not_successful", "provenance_missing"}
    if hard_reject.intersection(reasons):
        admission = Admission.REJECT
    elif reasons:
        admission = Admission.HOLD
    else:
        admission = Admission.RELY

    return AdmissionDecision(
        memory_id=candidate.memory_id,
        admission=admission,
        reasons=tuple(reasons),
    )

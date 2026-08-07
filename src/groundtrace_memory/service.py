from __future__ import annotations

from datetime import datetime
from typing import Any

from .embeddings import BedrockEmbedder
from .models import Admission
from .repository import MemoryRepository
from .warrant import admit_memory


class MemoryService:
    def __init__(self, repository: MemoryRepository, embedder: BedrockEmbedder) -> None:
        self._repository = repository
        self._embedder = embedder

    def remember(self, payload: dict[str, Any]) -> dict[str, Any]:
        embedding = self._embedder.embed(payload["incident_text"])
        memory_id = self._repository.store_memory(
            tenant_id=payload["tenant_id"],
            incident_text=payload["incident_text"],
            action_text=payload["action_text"],
            outcome_success=bool(payload["outcome_success"]),
            verified=bool(payload["verified"]),
            occurred_at=datetime.fromisoformat(payload["occurred_at"]),
            provenance=dict(payload["provenance"]),
            embedding=embedding,
        )
        return {"memory_id": memory_id, "status": "stored"}

    def recall(self, payload: dict[str, Any]) -> dict[str, Any]:
        embedding = self._embedder.embed(payload["incident_text"])
        candidates = self._repository.find_similar(
            tenant_id=payload["tenant_id"],
            embedding=embedding,
        )
        decisions = [admit_memory(candidate) for candidate in candidates]
        relied = [
            candidate
            for candidate, decision in zip(candidates, decisions, strict=True)
            if decision.admission == Admission.RELY
        ]
        recommendation = relied[0].action_text if relied else None
        if recommendation:
            status = "recommended"
        elif decisions and all(decision.admission == Admission.REJECT for decision in decisions):
            status = "rejected"
        else:
            status = "held"
        candidate_trace = [
            {
                "memory_id": candidate.memory_id,
                "similarity": candidate.similarity,
                "admission": decision.admission,
                "reasons": list(decision.reasons),
            }
            for candidate, decision in zip(candidates, decisions, strict=True)
        ]
        trace_id = self._repository.record_decision_trace(
            tenant_id=payload["tenant_id"],
            incident_text=payload["incident_text"],
            recommendation=recommendation,
            status=status,
            candidate_trace=candidate_trace,
        )
        return {
            "trace_id": trace_id,
            "recommendation": recommendation,
            "status": status,
            "candidates": candidate_trace,
        }

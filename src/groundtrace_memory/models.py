from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class Admission(StrEnum):
    RELY = "RELY"
    HOLD = "HOLD"
    REJECT = "REJECT"


@dataclass(frozen=True)
class MemoryCandidate:
    memory_id: str
    incident_text: str
    action_text: str
    outcome_success: bool
    verified: bool
    occurred_at: datetime
    similarity: float
    provenance: dict[str, Any]

    @property
    def age_days(self) -> int:
        now = datetime.now(timezone.utc)
        occurred = self.occurred_at
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=timezone.utc)
        return max(0, (now - occurred).days)


@dataclass(frozen=True)
class AdmissionDecision:
    memory_id: str
    admission: Admission
    reasons: tuple[str, ...]

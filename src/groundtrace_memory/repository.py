from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .models import MemoryCandidate


class MemoryRepository:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def healthcheck(self) -> bool:
        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() == (1,)

    def store_memory(
        self,
        *,
        tenant_id: str,
        incident_text: str,
        action_text: str,
        outcome_success: bool,
        verified: bool,
        occurred_at: datetime,
        provenance: dict[str, Any],
        embedding: list[float],
    ) -> str:
        vector = "[" + ",".join(str(value) for value in embedding) + "]"
        statement = """
            INSERT INTO incident_memories (
                tenant_id, incident_text, action_text, outcome_success,
                verified, occurred_at, provenance, embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s::JSONB, %s::VECTOR)
            RETURNING memory_id::STRING
        """
        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    statement,
                    (
                        tenant_id,
                        incident_text,
                        action_text,
                        outcome_success,
                        verified,
                        occurred_at,
                        json.dumps(provenance),
                        vector,
                    ),
                )
                memory_id = cursor.fetchone()[0]
            connection.commit()
        return memory_id

    def find_similar(
        self,
        *,
        tenant_id: str,
        embedding: list[float],
        limit: int = 5,
    ) -> list[MemoryCandidate]:
        vector = "[" + ",".join(str(value) for value in embedding) + "]"
        statement = """
            SELECT
                memory_id::STRING AS memory_id,
                incident_text,
                action_text,
                outcome_success,
                verified,
                occurred_at,
                provenance,
                1 - (embedding <=> %s::VECTOR) AS similarity
            FROM incident_memories
            WHERE tenant_id = %s
            ORDER BY embedding <=> %s::VECTOR
            LIMIT %s
        """
        with psycopg.connect(self._database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, (vector, tenant_id, vector, limit))
                rows = cursor.fetchall()

        return [
            MemoryCandidate(
                memory_id=row["memory_id"],
                incident_text=row["incident_text"],
                action_text=row["action_text"],
                outcome_success=row["outcome_success"],
                verified=row["verified"],
                occurred_at=row["occurred_at"],
                similarity=float(row["similarity"]),
                provenance=row["provenance"],
            )
            for row in rows
        ]

    def record_decision_trace(
        self,
        *,
        tenant_id: str,
        incident_text: str,
        recommendation: str | None,
        status: str,
        candidate_trace: list[dict[str, Any]],
    ) -> str:
        statement = """
            INSERT INTO decision_traces (
                tenant_id,
                incident_text,
                recommendation,
                status,
                candidate_trace
            )
            VALUES (%s, %s, %s, %s, %s::JSONB)
            RETURNING trace_id::STRING
        """
        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    statement,
                    (
                        tenant_id,
                        incident_text,
                        recommendation,
                        status,
                        json.dumps(candidate_trace),
                    ),
                )
                trace_id = cursor.fetchone()[0]
            connection.commit()
        return trace_id

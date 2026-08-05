from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import psycopg

VECTOR_DIMENSIONS = 1024
TEST_TENANT = "groundtrace-smoke-test"


def vector_literal() -> str:
    values = ["1"] + ["0"] * (VECTOR_DIMENSIONS - 1)
    return "[" + ",".join(values) + "]"


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        return 2

    vector = vector_literal()
    connection = psycopg.connect(database_url)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), version()")
            database_name, database_version = cursor.fetchone()

            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('incident_memories', 'decision_traces')
                ORDER BY table_name
                """
            )
            tables = [row[0] for row in cursor.fetchall()]
            if tables != ["decision_traces", "incident_memories"]:
                raise RuntimeError(f"Expected two GroundTrace tables; found {tables!r}")

            cursor.execute(
                """
                INSERT INTO incident_memories (
                    tenant_id,
                    incident_text,
                    action_text,
                    outcome_success,
                    verified,
                    occurred_at,
                    provenance,
                    embedding
                )
                VALUES (%s, %s, %s, true, true, %s, %s::JSONB, %s::VECTOR)
                RETURNING memory_id::STRING
                """,
                (
                    TEST_TENANT,
                    "Synthetic database smoke-test incident",
                    "Return the synthetic smoke-test action",
                    datetime.now(timezone.utc),
                    json.dumps({"source": "scripts/smoke_db.py", "synthetic": True}),
                    vector,
                ),
            )
            memory_id = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT
                    memory_id::STRING,
                    action_text,
                    1 - (embedding <=> %s::VECTOR) AS similarity
                FROM incident_memories
                WHERE tenant_id = %s
                ORDER BY embedding <=> %s::VECTOR
                LIMIT 1
                """,
                (vector, TEST_TENANT, vector),
            )
            retrieved_id, action_text, similarity = cursor.fetchone()

            if retrieved_id != memory_id:
                raise RuntimeError(
                    f"Vector recall returned {retrieved_id}, expected inserted memory {memory_id}"
                )
            if float(similarity) < 0.999999:
                raise RuntimeError(f"Expected near-identical vector similarity; got {similarity}")

        connection.rollback()
        print("GROUNDTRACE DB SMOKE TEST: PASS")
        print(f"database: {database_name}")
        print(f"tables: {', '.join(tables)}")
        print(f"retrieved memory: {memory_id}")
        print(f"similarity: {float(similarity):.6f}")
        print(f"action: {action_text}")
        print("cleanup: transaction rolled back; no synthetic row retained")
        print(f"server: {database_version}")
        return 0
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import psycopg

from groundtrace_memory.embeddings import BedrockEmbedder
from groundtrace_memory.repository import MemoryRepository
from groundtrace_memory.service import MemoryService

TEST_TENANT = "groundtrace-e2e-smoke"


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        return 2

    region = os.getenv("BEDROCK_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-west-2"))
    model_id = os.getenv("BEDROCK_MODEL_ID", "amazon.titan-embed-text-v2:0")

    repository = MemoryRepository(database_url)
    embedder = BedrockEmbedder(region_name=region, model_id=model_id)
    service = MemoryService(repository, embedder)

    remembered = service.remember(
        {
            "tenant_id": TEST_TENANT,
            "incident_text": "Database connection pool saturation caused elevated API latency",
            "action_text": "Inspect connection pool saturation and reduce burst concurrency",
            "outcome_success": True,
            "verified": True,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "provenance": {
                "source": "scripts/smoke_e2e.py",
                "synthetic": True,
                "verification": "controlled_smoke_test",
            },
        }
    )

    recalled = service.recall(
        {
            "tenant_id": TEST_TENANT,
            "incident_text": "API latency is rising while database connections are saturated",
        }
    )

    try:
        if recalled["status"] != "recommended":
            raise RuntimeError(f"Expected recommended status, got {recalled!r}")
        if recalled["recommendation"] != (
            "Inspect connection pool saturation and reduce burst concurrency"
        ):
            raise RuntimeError(f"Unexpected recommendation: {recalled!r}")
        if not recalled["candidates"]:
            raise RuntimeError("No memory candidates were returned")
        if recalled["candidates"][0]["admission"] != "RELY":
            raise RuntimeError(f"Expected RELY admission, got {recalled!r}")

        print("GROUNDTRACE END-TO-END SMOKE TEST: PASS")
        print(f"bedrock model: {model_id}")
        print(f"region: {region}")
        print(f"stored memory: {remembered['memory_id']}")
        print(f"decision trace: {recalled['trace_id']}")
        print(f"admission: {recalled['candidates'][0]['admission']}")
        print(f"similarity: {recalled['candidates'][0]['similarity']:.6f}")
        print(f"recommendation: {recalled['recommendation']}")
        return 0
    finally:
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM decision_traces WHERE tenant_id = %s", (TEST_TENANT,))
                cursor.execute("DELETE FROM incident_memories WHERE tenant_id = %s", (TEST_TENANT,))
            connection.commit()
        print("cleanup: synthetic memory and trace removed")


if __name__ == "__main__":
    raise SystemExit(main())

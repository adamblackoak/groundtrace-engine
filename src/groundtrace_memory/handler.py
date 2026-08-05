from __future__ import annotations

import json
import os
from typing import Any

from .embeddings import BedrockEmbedder
from .repository import MemoryRepository
from .service import MemoryService


def _service() -> MemoryService:
    repository = MemoryRepository(os.environ["DATABASE_URL"])
    embedder = BedrockEmbedder(
        region_name=os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1")),
        model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.titan-embed-text-v2:0"),
    )
    return MemoryService(repository, embedder)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    try:
        body = event.get("body", event)
        if isinstance(body, str):
            body = json.loads(body)
        operation = body.get("operation", "recall")
        service = _service()
        if operation == "remember":
            result = service.remember(body)
        elif operation == "recall":
            result = service.recall(body)
        elif operation == "health":
            result = {"database": service._repository.healthcheck()}
        else:
            raise ValueError(f"Unsupported operation: {operation}")
        return {"statusCode": 200, "body": json.dumps(result, default=str)}
    except (KeyError, TypeError, ValueError) as exc:
        return {"statusCode": 400, "body": json.dumps({"error": str(exc)})}

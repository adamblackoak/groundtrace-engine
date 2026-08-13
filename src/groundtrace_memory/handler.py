from __future__ import annotations

import hmac
import json
import os
from functools import lru_cache
from typing import Any

import boto3

from .embeddings import BedrockEmbedder
from .repository import MemoryRepository
from .service import MemoryService


@lru_cache(maxsize=1)
def _database_url() -> str:
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        return direct_url

    secret_arn = os.environ["DATABASE_URL_SECRET_ARN"]
    region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-west-2"))
    response = boto3.client("secretsmanager", region_name=region).get_secret_value(
        SecretId=secret_arn
    )
    secret_string = response["SecretString"]

    try:
        decoded = json.loads(secret_string)
    except json.JSONDecodeError:
        return secret_string

    if isinstance(decoded, dict) and isinstance(decoded.get("DATABASE_URL"), str):
        return decoded["DATABASE_URL"]
    raise ValueError("Database secret must be a URI string or contain a DATABASE_URL field")


def _service() -> MemoryService:
    repository = MemoryRepository(_database_url())
    embedder = BedrockEmbedder(
        region_name=os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "eu-west-2")),
        model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.titan-embed-text-v2:0"),
    )
    return MemoryService(repository, embedder)


def _is_authorized(event: dict[str, Any]) -> bool:
    expected = os.getenv("DEMO_API_TOKEN")
    if not expected:
        return False

    headers = event.get("headers") or {}
    authorization = ""
    if isinstance(headers, dict):
        for key, value in headers.items():
            if str(key).lower() == "authorization" and isinstance(value, str):
                authorization = value
                break

    scheme, separator, token = authorization.partition(" ")
    return (
        bool(separator)
        and scheme.lower() == "bearer"
        and hmac.compare_digest(token, expected)
    )


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    if not _is_authorized(event):
        return {
            "statusCode": 401,
            "headers": {"WWW-Authenticate": "Bearer"},
            "body": json.dumps({"error": "Unauthorized"}),
        }

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

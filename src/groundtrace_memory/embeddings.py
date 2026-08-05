from __future__ import annotations

import json

import boto3


class BedrockEmbedder:
    def __init__(self, *, region_name: str, model_id: str) -> None:
        self._client = boto3.client("bedrock-runtime", region_name=region_name)
        self._model_id = model_id

    def embed(self, text: str) -> list[float]:
        response = self._client.invoke_model(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(
                {
                    "inputText": text,
                    "dimensions": 1024,
                    "normalize": True,
                }
            ),
        )
        payload = json.loads(response["body"].read())
        return [float(value) for value in payload["embedding"]]

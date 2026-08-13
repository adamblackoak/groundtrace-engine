import json

from groundtrace_memory import handler


def test_missing_bearer_token_is_rejected_before_service_construction(monkeypatch):
    monkeypatch.setenv("DEMO_API_TOKEN", "x" * 32)

    def fail_if_called():
        raise AssertionError("service should not be constructed for unauthorized requests")

    monkeypatch.setattr(handler, "_service", fail_if_called)

    response = handler.lambda_handler({"headers": {}, "body": "{}"}, None)

    assert response["statusCode"] == 401
    assert json.loads(response["body"]) == {"error": "Unauthorized"}


def test_valid_bearer_token_allows_request(monkeypatch):
    token = "y" * 32
    monkeypatch.setenv("DEMO_API_TOKEN", token)

    class FakeRepository:
        def healthcheck(self):
            return True

    class FakeService:
        _repository = FakeRepository()

    monkeypatch.setattr(handler, "_service", lambda: FakeService())

    response = handler.lambda_handler(
        {
            "headers": {"Authorization": f"Bearer {token}"},
            "body": json.dumps({"operation": "health"}),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"database": True}

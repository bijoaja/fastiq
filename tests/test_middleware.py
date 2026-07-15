import logging
import os
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from app.utils.uuid import generate_uuid7
from app.config.logger import setup_logging, request_id_ctx
from app.core.middleware import RequestLoggingMiddleware

def test_uuid7_generation():
    # Test generation and type
    val = generate_uuid7()
    assert isinstance(val, uuid.UUID)
    # UUIDv7 starts with version 7
    assert val.version == 7

def test_request_logging_middleware(capsys):
    # Setup FastAPI app
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    def test_endpoint():
        req_id = request_id_ctx.get()
        assert req_id != "-"
        return {"request_id": req_id}

    setup_logging()
    client = TestClient(app)

    # 1. Request without X-Request-ID (should generate one)
    response = client.get("/test")
    assert response.status_code == 200
    res_data = response.json()
    req_id = res_data["request_id"]
    assert req_id is not None
    assert response.headers.get("X-Request-ID") == req_id

    # The log message goes to stderr because of standard console handler
    captured = capsys.readouterr()
    assert "Method: GET | Path: /test" in captured.err
    assert req_id in captured.err

    assert os.path.exists("logs/app.log")
    with open("logs/app.log", "r") as f:
        lines = f.readlines()
        assert any(req_id in line for line in lines)
        assert any("Method: GET | Path: /test" in line for line in lines)

    # 2. Request with X-Request-ID (should reuse it)
    custom_id = "test-custom-request-id-1234"
    response2 = client.get("/test", headers={"X-Request-ID": custom_id})
    assert response2.status_code == 200
    res_data2 = response2.json()
    assert res_data2["request_id"] == custom_id
    assert response2.headers.get("X-Request-ID") == custom_id

    captured2 = capsys.readouterr()
    assert "Method: GET | Path: /test" in captured2.err
    assert custom_id in captured2.err

    with open("logs/app.log", "r") as f:
        lines = f.readlines()
        assert any(custom_id in line for line in lines)
        assert any("Method: GET | Path: /test" in line for line in lines)

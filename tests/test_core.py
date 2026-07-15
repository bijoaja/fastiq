from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
import pytest
from app.core.responses import ApiResponse, ApiListResponse, ApiErrorResponse
from app.core.pagination import build_pagination_info
from app.core.exceptions import (
    register_exception_handlers,
    NotFoundException,
    BadRequestException,
)

def test_responses():
    res = ApiResponse(data="test data")
    assert res.success is True
    assert res.message == "Success"
    assert res.data == "test data"

def test_pagination():
    info = build_pagination_info(page=2, per_page=10, total=25)
    assert info.page == 2
    assert info.per_page == 10
    assert info.total == 25
    assert info.total_pages == 3

class DummyBody(BaseModel):
    name: str
    age: int

def test_exception_handlers():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    def get_not_found():
        raise NotFoundException(message="Item not found")

    @app.get("/bad-request")
    def get_bad_request():
        raise BadRequestException(message="Invalid input")

    @app.get("/http-error")
    def get_http_error():
        raise HTTPException(status_code=403, detail="Forbidden action")

    @app.get("/generic-error")
    def get_generic_error():
        raise ValueError("Something went wrong internally")

    @app.post("/validation")
    def post_validation(body: DummyBody):
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)

    # 1. Test NotFoundException
    response = client.get("/not-found")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Item not found"
    assert data["errors"] == []

    # 2. Test BadRequestException
    response2 = client.get("/bad-request")
    assert response2.status_code == 400
    data2 = response2.json()
    assert data2["success"] is False
    assert data2["message"] == "Invalid input"

    # 3. Test Starlette/FastAPI HTTPException
    response3 = client.get("/http-error")
    assert response3.status_code == 403
    data3 = response3.json()
    assert data3["success"] is False
    assert data3["message"] == "Forbidden action"
    assert data3["errors"] == []

    # 4. Test RequestValidationError
    response4 = client.post("/validation", json={"name": "Alice"})  # missing age
    assert response4.status_code == 422
    data4 = response4.json()
    assert data4["success"] is False
    assert data4["message"] == "Validation Error"
    assert len(data4["errors"]) > 0
    assert data4["errors"][0]["field"] == "age"

    # 5. Test Generic Exception (500)
    # Turn off debug mode in settings mock if necessary, but with DEBUG=true we get the exact error message
    from app.config.settings import settings
    original_debug = settings.DEBUG
    try:
        settings.DEBUG = False
        response5 = client.get("/generic-error")
        assert response5.status_code == 500
        data5 = response5.json()
        assert data5["success"] is False
        assert data5["message"] == "Internal server error"
        assert data5["errors"] == []

        settings.DEBUG = True
        response6 = client.get("/generic-error")
        assert response6.status_code == 500
        data6 = response6.json()
        assert data6["success"] is False
        assert "Something went wrong internally" in data6["message"]
    finally:
        settings.DEBUG = original_debug

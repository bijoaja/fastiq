import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_smoke_flow(client: AsyncClient):
    # 1. Uji endpoint /health
    response = await client.get("/health")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["message"] == "Success"
    assert res_data["data"] == {"status": "ok"}

    # 2. Uji POST /api/users/
    payload = {
        "email": "smoke_test@example.com",
        "password": "password123",
        "name": "Smoke User"
    }
    response = await client.post("/api/users/", json=payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["email"] == "smoke_test@example.com"
    assert res_data["data"]["name"] == "Smoke User"
    user_id = res_data["data"]["id"]
    assert user_id is not None

    # 3. Uji GET /api/users/{id}
    response = await client.get(f"/api/users/{user_id}")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["id"] == user_id
    assert res_data["data"]["email"] == "smoke_test@example.com"
    assert res_data["data"]["name"] == "Smoke User"

    # 4. Uji GET /api/users/
    response = await client.get("/api/users/")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    # Pastikan user yang baru dibuat muncul di list
    users_list = res_data["data"]
    assert len(users_list) == 1
    assert users_list[0]["id"] == user_id
    assert users_list[0]["email"] == "smoke_test@example.com"

    # Pastikan total pagination adalah 1
    assert res_data["pagination"]["total"] == 1

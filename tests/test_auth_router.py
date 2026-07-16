import pytest

@pytest.mark.asyncio
async def test_register_login_me_refresh_logout_flow(client):
    # Register
    register_payload = {"email": "flow@example.com", "password": "password123", "name": "Flow User"}
    register_resp = await client.post("/api/auth/register", json=register_payload)
    assert register_resp.status_code == 201
    assert register_resp.json()["data"]["email"] == "flow@example.com"

    # Login
    login_resp = await client.post("/api/auth/login", json={"email": "flow@example.com", "password": "password123"})
    assert login_resp.status_code == 200
    tokens = login_resp.json()["data"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    # Access protected route
    me_resp = await client.get("/api/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "flow@example.com"

    # Protected route without token
    no_auth_resp = await client.get("/api/users/me")
    assert no_auth_resp.status_code == 401

    # Refresh
    refresh_resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()["data"]
    assert new_tokens["refresh_token"] != refresh_token

    # Reusing the old (rotated) refresh token must fail
    reuse_resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_resp.status_code == 401

    # Logout with the new refresh token
    logout_resp = await client.post("/api/auth/logout", json={"refresh_token": new_tokens["refresh_token"]})
    assert logout_resp.status_code == 200

    # Refresh after logout must fail
    post_logout_refresh = await client.post("/api/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]})
    assert post_logout_refresh.status_code == 401

@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    await client.post("/api/auth/register", json={"email": "wp@example.com", "password": "password123", "name": "WP"})
    resp = await client.post("/api/auth/login", json={"email": "wp@example.com", "password": "wrong-password"})
    assert resp.status_code == 401

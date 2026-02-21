import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "username": "alice", "password": "Password123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "bob@example.com", "username": "bob", "password": "Password123"}
    r1 = await client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/api/auth/register", json=payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    resp = await client.post(
        "/api/auth/register",
        json={"email": "weak@example.com", "username": "weakuser", "password": "short"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "charlie@example.com", "username": "charlie", "password": "MyPass999"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "charlie@example.com", "password": "MyPass999"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "dave@example.com", "username": "dave", "password": "Correct999"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "dave@example.com", "password": "Wrong999"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"email": "eve@example.com", "username": "eve", "password": "EvePass999"},
    )
    login = await client.post(
        "/api/auth/login",
        json={"email": "eve@example.com", "password": "EvePass999"},
    )
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(client: AsyncClient):
    resp = await client.get("/api/profiles")
    assert resp.status_code == 403

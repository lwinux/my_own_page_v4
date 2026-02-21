import json
import pytest
from httpx import AsyncClient

VALID_DRAFT = {
    "schema_version": 1,
    "personal": {
        "full_name": "Jane Smith",
        "title": "Product Manager",
        "email": "jane@example.com",
        "summary": "Driving product from zero to one.",
    },
    "experience": [],
    "education": [],
    "skills": [{"category": "Tools", "items": ["Jira", "Figma"]}],
    "projects": [],
    "languages": [{"language": "English", "proficiency": "Native"}],
    "certifications": [],
}


@pytest.mark.asyncio
async def test_publish_creates_version(auth_client: AsyncClient):
    p = await auth_client.post(
        "/api/profiles",
        json={"profile_name": "Publish Test Profile", "company_note": "Test company"},
    )
    assert p.status_code == 201
    pid = p.json()["id"]

    # Save draft
    dr = await auth_client.put(f"/api/profiles/{pid}/draft", json=VALID_DRAFT)
    assert dr.status_code == 200

    # Publish
    pub = await auth_client.post(f"/api/profiles/{pid}/publish")
    assert pub.status_code == 201
    data = pub.json()
    assert data["version_number"] == 1
    assert "token" in data
    assert len(data["token"]) == 64
    assert data["public_url"].endswith(data["token"])


@pytest.mark.asyncio
async def test_publish_increments_version(auth_client: AsyncClient):
    p = await auth_client.post(
        "/api/profiles",
        json={"profile_name": "Version Increment Test", "company_note": ""},
    )
    pid = p.json()["id"]

    await auth_client.put(f"/api/profiles/{pid}/draft", json=VALID_DRAFT)
    v1 = await auth_client.post(f"/api/profiles/{pid}/publish")
    assert v1.json()["version_number"] == 1

    await auth_client.put(f"/api/profiles/{pid}/draft", json=VALID_DRAFT)
    v2 = await auth_client.post(f"/api/profiles/{pid}/publish")
    assert v2.json()["version_number"] == 2

    # Each publish creates a unique token
    assert v1.json()["token"] != v2.json()["token"]


@pytest.mark.asyncio
async def test_publish_without_draft_returns_404(auth_client: AsyncClient):
    p = await auth_client.post(
        "/api/profiles",
        json={"profile_name": "No Draft Profile", "company_note": ""},
    )
    pid = p.json()["id"]

    resp = await auth_client.post(f"/api/profiles/{pid}/publish")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_versions(auth_client: AsyncClient):
    p = await auth_client.post(
        "/api/profiles",
        json={"profile_name": "Versions List Test", "company_note": ""},
    )
    pid = p.json()["id"]

    await auth_client.put(f"/api/profiles/{pid}/draft", json=VALID_DRAFT)
    await auth_client.post(f"/api/profiles/{pid}/publish")
    await auth_client.put(f"/api/profiles/{pid}/draft", json=VALID_DRAFT)
    await auth_client.post(f"/api/profiles/{pid}/publish")

    versions = await auth_client.get(f"/api/profiles/{pid}/versions")
    assert versions.status_code == 200
    data = versions.json()
    assert len(data) == 2
    assert data[0]["version_number"] > data[1]["version_number"]

import pytest
from httpx import AsyncClient

VALID_DRAFT = {
    "schema_version": 1,
    "personal": {
        "full_name": "Public User",
        "title": "Frontend Developer",
        "email": "public@example.com",
        "summary": "Building beautiful interfaces.",
    },
    "experience": [],
    "education": [],
    "skills": [],
    "projects": [
        {
            "name": "My Portfolio",
            "description": "A personal site",
            "tech_stack": ["React", "TypeScript"],
        }
    ],
    "languages": [],
    "certifications": [],
}


async def _publish_profile(client: AsyncClient, profile_name: str) -> dict:
    """Helper: create profile, save draft, publish, return publish response."""
    p = await client.post(
        "/api/profiles",
        json={"profile_name": profile_name, "company_note": ""},
    )
    assert p.status_code == 201, p.text
    pid = p.json()["id"]

    dr = await client.put(f"/api/profiles/{pid}/draft", json=VALID_DRAFT)
    assert dr.status_code == 200

    pub = await client.post(f"/api/profiles/{pid}/publish")
    assert pub.status_code == 201
    return pub.json()


@pytest.mark.asyncio
async def test_get_public_profile_by_token(auth_client: AsyncClient, client: AsyncClient):
    pub = await _publish_profile(auth_client, "Public Token Test")
    token = pub["token"]

    # Public endpoint — no auth
    resp = await client.get(f"/api/public/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["json_data"]["personal"]["full_name"] == "Public User"
    assert "profile_slug" in data
    assert data["version_number"] == 1


@pytest.mark.asyncio
async def test_public_endpoint_returns_correct_slug(auth_client: AsyncClient, client: AsyncClient):
    pub = await _publish_profile(auth_client, "Slug Check Profile")
    token = pub["token"]

    resp = await client.get(f"/api/public/{token}")
    assert resp.status_code == 200
    assert "slug-check-profile" in resp.json()["profile_slug"]


@pytest.mark.asyncio
async def test_public_endpoint_invalid_token(client: AsyncClient):
    resp = await client.get("/api/public/this-token-does-not-exist-at-all-abc123")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_url_matches_slug_token(auth_client: AsyncClient, client: AsyncClient):
    pub = await _publish_profile(auth_client, "URL Match Test")
    token = pub["token"]
    public_url = pub["public_url"]

    resp = await client.get(f"/api/public/{token}")
    assert resp.status_code == 200
    slug = resp.json()["profile_slug"]
    assert public_url == f"/{slug}-{token}"

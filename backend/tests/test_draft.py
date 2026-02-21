import json
import pytest
from httpx import AsyncClient

VALID_DRAFT = {
    "schema_version": 1,
    "personal": {
        "full_name": "John Doe",
        "title": "Software Engineer",
        "email": "john@example.com",
        "summary": "Experienced engineer with 8+ years in backend systems.",
    },
    "experience": [
        {
            "company": "Acme Corp",
            "position": "Senior Engineer",
            "start_date": "2020-01",
            "highlights": ["Led migration to microservices", "Reduced latency by 40%"],
        }
    ],
    "education": [
        {
            "institution": "MIT",
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "start_date": "2012-09",
            "end_date": "2016-06",
        }
    ],
    "skills": [{"category": "Backend", "items": ["Python", "Go", "PostgreSQL"]}],
    "projects": [],
    "languages": [{"language": "English", "proficiency": "Native"}],
    "certifications": [],
}


@pytest.mark.asyncio
async def test_save_and_get_draft(auth_client: AsyncClient):
    # Create profile first
    p = await auth_client.post(
        "/api/profiles", json={"profile_name": "Draft Test Profile", "company_note": ""}
    )
    assert p.status_code == 201
    pid = p.json()["id"]

    # Save draft
    r = await auth_client.put(f"/api/profiles/{pid}/draft", json=VALID_DRAFT)
    assert r.status_code == 200
    assert r.json()["draft"]["personal"]["full_name"] == "John Doe"

    # Get draft
    r2 = await auth_client.get(f"/api/profiles/{pid}/draft")
    assert r2.status_code == 200
    assert r2.json()["draft"]["personal"]["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_draft_not_found(auth_client: AsyncClient):
    p = await auth_client.post(
        "/api/profiles", json={"profile_name": "Empty Draft Profile", "company_note": ""}
    )
    pid = p.json()["id"]

    r = await auth_client.get(f"/api/profiles/{pid}/draft")
    assert r.status_code == 200
    assert r.json()["draft"] is None


@pytest.mark.asyncio
async def test_delete_draft(auth_client: AsyncClient):
    p = await auth_client.post(
        "/api/profiles", json={"profile_name": "Delete Draft Profile", "company_note": ""}
    )
    pid = p.json()["id"]

    await auth_client.put(f"/api/profiles/{pid}/draft", json=VALID_DRAFT)
    r = await auth_client.delete(f"/api/profiles/{pid}/draft")
    assert r.status_code == 200
    assert r.json()["deleted"] is True

    r2 = await auth_client.get(f"/api/profiles/{pid}/draft")
    assert r2.json()["draft"] is None


@pytest.mark.asyncio
async def test_draft_validation_rejects_invalid(auth_client: AsyncClient):
    p = await auth_client.post(
        "/api/profiles", json={"profile_name": "Validation Test", "company_note": ""}
    )
    pid = p.json()["id"]

    bad_draft = {**VALID_DRAFT, "personal": {"full_name": "", "title": "Dev", "email": "bad", "summary": "x"}}
    r = await auth_client.put(f"/api/profiles/{pid}/draft", json=bad_draft)
    assert r.status_code == 422

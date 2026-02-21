from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.redis_client import get_redis
from app.schemas.profile import (
    CreateProfileRequest,
    PublishResponse,
    UpdateProfileRequest,
)
from app.schemas.profile_data import ProfileData
from app.services.draft_service import DraftService
from app.services.profile_service import ProfileService
from app.services.publish_service import PublishService

router = APIRouter(prefix="/profiles", tags=["profiles"])


# ── Profile CRUD ──────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_profile(
    body: CreateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await ProfileService(db).create_profile(body, str(current_user.id))


@router.get("")
async def list_profiles(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await ProfileService(db).list_profiles(str(current_user.id))


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await ProfileService(db).get_profile(profile_id, str(current_user.id))


@router.patch("/{profile_id}")
async def update_profile(
    profile_id: str,
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await ProfileService(db).update_profile(profile_id, str(current_user.id), body)


# ── Draft (Redis) ─────────────────────────────────────────────────────────────

@router.get("/{profile_id}/draft")
async def get_draft(
    profile_id: str,
    redis: Redis = Depends(get_redis),
    current_user=Depends(get_current_user),
):
    draft = await DraftService(redis).get_draft(profile_id)
    if draft is None:
        return {"draft": None}
    return {"draft": draft}


@router.put("/{profile_id}/draft", status_code=200)
async def save_draft(
    profile_id: str,
    body: ProfileData,
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Ensure the profile belongs to the user before saving draft
    await ProfileService(db).get_profile(profile_id, str(current_user.id))
    saved = await DraftService(redis).save_draft(profile_id, body)
    return {"draft": saved}


@router.delete("/{profile_id}/draft", status_code=200)
async def delete_draft(
    profile_id: str,
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await ProfileService(db).get_profile(profile_id, str(current_user.id))
    existed = await DraftService(redis).delete_draft(profile_id)
    return {"deleted": existed}


# ── Publish (Postgres) ────────────────────────────────────────────────────────

@router.post("/{profile_id}/publish", response_model=PublishResponse, status_code=201)
async def publish_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user=Depends(get_current_user),
):
    draft_svc = DraftService(redis)
    publish_svc = PublishService(db, draft_svc)
    return await publish_svc.publish(profile_id, str(current_user.id))


@router.get("/{profile_id}/versions")
async def list_versions(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await ProfileService(db).list_versions(profile_id, str(current_user.id))

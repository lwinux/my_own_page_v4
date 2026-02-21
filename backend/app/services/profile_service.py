import re
import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.profile_version import ProfileVersion
from app.schemas.profile import CreateProfileRequest, UpdateProfileRequest

logger = structlog.get_logger(__name__)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text[:100] or "profile"


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_profile(self, data: CreateProfileRequest, user_id: str) -> dict:
        slug_base = slugify(data.profile_name)

        existing = await self.db.execute(
            select(Profile).where(
                Profile.user_id == uuid.UUID(user_id),
                Profile.profile_slug == slug_base,
                Profile.is_active.is_(True),
            )
        )
        if existing.scalar_one_or_none():
            slug_base = f"{slug_base}-{uuid.uuid4().hex[:6]}"

        profile = Profile(
            user_id=uuid.UUID(user_id),
            profile_name=data.profile_name,
            profile_slug=slug_base,
            company_note=data.company_note or "",
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        logger.info("profile_created", profile_id=str(profile.id), user_id=user_id)
        return self._serialize(profile)

    async def list_profiles(self, user_id: str) -> list[dict]:
        result = await self.db.execute(
            select(Profile)
            .options(selectinload(Profile.versions))
            .where(
                Profile.user_id == uuid.UUID(user_id),
                Profile.is_active.is_(True),
            )
            .order_by(Profile.created_at.desc())
        )
        profiles = result.scalars().all()
        return [self._serialize(p) for p in profiles]

    async def get_profile(self, profile_id: str, user_id: str) -> dict:
        profile = await self._fetch(profile_id, user_id)
        return self._serialize(profile, include_versions=True)

    async def update_profile(
        self, profile_id: str, user_id: str, data: UpdateProfileRequest
    ) -> dict:
        profile = await self._fetch(profile_id, user_id)

        if data.profile_name is not None:
            profile.profile_name = data.profile_name
            profile.profile_slug = slugify(data.profile_name)
        if data.company_note is not None:
            profile.company_note = data.company_note

        await self.db.commit()
        await self.db.refresh(profile)
        return self._serialize(profile, include_versions=True)

    async def list_versions(self, profile_id: str, user_id: str) -> list[dict]:
        profile = await self._fetch(profile_id, user_id)
        return [
            self._serialize_version(v, profile.profile_slug)
            for v in sorted(profile.versions, key=lambda x: x.version_number, reverse=True)
        ]

    # ── Internals ─────────────────────────────────────────────────────────────

    async def _fetch(self, profile_id: str, user_id: str) -> Profile:
        try:
            pid, uid = uuid.UUID(profile_id), uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ID format")

        result = await self.db.execute(
            select(Profile)
            .options(selectinload(Profile.versions))
            .where(
                Profile.id == pid,
                Profile.user_id == uid,
                Profile.is_active.is_(True),
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return profile

    def _serialize_version(self, v: ProfileVersion, slug: str) -> dict:
        return {
            "id": str(v.id),
            "version_number": v.version_number,
            "token": v.token,
            "created_at": v.created_at.isoformat(),
            "public_url": f"/{slug}-{v.token}",
        }

    def _serialize(self, profile: Profile, include_versions: bool = False) -> dict:
        versions = sorted(profile.versions, key=lambda v: v.version_number)
        latest = versions[-1] if versions else None

        data: dict = {
            "id": str(profile.id),
            "profile_name": profile.profile_name,
            "profile_slug": profile.profile_slug,
            "company_note": profile.company_note,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
            "latest_version": self._serialize_version(latest, profile.profile_slug)
            if latest
            else None,
        }
        if include_versions:
            data["versions"] = [
                self._serialize_version(v, profile.profile_slug) for v in reversed(versions)
            ]
        return data

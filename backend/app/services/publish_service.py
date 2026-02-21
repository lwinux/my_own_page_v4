import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.profile_version import ProfileVersion
from app.services.draft_service import DraftService
from app.utils.security import generate_publish_token

logger = structlog.get_logger(__name__)


class PublishService:
    def __init__(self, db: AsyncSession, draft_service: DraftService) -> None:
        self.db = db
        self.draft_service = draft_service

    async def publish(self, profile_id: str, user_id: str) -> dict:
        profile = await self._fetch_profile(profile_id, user_id)

        # Validate draft exists and conforms to schema
        profile_data = await self.draft_service.load_validated(profile_id)

        # Atomically get next version number
        result = await self.db.execute(
            select(func.coalesce(func.max(ProfileVersion.version_number), 0)).where(
                ProfileVersion.profile_id == profile.id
            )
        )
        next_version = (result.scalar() or 0) + 1

        token = generate_publish_token()

        version = ProfileVersion(
            profile_id=profile.id,
            version_number=next_version,
            token=token,
            json_data=profile_data.model_dump(),
        )
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)

        public_url = f"/{profile.profile_slug}-{token}"
        logger.info(
            "profile_published",
            profile_id=profile_id,
            version=next_version,
            token=token[:8] + "...",
        )
        return {
            "public_url": public_url,
            "token": token,
            "version_number": next_version,
            "version_id": str(version.id),
            "created_at": version.created_at.isoformat(),
        }

    async def get_public_by_token(self, token: str) -> dict:
        result = await self.db.execute(
            select(ProfileVersion, Profile)
            .join(Profile, ProfileVersion.profile_id == Profile.id)
            .where(ProfileVersion.token == token)
        )
        row = result.first()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile version not found",
            )
        version, profile = row
        return {
            "profile_slug": profile.profile_slug,
            "profile_name": profile.profile_name,
            "version_number": version.version_number,
            "created_at": version.created_at.isoformat(),
            "json_data": version.json_data,
        }

    async def _fetch_profile(self, profile_id: str, user_id: str) -> Profile:
        try:
            pid, uid = uuid.UUID(profile_id), uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ID format")

        result = await self.db.execute(
            select(Profile).where(
                Profile.id == pid,
                Profile.user_id == uid,
                Profile.is_active.is_(True),
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return profile

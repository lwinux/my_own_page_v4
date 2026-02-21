import json

import structlog
from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.schemas.profile_data import ProfileData

logger = structlog.get_logger(__name__)

_DRAFT_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days


class DraftService:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    def _key(self, profile_id: str) -> str:
        return f"draft:profile:{profile_id}"

    async def get_draft(self, profile_id: str) -> dict | None:
        raw = await self.redis.get(self._key(profile_id))
        if raw is None:
            return None
        return json.loads(raw)

    async def save_draft(self, profile_id: str, data: ProfileData) -> dict:
        payload = data.model_dump_json()
        await self.redis.setex(self._key(profile_id), _DRAFT_TTL_SECONDS, payload)
        logger.info("draft_saved", profile_id=profile_id)
        return data.model_dump()

    async def delete_draft(self, profile_id: str) -> bool:
        deleted = await self.redis.delete(self._key(profile_id))
        logger.info("draft_deleted", profile_id=profile_id, existed=bool(deleted))
        return bool(deleted)

    async def load_validated(self, profile_id: str) -> ProfileData:
        """Load draft and validate — raises 404 if not found."""
        raw = await self.get_draft(profile_id)
        if raw is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No draft found for this profile. Save a draft first.",
            )
        return ProfileData.model_validate(raw)

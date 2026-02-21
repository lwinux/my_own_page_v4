from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.profile import Profile
from app.models.profile_version import ProfileVersion
from app.schemas.public import PublicProfileResponse

router = APIRouter(tags=["public"])


@router.get("/public/{token}", response_model=PublicProfileResponse)
async def get_public_profile(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — no authentication required.
    Returns profile JSON data for frontend2 to render.
    """
    result = await db.execute(
        select(ProfileVersion, Profile)
        .join(Profile, ProfileVersion.profile_id == Profile.id)
        .where(ProfileVersion.token == token)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    version, profile = row
    return {
        "profile_slug": profile.profile_slug,
        "profile_name": profile.profile_name,
        "version_number": version.version_number,
        "created_at": version.created_at.isoformat(),
        "json_data": version.json_data,
    }

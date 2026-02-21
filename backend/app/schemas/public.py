from pydantic import BaseModel
from app.schemas.profile_data import ProfileData


class PublicProfileResponse(BaseModel):
    """Payload returned by GET /api/public/<token> — consumed by frontend2."""

    profile_slug: str
    profile_name: str
    version_number: int
    created_at: str
    json_data: ProfileData

from typing import Optional
from pydantic import BaseModel, field_validator


class CreateProfileRequest(BaseModel):
    profile_name: str
    company_note: Optional[str] = ""

    @field_validator("profile_name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("profile_name cannot be empty")
        if len(v) > 255:
            raise ValueError("profile_name must be ≤ 255 characters")
        return v

    @field_validator("company_note", mode="before")
    @classmethod
    def strip_note(cls, v: str | None) -> str:
        if v is None:
            return ""
        return v.strip()


class UpdateProfileRequest(BaseModel):
    profile_name: Optional[str] = None
    company_note: Optional[str] = None

    @field_validator("profile_name", mode="before")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("profile_name cannot be empty")
        return v

    @field_validator("company_note", mode="before")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip()


class VersionOut(BaseModel):
    id: str
    version_number: int
    token: str
    created_at: str
    public_url: str


class ProfileOut(BaseModel):
    id: str
    profile_name: str
    profile_slug: str
    company_note: str
    created_at: str
    updated_at: str
    latest_version: Optional[VersionOut] = None


class ProfileDetailOut(ProfileOut):
    versions: list[VersionOut] = []


class PublishResponse(BaseModel):
    public_url: str
    token: str
    version_number: int
    version_id: str
    created_at: str

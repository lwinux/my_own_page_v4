"""
ProfileData v1 — the canonical schema stored as JSON in profile_versions.json_data
and temporarily in Redis drafts.

Validation rules:
- All string fields are stripped of leading/trailing whitespace.
- Required string fields raise ValueError if empty after stripping.
- Date fields must match YYYY-MM format.
- Lists filter out empty strings / empty objects.
- schema_version is always forced to 1 (forward-compatibility hook).
"""
import re
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, field_validator, model_validator


_DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _require(v: str, field: str = "field") -> str:
    v = v.strip()
    if not v:
        raise ValueError(f"{field} cannot be empty")
    return v


def _validate_date(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    if v and not _DATE_RE.match(v):
        raise ValueError("Date must be in YYYY-MM format")
    return v or None


# ── Sub-models ────────────────────────────────────────────────────────────────

class PersonalInfo(BaseModel):
    full_name: str
    title: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    summary: str

    @field_validator("full_name", "title", "summary", mode="before")
    @classmethod
    def strip_required(cls, v: str) -> str:
        return _require(v)

    @field_validator("phone", "location", "linkedin", "github", "website", mode="before")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class ExperienceItem(BaseModel):
    company: str
    position: str
    start_date: str
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    highlights: list[str] = []

    @field_validator("company", "position", mode="before")
    @classmethod
    def strip_required(cls, v: str) -> str:
        return _require(v)

    @field_validator("start_date", mode="before")
    @classmethod
    def validate_start(cls, v: str) -> str:
        result = _validate_date(v)
        if result is None:
            raise ValueError("start_date is required")
        return result

    @field_validator("end_date", mode="before")
    @classmethod
    def validate_end(cls, v: str | None) -> str | None:
        return _validate_date(v)

    @field_validator("highlights", mode="before")
    @classmethod
    def filter_highlights(cls, v: list) -> list[str]:
        return [h.strip() for h in v if isinstance(h, str) and h.strip()]


class EducationItem(BaseModel):
    institution: str
    degree: str
    field: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    gpa: Optional[str] = None

    @field_validator("institution", "degree", mode="before")
    @classmethod
    def strip_required(cls, v: str) -> str:
        return _require(v)

    @field_validator("start_date", mode="before")
    @classmethod
    def validate_start(cls, v: str) -> str:
        result = _validate_date(v)
        if result is None:
            raise ValueError("start_date is required")
        return result

    @field_validator("end_date", mode="before")
    @classmethod
    def validate_end(cls, v: str | None) -> str | None:
        return _validate_date(v)


class SkillGroup(BaseModel):
    category: str
    items: list[str]

    @field_validator("category", mode="before")
    @classmethod
    def strip_category(cls, v: str) -> str:
        return _require(v)

    @field_validator("items", mode="before")
    @classmethod
    def filter_items(cls, v: list) -> list[str]:
        return [i.strip() for i in v if isinstance(i, str) and i.strip()]


class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    tech_stack: list[str] = []
    highlights: list[str] = []

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return _require(v)

    @field_validator("tech_stack", "highlights", mode="before")
    @classmethod
    def filter_list(cls, v: list) -> list[str]:
        return [s.strip() for s in v if isinstance(s, str) and s.strip()]


class LanguageItem(BaseModel):
    language: str
    proficiency: Literal["Native", "Fluent", "Advanced", "Intermediate", "Basic"]

    @field_validator("language", mode="before")
    @classmethod
    def strip_language(cls, v: str) -> str:
        return _require(v)


class CertificationItem(BaseModel):
    name: str
    issuer: str
    date: Optional[str] = None
    url: Optional[str] = None

    @field_validator("name", "issuer", mode="before")
    @classmethod
    def strip_required(cls, v: str) -> str:
        return _require(v)

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v: str | None) -> str | None:
        return _validate_date(v)


# ── Root schema ───────────────────────────────────────────────────────────────

class ProfileData(BaseModel):
    schema_version: Literal[1] = 1
    personal: PersonalInfo
    experience: list[ExperienceItem] = []
    education: list[EducationItem] = []
    skills: list[SkillGroup] = []
    projects: list[ProjectItem] = []
    languages: list[LanguageItem] = []
    certifications: list[CertificationItem] = []

    @model_validator(mode="before")
    @classmethod
    def ensure_schema_version(cls, data: dict) -> dict:
        if isinstance(data, dict):
            data.setdefault("schema_version", 1)
        return data

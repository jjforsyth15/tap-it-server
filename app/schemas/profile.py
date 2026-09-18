from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID

from app.models.profile import ProfileStatus
from app.models.enums import ContactType


class ProfileCreate(BaseModel):
    profile_name: str
    bio: str | None = None
    subtitle: str | None = Field(default=None, max_length=100)
    organization: str | None = Field(default=None, max_length=100)
    profile_status: ProfileStatus = ProfileStatus.active
    profile_image_url: str | None = None


class ProfileResponse(BaseModel):
    profile_id: UUID
    user_id: UUID
    profile_name: str
    bio: str | None = None
    subtitle: str | None = None
    organization: str | None = None
    profile_status: ProfileStatus
    profile_image_url: str | None = None
    display_order: int
    link_count: int = 0
    card_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileCreateResponse(BaseModel):
    message: str
    profile: ProfileResponse


class ProfileUpdate(BaseModel):
    profile_name: str | None = None
    bio: str | None = None
    subtitle: str | None = Field(default=None, max_length=100)
    organization: str | None = Field(default=None, max_length=100)
    profile_status: ProfileStatus | None = None
    profile_image_url: str | None = None

    @field_validator("profile_image_url", mode="before")
    @classmethod
    def empty_string_to_none(cls, value):
        if value == "":
            return None

        return value


class PublicProfileLinkResponse(BaseModel):
    label: str
    url: str

    class Config:
        from_attributes = True


class PublicProfileContactResponse(BaseModel):
    contact_type: ContactType
    label: str | None = None
    value: str
    is_primary: bool

    class Config:
        from_attributes = True


class PublicProfileResponse(BaseModel):
    profile_id: UUID
    profile_name: str
    bio: str | None = None
    subtitle: str | None = None
    organization: str | None = None
    profile_status: ProfileStatus
    profile_image_url: str | None = None
    links: list[PublicProfileLinkResponse] = Field(default_factory=list)
    contact_info: list[PublicProfileContactResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ProfileOrderUpdateItem(BaseModel):
    profile_id: UUID
    display_order: int


class ProfileOrderUpdateRequest(BaseModel):
    profiles: list[ProfileOrderUpdateItem]

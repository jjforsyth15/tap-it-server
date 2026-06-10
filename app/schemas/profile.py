from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID

from app.models.profile import ProfileStatus

class ProfileCreate(BaseModel):
    profile_name: str
    bio: str | None = None
    profile_status: ProfileStatus = ProfileStatus.active
    profile_image_url: str | None = None
    
class ProfileResponse(BaseModel):
    profile_id: UUID
    user_id: UUID
    profile_name: str
    bio: str | None = None
    profile_status: ProfileStatus
    profile_image_url: str | None = None
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
        
        
        
class PublicProfileResponse(BaseModel):
    profile_id: UUID
    profile_name: str
    bio: str | None = None
    profile_status: ProfileStatus
    profile_image_url: str | None = None
    links: list[PublicProfileLinkResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
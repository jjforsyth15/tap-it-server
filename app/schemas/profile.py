from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional

class ProfileCreate(BaseModel):
    profile_name: str
    bio: str | None = None
    
class ProfileResponse(BaseModel):
    profile_id: UUID
    user_id: UUID
    profile_name: str
    bio: str | None = None
    is_active: bool
    created_at: datetime    
    class Config:
        from_attributes = True
        
class ProfileCreateResponse(BaseModel):
    message: str
    profile: ProfileResponse
    
    
class ProfileUpdate(BaseModel):
    profile_name: Optional[str] = None
    bio: Optional[str] = None
    website_url: Optional[HttpUrl] = None
    
    @field_validator("website_url", mode="before")
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
    website_url: str | None = None
    links: list[PublicProfileLinkResponse] = []
    
    class Config:
        from_attributes = True
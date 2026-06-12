from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional


class ProfileLinkCreate(BaseModel):
    label: str
    url: HttpUrl
    
    @field_validator("url", mode="before")
    @classmethod
    def empty_string_to_none(cls, value):
        if value == "":
            return ValueError("URL cannot be empty")
        
        return value
    
    
class ProfileLinkResponse(BaseModel):
    link_id: UUID
    profile_id: UUID
    label: str
    url: HttpUrl
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        

class ProfileLinkUpdate(BaseModel):
    label: Optional[str] = None
    url: Optional[HttpUrl] = None
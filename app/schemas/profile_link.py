from urllib.parse import urlparse
from pydantic import BaseModel, HttpUrl, field_validator, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class ProfileLinkCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    url: str = Field(min_length=1, max_length=2048)
    
    @field_validator("url", mode="before")
    @classmethod       
    def validate_url(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("URL must begin with http:// or https://")
        
        value = value.strip()
        parsed_url = urlparse(value)
        
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("Invalid URL format. Must start with http:// or https://")
        
        return value    
    
class ProfileLinkResponse(BaseModel):
    link_id: UUID
    profile_id: UUID
    label: str
    url: HttpUrl
    display_order: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        

class ProfileLinkUpdate(BaseModel):
    label: Optional[str] = None
    url: Optional[HttpUrl] = None
    
    
class ProfileLinkOrderItem(BaseModel):
    link_id: UUID
    display_order: int
    
    
class ProfileLinkReorderRequest(BaseModel):
    links: list[ProfileLinkOrderItem]
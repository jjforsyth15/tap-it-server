from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

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
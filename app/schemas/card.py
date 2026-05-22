from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
class CardCreate(BaseModel):
    profile_id: UUID
    card_name: str
    
class CardResponse(BaseModel):
    card_id: UUID
    profile_id: UUID
    card_name: str
    card_code: str
    pointing_url: str
    card_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        
class CardCreateResponse(BaseModel):
    message: str
    card: CardResponse
    
    
class CardStatusUpdate(BaseModel):
    card_status: str
    

class PublicCardResponse(BaseModel):
    card_code: str
    card_name: str
    card_status: str
    profile_id: UUID | None = None
    
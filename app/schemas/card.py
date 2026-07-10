from app.models.card import CardStatus
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
class CardCreate(BaseModel):
    profile_id: UUID | None = None
    card_name: str
    
class CardUpdate(BaseModel):
    card_name: str | None = None
    profile_id: UUID | None = None
    card_status: CardStatus | None = None
    
class CardResponse(BaseModel):
    card_id: UUID
    profile_id: UUID | None = None
    card_name: str
    card_code: str
    pointing_url: str
    card_status: CardStatus
    created_at: datetime
    activated_at: datetime | None = None
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
class CardCreateResponse(BaseModel):
    message: str
    card: CardResponse
    
    
class CardStatusUpdate(BaseModel):
    card_status: CardStatus

class PublicCardResponse(BaseModel):
    card_code: str
    card_name: str
    card_status: CardStatus
    profile_id: UUID | None = None
    
    
class CardAdjustmentResponse(BaseModel):
    message: str
    card: CardResponse
    

class CardActivateRequest(BaseModel):
    card_code: str
    new_profile_id: UUID | None = None
    
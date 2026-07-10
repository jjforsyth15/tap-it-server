from app.models.card import CardStatus
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from app.models.beta_feedback import FeedbackType, FeedbackStatus

class FeedbackCreate(BaseModel):
    feedback_type: FeedbackType
    feedback_description: str
    page_url: str
    contact_info: str | None = None
    browser_info: str | None = None
    screen_size: str | None = None
    
class FeedbackResponse(BaseModel):
    feedback_id: UUID
    user_id: UUID | None = None
    feedback_type: FeedbackType
    feedback_description: str
    page_url: str
    contact_info: str | None = None
    browser_info: str | None = None
    screen_size: str | None = None
    feedback_status: FeedbackStatus
    created_at: datetime
    
    class Config:
        from_attributes = True
        
        
class FeedbackCreateResponse(BaseModel):
    message: str
    feedback: FeedbackResponse
    
    
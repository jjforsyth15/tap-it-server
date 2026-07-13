from app.models.card import CardStatus
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from app.models.beta_feedback import FeedbackType, FeedbackStatus

class FeedbackCreateRequest(BaseModel):
    feedback_type: FeedbackType
    feedback_description: str = Field(min_length=3, max_length=5000)
    page_url: str = Field(min_length=3, max_length=2048)
    contact_info: str | None = None
    browser_info: str | None = None
    screen_size: str | None = None
    version: str | None = None   
    
class FeedbackResponse(BaseModel):
    feedback_id: UUID
    user_id: UUID | None = None
    feedback_type: FeedbackType
    contact_info: str | None = None
    page_url: str
    feedback_description: str
    browser_info: str | None = None
    screen_size: str | None = None
    feedback_status: FeedbackStatus
    version: str | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        
        
class FeedbackCreateResponse(BaseModel):
    message: str
    feedback: FeedbackResponse
    
    
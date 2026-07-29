from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional

class DashboardSummaryResponse(BaseModel):
    total_users: int
    total_profiles: int
    total_cards: int
    active_cards: int
    inactive_cards: int
    lost_cards: int
    total_feedback: int
    open_feedback: int
    in_progress_feedback: int
    resolved_feedback: int

    class Config:
        from_attributes = True
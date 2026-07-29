from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

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
        
        
class AdminActivityType(str, Enum):
    USER_REGISTERED = "user_registered"
    PROFILE_CREATED = "profile_created"
    CARD_ACTIVATED = "card_activated"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    
class AdminRecentActivityItem(BaseModel):
    activity_type: AdminActivityType
    description: str
    created_at: datetime
    resource_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
class AdminRecentActivityResponse(BaseModel):
    activities: list[AdminRecentActivityItem]
    
    
class AdminActionItemType(str, Enum):
    PENDING_FEEDBACK = "pending_feedback"
    UNASSIGNED_CARDS = "unassigned_cards"
    LOST_CARDS = "lost_cards"
    INACTIVE_USERS = "inactive_users"
    CARD_REQUESTS = "card_requests"
    
class AdminActionItem(BaseModel):
    action_type: AdminActionItemType
    label: str
    count: int
    priority: str
    target_path: str | None = None
    
class AdminActionItemsResponse(BaseModel):
    action_items: list[AdminActionItem] = Field(default_factory=list)
    total_action_items: int
    
class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"  
class AdminDashboardHealthResponse(BaseModel):
    overall_status: HealthStatus
    database_status: HealthStatus
    api_status: HealthStatus
    environment: str
    version: str
    timestamp: datetime
    

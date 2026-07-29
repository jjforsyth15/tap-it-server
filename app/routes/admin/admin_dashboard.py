from fastapi import APIRouter, Depends, HTTPException, Query
import pydantic
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.card import Card
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.schemas.admin.admin_dashboard import AdminActionItemsResponse, DashboardSummaryResponse, AdminRecentActivityResponse, AdminDashboardHealthResponse
from app.core.dependencies import require_admin
from app.models.beta_feedback import BetaFeedback
from app.models.enums import CardStatus, FeedbackStatus
from app.services.admin.admin_dashboard_service import get_recent_activity, get_admin_action_items, get_admin_dashboard_health

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])

# Get the admin dashboard summary - GET /admin/dashboard/summary - protected route
@router.get("/summary", response_model=DashboardSummaryResponse)
def admin_dashboard_summary(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    response = DashboardSummaryResponse(
        total_users=db.query(User).count(),
        total_profiles=db.query(Profile).count(),
        total_cards=db.query(Card).count(),
        active_cards=db.query(Card).filter(Card.card_status == CardStatus.active).count(),
        inactive_cards=db.query(Card).filter(Card.card_status == CardStatus.inactive).count(),
        lost_cards=db.query(Card).filter(Card.card_status == CardStatus.lost).count(),
        total_feedback=db.query(BetaFeedback).count(),
        open_feedback=db.query(BetaFeedback).filter(BetaFeedback.feedback_status == FeedbackStatus.open).count(),
        in_progress_feedback=db.query(BetaFeedback).filter(BetaFeedback.feedback_status == FeedbackStatus.in_progress).count(),
        resolved_feedback=db.query(BetaFeedback).filter(BetaFeedback.feedback_status == FeedbackStatus.resolved).count()
    )   
    
    return response


@router.get("/recent-activity", response_model=AdminRecentActivityResponse)
def recent_activity(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> AdminRecentActivityResponse:
    activities = get_recent_activity(db, limit)
    
    return AdminRecentActivityResponse(activities=activities)
    
    
# Get admin dashboard action items - GET /admin/dashboard/action-items - protected route
@router.get("/action-items")
def action_items(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> AdminActionItemsResponse:
    items = get_admin_action_items(db)
    
    return AdminActionItemsResponse(
        action_items=items,
        total_action_items=sum(item.count for item in items)
    )
    
    
@router.get("/health", response_model=AdminDashboardHealthResponse)
def health_check(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> AdminDashboardHealthResponse:
    return get_admin_dashboard_health(db)
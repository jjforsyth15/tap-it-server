from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.card import Card
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.schemas.admin.admin_dashboard import DashboardSummaryResponse
from app.core.dependencies import require_admin
from app.models.beta_feedback import BetaFeedback
from app.models.enums import CardStatus, FeedbackStatus

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])

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
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
import uuid
from app.models.beta_feedback import BetaFeedback, FeedbackStatus
from app.schemas.beta import FeedbackCreateRequest, FeedbackCreateResponse
from app.core.dependencies import get_current_user_optional
from app.models.user import User

from app.core.rate_limiter import limiter

router = APIRouter(prefix="/beta", tags=["beta"])

@router.post("/feedback", response_model=FeedbackCreateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def create_feedback(
    request: Request,
    feedback_data: FeedbackCreateRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    new_feedback = BetaFeedback(
        feedback_id=uuid.uuid4(),
        user_id=current_user.user_id if current_user else None,
        feedback_type=feedback_data.feedback_type,
        contact_info=feedback_data.contact_info,
        page_url=feedback_data.page_url,
        feedback_description=feedback_data.feedback_description.strip(),
        browser_info=feedback_data.browser_info,
        screen_size=feedback_data.screen_size,
        version=feedback_data.version,
        feedback_status=FeedbackStatus.open,
    )
    
    db.add(new_feedback)
    
    try:
        db.commit()
        db.refresh(new_feedback)
    except Exception:
        db.rollback()
        raise
    
    return {
        "message": "Feedback submitted successfully",
        "feedback": new_feedback
    }
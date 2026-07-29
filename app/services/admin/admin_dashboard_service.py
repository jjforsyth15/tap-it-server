from app.models.beta_feedback import BetaFeedback
from app.models.card import Card
from app.models.profile import Profile
from app.models.user import User
from app.schemas.admin.admin_dashboard import AdminActivityType, AdminRecentActivityItem, AdminActionItemType, AdminActionItem, AdminDashboardHealthResponse, HealthStatus
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models.enums import CardStatus, FeedbackStatus
from datetime import datetime, timezone
import os


def get_recent_activity(db: Session, limit: int = 10) -> list[AdminRecentActivityItem]:
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    profiles = db.query(Profile).order_by(Profile.created_at.desc()).limit(limit).all()
    activated_cards = db.query(Card).filter(Card.card_status == CardStatus.active).order_by(Card.created_at.desc()).limit(limit).all()
    feedback = db.query(BetaFeedback).order_by(BetaFeedback.created_at.desc()).limit(limit).all()
    
    activities: list[AdminRecentActivityItem] = []
    
    for user in users:
        activities.append(AdminRecentActivityItem(
            activity_type=AdminActivityType.USER_REGISTERED,
            description="A new user registered.",
            created_at=user.created_at,
            resource_id=user.user_id,
            metadata={
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                },
        ))
        
    for profile in profiles:
        activities.append(AdminRecentActivityItem(
            activity_type=AdminActivityType.PROFILE_CREATED,
            description="A new profile was created.",
            created_at=profile.created_at,
            resource_id=profile.profile_id,
            metadata={
                "user_id": str(profile.user_id),
                "profile_name": profile.profile_name,
                },
        ))
        
    for card in activated_cards:
        activities.append(AdminRecentActivityItem(
            activity_type=AdminActivityType.CARD_ACTIVATED,
            description="A new card was activated.",
            created_at=card.created_at,
            resource_id=card.card_id,
            metadata={
                "card_name": card.card_name,
                "profile_id": (card.profile_id if card.profile_id is not None else None),
                },
        ))
        
    for feedback in feedback:
        activities.append(AdminRecentActivityItem(
            activity_type=AdminActivityType.FEEDBACK_SUBMITTED,
            description="A new feedback was submitted.",
            created_at=feedback.created_at,
            resource_id=feedback.feedback_id,
            metadata={
                "feedback_type": feedback.feedback_type,
                "feedback_status": feedback.feedback_status,
                },
        ))
        
    activities.sort(key=lambda activity: activity.created_at, reverse=True)
    
    return activities[:limit]


def get_admin_action_items(db: Session,) -> list[AdminActionItem]:
    action_items: list[AdminActionItem] = []
    
    pending_feedback_count = db.query(func.count(BetaFeedback.feedback_id)).filter(BetaFeedback.feedback_status == FeedbackStatus.open).scalar() or 0
    unassigned_cards_count = db.query(func.count(Card.card_id)).filter(Card.profile_id == None).scalar() or 0
    lost_cards_count = db.query(func.count(Card.card_id)).filter(Card.card_status == CardStatus.lost).scalar() or 0
    inactive_users = db.query(func.count(User.user_id)).filter(User.is_active == False).scalar() or 0
    # Add card requests count 
    
    if pending_feedback_count > 0:
        action_items.append(AdminActionItem(
            action_type=AdminActionItemType.PENDING_FEEDBACK,
            label="Pending Feedback",
            count=pending_feedback_count,
            priority="high",
            target_path="/admin/feedback"
        ))
        
    if unassigned_cards_count > 0:
        action_items.append(AdminActionItem(
            action_type=AdminActionItemType.UNASSIGNED_CARDS,
            label="Unassigned Cards",
            count=unassigned_cards_count,
            priority="medium",
            target_path="/admin/cards"
        ))
        
    if lost_cards_count > 0:
        action_items.append(AdminActionItem(
            action_type=AdminActionItemType.LOST_CARDS,
            label="Lost Cards",
            count=lost_cards_count,
            priority="medium",
            target_path="/admin/cards"
        ))
        
    if inactive_users > 0:
        action_items.append(AdminActionItem(
            action_type=AdminActionItemType.INACTIVE_USERS,
            label="Inactive Users",
            count=inactive_users,
            priority="low",
            target_path="/admin/users"
        ))
        
    priority_order = {"high": 0, "medium": 1, "low": 2,}
    
    action_items.sort(
        key=lambda item: (
            priority_order.get(item.priority, 99), 
            -item.count
        )
    )
    
    return action_items

def get_admin_dashboard_health(db: Session) -> AdminDashboardHealthResponse:
    database_status = HealthStatus.HEALTHY
    environment = os.getenv("ENVIRONMENT", "development")
    version = os.getenv("APP_VERSION", "1.0.0-beta1")
    
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = HealthStatus.UNHEALTHY
        
    overall_status = HealthStatus.HEALTHY if database_status == HealthStatus.HEALTHY else HealthStatus.DEGRADED
    
    return AdminDashboardHealthResponse(
        overall_status=overall_status,
        database_status=database_status,
        api_status=HealthStatus.HEALTHY,
        version=version,
        environment=environment,
        timestamp=datetime.now(timezone.utc)
    )
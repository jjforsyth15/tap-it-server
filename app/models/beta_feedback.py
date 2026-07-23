import uuid
import enum
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base 


class FeedbackType(enum.Enum):
    bug = "bug"
    suggestion = "suggestion"
    other = "other"
    
class FeedbackStatus(enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    

class BetaFeedback(Base):
    __tablename__ = "beta_feedback"
    
    feedback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    feedback_type: Mapped[FeedbackType] = mapped_column(
        Enum(FeedbackType),
        nullable=False
    )
    contact_info: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    page_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False
    )
    feedback_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=False
    )
    browser_info: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    screen_size: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    feedback_status: Mapped[FeedbackStatus] = mapped_column(
        Enum(FeedbackStatus),
        nullable=False,
        default=FeedbackStatus.open
    )
    version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    user = relationship("User", back_populates="beta_feedback")
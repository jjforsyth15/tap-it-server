import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base 

class Card(Base):
    __tablename__ = "cards"
    
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.profile_id", ondelete="CASCADE"),
        nullable=False
    )
    card_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    pointing_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=False,
        default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    profile = relationship("Profile", back_populates="cards")
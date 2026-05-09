import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, Text, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base 


class CardStatus(str, enum.Enum):
    inactive = "inactive"
    active = "active"
    deactivated = "deactivated"
    lost = "lost"
    disabled = "disabled"
    
class Card(Base):
    __tablename__ = "cards"
    
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.profile_id", ondelete="CASCADE"),
        nullable=True
    )
    card_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    card_code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False
    )
    pointing_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False
    )
    card_status: Mapped[CardStatus] = mapped_column(
        Enum(CardStatus, name="card_status"),
        nullable=False,
        default=CardStatus.inactive
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    profile = relationship("Profile", back_populates="cards")
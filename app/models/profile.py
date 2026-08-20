import enum
import uuid
from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, Text, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.enums import ProfileStatus

from app.db.base import Base

class Profile(Base):
    __tablename__ = "profiles"
    
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True
        )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
        )
    profile_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
        )
    bio: Mapped[str] = mapped_column(
        Text(), 
        nullable=True
        )    
    profile_status: Mapped[ProfileStatus] = mapped_column(
        Enum(ProfileStatus, name="profile_status"), 
        nullable=False, 
        default=ProfileStatus.active
        )
    profile_image_url: Mapped[str | None] = mapped_column(
        String(), 
        nullable=True
        )
    display_order: Mapped[int] = mapped_column(
        Integer(), 
        nullable=False, 
        default=0
        )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    
    user = relationship("User", back_populates="profiles")
    cards = relationship("Card", back_populates="profile")
    links = relationship("ProfileLink", back_populates="profile", cascade="all, delete-orphan", order_by="ProfileLink.display_order.asc()")
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    instagram_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=True
    )
    website_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=True
    )
    
    user = relationship("User", back_populates="profiles")
    cards = relationship("Card", back_populates="profile", cascade="all, delete-orphan")
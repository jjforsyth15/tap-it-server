import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.enums import UserType

from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True
        )
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False
        )
    phone_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=True
        )
    password_hash: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
        )
    first_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
        )
    last_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
        )
    is_verified: Mapped[bool] = mapped_column(
        Boolean(), 
        nullable=False, 
        default=False
        )
    is_active: Mapped[bool] = mapped_column(
        Boolean(), 
        nullable=False, 
        default=True
        )
    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=UserType.USER
        )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    profiles = relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    beta_feedback = relationship("BetaFeedback", back_populates="user", passive_deletes=True)
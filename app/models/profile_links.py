import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base 

class ProfileLink(Base):
    __tablename__ = "profile_links"
    
    link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True,
        default=uuid.uuid4
        )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("profiles.profile_id", ondelete="CASCADE"),
        nullable=False
        )
    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False
        )
    url: Mapped[str] = mapped_column(
        String(2048), 
        nullable=False
        )  
    display_order: Mapped[int] = mapped_column(
        Integer,
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

    profile = relationship("Profile", back_populates="links")    

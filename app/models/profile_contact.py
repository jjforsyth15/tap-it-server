import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, func, Integer, Boolean, Enum, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.enums import ContactType

from app.db.base import Base


class ProfileContact(Base):
    __tablename__ = "profile_contacts"
    __table_args__ = (
        # enforces "at most one primary per (profile, contact_type)" at the
        # database level -- the service layer's check-then-act logic can't
        # guarantee this alone under concurrent requests
        Index(
            "ix_profile_contacts_single_primary",
            "profile_id",
            "contact_type",
            unique=True,
            postgresql_where=text("is_primary"),
        ),
    )

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.profile_id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_type: Mapped[ContactType] = mapped_column(
        Enum(ContactType, name="contact_type"), nullable=False
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    profile = relationship("Profile", back_populates="contact_info")

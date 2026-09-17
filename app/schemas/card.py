from app.models.card import CardStatus
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime


class CardCreate(BaseModel):
    profile_id: UUID | None = None
    card_name: str


class CardUpdate(BaseModel):
    card_name: str | None = None

    @field_validator("card_name")
    @classmethod
    def validate_card_name(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("card_name cannot be null")
        if not value:
            raise ValueError("Card name must be at least 1 character")
        if len(value) > 50:
            raise ValueError("Card name must be 50 characters or less")
        return value


class CardResponse(BaseModel):
    card_id: UUID
    profile_id: UUID | None = None
    card_name: str
    card_code: str
    card_status: CardStatus
    created_at: datetime
    activated_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


class CardCreateResponse(BaseModel):
    message: str
    card: CardResponse


class CardStatusUpdate(BaseModel):
    card_status: CardStatus


class PublicCardResponse(BaseModel):
    card_code: str
    card_name: str
    card_status: CardStatus
    profile_id: UUID | None = None


class CardAdjustmentResponse(BaseModel):
    message: str
    card: CardResponse


class CardActivateRequest(BaseModel):
    new_profile_id: UUID | None = None


class CardReactivateRequest(BaseModel):
    new_profile_id: UUID | None = None



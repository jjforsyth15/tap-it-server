from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from uuid import UUID
from typing import Optional
import phonenumbers
from email_validator import validate_email, EmailNotValidError

from app.models.enums import ContactType


# shared phone/email format validation, used by ProfileContactCreate directly
# and by the update path (which can't use a field_validator since contact_type
# isn't part of the update payload -- it's immutable after creation)
def normalize_contact_value(
    contact_type: ContactType, value: str, region: str | None = None
) -> str:
    if contact_type == ContactType.phone:
        if not region:
            raise ValueError("A region is required to validate a phone number.")

        try:
            parsed = phonenumbers.parse(value, region)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number.")

        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number.")

        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    if contact_type == ContactType.email:
        try:
            result = validate_email(value, check_deliverability=False)
        except EmailNotValidError as exc:
            raise ValueError(str(exc))

        return result.normalized

    raise ValueError("Unsupported contact type.")


class ProfileContactCreate(BaseModel):
    contact_type: ContactType
    region: Optional[str] = None
    label: Optional[str] = Field(default=None, max_length=255)
    value: str = Field(min_length=1, max_length=255)
    is_primary: bool = False

    @model_validator(mode="after")
    def normalize_value(self):
        self.value = normalize_contact_value(self.contact_type, self.value, self.region)
        return self


class ProfileContactResponse(BaseModel):
    contact_id: UUID
    profile_id: UUID
    contact_type: ContactType
    label: Optional[str] = None
    value: str
    is_primary: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileContactUpdate(BaseModel):
    label: Optional[str] = Field(default=None, max_length=255)
    value: Optional[str] = Field(default=None, min_length=1, max_length=255)
    region: Optional[str] = None
    is_primary: Optional[bool] = None


class ProfileContactOrderItem(BaseModel):
    contact_id: UUID
    display_order: int


class ProfileContactReorderRequest(BaseModel):
    contacts: list[ProfileContactOrderItem]

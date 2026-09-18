from pydantic import BaseModel, Field, field_validator, model_validator
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

    # value/is_primary back non-nullable columns -- unlike label, explicitly
    # sending null for either isn't a valid "clear this" instruction, so reject
    # it here instead of letting it reach the database as an IntegrityError.
    # This validator only runs when the field is actually present in the
    # payload (Pydantic doesn't validate an omitted field's default), so
    # simply not sending the field still means "leave unchanged".
    @field_validator("value", "is_primary", mode="before")
    @classmethod
    def reject_explicit_null(cls, value, info):
        if value is None:
            raise ValueError(f"{info.field_name} cannot be set to null.")
        return value


class ProfileContactOrderItem(BaseModel):
    contact_id: UUID
    # bounded to fit Postgres's 4-byte INTEGER column -- an unbounded Python
    # int (e.g. 10**100) would otherwise pass validation here and only fail
    # at commit time as an unhandled 500
    display_order: int = Field(ge=0, le=2147483647)


class ProfileContactReorderRequest(BaseModel):
    # capped so one request can't force an unbounded number of downstream
    # database lookups in the route
    contacts: list[ProfileContactOrderItem] = Field(min_length=1, max_length=100)

    @field_validator("contacts")
    @classmethod
    def reject_duplicate_contact_ids(cls, contacts):
        contact_ids = [item.contact_id for item in contacts]
        if len(contact_ids) != len(set(contact_ids)):
            raise ValueError("Duplicate contact_id values are not allowed.")
        return contacts

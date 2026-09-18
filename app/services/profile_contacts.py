from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.profile_contact import ProfileContact
from app.models.enums import ContactType
from app.schemas.profile_contact import ProfileContactCreate, normalize_contact_value


# un-set is_primary on every other contact of this type for this profile
def enforce_single_primary(
    profile_id: UUID, contact_type: ContactType, keep_contact_id: UUID, db: Session
) -> None:
    db.query(ProfileContact).filter(
        ProfileContact.profile_id == profile_id,
        ProfileContact.contact_type == contact_type,
        ProfileContact.contact_id != keep_contact_id,
    ).update({ProfileContact.is_primary: False}, synchronize_session=False)


def has_contact_of_type(profile_id: UUID, contact_type: ContactType, db: Session) -> bool:
    return (
        db.query(ProfileContact)
        .filter(
            ProfileContact.profile_id == profile_id,
            ProfileContact.contact_type == contact_type,
        )
        .first()
        is not None
    )


# build, add, and flush a new ProfileContact, applying the primary business
# rules: the first contact of a type auto-becomes primary, and marking any
# contact primary un-sets every other primary of that type on the profile.
# The database also enforces "at most one primary per (profile, type)" via a
# partial unique index, since the has_contact_of_type()-then-insert check above
# is a check-then-act race under concurrent requests -- the flush here is what
# actually proves the invariant held; the route still owns the final commit.
def build_new_contact(
    profile_id: UUID, contact_data: ProfileContactCreate, db: Session
) -> ProfileContact:
    is_primary = contact_data.is_primary or not has_contact_of_type(
        profile_id, contact_data.contact_type, db
    )

    contact = ProfileContact(
        contact_id=uuid4(),
        profile_id=profile_id,
        contact_type=contact_data.contact_type,
        label=contact_data.label,
        value=contact_data.value,
        is_primary=is_primary,
    )

    if is_primary:
        # unset any existing primary of this type BEFORE inserting the new
        # row, so the two statements never both see "primary" at once within
        # this transaction
        enforce_single_primary(
            profile_id, contact_data.contact_type, contact.contact_id, db
        )

    db.add(contact)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Another contact of this type was just set as primary for this profile. Please retry.",
        )

    return contact


# apply a validated update payload (ProfileContactUpdate.model_dump(exclude_unset=True))
# to an existing contact -- contact_type is immutable, so "value" is re-normalized
# against the contact's existing type rather than a type carried in the payload
def apply_contact_update(contact: ProfileContact, update_data: dict, db: Session) -> None:
    region = update_data.pop("region", None)

    if update_data.get("value") is not None:
        try:
            update_data["value"] = normalize_contact_value(
                contact.contact_type, update_data["value"], region
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    # unset any other primary of this type BEFORE this contact's own
    # is_primary is set, so autoflush never briefly sees two primaries at once
    if update_data.get("is_primary") is True:
        enforce_single_primary(
            contact.profile_id, contact.contact_type, contact.contact_id, db
        )

    for key, value in update_data.items():
        setattr(contact, key, value)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Another contact of this type was just set as primary for this profile. Please retry.",
        )
